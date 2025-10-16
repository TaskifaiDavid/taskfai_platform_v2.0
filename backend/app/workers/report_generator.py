"""
Report generator for PDF, CSV, and Excel exports
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
import asyncpg
from uuid import UUID
import io
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import pandas as pd


class ReportGenerator:
    """Generate sales reports in multiple formats"""

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize report generator

        Args:
            db_pool: Database connection pool for tenant database
        """
        self.db_pool = db_pool

    async def generate_report(
        self,
        user_id: UUID,
        format: str,  # 'pdf', 'csv', 'excel'
        channel: str = 'all',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        reseller: Optional[str] = None,
        product: Optional[str] = None
    ) -> bytes:
        """
        Generate sales report in specified format

        Args:
            user_id: User ID for RLS filtering
            format: Output format ('pdf', 'csv', 'excel')
            channel: Sales channel filter
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            reseller: Reseller filter (optional)
            product: Product filter (optional)

        Returns:
            Report file as bytes
        """
        # Fetch sales data
        sales_data = await self._fetch_sales_data(
            user_id, channel, start_date, end_date, reseller, product
        )

        if format == 'pdf':
            return self._generate_pdf(sales_data, channel, start_date, end_date)
        elif format == 'csv':
            return self._generate_csv(sales_data)
        elif format == 'excel':
            return self._generate_excel(sales_data)
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def _fetch_sales_data(
        self,
        user_id: UUID,
        channel: str,
        start_date: Optional[date],
        end_date: Optional[date],
        reseller: Optional[str],
        product: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fetch sales data for report"""

        async with self.db_pool.acquire() as conn:
            await conn.execute("SET LOCAL app.current_user_id = $1", str(user_id))

            sales = []

            if channel in ('offline', 'all'):
                offline = await self._fetch_offline_sales(
                    conn, start_date, end_date, reseller, product
                )
                sales.extend(offline)

            if channel in ('online', 'all'):
                online = await self._fetch_online_sales(
                    conn, start_date, end_date, product
                )
                sales.extend(online)

            return sales

    async def _fetch_offline_sales(
        self,
        conn: asyncpg.Connection,
        start_date: Optional[date],
        end_date: Optional[date],
        reseller: Optional[str],
        product: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fetch offline sales for report"""

        filters = []
        params = []
        param_count = 0

        if start_date and end_date:
            param_count += 1
            filters.append(f"make_date(year, month, 1) >= ${param_count}")
            params.append(start_date)
            param_count += 1
            filters.append(f"make_date(year, month, 1) <= ${param_count}")
            params.append(end_date)

        if reseller:
            param_count += 1
            filters.append(f"reseller ILIKE ${param_count}")
            params.append(f"%{reseller}%")

        if product:
            param_count += 1
            filters.append(f"functional_name ILIKE ${param_count}")
            params.append(f"%{product}%")

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        query = f"""
            SELECT
                make_date(year, month, 1) as date,
                functional_name as product_name,
                product_ean,
                reseller,
                sales_eur as revenue,
                quantity,
                currency,
                'Offline (B2B)' as channel
            FROM sellout_entries2
            {where_clause}
            ORDER BY year DESC, month DESC
            LIMIT 10000
        """

        rows = await conn.fetch(query, *params)

        return [
            {
                'Date': row['date'].isoformat(),
                'Product': row['product_name'],
                'EAN': row['product_ean'] or 'N/A',
                'Reseller': row['reseller'],
                'Revenue (EUR)': f"{float(row['revenue']):.2f}",
                'Quantity': row['quantity'],
                'Currency': row['currency'],
                'Channel': row['channel']
            }
            for row in rows
        ]

    async def _fetch_online_sales(
        self,
        conn: asyncpg.Connection,
        start_date: Optional[date],
        end_date: Optional[date],
        product: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fetch online sales for report"""

        filters = []
        params = []
        param_count = 0

        if start_date:
            param_count += 1
            filters.append(f"order_date >= ${param_count}")
            params.append(start_date)

        if end_date:
            param_count += 1
            filters.append(f"order_date <= ${param_count}")
            params.append(end_date)

        if product:
            param_count += 1
            filters.append(f"functional_name ILIKE ${param_count}")
            params.append(f"%{product}%")

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        query = f"""
            SELECT
                order_date as date,
                functional_name as product_name,
                product_ean,
                sales_eur as revenue,
                quantity,
                country,
                'Online (D2C)' as channel
            FROM ecommerce_orders
            {where_clause}
            ORDER BY order_date DESC
            LIMIT 10000
        """

        rows = await conn.fetch(query, *params)

        return [
            {
                'Date': row['date'].isoformat(),
                'Product': row['product_name'],
                'EAN': row['product_ean'] or 'N/A',
                'Reseller': 'Direct',
                'Revenue (EUR)': f"{float(row['revenue']):.2f}",
                'Quantity': row['quantity'],
                'Currency': 'EUR',
                'Channel': row['channel']
            }
            for row in rows
        ]

    def _generate_pdf(
        self,
        sales_data: List[Dict[str, Any]],
        channel: str,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> bytes:
        """Generate PDF report using ReportLab"""

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        # Title
        title = Paragraph("TaskifAI Sales Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))

        # Report info
        info_style = styles['Normal']
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        info = Paragraph(f"<b>Generated:</b> {report_date}<br/>"
                        f"<b>Channel:</b> {channel.title()}<br/>"
                        f"<b>Period:</b> {start_date or 'All'} to {end_date or 'All'}",
                        info_style)
        elements.append(info)
        elements.append(Spacer(1, 0.3*inch))

        # Summary statistics
        if sales_data:
            total_revenue = sum(float(sale['Revenue (EUR)']) for sale in sales_data)
            total_quantity = sum(sale['Quantity'] for sale in sales_data)

            summary = Paragraph(
                f"<b>Summary:</b> {len(sales_data)} transactions | "
                f"Total Revenue: €{total_revenue:,.2f} | "
                f"Total Units: {total_quantity:,}",
                info_style
            )
            elements.append(summary)
            elements.append(Spacer(1, 0.3*inch))

        # Table data
        if sales_data:
            # Prepare table data
            table_data = [list(sales_data[0].keys())]  # Headers
            for sale in sales_data[:100]:  # Limit to 100 rows for PDF
                table_data.append(list(sale.values()))

            # Create table
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(table)
        else:
            elements.append(Paragraph("No data available for the selected filters.", info_style))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.read()

    def _generate_csv(self, sales_data: List[Dict[str, Any]]) -> bytes:
        """Generate CSV report"""

        if not sales_data:
            return b"No data available"

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=sales_data[0].keys())
        writer.writeheader()
        writer.writerows(sales_data)

        return buffer.getvalue().encode('utf-8')

    def _generate_excel(self, sales_data: List[Dict[str, Any]]) -> bytes:
        """Generate Excel report using pandas"""

        if not sales_data:
            # Return empty Excel
            buffer = io.BytesIO()
            pd.DataFrame().to_excel(buffer, index=False)
            buffer.seek(0)
            return buffer.read()

        # Create DataFrame
        df = pd.DataFrame(sales_data)

        # Generate Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sales Report', index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets['Sales Report']
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

        buffer.seek(0)
        return buffer.read()
