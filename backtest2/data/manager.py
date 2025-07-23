"""Data manager with temporal consistency enforcement"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
import pytz
import pandas as pd
import numpy as np

from ..core.config import DataConfig
from ..core.types import MarketData
from .cache import CacheManager
from .validators import TemporalValidator, DataQualityValidator


class DataManager:
    """Manages data acquisition with strict temporal consistency"""
    
    def __init__(self, config: DataConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.cache_manager = CacheManager(
            enabled=config.cache_enabled,
            ttl=config.cache_ttl
        )
        self.timezone = pytz.timezone(config.timezone)
        self.api_clients = {}
        self._initialize_api_clients()
        
    def _initialize_api_clients(self):
        """Initialize API clients for data sources"""
        # This would initialize actual API clients
        # For now, using mock implementations
        from .sources import YahooFinanceClient, TauricTradingDBClient
        
        if self.config.primary_source == "TauricTradingDB":
            self.api_clients['primary'] = TauricTradingDBClient()
        else:
            self.api_clients['primary'] = YahooFinanceClient()
            
        # Initialize fallback sources
        for source in self.config.fallback_sources:
            if source == "YahooFinance":
                self.api_clients[source] = YahooFinanceClient()
                
    async def initialize(self):
        """Initialize data manager"""
        self.logger.info("Initializing data manager")
        # Initialize cache
        await self.cache_manager.initialize()
        
    async def get_data(self, symbol: str, date: datetime) -> Optional[MarketData]:
        """Get market data for a symbol on a specific date
        
        Args:
            symbol: Stock symbol
            date: Date for which to get data
            
        Returns:
            MarketData or None if not available
        """
        # Normalize date to timezone
        date = self._normalize_date(date)
        
        # Check temporal consistency
        if not self._is_valid_date(date):
            raise ValueError(f"Cannot access future data: {date}")
            
        # Try cache first
        cache_key = f"{symbol}_{date.strftime('%Y%m%d')}"
        cached_data = await self.cache_manager.get(cache_key)
        
        if cached_data and not self.config.force_refresh:
            self.logger.debug(f"Cache hit for {symbol} on {date}")
            return cached_data
            
        # Fetch from data sources
        market_data = await self._fetch_data(symbol, date)
        
        if market_data:
            # Validate data quality
            if self._validate_data(market_data):
                # Cache the data
                await self.cache_manager.set(cache_key, market_data)
                return market_data
            else:
                self.logger.warning(f"Data validation failed for {symbol} on {date}")
                
        return None
        
    async def _fetch_data(self, symbol: str, date: datetime) -> Optional[MarketData]:
        """Fetch data from sources with fallback"""
        # Try primary source
        try:
            data = await self._fetch_from_source(
                self.api_clients['primary'],
                symbol,
                date
            )
            if data:
                return data
        except Exception as e:
            self.logger.error(f"Primary source failed: {e}")
            
        # Try fallback sources
        for source_name in self.config.fallback_sources:
            if source_name in self.api_clients:
                try:
                    data = await self._fetch_from_source(
                        self.api_clients[source_name],
                        symbol,
                        date
                    )
                    if data:
                        self.logger.info(f"Using fallback source: {source_name}")
                        return data
                except Exception as e:
                    self.logger.error(f"Fallback source {source_name} failed: {e}")
                    
        return None
        
    async def _fetch_from_source(self, client: Any, symbol: str, date: datetime) -> Optional[MarketData]:
        """Fetch data from a specific source"""
        # Ensure deterministic execution order
        async with self._ensure_deterministic_order():
            # Get price data
            price_data = await client.get_price_data(symbol, date)
            if not price_data:
                return None
                
            # Get additional data with temporal consistency
            news_data = await self._get_news_data(client, symbol, date)
            fundamental_data = await self._get_fundamental_data(client, symbol, date)
            technical_data = self._calculate_technical_indicators(price_data)
            
            # Create MarketData object
            market_data = MarketData(
                date=date,
                symbol=symbol,
                open=price_data.get('open'),
                high=price_data.get('high'),
                low=price_data.get('low'),
                close=price_data.get('close'),
                volume=price_data.get('volume'),
                adjusted_close=price_data.get('adjusted_close'),
                news=news_data,
                fundamentals=fundamental_data,
                technicals=technical_data,
                sentiment=self._calculate_sentiment(news_data)
            )
            
            return market_data
            
    async def _get_news_data(self, client: Any, symbol: str, date: datetime) -> List[Dict[str, Any]]:
        """Get news data with temporal filtering"""
        # Set end_date to prevent future data
        end_date = date
        start_date = date - timedelta(days=7)  # Look back 7 days
        
        news = await client.get_news(symbol, start_date, end_date)
        
        # Filter out after-hours news for next day assignment
        filtered_news = []
        for item in news:
            news_time = item.get('timestamp')
            if news_time:
                # If news is after 4 PM, assign to next trading day
                if news_time.hour >= 16:
                    news_date = news_time.date() + timedelta(days=1)
                else:
                    news_date = news_time.date()
                    
                if news_date <= date.date():
                    filtered_news.append(item)
                    
        return filtered_news
        
    async def _get_fundamental_data(self, client: Any, symbol: str, date: datetime) -> Dict[str, Any]:
        """Get fundamental data with proper time alignment"""
        fundamentals = await client.get_fundamentals(symbol, date)
        
        if not fundamentals:
            return {}
            
        # Roll forward quarterly data
        processed_fundamentals = {}
        for key, value in fundamentals.items():
            if isinstance(value, dict) and 'date' in value:
                data_date = value['date']
                # Only include if data was available by the requested date
                if data_date <= date:
                    processed_fundamentals[key] = value['value']
            else:
                processed_fundamentals[key] = value
                
        return processed_fundamentals
        
    def _calculate_technical_indicators(self, price_data: Dict[str, float]) -> Dict[str, float]:
        """Calculate technical indicators"""
        # This is a simplified version - real implementation would use historical data
        technicals = {}
        
        # Simple calculations based on current price data
        if price_data:
            close = price_data.get('close', 0)
            high = price_data.get('high', 0)
            low = price_data.get('low', 0)
            
            # True Range
            technicals['true_range'] = high - low if high > low else 0
            
            # Price position in range
            if high > low:
                technicals['price_position'] = (close - low) / (high - low)
            else:
                technicals['price_position'] = 0.5
                
        return technicals
        
    def _calculate_sentiment(self, news_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate sentiment scores from news"""
        if not news_data:
            return {'overall': 0.0, 'count': 0}
            
        sentiments = []
        for item in news_data:
            if 'sentiment' in item:
                sentiments.append(item['sentiment'])
                
        if sentiments:
            return {
                'overall': np.mean(sentiments),
                'positive': len([s for s in sentiments if s > 0.2]) / len(sentiments),
                'negative': len([s for s in sentiments if s < -0.2]) / len(sentiments),
                'count': len(sentiments)
            }
        else:
            return {'overall': 0.0, 'count': 0}
            
    def _normalize_date(self, date: datetime) -> datetime:
        """Normalize date to configured timezone"""
        if date.tzinfo is None:
            date = self.timezone.localize(date)
        else:
            date = date.astimezone(self.timezone)
        return date
        
    def _is_valid_date(self, date: datetime) -> bool:
        """Check if date is not in the future"""
        now = datetime.now(self.timezone)
        return date <= now
        
    def _validate_data(self, data: MarketData) -> bool:
        """Validate data quality"""
        validator = DataQualityValidator()
        return validator.validate(data)
        
    @asyncio.coroutine
    def _ensure_deterministic_order(self):
        """Ensure deterministic execution order for API calls"""
        # This would implement a locking mechanism to ensure
        # API calls are made in a deterministic order
        yield
        
    async def close(self):
        """Close data connections"""
        await self.cache_manager.close()
        for client in self.api_clients.values():
            if hasattr(client, 'close'):
                await client.close()