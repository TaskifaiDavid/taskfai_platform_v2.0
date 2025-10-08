"""
KPI calculator for analytics dashboard
"""

from typing import Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
import asyncpg
from uuid import UUID


class KPICalculator:
    """Calculate key performance indicators for sales analytics"""

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize KPI calculator

        Args:
            db_pool: Database connection pool for tenant database
        """
        self.db_pool = db_pool

    async def calculate_kpis(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        channel: Optional[str] = None  # 'offline', 'online', or None for all
    ) -> Dict[str, Any]:
        """
        Calculate KPIs for a date range

        Args:
            user_id: User ID for RLS filtering
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            channel: Sales channel filter (optional)

        Returns:
            Dictionary with KPI metrics
        """
        async with self.db_pool.acquire() as conn:
            # Set user context for RLS
            await conn.execute("SET LOCAL app.current_user_id = $1", str(user_id))

            # Calculate offline (B2B) KPIs
            offline_kpis = await self._calculate_offline_kpis(
                conn, start_date, end_date
            ) if channel in (None, 'offline') else {}

            # Calculate online (D2C) KPIs
            online_kpis = await self._calculate_online_kpis(
                conn, start_date, end_date
            ) if channel in (None, 'online') else {}

            # Calculate combined KPIs
            total_revenue = Decimal(0)
            total_units = 0

            if offline_kpis:
                total_revenue += offline_kpis.get('total_revenue', Decimal(0))
                total_units += offline_kpis.get('total_units', 0)

            if online_kpis:
                total_revenue += online_kpis.get('total_revenue', Decimal(0))
                total_units += online_kpis.get('total_units', 0)

            return {
                'total_revenue': float(total_revenue),
                'total_units': total_units,
                'average_order_value': float(total_revenue / total_units) if total_units > 0 else 0,
                'offline': offline_kpis,
                'online': online_kpis,
                'date_range': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            }

    async def _calculate_offline_kpis(
        self,
        conn: asyncpg.Connection,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict[str, Any]:
        """Calculate offline (B2B) sales KPIs"""

        # Build date filter
        date_filter = ""
        params = []

        if start_date and end_date:
            # Convert month/year to date range
            date_filter = """
                AND (
                    make_date(year, month, 1) >= $1
                    AND make_date(year, month, 1) <= $2
                )
            """
            params = [start_date, end_date]

        query = f"""
            SELECT
                COUNT(*) as transaction_count,
                SUM(sales_eur) as total_revenue,
                SUM(quantity) as total_units,
                AVG(sales_eur) as avg_transaction_value,
                COUNT(DISTINCT reseller_id) as unique_resellers,
                COUNT(DISTINCT product_id) as unique_products
            FROM sellout_entries2
            WHERE 1=1 {date_filter}
        """

        row = await conn.fetchrow(query, *params)

        return {
            'transaction_count': row['transaction_count'] or 0,
            'total_revenue': row['total_revenue'] or Decimal(0),
            'total_units': row['total_units'] or 0,
            'avg_transaction_value': float(row['avg_transaction_value'] or 0),
            'unique_resellers': row['unique_resellers'] or 0,
            'unique_products': row['unique_products'] or 0
        }

    async def _calculate_online_kpis(
        self,
        conn: asyncpg.Connection,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict[str, Any]:
        """Calculate online (D2C) sales KPIs"""

        # Build date filter
        date_filter = ""
        params = []

        if start_date and end_date:
            date_filter = "AND order_date >= $1 AND order_date <= $2"
            params = [start_date, end_date]

        query = f"""
            SELECT
                COUNT(*) as order_count,
                SUM(sales_eur) as total_revenue,
                SUM(quantity) as total_units,
                AVG(sales_eur) as avg_order_value,
                SUM(cost_of_goods) as total_cogs,
                SUM(stripe_fee) as total_fees,
                COUNT(DISTINCT country) as unique_countries
            FROM ecommerce_orders
            WHERE 1=1 {date_filter}
        """

        row = await conn.fetchrow(query, *params)

        total_revenue = row['total_revenue'] or Decimal(0)
        total_cogs = row['total_cogs'] or Decimal(0)
        total_fees = row['total_fees'] or Decimal(0)

        gross_profit = total_revenue - total_cogs - total_fees
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

        return {
            'order_count': row['order_count'] or 0,
            'total_revenue': total_revenue,
            'total_units': row['total_units'] or 0,
            'avg_order_value': float(row['avg_order_value'] or 0),
            'total_cogs': total_cogs,
            'total_fees': total_fees,
            'gross_profit': float(gross_profit),
            'profit_margin': float(profit_margin),
            'unique_countries': row['unique_countries'] or 0
        }

    async def get_top_products(
        self,
        user_id: UUID,
        limit: int = 10,
        channel: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[Dict[str, Any]]:
        """
        Get top products by revenue

        Args:
            user_id: User ID for RLS filtering
            limit: Number of top products to return
            channel: 'offline', 'online', or None for all
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            List of top products with metrics
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute("SET LOCAL app.current_user_id = $1", str(user_id))

            if channel == 'offline' or channel is None:
                offline_top = await self._get_top_offline_products(
                    conn, limit, start_date, end_date
                )
            else:
                offline_top = []

            if channel == 'online' or channel is None:
                online_top = await self._get_top_online_products(
                    conn, limit, start_date, end_date
                )
            else:
                online_top = []

            # Combine and sort
            all_products = offline_top + online_top
            all_products.sort(key=lambda x: x['revenue'], reverse=True)

            return all_products[:limit]

    async def _get_top_offline_products(
        self,
        conn: asyncpg.Connection,
        limit: int,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> list[Dict[str, Any]]:
        """Get top offline products"""

        date_filter = ""
        params = [limit]

        if start_date and end_date:
            date_filter = """
                AND (
                    make_date(year, month, 1) >= $2
                    AND make_date(year, month, 1) <= $3
                )
            """
            params = [limit, start_date, end_date]

        query = f"""
            SELECT
                functional_name,
                product_ean,
                SUM(sales_eur) as revenue,
                SUM(quantity) as units,
                COUNT(*) as transactions,
                'offline' as channel
            FROM sellout_entries2
            WHERE 1=1 {date_filter}
            GROUP BY functional_name, product_ean
            ORDER BY revenue DESC
            LIMIT $1
        """

        rows = await conn.fetch(query, *params)

        return [
            {
                'product_name': row['functional_name'],
                'product_ean': row['product_ean'],
                'revenue': float(row['revenue']),
                'units': row['units'],
                'transactions': row['transactions'],
                'channel': row['channel']
            }
            for row in rows
        ]

    async def _get_top_online_products(
        self,
        conn: asyncpg.Connection,
        limit: int,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> list[Dict[str, Any]]:
        """Get top online products"""

        date_filter = ""
        params = [limit]

        if start_date and end_date:
            date_filter = "AND order_date >= $2 AND order_date <= $3"
            params = [limit, start_date, end_date]

        query = f"""
            SELECT
                functional_name,
                product_ean,
                SUM(sales_eur) as revenue,
                SUM(quantity) as units,
                COUNT(*) as orders,
                'online' as channel
            FROM ecommerce_orders
            WHERE 1=1 {date_filter}
            GROUP BY functional_name, product_ean
            ORDER BY revenue DESC
            LIMIT $1
        """

        rows = await conn.fetch(query, *params)

        return [
            {
                'product_name': row['functional_name'],
                'product_ean': row['product_ean'],
                'revenue': float(row['revenue']),
                'units': row['units'],
                'transactions': row['orders'],
                'channel': row['channel']
            }
            for row in rows
        ]
