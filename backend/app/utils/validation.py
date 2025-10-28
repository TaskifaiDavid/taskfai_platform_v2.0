"""
Data validation utilities for vendor data processing

This module contains common validation and type conversion utilities
extracted from vendor processors to eliminate code duplication.

All functions follow consistent patterns:
- Raise ValueError for invalid data (processor can handle)
- Return None for optional fields when appropriate
- Provide clear error messages with context
"""

from typing import Any, Optional


def validate_ean(
    value: Any,
    required: bool = True,
    strict: bool = True
) -> Optional[str]:
    """
    Validate EAN-13 code

    Args:
        value: Raw EAN value (can be str, int, float, etc.)
        required: If True, raises ValueError when value is empty
        strict: If True, raises ValueError for invalid EAN; if False, returns None

    Returns:
        Validated 13-digit EAN string, or None if validation fails in non-strict mode

    Raises:
        ValueError: If required=True and value is empty, or if strict=True and EAN is invalid

    Examples:
        >>> validate_ean("1234567890123")
        '1234567890123'

        >>> validate_ean(1234567890123.0)  # Excel number format
        '1234567890123'

        >>> validate_ean("", required=False)
        None

        >>> validate_ean("invalid", strict=False)
        None
    """
    # Handle empty values
    if not value:
        if required:
            raise ValueError("EAN cannot be empty")
        return None

    # Convert to string and clean
    ean_str = str(value).strip()

    # Remove decimal point (Excel sometimes formats numbers as floats)
    if '.' in ean_str:
        ean_str = ean_str.split('.')[0]

    # Validate format: 13 digits
    if len(ean_str) != 13 or not ean_str.isdigit():
        if strict:
            raise ValueError(f"Invalid EAN format: {ean_str} (must be 13 digits)")
        return None

    return ean_str


def validate_month(value: Any) -> int:
    """
    Validate month value (1-12)

    Args:
        value: Raw month value

    Returns:
        Validated month as integer (1-12)

    Raises:
        ValueError: If month is invalid or out of range

    Examples:
        >>> validate_month(6)
        6

        >>> validate_month("12")
        12

        >>> validate_month(13)
        Traceback: ValueError: Invalid month: 13 (must be 1-12)
    """
    month = to_int(value, "Month")

    if month < 1 or month > 12:
        raise ValueError(f"Invalid month: {month} (must be 1-12)")

    return month


def validate_year(value: Any, min_year: int = 2000, max_year: int = 2100) -> int:
    """
    Validate year value

    Args:
        value: Raw year value
        min_year: Minimum acceptable year (default: 2000)
        max_year: Maximum acceptable year (default: 2100)

    Returns:
        Validated year as integer

    Raises:
        ValueError: If year is invalid or out of range

    Examples:
        >>> validate_year(2025)
        2025

        >>> validate_year("2024")
        2024

        >>> validate_year(1999)
        Traceback: ValueError: Invalid year: 1999 (must be between 2000 and 2100)
    """
    year = to_int(value, "Year")

    if year < min_year or year > max_year:
        raise ValueError(
            f"Invalid year: {year} (must be between {min_year} and {max_year})"
        )

    return year


def to_int(value: Any, field_name: str) -> int:
    """
    Convert value to integer with error handling

    Args:
        value: Value to convert
        field_name: Name of field (for error messages)

    Returns:
        Integer value

    Raises:
        ValueError: If value is None or cannot be converted to integer

    Examples:
        >>> to_int(42, "Quantity")
        42

        >>> to_int("123", "ID")
        123

        >>> to_int(45.7, "Count")
        45

        >>> to_int(None, "Value")
        Traceback: ValueError: Value cannot be None
    """
    if value is None:
        raise ValueError(f"{field_name} cannot be None")

    try:
        # Convert to float first to handle decimal strings, then to int
        return int(float(value))
    except (ValueError, TypeError):
        raise ValueError(f"Invalid integer for {field_name}: {value}")


def to_float(
    value: Any,
    field_name: str,
    allow_none: bool = False,
    default: Optional[float] = None
) -> Optional[float]:
    """
    Convert value to float with error handling

    Args:
        value: Value to convert
        field_name: Name of field (for error messages)
        allow_none: If True, returns default for None/empty values
        default: Default value when allow_none=True (default: None)

    Returns:
        Float value, or default if value is empty and allow_none=True

    Raises:
        ValueError: If value cannot be converted to float and allow_none=False

    Examples:
        >>> to_float(42.5, "Price")
        42.5

        >>> to_float("123.45", "Amount")
        123.45

        >>> to_float(None, "Optional", allow_none=True)
        None

        >>> to_float("", "Price", allow_none=True, default=0.0)
        0.0

        >>> to_float(None, "Required")
        Traceback: ValueError: Required cannot be None
    """
    if value is None or value == "":
        if allow_none:
            return default
        raise ValueError(f"{field_name} cannot be None")

    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid float for {field_name}: {value}")


def to_string(value: Any, allow_none: bool = True, default: str = "") -> Optional[str]:
    """
    Convert value to string with None handling

    Args:
        value: Value to convert
        allow_none: If True, returns None for None values; if False, returns default
        default: Default value when value is None and allow_none=False

    Returns:
        String value or None

    Examples:
        >>> to_string("test")
        'test'

        >>> to_string(123)
        '123'

        >>> to_string(None, allow_none=True)
        None

        >>> to_string(None, allow_none=False, default="N/A")
        'N/A'
    """
    if value is None:
        return None if allow_none else default

    return str(value).strip()
