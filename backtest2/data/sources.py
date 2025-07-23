"""Data source clients for backtest system"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Add TradingMultiAgents to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../TradingMultiAgents'))

try:
    from tradingagents.dataflows import (
        get_finnhub_news,
        get_finnhub_insider_sentiment,
        get_finnhub_insider_transactions,
        get_yfin_stock_price,
        get_yfin_time_series,
        get_google_news,
        get_reddit_news
    )
    TRADINGAGENTS_AVAILABLE = True
except ImportError:
    TRADINGAGENTS_AVAILABLE = False
    logging.warning("TradingMultiAgents dataflows not available")

from ..core.types import MarketData
import random


class BaseDataClient:
    """Base class for data clients"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def get_price_data(self, symbol: str, date: datetime) -> Optional[Dict[str, float]]:
        """Get price data for a symbol on a date"""
        raise NotImplementedError
        
    async def get_news(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get news data for a symbol in date range"""
        raise NotImplementedError
        
    async def get_fundamentals(self, symbol: str, date: datetime) -> Dict[str, Any]:
        """Get fundamental data for a symbol"""
        raise NotImplementedError


class YahooFinanceClient(BaseDataClient):
    """Yahoo Finance data client"""
    
    async def get_price_data(self, symbol: str, date: datetime) -> Optional[Dict[str, float]]:
        """Get price data from Yahoo Finance"""
        if not TRADINGAGENTS_AVAILABLE:
            return self._get_mock_price_data(symbol, date)
            
        try:
            # Get daily price
            date_str = date.strftime("%Y-%m-%d")
            result = get_yfin_stock_price(symbol, date_str)
            
            if result and isinstance(result, dict):
                return {
                    'open': float(result.get('Open', 0)),
                    'high': float(result.get('High', 0)),
                    'low': float(result.get('Low', 0)),
                    'close': float(result.get('Close', 0)),
                    'volume': float(result.get('Volume', 0)),
                    'adjusted_close': float(result.get('Adj Close', result.get('Close', 0)))
                }
        except Exception as e:
            self.logger.error(f"Error fetching Yahoo Finance data: {e}")
            
        return None
        
    async def get_news(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Yahoo Finance doesn't provide news through this API"""
        return []
        
    async def get_fundamentals(self, symbol: str, date: datetime) -> Dict[str, Any]:
        """Get fundamental data"""
        # Yahoo Finance fundamental data would require additional implementation
        return {}
        
    def _get_mock_price_data(self, symbol: str, date: datetime) -> Dict[str, float]:
        """Generate mock price data for testing"""
        import random
        base_price = hash(symbol) % 1000 + 50
        
        # Add some randomness based on date
        random.seed(f"{symbol}_{date.strftime('%Y%m%d')}")
        variation = random.uniform(0.95, 1.05)
        
        close = base_price * variation
        return {
            'open': close * random.uniform(0.99, 1.01),
            'high': close * random.uniform(1.01, 1.03),
            'low': close * random.uniform(0.97, 0.99),
            'close': close,
            'volume': random.randint(1000000, 10000000),
            'adjusted_close': close
        }


class FinnhubClient(BaseDataClient):
    """Finnhub data client"""
    
    async def get_price_data(self, symbol: str, date: datetime) -> Optional[Dict[str, float]]:
        """Finnhub primarily provides news, not price data"""
        # Use Yahoo Finance as fallback for price data
        yf_client = YahooFinanceClient()
        return await yf_client.get_price_data(symbol, date)
        
    async def get_news(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get news from Finnhub"""
        if not TRADINGAGENTS_AVAILABLE:
            return self._get_mock_news(symbol, start_date, end_date)
            
        try:
            # Calculate look back days
            look_back_days = (end_date - start_date).days
            date_str = end_date.strftime("%Y-%m-%d")
            
            # Get news
            news_result = get_finnhub_news(symbol, date_str, look_back_days)
            
            # Parse result
            if news_result:
                # The function returns formatted string, we need to parse it
                news_items = []
                # For now, return as single item
                news_items.append({
                    'timestamp': end_date,
                    'headline': f"News for {symbol}",
                    'summary': news_result,
                    'sentiment': 0.0  # Would need sentiment analysis
                })
                return news_items
                
        except Exception as e:
            self.logger.error(f"Error fetching Finnhub news: {e}")
            
        return []
        
    async def get_fundamentals(self, symbol: str, date: datetime) -> Dict[str, Any]:
        """Get insider sentiment from Finnhub"""
        if not TRADINGAGENTS_AVAILABLE:
            return {}
            
        try:
            date_str = date.strftime("%Y-%m-%d")
            sentiment = get_finnhub_insider_sentiment(symbol, date_str)
            
            if sentiment:
                return {'insider_sentiment': sentiment}
                
        except Exception as e:
            self.logger.error(f"Error fetching Finnhub fundamentals: {e}")
            
        return {}
        
    def _get_mock_news(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate mock news for testing"""
        news_items = []
        current = start_date
        
        while current <= end_date:
            if current.weekday() < 5:  # Weekdays only
                news_items.append({
                    'timestamp': current,
                    'headline': f"Mock news for {symbol} on {current.strftime('%Y-%m-%d')}",
                    'summary': f"This is a mock news article about {symbol}",
                    'sentiment': 0.1 if hash(f"{symbol}{current}") % 2 == 0 else -0.1
                })
            current += timedelta(days=1)
            
        return news_items


class TauricTradingDBClient(BaseDataClient):
    """Mock Tauric Trading DB client"""
    
    def __init__(self):
        super().__init__()
        # In real implementation, this would connect to cached database
        self.yf_client = YahooFinanceClient()
        self.finnhub_client = FinnhubClient()
        
    async def get_price_data(self, symbol: str, date: datetime) -> Optional[Dict[str, float]]:
        """Get cached price data"""
        # For now, fallback to Yahoo Finance
        return await self.yf_client.get_price_data(symbol, date)
        
    async def get_news(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get cached news data"""
        # For now, fallback to Finnhub
        return await self.finnhub_client.get_news(symbol, start_date, end_date)
        
    async def get_fundamentals(self, symbol: str, date: datetime) -> Dict[str, Any]:
        """Get cached fundamental data"""
        return await self.finnhub_client.get_fundamentals(symbol, date)


class MockDataSource:
    """Mock data source for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_prices = {
            "AAPL": 150.0,
            "MSFT": 300.0,
            "GOOGL": 2500.0,
            "AMZN": 3000.0,
            "META": 350.0,
            "SPY": 400.0,
            "JP225": 30000.0
        }
        
    async def get_data(self, symbol: str, date: datetime) -> Optional[MarketData]:
        """Get mock market data"""
        # Generate deterministic but varying prices
        base_price = self.base_prices.get(symbol, 100.0)
        
        # Use date for price variation
        days_from_epoch = (date - datetime(2020, 1, 1)).days
        price_variation = (days_from_epoch % 30 - 15) / 100  # -15% to +15%
        
        open_price = base_price * (1 + price_variation)
        high_price = open_price * 1.02
        low_price = open_price * 0.98
        close_price = open_price * (1 + random.uniform(-0.01, 0.01))
        
        # Volume based on symbol
        base_volume = 10000000 if symbol in ["AAPL", "MSFT"] else 5000000
        volume = base_volume * random.uniform(0.8, 1.2)
        
        # Mock news
        news = []
        if random.random() > 0.7:
            news.append({
                "title": f"{symbol} announces quarterly results",
                "sentiment": random.uniform(-0.5, 0.5)
            })
            
        return MarketData(
            symbol=symbol,
            date=date,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=int(volume),
            news=news,
            sentiment={"overall": random.uniform(-0.3, 0.3)}
        )