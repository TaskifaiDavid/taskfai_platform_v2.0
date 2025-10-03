"""
File validation service for upload files
"""

from typing import Tuple
from pathlib import Path

# Allowed file extensions
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}

# Maximum file size in bytes (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024


def validate_file_extension(filename: str) -> Tuple[bool, str]:
    """
    Validate file extension

    Args:
        filename: Name of the file to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    file_ext = Path(filename).suffix.lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"

    return True, ""


def validate_file_size(file_size: int) -> Tuple[bool, str]:
    """
    Validate file size

    Args:
        file_size: Size of file in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        return False, f"File too large. Maximum size: {max_mb}MB"

    if file_size == 0:
        return False, "File is empty"

    return True, ""


def validate_upload_file(filename: str, file_size: int) -> Tuple[bool, str]:
    """
    Validate uploaded file

    Args:
        filename: Name of the file
        file_size: Size of file in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate extension
    is_valid, error = validate_file_extension(filename)
    if not is_valid:
        return False, error

    # Validate size
    is_valid, error = validate_file_size(file_size)
    if not is_valid:
        return False, error

    return True, ""
