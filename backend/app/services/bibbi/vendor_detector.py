"""
BIBBI Vendor Detection Service

Detects which reseller a file belongs to based on filename, sheet names, and column headers.

Supports 8 BIBBI resellers:
1. Aromateque
2. Boxnox
3. Creme de la Creme (CDLC)
4. Galilu
5. Liberty
6. Selfridges
7. Skins NL
8. Skins SA
"""

from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import openpyxl


class BibbιVendorDetector:
    """Detect vendor from uploaded file for BIBBI tenant"""

    # BIBBI-specific vendor detection patterns
    # Based on /backend/BIBBI/Resellers/resellers_info.md
    BIBBI_VENDOR_PATTERNS = {
        "aromateque": {
            "filename_keywords": ["aromateque"],
            "sheet_names": ["Sheet1", "Sales", "Data"],
            "required_columns": ["Brand", "Month", "Product"],
            "store_indicators": ["Store", "Location", "Shop"],
            "currency": "EUR",
            "description": "Aromateque - Living document (monthly additions)"
        },
        "boxnox": {
            "filename_keywords": ["boxnox"],
            "sheet_names": ["Sell Out by EAN", "Sheet1"],
            "required_columns": ["Product EAN", "Functional Name", "Sold Qty", "Sales Amount"],
            "store_indicators": ["POS"],  # POS column = store identifier
            "currency": "EUR",
            "description": "BOXNOX - Monthly reports with POS store tracking"
        },
        "cdlc": {
            "filename_keywords": ["cdlc", "creme", "corner"],
            "sheet_names": ["Sheet1", "Sales"],
            "required_columns": ["EAN", "Product", "Total"],
            "store_indicators": ["e-shop", "Store"],  # "e-shop" = online
            "currency": "EUR",
            "description": "Creme de la Creme - EAN needs conversion to functional name"
        },
        "galilu": {
            "filename_keywords": ["galilu", "poland"],
            "sheet_names": ["Sheet1", "Data"],  # Multiple sheets = multiple stores
            "required_columns": ["Product", "Month", "Year"],
            "store_indicators": ["sheet_name"],  # Each sheet = different store
            "currency": "PLN",
            "multi_sheet_stores": True,  # Special flag: each sheet is a store
            "description": "Galilu - No EAN, needs product matching, multi-sheet stores"
        },
        "liberty": {
            "filename_keywords": ["liberty", "continuity", "supplier size report", "supplier report", "weekly sell"],
            "sheet_names": ["Sheet1", "Sales", "Sales By Size", "Size Analysis", "Product Group Analysis", "Total", "Total 2023", "Total 2024", "Total 2025", "w."],
            "required_columns": ["EAN", "Product", "Sold", "Value", "Flagship", "Internet", "Sales Channel", "Warehouse", "Brand", "Weekly", "sku"],
            "store_indicators": ["Flagship", "online", "Internet", "All Sales Channels"],  # Flagship = physical
            "currency": "GBP",
            "special_handling": ["duplicate_rows", "returns_in_parentheses"],
            "description": "Liberty - GBP to EUR, duplicate rows, returns parsing, supports both weekly and continuity formats"
        },
        "selfridges": {
            "filename_keywords": ["selfridges"],
            "sheet_names": ["Sheet1", "Weekly", "Sales"],
            "required_columns": ["EAN", "Product", "Sold", "Sales"],
            "store_indicators": ["Store 1", "Store 2", "Store 3", "Store 4", "online"],
            "frequency": "weekly",
            "currency": "GBP",
            "description": "Selfridges - 4 physical stores + 1 online, weekly reports"
        },
        "skins_nl": {
            "filename_keywords": ["skins", "netherlands", "nl"],
            "sheet_names": ["SalesPerLocation", "Sheet1"],
            "required_columns": ["EAN", "Product"],
            "store_indicators": ["Location", "Store"],
            "sheet_specific": "SalesPerLocation",  # Must use this sheet
            "currency": "EUR",
            "description": "Skins NL - Sales per location sheet, reports to SA"
        },
        "skins_sa": {
            "filename_keywords": ["skins", "south africa", "sa", "rand"],
            "sheet_names": ["Sheet1", "Sales"],
            "required_columns": ["OrderDate", "Stockcode", "Qty", "Amount"],
            "store_indicators": ["column_a"],  # Column A: "ON" = online
            "currency": "ZAR",
            "special_handling": ["column_a_store_codes"],
            "description": "Skins SA - ZAR currency, Column A for store codes"
        }
    }

    def detect_vendor(
        self,
        file_path: str,
        filename: str
    ) -> Tuple[Optional[str], float, Dict[str, Any]]:
        """
        Detect vendor from file

        Args:
            file_path: Path to uploaded file
            filename: Original filename

        Returns:
            Tuple of (vendor_name, confidence_score, metadata)
            Returns (None, 0.0, {}) if vendor cannot be detected

        Metadata includes:
            - detected_vendor: Vendor name
            - confidence: Confidence score (0.0-1.0)
            - currency: Expected currency
            - has_store_column: Whether store data is present
            - sheet_info: Sheet names and structure
            - special_handling: List of special cases to handle
        """
        file_path_obj = Path(file_path)
        file_ext = file_path_obj.suffix.lower()

        # Only support Excel files for BIBBI resellers
        if file_ext not in [".xlsx", ".xls"]:
            return None, 0.0, {}

        return self._detect_from_excel(file_path, filename)

    def _detect_from_excel(
        self,
        file_path: str,
        filename: str
    ) -> Tuple[Optional[str], float, Dict[str, Any]]:
        """
        Detect vendor from Excel file with enhanced metadata

        Returns vendor name, confidence score, and detailed metadata for processing
        """
        try:
            workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            sheet_names = workbook.sheetnames

            best_match = None
            best_score = 0.0
            best_metadata = {}

            for vendor, patterns in self.BIBBI_VENDOR_PATTERNS.items():
                score = 0.0
                metadata = {
                    "vendor": vendor,
                    "currency": patterns.get("currency"),
                    "description": patterns.get("description"),
                    "special_handling": patterns.get("special_handling", []),
                    "store_indicators": patterns.get("store_indicators", []),
                    "sheet_info": []
                }

                # 1. Check filename keywords (40% weight)
                filename_lower = filename.lower()
                for keyword in patterns["filename_keywords"]:
                    if keyword.lower() in filename_lower:
                        score += 0.4
                        metadata["filename_match"] = keyword
                        break

                # 2. Check sheet names (30% weight)
                for pattern_sheet in patterns["sheet_names"]:
                    if pattern_sheet in sheet_names:
                        score += 0.3
                        metadata["sheet_match"] = pattern_sheet
                        break

                # 3. Check column headers in first sheet (30% weight)
                if sheet_names and score > 0:
                    first_sheet = workbook[sheet_names[0]]
                    headers = []

                    # Get first row headers
                    for cell in first_sheet[1]:
                        if cell.value:
                            headers.append(str(cell.value))

                    # Check required columns
                    matching_columns = 0
                    matched_cols = []
                    for required_col in patterns["required_columns"]:
                        for header in headers:
                            if required_col.lower() in header.lower():
                                matching_columns += 1
                                matched_cols.append(required_col)
                                break

                    if matching_columns > 0:
                        column_score = (matching_columns / len(patterns["required_columns"])) * 0.3
                        score += column_score
                        metadata["matched_columns"] = matched_cols
                        metadata["column_headers"] = headers

                # 4. Store detection hints
                metadata["has_store_column"] = self._detect_store_column(
                    sheet_names,
                    patterns.get("store_indicators", []),
                    workbook
                )

                # 5. Special flags
                metadata["multi_sheet_stores"] = patterns.get("multi_sheet_stores", False)
                metadata["frequency"] = patterns.get("frequency", "monthly")

                # 6. Sheet information
                for sheet_name in sheet_names:
                    metadata["sheet_info"].append({
                        "name": sheet_name,
                        "is_primary": sheet_name == patterns["sheet_names"][0] if patterns["sheet_names"] else False
                    })

                # Update best match
                if score > best_score:
                    best_score = score
                    best_match = vendor
                    best_metadata = metadata

            workbook.close()

            # Only return vendor if confidence is above threshold
            if best_score >= 0.5:
                return best_match, best_score, best_metadata

            return None, 0.0, {}

        except Exception as e:
            print(f"[BibbιVendorDetector] Error detecting vendor: {e}")
            return None, 0.0, {}

    def _detect_store_column(
        self,
        sheet_names: list,
        store_indicators: list,
        workbook
    ) -> bool:
        """
        Detect if file contains store-level data

        Checks:
        - Column headers for store indicators
        - Multiple sheets (Galilu pattern)
        - Specific column patterns (Skins SA Column A)

        Returns:
            True if store data detected
        """
        if not store_indicators:
            return False

        # Check for multi-sheet store pattern (Galilu)
        if "sheet_name" in store_indicators and len(sheet_names) > 1:
            return True

        # Check first sheet for store columns
        if sheet_names:
            first_sheet = workbook[sheet_names[0]]
            headers = []

            for cell in first_sheet[1]:
                if cell.value:
                    headers.append(str(cell.value).lower())

            # Check if any store indicator is in headers
            for indicator in store_indicators:
                indicator_lower = indicator.lower()
                for header in headers:
                    if indicator_lower in header:
                        return True

        return False


# Global instance for BIBBI vendor detection
bibbi_vendor_detector = BibbιVendorDetector()


def detect_bibbi_vendor(
    file_path: str,
    filename: str
) -> Tuple[Optional[str], float, Dict[str, Any]]:
    """
    Convenience function for BIBBI vendor detection

    Args:
        file_path: Path to uploaded file
        filename: Original filename

    Returns:
        Tuple of (vendor_name, confidence_score, metadata)
    """
    return bibbi_vendor_detector.detect_vendor(file_path, filename)
