"""
Validation utilities for the backtesting module.
"""

import re
from datetime import datetime
from typing import List, Tuple
from .constants import TICKER_PATTERN, DATE_FORMAT, MIN_INITIAL_CAPITAL, MIN_SLIPPAGE, MAX_SLIPPAGE


class ValidationError(ValueError):
    """Custom exception for validation errors."""
    pass


def validate_ticker(ticker: str) -> str:
    """
    Validate and sanitize ticker symbol.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Sanitized ticker symbol
        
    Raises:
        ValidationError: If ticker is invalid
    """
    if not ticker:
        raise ValidationError("Ticker cannot be empty")
    
    ticker = ticker.strip().upper()
    
    if not re.match(TICKER_PATTERN, ticker):
        raise ValidationError(f"Invalid ticker format: {ticker}. Must be 1-10 characters, alphanumeric with dots/dashes allowed.")
    
    return ticker


def validate_tickers(tickers: List[str]) -> List[str]:
    """
    Validate a list of ticker symbols.
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        List of validated ticker symbols
        
    Raises:
        ValidationError: If any ticker is invalid
    """
    if not tickers:
        raise ValidationError("At least one ticker must be provided")
    
    validated = []
    for ticker in tickers:
        validated.append(validate_ticker(ticker))
    
    # Check for duplicates
    if len(set(validated)) != len(validated):
        raise ValidationError("Duplicate tickers found")
    
    return validated


def validate_date_range(start_date: str, end_date: str) -> Tuple[datetime, datetime]:
    """
    Validate date range for backtesting.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        Tuple of (start_datetime, end_datetime)
        
    Raises:
        ValidationError: If dates are invalid
    """
    try:
        start_dt = datetime.strptime(start_date, DATE_FORMAT)
        end_dt = datetime.strptime(end_date, DATE_FORMAT)
    except ValueError as e:
        raise ValidationError(f"Invalid date format. Use YYYY-MM-DD. Error: {str(e)}")
    
    # Check date order
    if start_dt >= end_dt:
        raise ValidationError("Start date must be before end date")
    
    # Check not future dates
    today = datetime.now()
    if end_dt > today:
        raise ValidationError("End date cannot be in the future")
    
    # Check reasonable range (not too far in the past)
    if start_dt.year < 1970:
        raise ValidationError("Start date cannot be before 1970")
    
    return start_dt, end_dt


def validate_capital(capital: float) -> float:
    """
    Validate initial capital amount.
    
    Args:
        capital: Initial capital amount
        
    Returns:
        Validated capital amount
        
    Raises:
        ValidationError: If capital is invalid
    """
    if capital < MIN_INITIAL_CAPITAL:
        raise ValidationError(f"Initial capital must be at least ${MIN_INITIAL_CAPITAL}")
    
    if capital > 1e9:  # 1 billion
        raise ValidationError("Initial capital seems unreasonably high")
    
    return capital


def validate_slippage(slippage: float) -> float:
    """
    Validate slippage percentage.
    
    Args:
        slippage: Slippage as decimal (e.g., 0.001 for 0.1%)
        
    Returns:
        Validated slippage
        
    Raises:
        ValidationError: If slippage is invalid
    """
    if slippage < MIN_SLIPPAGE:
        raise ValidationError(f"Slippage cannot be negative")
    
    if slippage > MAX_SLIPPAGE:
        raise ValidationError(f"Slippage cannot exceed {MAX_SLIPPAGE*100}%")
    
    return slippage