"""
Sales data aggregator with filtering and pagination
"""

from typing import Dict, List, Any, Optional
from datetime import date, datetime
from decimal import Decimal
import asyncpg
from uuid import UUID


class SalesAggregator:
    """Aggregate and filter sales data with pagination"""

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize sales aggregator

        Args:
            db_pool: Database connection pool for tenant database
        """
        self.db_pool = db_pool

    async def get_sales_data(
        self,
        user_id: UUID,
        channel: str = 'all',  # 'offline', 'online', or 'all'
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        reseller: Optional[str] = None,
        product: Optional[str] = None,
        country: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get filtered sales data with pagination

        Args:
            user_id: User ID for RLS filtering
            channel: Sales channel ('offline', 'online', or 'all')
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            reseller: Reseller name filter (optional)
            product: Product name filter (optional, fuzzy match)
            country: Country filter (optional, online only)
            page: Page number (1-indexed)
            page_size: Number of records per page

        Returns:
            Dictionary with sales data and pagination info
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute("SET LOCAL app.current_user_id = $1", str(user_id))

            sales = []
            total_count = 0

            if channel in ('offline', 'all'):
                offline_data = await self._get_offline_sales(
                    conn, start_date, end_date, reseller, product, page, page_size
                )
                sales.extend(offline_data['sales'])
                total_count += offline_data['total_count']

            if channel in ('online', 'all'):
                online_data = await self._get_online_sales(
                    conn, start_date, end_date, product, country, page, page_size
                )
                sales.extend(online_data['sales'])
                total_count += online_data['total_count']

            # Sort by date descending
            sales.sort(key=lambda x: x['date'], reverse=True)

            # Apply pagination to combined results if fetching both channels
            if channel == 'all':
                offset = (page - 1) * page_size
                sales = sales[offset:offset + page_size]

            return {
                'sales': sales,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                },
                'filters': {
                    'channel': channel,
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None,
                    'reseller': reseller,
                    'product': product,
                    'country': country
                }
            }

    async def _get_offline_sales(
        self,
        conn: asyncpg.Connection,
        start_date: Optional[date],
        end_date: Optional[date],
        reseller: Optional[str],
        product: Optional[str],
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """Get offline (B2B) sales data"""

        filters = []
        params = []
        param_count = 0

        # Date filter
        if start_date and end_date:
            param_count += 1
            filters.append(f"make_date(year, month, 1) >= ${param_count}")
            params.append(start_date)
            param_count += 1
            filters.append(f"make_date(year, month, 1) <= ${param_count}")
            params.append(end_date)

        # Reseller filter
        if reseller:
            param_count += 1
            filters.append(f"reseller ILIKE ${param_count}")
            params.append(f"%{reseller}%")

        # Product filter (fuzzy search)
        if product:
            param_count += 1
            filters.append(f"functional_name ILIKE ${param_count}")
            params.append(f"%{product}%")

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        # Count query
        count_query = f"""
            SELECT COUNT(*) as total
            FROM sellout_entries2
            {where_clause}
        """

        count_row = await conn.fetchrow(count_query, *params)
        total_count = count_row['total']

        # Data query with pagination
        offset = (page - 1) * page_size
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count

        params.extend([page_size, offset])

        data_query = f"""
            SELECT
                sale_id,
                functional_name as product_name,
                product_ean,
                reseller,
                sales_eur as revenue,
                quantity,
                currency,
                make_date(year, month, 1) as date,
                month,
                year,
                'offline' as channel,
                created_at
            FROM sellout_entries2
            {where_clause}
            ORDER BY year DESC, month DESC, created_at DESC
            LIMIT ${limit_param} OFFSET ${offset_param}
        """

        rows = await conn.fetch(data_query, *params)

        sales = [
            {
                'sale_id': str(row['sale_id']),
                'product_name': row['product_name'],
                'product_ean': row['product_ean'],
                'reseller': row['reseller'],
                'revenue': float(row['revenue']),
                'quantity': row['quantity'],
                'currency': row['currency'],
                'date': row['date'].isoformat(),
                'channel': row['channel'],
                'country': None,  # Not available for offline
                'created_at': row['created_at'].isoformat()
            }
            for row in rows
        ]

        return {
            'sales': sales,
            'total_count': total_count
        }

    async def _get_online_sales(
        self,
        conn: asyncpg.Connection,
        start_date: Optional[date],
        end_date: Optional[date],
        product: Optional[str],
        country: Optional[str],
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """Get online (D2C) sales data"""

        filters = []
        params = []
        param_count = 0

        # Date filter
        if start_date:
            param_count += 1
            filters.append(f"order_date >= ${param_count}")
            params.append(start_date)

        if end_date:
            param_count += 1
            filters.append(f"order_date <= ${param_count}")
            params.append(end_date)

        # Product filter (fuzzy search)
        if product:
            param_count += 1
            filters.append(f"functional_name ILIKE ${param_count}")
            params.append(f"%{product}%")

        # Country filter
        if country:
            param_count += 1
            filters.append(f"country ILIKE ${param_count}")
            params.append(f"%{country}%")

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        # Count query
        count_query = f"""
            SELECT COUNT(*) as total
            FROM ecommerce_orders
            {where_clause}
        """

        count_row = await conn.fetchrow(count_query, *params)
        total_count = count_row['total']

        # Data query with pagination
        offset = (page - 1) * page_size
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count

        params.extend([page_size, offset])

        data_query = f"""
            SELECT
                order_id,
                functional_name as product_name,
                product_ean,
                sales_eur as revenue,
                quantity,
                cost_of_goods,
                stripe_fee,
                order_date as date,
                country,
                city,
                'online' as channel,
                created_at
            FROM ecommerce_orders
            {where_clause}
            ORDER BY order_date DESC, created_at DESC
            LIMIT ${limit_param} OFFSET ${offset_param}
        """

        rows = await conn.fetch(data_query, *params)

        sales = [
            {
                'sale_id': str(row['order_id']),
                'product_name': row['product_name'],
                'product_ean': row['product_ean'],
                'reseller': None,  # Not available for online
                'revenue': float(row['revenue']),
                'quantity': row['quantity'],
                'currency': 'EUR',  # Online always EUR
                'date': row['date'].isoformat(),
                'channel': row['channel'],
                'country': row['country'],
                'city': row['city'],
                'cost_of_goods': float(row['cost_of_goods']) if row['cost_of_goods'] else None,
                'stripe_fee': float(row['stripe_fee']) if row['stripe_fee'] else None,
                'created_at': row['created_at'].isoformat()
            }
            for row in rows
        ]

        return {
            'sales': sales,
            'total_count': total_count
        }

    async def get_sales_summary(
        self,
        user_id: UUID,
        group_by: str = 'month',  # 'month', 'product', 'reseller', 'country'
        channel: str = 'all',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated sales summary

        Args:
            user_id: User ID for RLS filtering
            group_by: Grouping dimension
            channel: Sales channel filter
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            List of aggregated sales by grouping dimension
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute("SET LOCAL app.current_user_id = $1", str(user_id))

            if group_by == 'month':
                return await self._get_monthly_summary(
                    conn, channel, start_date, end_date
                )
            elif group_by == 'product':
                return await self._get_product_summary(
                    conn, channel, start_date, end_date
                )
            elif group_by == 'reseller':
                return await self._get_reseller_summary(
                    conn, start_date, end_date
                )
            elif group_by == 'country':
                return await self._get_country_summary(
                    conn, start_date, end_date
                )
            else:
                raise ValueError(f"Invalid group_by: {group_by}")

    async def _get_monthly_summary(
        self,
        conn: asyncpg.Connection,
        channel: str,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[Dict[str, Any]]:
        """Get sales summary grouped by month"""

        results = []

        if channel in ('offline', 'all'):
            # Offline monthly summary
            filters = []
            params = []

            if start_date and end_date:
                filters.append("make_date(year, month, 1) >= $1 AND make_date(year, month, 1) <= $2")
                params = [start_date, end_date]

            where_clause = "WHERE " + " AND ".join(filters) if filters else ""

            query = f"""
                SELECT
                    year,
                    month,
                    make_date(year, month, 1) as period,
                    SUM(sales_eur) as revenue,
                    SUM(quantity) as units,
                    COUNT(*) as transactions,
                    'offline' as channel
                FROM sellout_entries2
                {where_clause}
                GROUP BY year, month
                ORDER BY year DESC, month DESC
            """

            rows = await conn.fetch(query, *params)
            results.extend([
                {
                    'period': row['period'].isoformat(),
                    'revenue': float(row['revenue']),
                    'units': row['units'],
                    'transactions': row['transactions'],
                    'channel': row['channel']
                }
                for row in rows
            ])

        if channel in ('online', 'all'):
            # Online monthly summary
            filters = []
            params = []

            if start_date:
                filters.append("order_date >= $1")
                params.append(start_date)

            if end_date:
                param_num = len(params) + 1
                filters.append(f"order_date <= ${param_num}")
                params.append(end_date)

            where_clause = "WHERE " + " AND ".join(filters) if filters else ""

            query = f"""
                SELECT
                    DATE_TRUNC('month', order_date)::date as period,
                    SUM(sales_eur) as revenue,
                    SUM(quantity) as units,
                    COUNT(*) as orders,
                    'online' as channel
                FROM ecommerce_orders
                {where_clause}
                GROUP BY DATE_TRUNC('month', order_date)
                ORDER BY period DESC
            """

            rows = await conn.fetch(query, *params)
            results.extend([
                {
                    'period': row['period'].isoformat(),
                    'revenue': float(row['revenue']),
                    'units': row['units'],
                    'transactions': row['orders'],
                    'channel': row['channel']
                }
                for row in rows
            ])

        return results

    async def _get_product_summary(
        self,
        conn: asyncpg.Connection,
        channel: str,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[Dict[str, Any]]:
        """Get sales summary grouped by product"""
        # Implementation similar to monthly, group by functional_name
        # Simplified for brevity
        return []

    async def _get_reseller_summary(
        self,
        conn: asyncpg.Connection,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[Dict[str, Any]]:
        """Get sales summary grouped by reseller (offline only)"""
        # Implementation for reseller grouping
        return []

    async def _get_country_summary(
        self,
        conn: asyncpg.Connection,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[Dict[str, Any]]:
        """Get sales summary grouped by country (online only)"""
        # Implementation for country grouping
        return []
