"""
Unit tests for the validation module.
"""

import unittest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtest.validation import (
    validate_ticker, validate_tickers, validate_date_range,
    validate_capital, validate_slippage, ValidationError
)


class TestTickerValidation(unittest.TestCase):
    """Test ticker validation functions."""
    
    def test_valid_tickers(self):
        """Test valid ticker formats."""
        valid_tickers = [
            ("AAPL", "AAPL"),
            ("aapl", "AAPL"),  # Should uppercase
            ("MSFT", "MSFT"),
            ("BRK-B", "BRK-B"),  # With dash
            ("TSM.TW", "TSM.TW"),  # With dot
            ("123", "123"),  # Numeric
            ("A", "A"),  # Single char
        ]
        
        for input_ticker, expected in valid_tickers:
            with self.subTest(ticker=input_ticker):
                result = validate_ticker(input_ticker)
                self.assertEqual(result, expected)
    
    def test_invalid_tickers(self):
        """Test invalid ticker formats."""
        invalid_tickers = [
            "",  # Empty
            "   ",  # Whitespace only
            "TOOLONGTICKER",  # Too long
            "AAPL!",  # Invalid character
            "AAPL@NASDAQ",  # Invalid character
            "AAPL MSFT",  # Space
        ]
        
        for ticker in invalid_tickers:
            with self.subTest(ticker=ticker):
                with self.assertRaises(ValidationError):
                    validate_ticker(ticker)
    
    def test_validate_tickers_list(self):
        """Test validation of ticker lists."""
        # Valid list
        tickers = validate_tickers(["AAPL", "MSFT", "GOOGL"])
        self.assertEqual(tickers, ["AAPL", "MSFT", "GOOGL"])
        
        # Empty list
        with self.assertRaises(ValidationError):
            validate_tickers([])
        
        # Duplicates
        with self.assertRaises(ValidationError):
            validate_tickers(["AAPL", "MSFT", "AAPL"])


class TestDateValidation(unittest.TestCase):
    """Test date range validation."""
    
    def test_valid_date_ranges(self):
        """Test valid date ranges."""
        # Normal range
        start_dt, end_dt = validate_date_range("2023-01-01", "2023-12-31")
        self.assertEqual(start_dt.year, 2023)
        self.assertEqual(end_dt.year, 2023)
        
        # Single day
        start_dt, end_dt = validate_date_range("2023-01-01", "2023-01-02")
        self.assertEqual((end_dt - start_dt).days, 1)
    
    def test_invalid_date_ranges(self):
        """Test invalid date ranges."""
        # Wrong order
        with self.assertRaises(ValidationError) as cm:
            validate_date_range("2023-12-31", "2023-01-01")
        self.assertIn("before", str(cm.exception))
        
        # Future end date
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        with self.assertRaises(ValidationError) as cm:
            validate_date_range("2023-01-01", future_date)
        self.assertIn("future", str(cm.exception))
        
        # Too old
        with self.assertRaises(ValidationError) as cm:
            validate_date_range("1969-01-01", "2023-01-01")
        self.assertIn("1970", str(cm.exception))
        
        # Invalid format
        with self.assertRaises(ValidationError):
            validate_date_range("2023/01/01", "2023/12/31")


class TestFinancialValidation(unittest.TestCase):
    """Test financial parameter validation."""
    
    def test_valid_capital(self):
        """Test valid capital amounts."""
        self.assertEqual(validate_capital(10000.0), 10000.0)
        self.assertEqual(validate_capital(100.0), 100.0)  # Minimum
        self.assertEqual(validate_capital(1000000.0), 1000000.0)  # 1M
    
    def test_invalid_capital(self):
        """Test invalid capital amounts."""
        # Too small
        with self.assertRaises(ValidationError):
            validate_capital(50.0)
        
        # Unreasonably large
        with self.assertRaises(ValidationError):
            validate_capital(2e9)  # 2 billion
    
    def test_valid_slippage(self):
        """Test valid slippage values."""
        self.assertEqual(validate_slippage(0.0), 0.0)  # No slippage
        self.assertEqual(validate_slippage(0.001), 0.001)  # 0.1%
        self.assertEqual(validate_slippage(0.01), 0.01)  # 1%
        self.assertEqual(validate_slippage(0.1), 0.1)  # 10% (max)
    
    def test_invalid_slippage(self):
        """Test invalid slippage values."""
        # Negative
        with self.assertRaises(ValidationError):
            validate_slippage(-0.001)
        
        # Too high
        with self.assertRaises(ValidationError):
            validate_slippage(0.15)  # 15%


if __name__ == '__main__':
    unittest.main()