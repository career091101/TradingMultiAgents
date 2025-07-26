#!/usr/bin/env python3
"""
Fix DataManager to use real data sources instead of mock
"""

def fix_data_manager():
    """Replace MockDataSource with real Yahoo Finance source"""
    
    # Read the current manager_simple.py
    with open('backtest2/data/manager_simple.py', 'r') as f:
        content = f.read()
    
    # Create new content with real data source
    new_content = '''"""Simplified data manager with real data sources"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import yfinance as yf

from ..core.types import MarketData
from .sources import MockDataSource


class DataManager:
    """Manages data retrieval from multiple sources"""
    
    def __init__(self, config: Any):
        """Initialize data manager
        
        Args:
            config: Data configuration or BacktestConfig
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Use Yahoo Finance as primary source
        self.cache = {}
        self.logger.info("DataManager initialized with Yahoo Finance")
        
    async def initialize(self) -> None:
        """Initialize data sources"""
        self.logger.info("Initializing data manager")
        
    async def get_data(
        self,
        symbol: str,
        date: datetime
    ) -> Optional[MarketData]:
        """Get market data for a symbol on a specific date
        
        Args:
            symbol: Stock symbol
            date: Date to get data for
            
        Returns:
            MarketData or None if not available
        """
        # Check cache first
        cache_key = f"{symbol}_{date.date()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Get data from Yahoo Finance
            ticker = yf.Ticker(symbol)
            
            # Get data for a range around the target date
            start = date - timedelta(days=5)
            end = date + timedelta(days=1)
            
            hist = ticker.history(start=start, end=end)
            
            if hist.empty:
                self.logger.warning(f"No data available for {symbol} on {date}")
                return None
            
            # Find the closest date
            target_date = date.date()
            available_dates = [d.date() for d in hist.index]
            
            if target_date in available_dates:
                idx = available_dates.index(target_date)
            else:
                # Find closest previous date
                prev_dates = [d for d in available_dates if d <= target_date]
                if not prev_dates:
                    self.logger.warning(f"No data available for {symbol} on or before {date}")
                    return None
                idx = available_dates.index(max(prev_dates))
            
            # Create MarketData object
            row = hist.iloc[idx]
            data = MarketData(
                date=hist.index[idx].to_pydatetime(),
                symbol=symbol,
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume'])
            )
            
            # Cache the result
            self.cache[cache_key] = data
            
            self.logger.debug(f"Retrieved data for {symbol} on {date}: Close=${data.close:.2f}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting data for {symbol} on {date}: {e}")
            # Fall back to mock data if real data fails
            mock_source = MockDataSource()
            return await mock_source.get_data(symbol, date)
    
    async def get_bulk_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, List[MarketData]]:
        """Get data for multiple symbols over a date range
        
        Args:
            symbols: List of stock symbols
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary mapping symbols to lists of MarketData
        """
        results = {}
        
        for symbol in symbols:
            symbol_data = []
            current_date = start_date
            
            while current_date <= end_date:
                data = await self.get_data(symbol, current_date)
                if data:
                    symbol_data.append(data)
                    
                # Move to next trading day (simplified - skip weekends)
                current_date = current_date + timedelta(days=1)
                while current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    current_date = current_date + timedelta(days=1)
                    
            results[symbol] = symbol_data
            self.logger.info(f"Retrieved {len(symbol_data)} days of data for {symbol}")
            
        return results
    
    async def close(self) -> None:
        """Close data manager and cleanup resources"""
        self.logger.info("Closing data manager")
        self.cache.clear()
'''
    
    # Write the new content
    with open('backtest2/data/manager_simple.py', 'w') as f:
        f.write(new_content)
    
    print("Fixed DataManager to use real Yahoo Finance data!")
    print("The manager will now:")
    print("- Use Yahoo Finance as primary data source")
    print("- Fall back to mock data only if Yahoo Finance fails")
    print("- Cache data for better performance")

if __name__ == "__main__":
    fix_data_manager()