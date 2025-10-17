"""Skins NL Processor - SalesPerLocation sheet, reports to SA"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BibbiBseProcessor

class SkinsNLProcessor(BibbiBseProcessor):
    VENDOR_NAME = "skins_nl"
    CURRENCY = "EUR"
    TARGET_SHEET = "SalesPerLocation"

    def get_vendor_name(self) -> str:
        return self.VENDOR_NAME

    def get_currency(self) -> str:
        return self.CURRENCY

    def extract_stores(self, file_path: str) -> List[Dict[str, Any]]:
        stores = []
        try:
            wb = self._load_workbook(file_path)
            sheet = wb.get(self.TARGET_SHEET) or wb[wb.sheetnames[0]]
            headers = self._get_sheet_headers(sheet)
            
            loc_idx = next((i for i, h in enumerate(headers) if "location" in h.lower() or "store" in h.lower()), None)
            if loc_idx:
                seen = set()
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    if not any(row): continue
                    lv = row[loc_idx] if loc_idx < len(row) else None
                    if lv and str(lv).strip() not in seen:
                        s = str(lv).strip()
                        seen.add(s)
                        stores.append({
                            "store_identifier": s.lower().replace(' ', '_'),
                            "store_name": f"Skins NL {s}",
                            "store_type": "online" if "online" in s.lower() else "physical",
                            "reseller_id": self.reseller_id,
                            "country": "Netherlands"
                        })
            wb.close()
            
            if not stores:
                stores = [{"store_identifier": "main", "store_name": "Skins NL Main", "store_type": "physical", "reseller_id": self.reseller_id, "country": "Netherlands"}]
        except:
            stores = [{"store_identifier": "main", "store_name": "Skins NL Main", "store_type": "physical", "reseller_id": self.reseller_id, "country": "Netherlands"}]
        return stores

    def extract_rows(self, file_path: str) -> List[Dict[str, Any]]:
        wb = self._load_workbook(file_path)
        sheet = wb.get(self.TARGET_SHEET) or wb[wb.sheetnames[0]]
        headers = self._get_sheet_headers(sheet)
        rows = [{h: row[i] if i < len(row) else None for i, h in enumerate(headers)} for row in sheet.iter_rows(min_row=2, values_only=True) if any(row)]
        wb.close()
        return rows

    def transform_row(self, raw_row: Dict[str, Any], batch_id: str) -> Optional[Dict[str, Any]]:
        t = self._create_base_row(batch_id)
        
        ean = raw_row.get("EAN") or raw_row.get("Product EAN")
        if not ean: raise ValueError("Missing EAN")
        t["product_id"] = self._validate_ean(ean)
        
        qty = raw_row.get("Quantity") or raw_row.get("Qty")
        if qty is None: raise ValueError("Missing Quantity")
        t["quantity"] = self._to_int(qty, "Quantity")
        t["is_return"] = False
        
        sales = raw_row.get("Amount") or raw_row.get("Sales")
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
        
        loc = raw_row.get("Location") or raw_row.get("Store")
        t["store_identifier"] = str(loc).strip().lower().replace(' ', '_') if loc else "main"
        return t

def get_skins_nl_processor(reseller_id: str) -> SkinsNLProcessor:
    return SkinsNLProcessor(reseller_id)
