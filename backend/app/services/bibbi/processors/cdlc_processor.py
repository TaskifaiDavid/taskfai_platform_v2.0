"""CDLC (Creme de la Creme) Processor"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BibbiBseProcessor

class CDLCProcessor(BibbiBseProcessor):
    VENDOR_NAME = "cdlc"
    CURRENCY = "EUR"

    def get_vendor_name(self) -> str:
        return self.VENDOR_NAME

    def get_currency(self) -> str:
        return self.CURRENCY

    def extract_stores(self, file_path: str) -> List[Dict[str, Any]]:
        stores = []
        seen = set()
        try:
            wb = self._load_workbook(file_path)
            sheet = wb[wb.sheetnames[0]]
            headers = self._get_sheet_headers(sheet)
            
            store_idx = next((i for i, h in enumerate(headers) if "store" in h.lower() or "shop" in h.lower()), None)
            
            if store_idx:
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    if not any(row): continue
                    store_val = row[store_idx] if store_idx < len(row) else None
                    if store_val:
                        store_str = str(store_val).strip()
                        if store_str and store_str not in seen:
                            seen.add(store_str)
                            is_online = store_str.lower() in ["e-shop", "online", "web"]
                            stores.append({
                                "store_identifier": store_str.lower().replace(' ', '_'),
                                "store_name": f"CDLC {store_str}",
                                "store_type": "online" if is_online else "physical",
                                "reseller_id": self.reseller_id
                            })
            wb.close()
            
            if not stores:
                stores = [{"store_identifier": "e-shop", "store_name": "CDLC E-shop", "store_type": "online", "reseller_id": self.reseller_id}]
        except Exception as e:
            print(f"[CDLC] Error: {e}")
            stores = [{"store_identifier": "e-shop", "store_name": "CDLC E-shop", "store_type": "online", "reseller_id": self.reseller_id}]
        return stores

    def extract_rows(self, file_path: str) -> List[Dict[str, Any]]:
        wb = self._load_workbook(file_path)
        sheet = wb[wb.sheetnames[0]]
        headers = self._get_sheet_headers(sheet)
        rows = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not any(row): continue
            row_dict = {h: row[i] if i < len(row) else None for i, h in enumerate(headers)}
            rows.append(row_dict)
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
        
        sales = raw_row.get("Total") or raw_row.get("Amount")
        if sales is None: raise ValueError("Missing Total/Amount")
        sales_eur = self._to_float(sales, "Total")
        t["sales_local_currency"] = sales_eur
        t["sales_eur"] = sales_eur
        
        month = raw_row.get("Month")
        year = raw_row.get("Year")
        if month and year:
            m, y = self._to_int(month, "Month"), self._to_int(year, "Year")
            t["sale_date"] = datetime(y, m, 1).date().isoformat()
            t["year"], t["month"], t["quarter"] = y, m, self._calculate_quarter(m)
        else:
            now = datetime.utcnow()
            t["sale_date"] = now.date().isoformat()
            t["year"], t["month"], t["quarter"] = now.year, now.month, self._calculate_quarter(now.month)
        
        store = raw_row.get("Store") or raw_row.get("Shop")
        t["store_identifier"] = str(store).strip().lower().replace(' ', '_') if store else "e-shop"
        return t

def get_cdlc_processor(reseller_id: str) -> CDLCProcessor:
    return CDLCProcessor(reseller_id)
