"""
Sales data aggregator with filtering and pagination
"""

from typing import Dict, List, Any, Optional
from datetime import date, datetime
from decimal import Decimal
from supabase import Client


class SalesAggregator:
    """Aggregate and filter sales data with pagination"""

    def __init__(self, supabase: Client):
        """
        Initialize sales aggregator

        Args:
            supabase: Supabase client for database operations
        """
        self.supabase = supabase

    def get_sales_data(
        self,
        user_id: str,
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
        sales = []
        total_count = 0

        if channel in ('offline', 'all'):
            offline_data = self._get_offline_sales(
                start_date, end_date, reseller, product, page, page_size
            )
            sales.extend(offline_data['sales'])
            total_count += offline_data['total_count']

        if channel in ('online', 'all'):
            online_data = self._get_online_sales(
                start_date, end_date, product, country, page, page_size
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

    def _get_offline_sales(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
        reseller: Optional[str],
        product: Optional[str],
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """Get offline (B2B) sales data"""

        # Query sellout_entries2
        query = self.supabase.table("sellout_entries2").select("*")

        # Apply filters
        if reseller:
            query = query.ilike("reseller", f"%{reseller}%")

        if product:
            query = query.ilike("functional_name", f"%{product}%")

        result = query.execute()

        if not result.data:
            return {'sales': [], 'total_count': 0}

        # Filter by date range (month/year based)
        records = result.data
        if start_date and end_date:
            filtered = []
            for r in records:
                if r.get('year') and r.get('month'):
                    try:
                        record_date = date(r['year'], r['month'], 1)
                        if start_date <= record_date <= end_date:
                            filtered.append(r)
                    except (ValueError, TypeError):
                        continue
            records = filtered

        total_count = len(records)

        # Sort by year, month descending
        records.sort(key=lambda x: (x.get('year', 0), x.get('month', 0)), reverse=True)

        # Apply pagination
        offset = (page - 1) * page_size
        paginated_records = records[offset:offset + page_size]

        sales = [
            {
                'sale_id': str(r.get('sale_id', '')),
                'product_name': r.get('functional_name', 'Unknown'),
                'product_ean': r.get('product_ean', ''),
                'reseller': r.get('reseller', ''),
                'revenue': float(r.get('sales_eur', 0) or 0),
                'quantity': int(r.get('quantity', 0) or 0),
                'currency': r.get('currency', 'EUR'),
                'date': date(r['year'], r['month'], 1).isoformat() if r.get('year') and r.get('month') else None,
                'channel': 'offline',
                'country': None,
                'created_at': r.get('created_at', '')
            }
            for r in paginated_records
        ]

        return {
            'sales': sales,
            'total_count': total_count
        }

    def _get_online_sales(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
        product: Optional[str],
        country: Optional[str],
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """Get online (D2C) sales data"""

        # Query ecommerce_orders
        query = self.supabase.table("ecommerce_orders").select("*")

        # Apply date filters
        if start_date:
            query = query.gte("order_date", start_date.isoformat())
        if end_date:
            query = query.lte("order_date", end_date.isoformat())

        # Product filter (fuzzy)
        if product:
            query = query.ilike("functional_name", f"%{product}%")

        # Country filter
        if country:
            query = query.ilike("country", f"%{country}%")

        # Order by date descending
        query = query.order("order_date", desc=True)

        result = query.execute()

        if not result.data:
            return {'sales': [], 'total_count': 0}

        records = result.data
        total_count = len(records)

        # Apply pagination
        offset = (page - 1) * page_size
        paginated_records = records[offset:offset + page_size]

        sales = [
            {
                'sale_id': str(r.get('order_id', '')),
                'product_name': r.get('functional_name', 'Unknown'),
                'product_ean': r.get('product_ean', ''),
                'reseller': None,
                'revenue': float(r.get('sales_eur', 0) or 0),
                'quantity': int(r.get('quantity', 0) or 0),
                'currency': 'EUR',
                'date': r.get('order_date', ''),
                'channel': 'online',
                'country': r.get('country', ''),
                'city': r.get('city', ''),
                'cost_of_goods': float(r.get('cost_of_goods', 0) or 0) if r.get('cost_of_goods') else None,
                'stripe_fee': float(r.get('stripe_fee', 0) or 0) if r.get('stripe_fee') else None,
                'created_at': r.get('created_at', '')
            }
            for r in paginated_records
        ]

        return {
            'sales': sales,
            'total_count': total_count
        }

    def get_sales_summary(
        self,
        user_id: str,
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
        if group_by == 'month':
            return self._get_monthly_summary(
                channel, start_date, end_date
            )
        elif group_by == 'product':
            return self._get_product_summary(
                channel, start_date, end_date
            )
        elif group_by == 'reseller':
            return self._get_reseller_summary(
                start_date, end_date
            )
        elif group_by == 'country':
            return self._get_country_summary(
                start_date, end_date
            )
        else:
            raise ValueError(f"Invalid group_by: {group_by}")

    def _get_monthly_summary(
        self,
        channel: str,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[Dict[str, Any]]:
        """Get sales summary grouped by month"""

        results = []

        if channel in ('offline', 'all'):
            # Offline monthly summary
            query = self.supabase.table("sellout_entries2").select("*")
            result = query.execute()

            if result.data:
                records = result.data

                # Filter by date if provided
                if start_date and end_date:
                    filtered = []
                    for r in records:
                        if r.get('year') and r.get('month'):
                            try:
                                record_date = date(r['year'], r['month'], 1)
                                if start_date <= record_date <= end_date:
                                    filtered.append(r)
                            except (ValueError, TypeError):
                                continue
                    records = filtered

                # Group by month in Python
                monthly = {}
                for r in records:
                    if r.get('year') and r.get('month'):
                        key = (r['year'], r['month'])
                        if key not in monthly:
                            monthly[key] = {
                                'period': date(r['year'], r['month'], 1).isoformat(),
                                'revenue': 0.0,
                                'units': 0,
                                'transactions': 0,
                                'channel': 'offline'
                            }
                        monthly[key]['revenue'] += float(r.get('sales_eur', 0) or 0)
                        monthly[key]['units'] += int(r.get('quantity', 0) or 0)
                        monthly[key]['transactions'] += 1

                results.extend(sorted(monthly.values(), key=lambda x: x['period'], reverse=True))

        if channel in ('online', 'all'):
            # Online monthly summary
            query = self.supabase.table("ecommerce_orders").select("*")

            if start_date:
                query = query.gte("order_date", start_date.isoformat())
            if end_date:
                query = query.lte("order_date", end_date.isoformat())

            result = query.execute()

            if result.data:
                # Group by month in Python
                monthly = {}
                for r in result.data:
                    order_date = r.get('order_date')
                    if order_date:
                        try:
                            dt = datetime.fromisoformat(order_date.replace('Z', '+00:00'))
                            period = date(dt.year, dt.month, 1).isoformat()

                            if period not in monthly:
                                monthly[period] = {
                                    'period': period,
                                    'revenue': 0.0,
                                    'units': 0,
                                    'transactions': 0,
                                    'channel': 'online'
                                }
                            monthly[period]['revenue'] += float(r.get('sales_eur', 0) or 0)
                            monthly[period]['units'] += int(r.get('quantity', 0) or 0)
                            monthly[period]['transactions'] += 1
                        except (ValueError, TypeError):
                            continue

                results.extend(sorted(monthly.values(), key=lambda x: x['period'], reverse=True))

        return results

    def _get_product_summary(
        self,
        channel: str,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[Dict[str, Any]]:
        """Get sales summary grouped by product"""

        results = {}

        if channel in ('offline', 'all'):
            query = self.supabase.table("sellout_entries2").select("*")
            result = query.execute()

            if result.data:
                for r in result.data:
                    # Filter by date if needed
                    if start_date and end_date and r.get('year') and r.get('month'):
                        try:
                            record_date = date(r['year'], r['month'], 1)
                            if not (start_date <= record_date <= end_date):
                                continue
                        except (ValueError, TypeError):
                            continue

                    product = r.get('functional_name', 'Unknown')
                    if product not in results:
                        results[product] = {
                            'product': product,
                            'revenue': 0.0,
                            'units': 0,
                            'transactions': 0
                        }
                    results[product]['revenue'] += float(r.get('sales_eur', 0) or 0)
                    results[product]['units'] += int(r.get('quantity', 0) or 0)
                    results[product]['transactions'] += 1

        if channel in ('online', 'all'):
            query = self.supabase.table("ecommerce_orders").select("*")

            if start_date:
                query = query.gte("order_date", start_date.isoformat())
            if end_date:
                query = query.lte("order_date", end_date.isoformat())

            result = query.execute()

            if result.data:
                for r in result.data:
                    product = r.get('functional_name', 'Unknown')
                    if product not in results:
                        results[product] = {
                            'product': product,
                            'revenue': 0.0,
                            'units': 0,
                            'transactions': 0
                        }
                    results[product]['revenue'] += float(r.get('sales_eur', 0) or 0)
                    results[product]['units'] += int(r.get('quantity', 0) or 0)
                    results[product]['transactions'] += 1

        return sorted(results.values(), key=lambda x: x['revenue'], reverse=True)

    def _get_reseller_summary(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[Dict[str, Any]]:
        """Get sales summary grouped by reseller (offline only)"""

        query = self.supabase.table("sellout_entries2").select("*")
        result = query.execute()

        if not result.data:
            return []

        records = result.data

        # Filter by date if provided
        if start_date and end_date:
            filtered = []
            for r in records:
                if r.get('year') and r.get('month'):
                    try:
                        record_date = date(r['year'], r['month'], 1)
                        if start_date <= record_date <= end_date:
                            filtered.append(r)
                    except (ValueError, TypeError):
                        continue
            records = filtered

        # Group by reseller
        resellers = {}
        for r in records:
            reseller = r.get('reseller', 'Unknown')
            if reseller not in resellers:
                resellers[reseller] = {
                    'reseller': reseller,
                    'revenue': 0.0,
                    'units': 0,
                    'transactions': 0
                }
            resellers[reseller]['revenue'] += float(r.get('sales_eur', 0) or 0)
            resellers[reseller]['units'] += int(r.get('quantity', 0) or 0)
            resellers[reseller]['transactions'] += 1

        return sorted(resellers.values(), key=lambda x: x['revenue'], reverse=True)

    def _get_country_summary(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[Dict[str, Any]]:
        """Get sales summary grouped by country (online only)"""

        query = self.supabase.table("ecommerce_orders").select("*")

        if start_date:
            query = query.gte("order_date", start_date.isoformat())
        if end_date:
            query = query.lte("order_date", end_date.isoformat())

        result = query.execute()

        if not result.data:
            return []

        # Group by country
        countries = {}
        for r in result.data:
            country = r.get('country', 'Unknown')
            if country not in countries:
                countries[country] = {
                    'country': country,
                    'revenue': 0.0,
                    'units': 0,
                    'transactions': 0
                }
            countries[country]['revenue'] += float(r.get('sales_eur', 0) or 0)
            countries[country]['units'] += int(r.get('quantity', 0) or 0)
            countries[country]['transactions'] += 1

        return sorted(countries.values(), key=lambda x: x['revenue'], reverse=True)
