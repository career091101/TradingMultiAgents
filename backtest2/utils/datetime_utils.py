"""Datetime utilities for consistent timezone handling"""

from datetime import datetime
from typing import Optional

def ensure_timezone_naive(dt: datetime) -> datetime:
    """Ensure datetime is timezone-naive for consistent comparisons"""
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') and dt.tzinfo is not None else dt

def ensure_timezone_aware(dt: datetime, tz=None) -> datetime:
    """Ensure datetime is timezone-aware"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        import pytz
        tz = tz or pytz.UTC
        return tz.localize(dt)
    return dt
