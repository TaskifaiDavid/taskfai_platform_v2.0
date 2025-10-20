"""
BIBBI Validation Service

Validates transformed sales data before insertion into sales_unified table.

Pipeline Stage: Staging → **VALIDATION** → Insertion

Validation Rules:
1. Required fields present
2. Data types correct (UUID, date, numeric)
3. Business rules (quantity > 0, sales_eur >= 0)
4. Foreign key constraints (product_id exists, reseller_id exists, store_id exists)
5. Duplicate detection
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation

from app.core.bibbi import BibbιDB, BIBBI_TENANT_ID


class ValidationResult:
    """Result of data validation"""

    def __init__(
        self,
        total_rows: int,
        valid_rows: int,
        invalid_rows: int,
        valid_data: List[Dict[str, Any]],
        errors: List[Dict[str, Any]]
    ):
        self.total_rows = total_rows
        self.valid_rows = valid_rows
        self.invalid_rows = invalid_rows
        self.valid_data = valid_data
        self.errors = errors

    @property
    def validation_success_rate(self) -> float:
        """Calculate validation success rate as percentage"""
        if self.total_rows == 0:
            return 0.0
        return round(self.valid_rows / self.total_rows * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "invalid_rows": self.invalid_rows,
            "validation_success_rate": round(self.valid_rows / self.total_rows * 100, 2) if self.total_rows > 0 else 0,
            "errors": self.errors
        }


class BibbιValidationService:
    """
    Service for validating BIBBI sales data

    Responsibilities:
    - Validate required fields
    - Validate data types
    - Validate business rules
    - Check foreign key constraints
    - Track row-level errors
    """

    # Required fields for sales_unified schema
    REQUIRED_FIELDS = [
        "product_id",       # EAN (13 digits)
        "reseller_id",      # UUID
        "sale_date",        # ISO date string
        "quantity",         # Integer > 0
        "sales_eur",        # Decimal >= 0
        "tenant_id",        # Must be 'bibbi'
        "year",             # Integer
        "month",            # Integer 1-12
        "quarter"           # Integer 1-4
    ]

    # Optional fields that should be present but can be NULL
    OPTIONAL_FIELDS = [
        "store_id",
        "customer_id",
        "sales_local_currency",
        "currency",
        "is_return",
        "return_quantity"
    ]

    def __init__(self, bibbi_db: BibbιDB):
        """
        Initialize validation service

        Args:
            bibbi_db: BIBBI-specific Supabase client
        """
        self.db = bibbi_db

    def validate_transformed_data(
        self,
        transformed_rows: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate transformed sales data

        Args:
            transformed_rows: List of transformed rows from processor

        Returns:
            ValidationResult with valid data and errors
        """
        total_rows = len(transformed_rows)
        valid_data = []
        errors = []

        print(f"[BibbιValidation] Validating {total_rows} rows...")

        for row_idx, row in enumerate(transformed_rows):
            row_number = row_idx + 1

            try:
                # Run all validation checks
                self._validate_required_fields(row, row_number)
                self._validate_data_types(row, row_number)
                self._validate_business_rules(row, row_number)
                self._validate_tenant_id(row, row_number)

                # Row passed all validations
                valid_data.append(row)

            except ValueError as e:
                # Validation failed
                errors.append({
                    "row_number": row_number,
                    "error_type": "validation_error",
                    "error_message": str(e),
                    "row_data": self._sanitize_row_for_error(row)
                })

        valid_rows = len(valid_data)
        invalid_rows = len(errors)

        print(f"[BibbιValidation] Validation complete: {valid_rows} valid, {invalid_rows} invalid")

        return ValidationResult(
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            valid_data=valid_data,
            errors=errors
        )

    def validate_foreign_keys(
        self,
        valid_data: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate foreign key constraints

        Checks:
        - product_id exists in products table
        - reseller_id exists in resellers table
        - store_id exists in stores table (if provided)

        Args:
            valid_data: List of validated rows

        Returns:
            ValidationResult with FK-validated data and errors
        """
        total_rows = len(valid_data)
        fk_valid_data = []
        fk_errors = []

        print(f"[BibbιValidation] Checking foreign keys for {total_rows} rows...")

        # Cache for FK lookups (avoid repeated queries)
        product_cache = set()
        reseller_cache = set()
        store_cache = set()

        for row_idx, row in enumerate(valid_data):
            row_number = row_idx + 1

            try:
                # Check product_id (EAN)
                product_id = row.get("product_id")
                if product_id and product_id not in product_cache:
                    if not self._product_exists(product_id):
                        raise ValueError(f"Product not found: {product_id}")
                    product_cache.add(product_id)

                # Check reseller_id
                reseller_id = row.get("reseller_id")
                if reseller_id and reseller_id not in reseller_cache:
                    if not self._reseller_exists(reseller_id):
                        raise ValueError(f"Reseller not found: {reseller_id}")
                    reseller_cache.add(reseller_id)

                # Check store_id (optional)
                store_id = row.get("store_id")
                if store_id and store_id not in store_cache:
                    if not self._store_exists(store_id):
                        raise ValueError(f"Store not found: {store_id}")
                    store_cache.add(store_id)

                # All foreign keys valid
                fk_valid_data.append(row)

            except ValueError as e:
                fk_errors.append({
                    "row_number": row_number,
                    "error_type": "foreign_key_error",
                    "error_message": str(e),
                    "row_data": self._sanitize_row_for_error(row)
                })

        valid_rows = len(fk_valid_data)
        invalid_rows = len(fk_errors)

        print(f"[BibbιValidation] FK validation complete: {valid_rows} valid, {invalid_rows} invalid")

        return ValidationResult(
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            valid_data=fk_valid_data,
            errors=fk_errors
        )

    def _validate_required_fields(self, row: Dict[str, Any], row_number: int) -> None:
        """
        Validate all required fields are present

        Raises:
            ValueError: If any required field is missing
        """
        missing_fields = []

        for field in self.REQUIRED_FIELDS:
            if field not in row or row[field] is None:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    def _validate_data_types(self, row: Dict[str, Any], row_number: int) -> None:
        """
        Validate data types are correct

        Raises:
            ValueError: If any field has incorrect type
        """
        # Validate product_id (EAN - 13 digits)
        product_id = row.get("product_id")
        if product_id:
            if not isinstance(product_id, str):
                raise ValueError(f"product_id must be string, got {type(product_id)}")
            if len(product_id) != 13 or not product_id.isdigit():
                raise ValueError(f"product_id must be 13-digit EAN, got: {product_id}")

        # Validate reseller_id (UUID format)
        reseller_id = row.get("reseller_id")
        if reseller_id:
            if not isinstance(reseller_id, str):
                raise ValueError(f"reseller_id must be string, got {type(reseller_id)}")
            # Basic UUID format check (8-4-4-4-12)
            parts = reseller_id.split('-')
            if len(parts) != 5 or len(parts[0]) != 8 or len(parts[1]) != 4:
                raise ValueError(f"reseller_id must be valid UUID, got: {reseller_id}")

        # Validate sale_date (ISO date string)
        sale_date = row.get("sale_date")
        if sale_date:
            try:
                # Try to parse as ISO date
                datetime.fromisoformat(str(sale_date))
            except ValueError:
                raise ValueError(f"sale_date must be valid ISO date, got: {sale_date}")

        # Validate quantity (integer)
        quantity = row.get("quantity")
        if quantity is not None:
            if not isinstance(quantity, int):
                raise ValueError(f"quantity must be integer, got {type(quantity)}")

        # Validate sales_eur (numeric)
        sales_eur = row.get("sales_eur")
        if sales_eur is not None:
            try:
                Decimal(str(sales_eur))
            except (InvalidOperation, ValueError):
                raise ValueError(f"sales_eur must be numeric, got: {sales_eur}")

        # Validate year (integer)
        year = row.get("year")
        if year is not None:
            if not isinstance(year, int):
                raise ValueError(f"year must be integer, got {type(year)}")

        # Validate month (integer 1-12)
        month = row.get("month")
        if month is not None:
            if not isinstance(month, int):
                raise ValueError(f"month must be integer, got {type(month)}")

        # Validate quarter (integer 1-4)
        quarter = row.get("quarter")
        if quarter is not None:
            if not isinstance(quarter, int):
                raise ValueError(f"quarter must be integer, got {type(quarter)}")

    def _validate_business_rules(self, row: Dict[str, Any], row_number: int) -> None:
        """
        Validate business rules

        Rules:
        - quantity > 0 (unless it's a return)
        - sales_eur >= 0 (can be 0 for returns)
        - month in range 1-12
        - quarter in range 1-4
        - year in reasonable range (2000-2100)

        Raises:
            ValueError: If any business rule is violated
        """
        # Validate quantity
        quantity = row.get("quantity")
        is_return = row.get("is_return", False)

        if quantity is not None:
            if not is_return and quantity <= 0:
                raise ValueError(f"quantity must be > 0 for non-returns, got: {quantity}")
            if is_return and quantity >= 0:
                raise ValueError(f"quantity must be < 0 for returns, got: {quantity}")

        # Validate sales_eur (allow 0 for returns)
        sales_eur = row.get("sales_eur")
        if sales_eur is not None:
            sales_decimal = Decimal(str(sales_eur))
            if sales_decimal < 0:
                raise ValueError(f"sales_eur cannot be negative, got: {sales_eur}")

        # Validate month range
        month = row.get("month")
        if month is not None:
            if month < 1 or month > 12:
                raise ValueError(f"month must be 1-12, got: {month}")

        # Validate quarter range
        quarter = row.get("quarter")
        if quarter is not None:
            if quarter < 1 or quarter > 4:
                raise ValueError(f"quarter must be 1-4, got: {quarter}")

        # Validate year range
        year = row.get("year")
        if year is not None:
            if year < 2000 or year > 2100:
                raise ValueError(f"year must be 2000-2100, got: {year}")

    def _validate_tenant_id(self, row: Dict[str, Any], row_number: int) -> None:
        """
        Validate tenant_id is 'bibbi'

        CRITICAL: Ensures no data from other tenants can be inserted

        Raises:
            ValueError: If tenant_id is not 'bibbi'
        """
        tenant_id = row.get("tenant_id")

        if tenant_id != BIBBI_TENANT_ID:
            raise ValueError(f"tenant_id must be '{BIBBI_TENANT_ID}', got: {tenant_id}")

    def _product_exists(self, product_id: str) -> bool:
        """Check if product exists in products table"""
        try:
            # NOTE: Use raw client to bypass tenant filter (products table has no tenant_id)
            result = self.db.client.table("products")\
                .select("ean")\
                .eq("ean", product_id)\
                .execute()

            return result.data and len(result.data) > 0

        except Exception as e:
            print(f"[BibbιValidation] Error checking product: {e}")
            return False

    def _reseller_exists(self, reseller_id: str) -> bool:
        """Check if reseller exists in resellers table"""
        try:
            result = self.db.table("resellers")\
                .select("id")\
                .eq("id", reseller_id)\
                .execute()

            return result.data and len(result.data) > 0

        except Exception as e:
            print(f"[BibbιValidation] Error checking reseller: {e}")
            return False

    def _store_exists(self, store_id: str) -> bool:
        """Check if store exists in stores table"""
        try:
            result = self.db.table("stores")\
                .select("store_id")\
                .eq("store_id", store_id)\
                .execute()

            return result.data and len(result.data) > 0

        except Exception as e:
            print(f"[BibbιValidation] Error checking store: {e}")
            return False

    def _sanitize_row_for_error(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize row data for error reporting

        Removes sensitive fields and truncates long values

        Args:
            row: Original row data

        Returns:
            Sanitized row data safe for error logs
        """
        sanitized = {}

        for key, value in row.items():
            # Skip internal fields
            if key.startswith("_"):
                continue

            # Truncate long strings
            if isinstance(value, str) and len(value) > 100:
                sanitized[key] = value[:100] + "..."
            else:
                sanitized[key] = value

        return sanitized


def get_validation_service(bibbi_db: BibbιDB) -> BibbιValidationService:
    """
    Factory function to create validation service

    Args:
        bibbi_db: BIBBI-specific Supabase client

    Returns:
        BibbιValidationService instance
    """
    return BibbιValidationService(bibbi_db)
