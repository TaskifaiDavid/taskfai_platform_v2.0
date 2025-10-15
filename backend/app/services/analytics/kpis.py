"""
KPI calculator for analytics dashboard.

IMPORTANT: This service uses Supabase service_key which bypasses Row-Level Security (RLS).
All queries MUST explicitly filter by user_id to ensure proper data isolation.
Without explicit user_id filtering, queries will return data across all tenants.
"""

from typing import Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
from supabase import Client


class KPICalculator:
    """Calculate key performance indicators for sales analytics"""

    def __init__(self, supabase: Client):
        """
        Initialize KPI calculator

        Args:
            supabase: Supabase client for database operations
        """
        self.supabase = supabase

    def calculate_kpis(
        self,
        user_id: str,
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
        # Calculate offline (B2B) KPIs
        offline_kpis = self._calculate_offline_kpis(
            start_date, end_date, user_id
        ) if channel in (None, 'offline') else {}

        # Calculate online (D2C) KPIs
        online_kpis = self._calculate_online_kpis(
            start_date, end_date, user_id
        ) if channel in (None, 'online') else {}

        # Calculate combined KPIs
        total_revenue = Decimal(0)
        total_units = 0
        avg_price = Decimal(0)

        if offline_kpis:
            total_revenue += offline_kpis.get('total_revenue', Decimal(0))
            total_units += offline_kpis.get('total_units', 0)

        if online_kpis:
            total_revenue += online_kpis.get('total_revenue', Decimal(0))
            total_units += online_kpis.get('total_units', 0)

        if total_units > 0:
            avg_price = total_revenue / total_units

        # Calculate upload count
        total_uploads = self._count_completed_uploads(user_id, start_date, end_date)

        # Extract additional online KPIs for dashboard
        gross_profit = online_kpis.get('gross_profit', 0) if online_kpis else 0
        profit_margin = online_kpis.get('profit_margin', 0) if online_kpis else 0
        unique_countries = online_kpis.get('unique_countries', 0) if online_kpis else 0
        order_count = online_kpis.get('order_count', 0) if online_kpis else 0

        return {
            'total_revenue': float(total_revenue),
            'total_units': total_units,
            'avg_price': float(avg_price),
            'average_order_value': float(avg_price),
            'total_uploads': total_uploads,
            'gross_profit': float(gross_profit),
            'profit_margin': float(profit_margin),
            'unique_countries': unique_countries,
            'order_count': order_count,
            'offline': offline_kpis,
            'online': online_kpis,
            'top_resellers': [],  # Placeholder
            'date_range': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            }
        }

    def _calculate_offline_kpis(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
        user_id: str
    ) -> Dict[str, Any]:
        """Calculate offline (B2B) sales KPIs"""

        # Query sellout_entries2 table with user_id filter
        query = self.supabase.table("sellout_entries2").select("sales_eur,quantity,reseller_id,product_id,month,year").eq("user_id", user_id)

        # Apply date filters if provided
        # Note: Supabase REST API doesn't support complex date operations easily
        # So we'll fetch and filter in Python
        result = query.execute()

        if not result.data:
            return {
                'transaction_count': 0,
                'total_revenue': Decimal(0),
                'total_units': 0,
                'avg_transaction_value': 0,
                'unique_resellers': 0,
                'unique_products': 0
            }

        # Filter by date range if provided
        records = result.data
        if start_date and end_date:
            filtered = []
            for r in records:
                if r.get('year') and r.get('month'):
                    record_date = date(r['year'], r['month'], 1)
                    if start_date <= record_date <= end_date:
                        filtered.append(r)
            records = filtered

        # Calculate aggregates
        total_revenue = sum(Decimal(str(r.get('sales_eur', 0) or 0)) for r in records)
        total_units = sum(int(r.get('quantity', 0) or 0) for r in records)
        unique_resellers = len(set(r.get('reseller_id') for r in records if r.get('reseller_id')))
        unique_products = len(set(r.get('product_id') for r in records if r.get('product_id')))

        return {
            'transaction_count': len(records),
            'total_revenue': total_revenue,
            'total_units': total_units,
            'avg_transaction_value': float(total_revenue / len(records)) if records else 0,
            'unique_resellers': unique_resellers,
            'unique_products': unique_products
        }

    def _calculate_online_kpis(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
        user_id: str
    ) -> Dict[str, Any]:
        """Calculate online (D2C) sales KPIs"""

        # Query ecommerce_orders table with user_id filter
        query = self.supabase.table("ecommerce_orders").select("sales_eur,quantity,cost_of_goods,stripe_fee,country,order_date").eq("user_id", user_id)

        # Apply date filters if provided
        if start_date:
            query = query.gte("order_date", start_date.isoformat())
        if end_date:
            query = query.lte("order_date", end_date.isoformat())

        result = query.execute()

        if not result.data:
            return {
                'order_count': 0,
                'total_revenue': Decimal(0),
                'total_units': 0,
                'avg_order_value': 0,
                'total_cogs': Decimal(0),
                'total_fees': Decimal(0),
                'gross_profit': 0,
                'profit_margin': 0,
                'unique_countries': 0
            }

        records = result.data

        # Calculate aggregates
        total_revenue = sum(Decimal(str(r.get('sales_eur', 0) or 0)) for r in records)
        total_units = sum(int(r.get('quantity', 0) or 0) for r in records)
        total_cogs = sum(Decimal(str(r.get('cost_of_goods', 0) or 0)) for r in records)
        total_fees = sum(Decimal(str(r.get('stripe_fee', 0) or 0)) for r in records)
        unique_countries = len(set(r.get('country') for r in records if r.get('country')))

        gross_profit = total_revenue - total_cogs - total_fees
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

        return {
            'order_count': len(records),
            'total_revenue': total_revenue,
            'total_units': total_units,
            'avg_order_value': float(total_revenue / len(records)) if records else 0,
            'total_cogs': total_cogs,
            'total_fees': total_fees,
            'gross_profit': float(gross_profit),
            'profit_margin': float(profit_margin),
            'unique_countries': unique_countries
        }

    def get_top_products(
        self,
        user_id: str,
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
        if channel == 'offline' or channel is None:
            offline_top = self._get_top_offline_products(
                limit, start_date, end_date, user_id
            )
        else:
            offline_top = []

        if channel == 'online' or channel is None:
            online_top = self._get_top_online_products(
                limit, start_date, end_date, user_id
            )
        else:
            online_top = []

        # Combine and sort
        all_products = offline_top + online_top
        all_products.sort(key=lambda x: x['revenue'], reverse=True)

        return all_products[:limit]

    def _get_top_offline_products(
        self,
        limit: int,
        start_date: Optional[date],
        end_date: Optional[date],
        user_id: str
    ) -> list[Dict[str, Any]]:
        """Get top offline products"""

        # Query sellout_entries2 with user_id filter
        query = self.supabase.table("sellout_entries2").select("functional_name,product_ean,sales_eur,quantity,month,year").eq("user_id", user_id)
        result = query.execute()

        if not result.data:
            return []

        # Filter by date if needed
        records = result.data
        if start_date and end_date:
            filtered = []
            for r in records:
                if r.get('year') and r.get('month'):
                    record_date = date(r['year'], r['month'], 1)
                    if start_date <= record_date <= end_date:
                        filtered.append(r)
            records = filtered

        # Group by product
        products = {}
        for r in records:
            key = (r.get('functional_name'), r.get('product_ean'))
            if key not in products:
                products[key] = {
                    'product_name': r.get('functional_name', 'Unknown'),
                    'product_ean': r.get('product_ean', ''),
                    'revenue': 0,
                    'units': 0,
                    'transactions': 0,
                    'channel': 'offline'
                }
            products[key]['revenue'] += float(r.get('sales_eur', 0) or 0)
            products[key]['units'] += int(r.get('quantity', 0) or 0)
            products[key]['transactions'] += 1

        # Sort by revenue and return top
        sorted_products = sorted(products.values(), key=lambda x: x['revenue'], reverse=True)
        return sorted_products[:limit]

    def _get_top_online_products(
        self,
        limit: int,
        start_date: Optional[date],
        end_date: Optional[date],
        user_id: str
    ) -> list[Dict[str, Any]]:
        """Get top online products"""

        # Query ecommerce_orders with user_id filter
        query = self.supabase.table("ecommerce_orders").select("functional_name,product_ean,sales_eur,quantity,order_date").eq("user_id", user_id)

        # Apply date filters
        if start_date:
            query = query.gte("order_date", start_date.isoformat())
        if end_date:
            query = query.lte("order_date", end_date.isoformat())

        result = query.execute()

        if not result.data:
            return []

        # Group by product
        products = {}
        for r in result.data:
            key = (r.get('functional_name'), r.get('product_ean'))
            if key not in products:
                products[key] = {
                    'product_name': r.get('functional_name', 'Unknown'),
                    'product_ean': r.get('product_ean', ''),
                    'revenue': 0,
                    'units': 0,
                    'transactions': 0,
                    'channel': 'online'
                }
            products[key]['revenue'] += float(r.get('sales_eur', 0) or 0)
            products[key]['units'] += int(r.get('quantity', 0) or 0)
            products[key]['transactions'] += 1

        # Sort by revenue and return top
        sorted_products = sorted(products.values(), key=lambda x: x['revenue'], reverse=True)
        return sorted_products[:limit]

    def _count_completed_uploads(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
        """
        Count completed upload batches for user

        Args:
            user_id: User ID for RLS filtering
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            Count of completed uploads
        """
        query = self.supabase.table("upload_batches")\
            .select("upload_batch_id", count="exact")\
            .eq("uploader_user_id", user_id)\
            .eq("processing_status", "completed")

        # Apply date filters if provided
        if start_date:
            query = query.gte("upload_timestamp", start_date.isoformat())
        if end_date:
            query = query.lte("upload_timestamp", end_date.isoformat())

        result = query.execute()
        return result.count or 0
