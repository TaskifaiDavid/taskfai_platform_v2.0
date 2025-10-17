"""Selfridges Processor - 4 physical stores + 1 online, weekly reports"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BibbiBseProcessor

class SelfridgesProcessor(BibbiBseProcessor):
    VENDOR_NAME = "selfridges"
    CURRENCY = "GBP"

    def get_vendor_name(self) -> str:
        return self.VENDOR_NAME

    def get_currency(self) -> str:
        return self.CURRENCY

    def extract_stores(self, file_path: str) -> List[Dict[str, Any]]:
        return [
            {"store_identifier": "london", "store_name": "Selfridges London", "store_type": "physical", "reseller_id": self.reseller_id, "city": "London", "country": "UK"},
            {"store_identifier": "manchester", "store_name": "Selfridges Manchester", "store_type": "physical", "reseller_id": self.reseller_id, "city": "Manchester", "country": "UK"},
            {"store_identifier": "birmingham", "store_name": "Selfridges Birmingham", "store_type": "physical", "reseller_id": self.reseller_id, "city": "Birmingham", "country": "UK"},
            {"store_identifier": "trafford", "store_name": "Selfridges Trafford", "store_type": "physical", "reseller_id": self.reseller_id, "city": "Manchester", "country": "UK"},
            {"store_identifier": "online", "store_name": "Selfridges Online", "store_type": "online", "reseller_id": self.reseller_id, "country": "UK"}
        ]

    def extract_rows(self, file_path: str) -> List[Dict[str, Any]]:
        wb = self._load_workbook(file_path)
        sheet = wb[wb.sheetnames[0]]
        headers = self._get_sheet_headers(sheet)
        rows = [{h: row[i] if i < len(row) else None for i, h in enumerate(headers)} for row in sheet.iter_rows(min_row=2, values_only=True) if any(row)]
        wb.close()
        return rows

    def transform_row(self, raw_row: Dict[str, Any], batch_id: str) -> Optional[Dict[str, Any]]:
        t = self._create_base_row(batch_id)
        
        ean = raw_row.get("EAN") or raw_row.get("Product EAN")
        if not ean: raise ValueError("Missing EAN")
        t["product_id"] = self._validate_ean(ean)
        
        qty = raw_row.get("Sold") or raw_row.get("Quantity")
        if qty is None: raise ValueError("Missing Sold/Quantity")
        t["quantity"] = self._to_int(qty, "Sold")
        t["is_return"] = False
        
        sales = raw_row.get("Sales") or raw_row.get("Amount")
        if sales is None: raise ValueError("Missing Sales/Amount")
        sales_gbp = self._to_float(sales, "Sales")
        t["sales_local_currency"] = sales_gbp
        t["sales_eur"] = self._convert_currency(sales_gbp, "GBP")
        
        date_val = raw_row.get("Date") or raw_row.get("Week")
        if date_val:
            try:
                dt = self._validate_date(date_val)
                t["sale_date"], t["year"], t["month"], t["quarter"] = dt.date().isoformat(), dt.year, dt.month, self._calculate_quarter(dt.month)
            except:
                now = datetime.utcnow()
                t["sale_date"], t["year"], t["month"], t["quarter"] = now.date().isoformat(), now.year, now.month, self._calculate_quarter(now.month)
        else:
            now = datetime.utcnow()
            t["sale_date"], t["year"], t["month"], t["quarter"] = now.date().isoformat(), now.year, now.month, self._calculate_quarter(now.month)
        
        store = raw_row.get("Store") or raw_row.get("Location")
        if store:
            s = str(store).strip().lower()
            if "online" in s: t["store_identifier"] = "online"
            elif "london" in s: t["store_identifier"] = "london"
            elif "manchester" in s or "trafford" in s: t["store_identifier"] = "manchester"
            elif "birmingham" in s: t["store_identifier"] = "birmingham"
            else: t["store_identifier"] = "london"
        else:
            t["store_identifier"] = "london"
        return t

def get_selfridges_processor(reseller_id: str) -> SelfridgesProcessor:
    return SelfridgesProcessor(reseller_id)
