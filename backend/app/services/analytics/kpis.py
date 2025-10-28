"""
KPI calculator for analytics dashboard.

IMPORTANT: This service uses Supabase service_key which bypasses Row-Level Security (RLS).
All queries MUST explicitly filter by user_id to ensure proper data isolation.
Without explicit user_id filtering, queries will return data across all tenants.

BIBBI MODE: When TENANT_ID_OVERRIDE=bibbi, user filtering is skipped because Bibbi
uses a dedicated single-tenant Supabase database with project-level isolation.
"""

from typing import Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
import os
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
        self.is_bibbi_mode = os.getenv("TENANT_ID_OVERRIDE") == "bibbi"

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

        # Query sales_unified table
        # In BIBBI mode (single-tenant database), skip user filtering
        # In multi-tenant mode, filter by user_id via uploads JOIN
        if self.is_bibbi_mode:
            query = self.supabase.table("sales_unified")\
                .select("sales_eur,quantity,reseller_id,product_ean,month,year")
        else:
            query = self.supabase.table("sales_unified")\
                .select("sales_eur,quantity,reseller_id,product_ean,month,year,uploads!inner(user_id)")\
                .eq("uploads.user_id", user_id)

        # Apply date filters if provided
        # Note: Supabase REST API doesn't support complex date operations easily
        # So we'll fetch and filter in Python
        result = query.limit(100000).execute()

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
        unique_products = len(set(r.get('product_ean') for r in records if r.get('product_ean')))

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

        # Query sales_unified table
        # In BIBBI mode (single-tenant database), skip user filtering
        # Filter by sales_channel='online' for D2C sales
        if self.is_bibbi_mode:
            query = self.supabase.table("sales_unified")\
                .select("sales_eur,quantity,cost_of_goods,payment_processing_fee,country,sale_date")\
                .eq("sales_channel", "online")
        else:
            query = self.supabase.table("sales_unified")\
                .select("sales_eur,quantity,cost_of_goods,payment_processing_fee,country,sale_date,uploads!inner(user_id)")\
                .eq("uploads.user_id", user_id)\
                .eq("sales_channel", "online")

        # Apply date filters if provided
        if start_date:
            query = query.gte("sale_date", start_date.isoformat())
        if end_date:
            query = query.lte("sale_date", end_date.isoformat())

        result = query.limit(100000).execute()

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
        total_fees = sum(Decimal(str(r.get('payment_processing_fee', 0) or 0)) for r in records)
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

        # Merge products across channels (combine offline + online for same product)
        merged_products = {}
        for product in offline_top + online_top:
            name = product['product_name']
            if name not in merged_products:
                merged_products[name] = {
                    'product_name': name,
                    'product_ean': product['product_ean'],
                    'revenue': 0,
                    'units': 0,
                    'transactions': 0,
                    'channel': 'both' if (offline_top and online_top) else product['channel']
                }
            merged_products[name]['revenue'] += product['revenue']
            merged_products[name]['units'] += product['units']
            merged_products[name]['transactions'] += product['transactions']

        # Sort by revenue and return top N
        all_products = sorted(merged_products.values(), key=lambda x: x['revenue'], reverse=True)
        return all_products[:limit]

    def _get_top_offline_products(
        self,
        limit: int,
        start_date: Optional[date],
        end_date: Optional[date],
        user_id: str
    ) -> list[Dict[str, Any]]:
        """Get top offline products"""

        # In BIBBI mode (single-tenant database), skip user filtering
        # In multi-tenant mode, filter by user_id via uploads JOIN
        if self.is_bibbi_mode:
            query = self.supabase.table("sales_unified")\
                .select("functional_name,product_ean,sales_eur,quantity,month,year")
        else:
            query = self.supabase.table("sales_unified")\
                .select("functional_name,product_ean,sales_eur,quantity,month,year,uploads!inner(user_id)")\
                .eq("uploads.user_id", user_id)

        result = query.limit(100000).execute()

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

        # Group by product name (aggregating all EAN variants)
        products = {}
        for r in records:
            key = r.get('functional_name')
            if key not in products:
                products[key] = {
                    'product_name': r.get('functional_name', 'Unknown'),
                    'product_ean': r.get('product_ean', ''),  # Store first EAN encountered
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

        # In BIBBI mode (single-tenant database), skip user filtering
        # In multi-tenant mode, filter by user_id via uploads JOIN
        # Filter by sales_channel='online' for D2C sales
        if self.is_bibbi_mode:
            query = self.supabase.table("sales_unified")\
                .select("functional_name,product_ean,sales_eur,quantity,sale_date")\
                .eq("sales_channel", "online")
        else:
            query = self.supabase.table("sales_unified")\
                .select("functional_name,product_ean,sales_eur,quantity,sale_date,uploads!inner(user_id)")\
                .eq("uploads.user_id", user_id)\
                .eq("sales_channel", "online")

        # Apply date filters
        if start_date:
            query = query.gte("sale_date", start_date.isoformat())
        if end_date:
            query = query.lte("sale_date", end_date.isoformat())

        result = query.limit(100000).execute()

        if not result.data:
            return []

        # Group by product name (aggregating all EAN variants)
        products = {}
        for r in result.data:
            key = r.get('functional_name')
            if key not in products:
                products[key] = {
                    'product_name': r.get('functional_name', 'Unknown'),
                    'product_ean': r.get('product_ean', ''),  # Store first EAN encountered
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
        # In BIBBI mode (single-tenant database), skip user filtering
        # In multi-tenant mode, filter by user_id
        if self.is_bibbi_mode:
            query = self.supabase.table("uploads")\
                .select("id", count="exact")\
                .eq("status", "completed")
        else:
            query = self.supabase.table("uploads")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("status", "completed")

        # Apply date filters if provided
        if start_date:
            query = query.gte("uploaded_at", start_date.isoformat())
        if end_date:
            query = query.lte("uploaded_at", end_date.isoformat())

        result = query.limit(100000).execute()
        return result.count or 0

    def calculate_units_per_transaction(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        channel: Optional[str] = None
    ) -> float:
        """
        Calculate average units per transaction

        Args:
            user_id: User ID for RLS filtering
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            channel: Sales channel filter (optional)

        Returns:
            Average units per transaction
        """
        # In BIBBI mode (single-tenant database), skip user filtering
        # In multi-tenant mode, filter by user_id via upload_batches JOIN
        if self.is_bibbi_mode:
            query = self.supabase.table("sales_unified")\
                .select("quantity,id")
        else:
            query = self.supabase.table("sales_unified")\
                .select("quantity,id,upload_batches!inner(uploader_user_id)")\
                .eq("upload_batches.uploader_user_id", user_id)

        # Apply channel filter
        if channel:
            query = query.eq("sales_channel", channel)

        # Apply date filters
        if start_date:
            query = query.gte("sale_date", start_date.isoformat())
        if end_date:
            query = query.lte("sale_date", end_date.isoformat())

        result = query.limit(100000).execute()

        if not result.data or len(result.data) == 0:
            return 0.0

        total_units = sum(int(r.get('quantity', 0) or 0) for r in result.data)
        transaction_count = len(result.data)

        return round(total_units / transaction_count, 2) if transaction_count > 0 else 0.0

    def calculate_channel_mix(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[Dict[str, Any]]:
        """
        Calculate revenue and units breakdown by sales channel

        Args:
            user_id: User ID for RLS filtering
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            List of channel mix data with revenue, units, and percentage
        """
        # In BIBBI mode (single-tenant database), skip user filtering
        # In multi-tenant mode, filter by user_id via upload_batches JOIN
        if self.is_bibbi_mode:
            query = self.supabase.table("sales_unified")\
                .select("sales_channel,sales_eur,quantity")
        else:
            query = self.supabase.table("sales_unified")\
                .select("sales_channel,sales_eur,quantity,upload_batches!inner(uploader_user_id)")\
                .eq("upload_batches.uploader_user_id", user_id)

        # Apply date filters
        if start_date:
            query = query.gte("sale_date", start_date.isoformat())
        if end_date:
            query = query.lte("sale_date", end_date.isoformat())

        result = query.limit(100000).execute()

        if not result.data:
            return []

        # Group by channel
        channel_data = {}
        total_revenue = Decimal(0)
        total_units = 0

        for r in result.data:
            channel = r.get('sales_channel') or 'unknown'
            revenue = Decimal(str(r.get('sales_eur', 0) or 0))
            units = int(r.get('quantity', 0) or 0)

            if channel not in channel_data:
                channel_data[channel] = {
                    'channel': channel,
                    'revenue': Decimal(0),
                    'units': 0,
                    'transactions': 0
                }

            channel_data[channel]['revenue'] += revenue
            channel_data[channel]['units'] += units
            channel_data[channel]['transactions'] += 1
            total_revenue += revenue
            total_units += units

        # Calculate percentages and format output
        result_list = []
        for channel, data in channel_data.items():
            revenue_pct = (data['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            units_pct = (data['units'] / total_units * 100) if total_units > 0 else 0

            result_list.append({
                'channel': channel,
                'revenue': float(data['revenue']),
                'revenue_percentage': round(float(revenue_pct), 2),
                'units': data['units'],
                'units_percentage': round(float(units_pct), 2),
                'transactions': data['transactions']
            })

        # Sort by revenue descending
        result_list.sort(key=lambda x: x['revenue'], reverse=True)
        return result_list

    def get_top_markets(
        self,
        user_id: str,
        limit: int = 7,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[Dict[str, Any]]:
        """
        Get top markets (countries) by revenue

        Args:
            user_id: User ID for RLS filtering
            limit: Number of top markets to return
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            List of top markets with revenue and units
        """
        # In BIBBI mode (single-tenant database), skip user filtering
        # In multi-tenant mode, filter by user_id via upload_batches JOIN
        if self.is_bibbi_mode:
            query = self.supabase.table("sales_unified")\
                .select("country,sales_eur,quantity")
        else:
            query = self.supabase.table("sales_unified")\
                .select("country,sales_eur,quantity,upload_batches!inner(uploader_user_id)")\
                .eq("upload_batches.uploader_user_id", user_id)

        # Apply date filters
        if start_date:
            query = query.gte("sale_date", start_date.isoformat())
        if end_date:
            query = query.lte("sale_date", end_date.isoformat())

        result = query.limit(100000).execute()

        if not result.data:
            return []

        # Group by country
        markets = {}
        for r in result.data:
            country = r.get('country') or 'Unknown'
            revenue = float(r.get('sales_eur', 0) or 0)
            units = int(r.get('quantity', 0) or 0)

            if country not in markets:
                markets[country] = {
                    'country': country,
                    'revenue': 0,
                    'units': 0,
                    'transactions': 0
                }

            markets[country]['revenue'] += revenue
            markets[country]['units'] += units
            markets[country]['transactions'] += 1

        # Sort by revenue and return top N
        sorted_markets = sorted(markets.values(), key=lambda x: x['revenue'], reverse=True)
        return sorted_markets[:limit]

    def get_top_resellers(
        self,
        user_id: str,
        limit: int = 10,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[Dict[str, Any]]:
        """
        Get top resellers by revenue (for bar chart)

        Args:
            user_id: User ID for RLS filtering
            limit: Number of top resellers to return
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            List of top resellers with revenue, units, and store count
        """
        # In BIBBI mode (single-tenant database), skip user filtering
        # In multi-tenant mode, filter by user_id via upload_batches JOIN
        if self.is_bibbi_mode:
            query = self.supabase.table("sales_unified")\
                .select("reseller_id,sales_eur,quantity,store_id")
        else:
            query = self.supabase.table("sales_unified")\
                .select("reseller_id,sales_eur,quantity,store_id,upload_batches!inner(uploader_user_id)")\
                .eq("upload_batches.uploader_user_id", user_id)

        # Apply date filters
        if start_date:
            query = query.gte("sale_date", start_date.isoformat())
        if end_date:
            query = query.lte("sale_date", end_date.isoformat())

        result = query.limit(100000).execute()

        if not result.data:
            return []

        # Group by reseller
        resellers = {}
        for r in result.data:
            reseller_id = r.get('reseller_id')
            if not reseller_id:
                continue

            revenue = float(r.get('sales_eur', 0) or 0)
            units = int(r.get('quantity', 0) or 0)
            store_id = r.get('store_id')

            if reseller_id not in resellers:
                resellers[reseller_id] = {
                    'reseller_id': reseller_id,
                    'revenue': 0,
                    'units': 0,
                    'transactions': 0,
                    'stores': set()
                }

            resellers[reseller_id]['revenue'] += revenue
            resellers[reseller_id]['units'] += units
            resellers[reseller_id]['transactions'] += 1
            if store_id:
                resellers[reseller_id]['stores'].add(store_id)

        # Get reseller names
        reseller_ids = list(resellers.keys())
        if reseller_ids:
            resellers_result = self.supabase.table("resellers")\
                .select("id,reseller")\
                .in_("id", reseller_ids)\
                .execute()

            reseller_names = {r['id']: r['reseller'] for r in resellers_result.data}

            # Add names to results
            for reseller_id, data in resellers.items():
                data['reseller_name'] = reseller_names.get(reseller_id, 'Unknown')
                data['store_count'] = len(data['stores'])
                del data['stores']  # Remove set (not JSON serializable)
        else:
            for data in resellers.values():
                data['reseller_name'] = 'Unknown'
                data['store_count'] = 0
                del data['stores']

        # Sort by revenue and return top N
        sorted_resellers = sorted(resellers.values(), key=lambda x: x['revenue'], reverse=True)
        return sorted_resellers[:limit]

    def get_top_stores(
        self,
        user_id: str,
        limit: int = 10,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[Dict[str, Any]]:
        """
        Get top performing stores by revenue

        Args:
            user_id: User ID for RLS filtering
            limit: Number of top stores to return
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            List of top stores with revenue and units
        """
        # In BIBBI mode (single-tenant database), skip user filtering
        # In multi-tenant mode, filter by user_id via upload_batches JOIN
        if self.is_bibbi_mode:
            query = self.supabase.table("sales_unified")\
                .select("store_id,sales_eur,quantity")
        else:
            query = self.supabase.table("sales_unified")\
                .select("store_id,sales_eur,quantity,upload_batches!inner(uploader_user_id)")\
                .eq("upload_batches.uploader_user_id", user_id)

        # Apply date filters
        if start_date:
            query = query.gte("sale_date", start_date.isoformat())
        if end_date:
            query = query.lte("sale_date", end_date.isoformat())

        result = query.limit(100000).execute()

        if not result.data:
            return []

        # Group by store
        stores = {}
        for r in result.data:
            store_id = r.get('store_id')
            if not store_id:
                continue

            revenue = float(r.get('sales_eur', 0) or 0)
            units = int(r.get('quantity', 0) or 0)

            if store_id not in stores:
                stores[store_id] = {
                    'store_id': store_id,
                    'revenue': 0,
                    'units': 0,
                    'transactions': 0
                }

            stores[store_id]['revenue'] += revenue
            stores[store_id]['units'] += units
            stores[store_id]['transactions'] += 1

        # Get store details
        store_ids = list(stores.keys())
        if store_ids:
            stores_result = self.supabase.table("stores")\
                .select("store_id,store_name,city,country")\
                .in_("store_id", store_ids)\
                .execute()

            store_details = {s['store_id']: s for s in stores_result.data}

            # Add store details to results
            for store_id, data in stores.items():
                details = store_details.get(store_id, {})
                data['store_name'] = details.get('store_name', 'Unknown')
                data['city'] = details.get('city', 'Unknown')
                data['country'] = details.get('country', 'Unknown')
        else:
            for data in stores.values():
                data['store_name'] = 'Unknown'
                data['city'] = 'Unknown'
                data['country'] = 'Unknown'

        # Sort by revenue and return top N
        sorted_stores = sorted(stores.values(), key=lambda x: x['revenue'], reverse=True)
        return sorted_stores[:limit]

    def calculate_product_velocity(
        self,
        user_id: str,
        fast_days: int = 30,
        slow_days: int = 90
    ) -> Dict[str, Any]:
        """
        Calculate product velocity (fast-moving vs slow-moving products)

        Args:
            user_id: User ID for RLS filtering
            fast_days: Days threshold for fast-moving products
            slow_days: Days threshold for slow-moving products

        Returns:
            Dictionary with fast and slow moving product counts and lists
        """
        from datetime import timedelta
        today = date.today()
        fast_date = today - timedelta(days=fast_days)
        slow_date = today - timedelta(days=slow_days)

        # In BIBBI mode (single-tenant database), skip user filtering
        # In multi-tenant mode, filter by user_id via upload_batches JOIN

        # Get products sold in last 30 days
        if self.is_bibbi_mode:
            fast_query = self.supabase.table("sales_unified")\
                .select("product_ean,functional_name,quantity,sales_eur")\
                .gte("sale_date", fast_date.isoformat())
        else:
            fast_query = self.supabase.table("sales_unified")\
                .select("product_ean,functional_name,quantity,sales_eur,upload_batches!inner(uploader_user_id)")\
                .eq("upload_batches.uploader_user_id", user_id)\
                .gte("sale_date", fast_date.isoformat())

        fast_result = fast_query.limit(100000).execute()

        # Get products sold in last 90 days
        if self.is_bibbi_mode:
            slow_query = self.supabase.table("sales_unified")\
                .select("product_ean,functional_name,quantity,sales_eur")\
                .gte("sale_date", slow_date.isoformat())
        else:
            slow_query = self.supabase.table("sales_unified")\
                .select("product_ean,functional_name,quantity,sales_eur,upload_batches!inner(uploader_user_id)")\
                .eq("upload_batches.uploader_user_id", user_id)\
                .gte("sale_date", slow_date.isoformat())

        slow_result = slow_query.limit(100000).execute()

        # Aggregate fast-moving products
        fast_products = {}
        if fast_result.data:
            for r in fast_result.data:
                ean = r.get('product_ean')
                if not ean:
                    continue
                if ean not in fast_products:
                    fast_products[ean] = {
                        'product_ean': ean,
                        'product_name': r.get('functional_name', 'Unknown'),
                        'units_sold': 0,
                        'revenue': 0
                    }
                fast_products[ean]['units_sold'] += int(r.get('quantity', 0) or 0)
                fast_products[ean]['revenue'] += float(r.get('sales_eur', 0) or 0)

        # Aggregate all products from 90 days
        all_products = set()
        if slow_result.data:
            for r in slow_result.data:
                ean = r.get('product_ean')
                if ean:
                    all_products.add(ean)

        # Slow movers: sold in 90 days but NOT in 30 days
        slow_movers = all_products - set(fast_products.keys())

        return {
            'fast_moving_count': len(fast_products),
            'slow_moving_count': len(slow_movers),
            'fast_moving_products': sorted(
                fast_products.values(),
                key=lambda x: x['units_sold'],
                reverse=True
            )[:10],  # Top 10 fast movers
            'days_thresholds': {
                'fast_days': fast_days,
                'slow_days': slow_days
            }
        }
