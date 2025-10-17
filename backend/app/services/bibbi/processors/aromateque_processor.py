"""Aromateque Processor - Living document with monthly additions"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BibbiBseProcessor

class AromatequProcessor(BibbiBseProcessor):
    VENDOR_NAME = "aromateque"
    CURRENCY = "EUR"

    def get_vendor_name(self) -> str:
        return self.VENDOR_NAME

    def get_currency(self) -> str:
        return self.CURRENCY

    def extract_stores(self, file_path: str) -> List[Dict[str, Any]]:
        stores = []
        try:
            wb = self._load_workbook(file_path)
            sheet = wb[wb.sheetnames[0]]
            headers = self._get_sheet_headers(sheet)
            
            store_idx = next((i for i, h in enumerate(headers) if "store" in h.lower() or "location" in h.lower()), None)
            if store_idx:
                seen = set()
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    if not any(row): continue
                    sv = row[store_idx] if store_idx < len(row) else None
                    if sv and str(sv).strip() not in seen:
                        s = str(sv).strip()
                        seen.add(s)
                        stores.append({
                            "store_identifier": s.lower().replace(' ', '_'),
                            "store_name": f"Aromateque {s}",
                            "store_type": "online" if "online" in s.lower() else "physical",
                            "reseller_id": self.reseller_id
                        })
            wb.close()
            
            if not stores:
                stores = [{"store_identifier": "main", "store_name": "Aromateque Main", "store_type": "physical", "reseller_id": self.reseller_id}]
        except:
            stores = [{"store_identifier": "main", "store_name": "Aromateque Main", "store_type": "physical", "reseller_id": self.reseller_id}]
        return stores

    def extract_rows(self, file_path: str) -> List[Dict[str, Any]]:
        wb = self._load_workbook(file_path)
        sheet = wb[wb.sheetnames[0]]
        headers = self._get_sheet_headers(sheet)
        rows = [{h: row[i] if i < len(row) else None for i, h in enumerate(headers)} for row in sheet.iter_rows(min_row=2, values_only=True) if any(row)]
        wb.close()
        return rows

    def transform_row(self, raw_row: Dict[str, Any], batch_id: str) -> Optional[Dict[str, Any]]:
        t = self._create_base_row(batch_id)
        
        ean = raw_row.get("EAN") or raw_row.get("Brand")
        if not ean: raise ValueError("Missing EAN/Brand")
        try:
            t["product_id"] = self._validate_ean(ean)
        except:
            raise ValueError(f"Invalid EAN: {ean}")
        
        qty = raw_row.get("Quantity") or raw_row.get("Qty")
        if qty is None: raise ValueError("Missing Quantity")
        t["quantity"] = self._to_int(qty, "Quantity")
        t["is_return"] = False
        
        sales = raw_row.get("Amount") or raw_row.get("Total")
        if sales is None: raise ValueError("Missing Amount")
        sales_eur = self._to_float(sales, "Amount")
        t["sales_local_currency"] = sales_eur
        t["sales_eur"] = sales_eur
        
        month, year = raw_row.get("Month"), raw_row.get("Year")
        if month and year:
            m, y = self._to_int(month, "Month"), self._to_int(year, "Year")
            t["sale_date"], t["year"], t["month"], t["quarter"] = datetime(y, m, 1).date().isoformat(), y, m, self._calculate_quarter(m)
        else:
            now = datetime.utcnow()
            t["sale_date"], t["year"], t["month"], t["quarter"] = now.date().isoformat(), now.year, now.month, self._calculate_quarter(now.month)
        
        store = raw_row.get("Store") or raw_row.get("Location")
        t["store_identifier"] = str(store).strip().lower().replace(' ', '_') if store else "main"
        return t

def get_aromateque_processor(reseller_id: str) -> AromatequProcessor:
    return AromatequProcessor(reseller_id)
