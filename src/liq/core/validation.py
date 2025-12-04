"""Validation utilities for the LIQ Stack.

Provides ValidationResult dataclass and helper functions for
validating financial data types.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating a data model.

    Attributes:
        is_valid: True if all hard validations passed
        errors: List of critical validation failures
        warnings: List of non-critical issues (e.g., unusual values)
    """

    is_valid: bool
    errors: list[str]
    warnings: list[str]


def is_timezone_aware(dt: datetime) -> bool:
    """Check if a datetime object is timezone-aware.

    Args:
        dt: Datetime object to check

    Returns:
        True if datetime has timezone info, False otherwise

    Examples:
        >>> from datetime import datetime, timezone
        >>> is_timezone_aware(datetime.now(timezone.utc))
        True
        >>> is_timezone_aware(datetime.now())
        False
    """
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None
