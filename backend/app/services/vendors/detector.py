"""
Vendor detection logic for uploaded files
"""

from pathlib import Path
from typing import Tuple, Optional
import openpyxl


class VendorDetector:
    """Detect vendor from uploaded file"""

    # Vendor detection patterns
    VENDOR_PATTERNS = {
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
            "filename_keywords": ["liberty"],
            "sheet_names": ["Sheet1"],
            "required_columns": ["EAN", "Product", "Sold"]
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
            "filename_keywords": ["continuity"],
            "sheet_names": ["Sheet1"],
            "required_columns": ["EAN", "Product"]
        },
        "online": {
            "filename_keywords": ["online", "ecommerce", "web"],
            "sheet_names": ["Orders", "Sheet1"],
            "required_columns": ["order_id", "ean", "quantity"]
        }
    }

    def detect_vendor(self, file_path: str, filename: str) -> Tuple[Optional[str], float]:
        """
        Detect vendor from file

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

                # Check filename keywords
                filename_lower = filename.lower()
                for keyword in patterns["filename_keywords"]:
                    if keyword.lower() in filename_lower:
                        score += 0.4
                        break

                # Check sheet names
                for sheet_name in patterns["sheet_names"]:
                    if sheet_name in sheet_names:
                        score += 0.3
                        break

                # Check column headers (in first sheet)
                if sheet_names and score > 0:
                    first_sheet = workbook[sheet_names[0]]
                    headers = []

                    # Get first row headers
                    for cell in first_sheet[1]:
                        if cell.value:
                            headers.append(str(cell.value))

                    # Check required columns
                    matching_columns = 0
                    for required_col in patterns["required_columns"]:
                        if any(required_col.lower() in header.lower() for header in headers):
                            matching_columns += 1

                    if matching_columns > 0:
                        score += (matching_columns / len(patterns["required_columns"])) * 0.3

                # Update best match
                if score > best_score:
                    best_score = score
                    best_match = vendor

            workbook.close()

            # Only return vendor if confidence is above threshold
            if best_score >= 0.5:
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
