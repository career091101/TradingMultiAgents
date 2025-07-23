"""Simplified data manager without pandas dependency"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

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
        
        # For minimal implementation, use mock data source
        self.primary_source = MockDataSource()
        self.cache = {}
        
    async def initialize(self) -> None:
        """Initialize data sources"""
        self.logger.info("Initializing data manager")
        # Minimal implementation - no initialization needed for mock
        
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
            # Get data from source
            data = await self.primary_source.get_data(symbol, date)
            
            # Cache the result
            if data:
                self.cache[cache_key] = data
                
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting data for {symbol} on {date}: {e}")
            return None
    
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
            
        return results
    
    async def close(self) -> None:
        """Close data connections"""
        self.logger.info("Closing data manager")
        # Clear cache
        self.cache.clear()