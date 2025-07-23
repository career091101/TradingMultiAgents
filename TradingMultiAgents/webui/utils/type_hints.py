"""
Type hints and type definitions for WebUI
"""

from typing import TypedDict, Dict, List, Optional, Any, Union, Callable
from datetime import datetime, date
from dataclasses import dataclass
from cli.models import AnalystType


class UserInfo(TypedDict):
    """User information type"""
    username: str
    role: str
    session_id: str
    created_at: datetime
    last_activity: datetime


class AnalysisResult(TypedDict):
    """Analysis result type"""
    ticker: str
    date: str
    status: str
    results: Dict[str, Any]
    timestamp: float
    path: str


class ProgressInfo(TypedDict):
    """Progress information type"""
    stage: str
    agent: str
    status: str
    progress: float
    message: str
    timestamp: str


class LegacyBacktestConfig(TypedDict):
    """Legacy backtest configuration type for WebUI"""
    start_date: str
    end_date: str
    initial_capital: float
    commission: float
    strategy: str
    parameters: Dict[str, Any]


class BacktestResult(TypedDict):
    """Backtest result type"""
    metrics: Dict[str, float]
    trades: List[Dict[str, Any]]
    equity_curve: List[float]
    files: Dict[str, str]


@dataclass
class ValidationError:
    """Input validation error"""
    field: str
    message: str
    value: Any


def validate_ticker(ticker: str) -> Optional[ValidationError]:
    """Validate ticker symbol"""
    if not ticker:
        return ValidationError("ticker", "Ticker symbol is required", ticker)
    
    if not ticker.isalnum():
        return ValidationError("ticker", "Ticker must be alphanumeric", ticker)
    
    if len(ticker) > 10:
        return ValidationError("ticker", "Ticker too long (max 10 chars)", ticker)
    
    return None


def validate_date_input(date_str: str) -> Optional[ValidationError]:
    """Validate date input"""
    if not date_str:
        return ValidationError("date", "Date is required", date_str)
    
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return ValidationError("date", "Invalid date format (use YYYY-MM-DD)", date_str)
    
    return None


def validate_numeric_range(
    value: Union[int, float], 
    min_val: Optional[Union[int, float]] = None,
    max_val: Optional[Union[int, float]] = None,
    field_name: str = "value"
) -> Optional[ValidationError]:
    """Validate numeric value is within range"""
    if min_val is not None and value < min_val:
        return ValidationError(field_name, f"Value must be at least {min_val}", value)
    
    if max_val is not None and value > max_val:
        return ValidationError(field_name, f"Value must be at most {max_val}", value)
    
    return None