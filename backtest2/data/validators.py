"""Data validation utilities"""

from datetime import datetime
from typing import Any, Dict, List
import logging

from ..core.types import MarketData


class TemporalValidator:
    """Validates temporal consistency of data"""
    
    @staticmethod
    def is_valid(data: Any, reference_date: datetime) -> bool:
        """Check if data doesn't contain future information"""
        if isinstance(data, dict):
            # Check for timestamp fields
            for key in ['timestamp', 'date', 'datetime']:
                if key in data:
                    data_date = data[key]
                    if isinstance(data_date, datetime):
                        if data_date > reference_date:
                            return False
                    elif isinstance(data_date, str):
                        try:
                            parsed_date = datetime.fromisoformat(data_date)
                            if parsed_date > reference_date:
                                return False
                        except:
                            pass
                            
        elif isinstance(data, list):
            # Check all items in list
            for item in data:
                if not TemporalValidator.is_valid(item, reference_date):
                    return False
                    
        return True


class DataQualityValidator:
    """Validates data quality"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def validate(self, data: MarketData) -> bool:
        """Validate market data quality"""
        # Check required fields
        if not all([data.open, data.high, data.low, data.close, data.volume]):
            self.logger.warning(f"Missing required price fields for {data.symbol}")
            return False
            
        # Check price consistency
        if data.high < data.low:
            self.logger.warning(f"High < Low for {data.symbol} on {data.date}")
            return False
            
        if data.high < data.open or data.high < data.close:
            self.logger.warning(f"High price inconsistency for {data.symbol}")
            return False
            
        if data.low > data.open or data.low > data.close:
            self.logger.warning(f"Low price inconsistency for {data.symbol}")
            return False
            
        # Check for negative or zero prices
        if any(price <= 0 for price in [data.open, data.high, data.low, data.close]):
            self.logger.warning(f"Invalid price (<= 0) for {data.symbol}")
            return False
            
        # Check volume
        if data.volume < 0:
            self.logger.warning(f"Negative volume for {data.symbol}")
            return False
            
        return True