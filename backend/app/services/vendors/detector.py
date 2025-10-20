"""
Vendor detection logic for uploaded files

Enhanced with fuzzy matching and content validation for robust vendor identification.
"""

from pathlib import Path
from typing import Tuple, Optional
import openpyxl
import difflib


class VendorDetector:
    """Detect vendor from uploaded file"""

    # Vendor detection patterns
    VENDOR_PATTERNS = {
        "demo": {
            "filename_keywords": ["demo"],
            "sheet_names": ["Sheet1"],
            "required_columns": ["Brand", "BrandName", "Month", "Information"]
        },
        "boxnox": {
            "filename_keywords": ["boxnox"],
            "sheet_names": ["Sell Out by EAN"],
            "required_columns": ["Product EAN", "Functional Name", "Sold Qty", "Sales Amount (EUR)"]
        },
        "galilu": {
            "filename_keywords": ["galilu", "poland"],
            "sheet_names": ["Sheet1", "Data"],
            "required_columns": ["EAN", "Product", "Month", "Year"]
        },
        "skins_sa": {
            "filename_keywords": ["skins", "south africa", "sa"],
            "sheet_names": ["Sheet1"],
            "required_columns": ["OrderDate", "EAN", "Qty", "Amount"]
        },
        "cdlc": {
            "filename_keywords": ["cdlc", "corner"],
            "sheet_names": ["Sheet1"],
            "required_columns": ["Product", "Total"]
        },
        "liberty": {
            "filename_keywords": ["liberty", "continuity", "supplier size report", "supplier report", "weekly sell"],
            "sheet_names": ["Sheet1", "Sales", "Sales By Size", "Size Analysis", "Product Group Analysis", "Total", "Total 2023", "Total 2024", "Total 2025", "w."],
            "required_columns": ["EAN", "Product", "Sold", "Value", "Flagship", "Internet", "Sales Channel", "Warehouse", "Brand", "Weekly", "sku"]
        },
        "selfridges": {
            "filename_keywords": ["selfridges"],
            "sheet_names": ["Sheet1"],
            "required_columns": ["EAN", "Product", "Sold"]
        },
        "ukraine": {
            "filename_keywords": ["ukraine", "tdsheet"],
            "sheet_names": ["TDSheet"],
            "required_columns": ["EAN", "Product"]
        },
        "skins_nl": {
            "filename_keywords": ["skins", "netherlands", "nl"],
            "sheet_names": ["Sheet1"],
            "required_columns": ["EAN", "Product"]
        },
        "continuity": {
            "filename_keywords": ["continuity", "supplier", "size report"],
            "sheet_names": ["Sheet1"],
            "required_columns": ["EAN", "Product", "Units", "Value", "Period"]
        },
        "online": {
            "filename_keywords": ["online", "ecommerce", "web"],
            "sheet_names": ["Orders", "Sheet1"],
            "required_columns": ["order_id", "ean", "quantity"]
        }
    }

    def _fuzzy_match_columns(self, headers: list[str], required_columns: list[str]) -> float:
        """
        Fuzzy match columns using similarity scoring

        Args:
            headers: Actual column headers from file
            required_columns: Required column names for vendor

        Returns:
            Match ratio (0.0 to 1.0)
        """
        if not required_columns:
            return 0.0

        headers_lower = [h.lower().strip() for h in headers if h]
        matched_count = 0

        for required_col in required_columns:
            required_lower = required_col.lower().strip()

            # Try exact match first
            if any(required_lower == h for h in headers_lower):
                matched_count += 1
                continue

            # Try fuzzy matching with 0.8 similarity threshold
            best_match = 0.0
            for header in headers_lower:
                # Use SequenceMatcher for fuzzy string comparison
                similarity = difflib.SequenceMatcher(None, required_lower, header).ratio()
                if similarity > best_match:
                    best_match = similarity

            # Consider it a match if similarity >= 0.8
            if best_match >= 0.8:
                matched_count += 1

        return matched_count / len(required_columns)

    def detect_vendor(self, file_path: str, filename: str) -> Tuple[Optional[str], float]:
        """
        Detect vendor from file using multi-factor analysis

        Args:
            file_path: Path to uploaded file
            filename: Original filename

        Returns:
            Tuple of (vendor_name, confidence_score)
            Returns (None, 0.0) if vendor cannot be detected
        """
        file_path_obj = Path(file_path)
        file_ext = file_path_obj.suffix.lower()

        # Check file type
        if file_ext in [".xlsx", ".xls"]:
            return self._detect_from_excel(file_path, filename)
        elif file_ext == ".csv":
            return self._detect_from_csv(file_path, filename)
        else:
            return None, 0.0

    def _detect_from_excel(self, file_path: str, filename: str) -> Tuple[Optional[str], float]:
        """
        Detect vendor from Excel file

        Args:
            file_path: Path to Excel file
            filename: Original filename

        Returns:
            Tuple of (vendor_name, confidence_score)
        """
        try:
            workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            sheet_names = workbook.sheetnames

            best_match = None
            best_score = 0.0

            for vendor, patterns in self.VENDOR_PATTERNS.items():
                score = 0.0

                # Check filename keywords (weight: 30%)
                filename_lower = filename.lower()
                for keyword in patterns["filename_keywords"]:
                    if keyword.lower() in filename_lower:
                        score += 0.3
                        break

                # Check sheet names (weight: 30%)
                for sheet_name in patterns["sheet_names"]:
                    if sheet_name in sheet_names:
                        score += 0.3
                        break

                # Check column headers using fuzzy matching (weight: 40%)
                if sheet_names:
                    first_sheet = workbook[sheet_names[0]]
                    headers = []

                    # Get first row headers
                    for cell in first_sheet[1]:
                        if cell.value:
                            headers.append(str(cell.value))

                    # Use fuzzy column matching
                    column_match_ratio = self._fuzzy_match_columns(headers, patterns["required_columns"])
                    score += column_match_ratio * 0.4

                # Update best match
                if score > best_score:
                    best_score = score
                    best_match = vendor

            workbook.close()

            # Lowered threshold from 0.5 to 0.4 for real-world file variance
            if best_score >= 0.4:
                return best_match, best_score

            return None, 0.0

        except Exception as e:
            print(f"Error detecting vendor from Excel: {e}")
            return None, 0.0

    def _detect_from_csv(self, file_path: str, filename: str) -> Tuple[Optional[str], float]:
        """
        Detect vendor from CSV file

        Args:
            file_path: Path to CSV file
            filename: Original filename

        Returns:
            Tuple of (vendor_name, confidence_score)
        """
        try:
            # Read first line to get headers
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                headers = [h.strip() for h in first_line.split(',')]

            best_match = None
            best_score = 0.0

            for vendor, patterns in self.VENDOR_PATTERNS.items():
                score = 0.0

                # Check filename keywords
                filename_lower = filename.lower()
                for keyword in patterns["filename_keywords"]:
                    if keyword.lower() in filename_lower:
                        score += 0.5
                        break

                # Check column headers
                matching_columns = 0
                for required_col in patterns["required_columns"]:
                    if any(required_col.lower() in header.lower() for header in headers):
                        matching_columns += 1

                if matching_columns > 0:
                    score += (matching_columns / len(patterns["required_columns"])) * 0.5

                # Update best match
                if score > best_score:
                    best_score = score
                    best_match = vendor

            # Only return vendor if confidence is above threshold
            if best_score >= 0.5:
                return best_match, best_score

            return None, 0.0

        except Exception as e:
            print(f"Error detecting vendor from CSV: {e}")
            return None, 0.0


# Global instance
vendor_detector = VendorDetector()
