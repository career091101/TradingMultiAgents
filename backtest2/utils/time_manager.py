"""Time management utilities"""

from datetime import datetime, timedelta
import pytz
from typing import Optional


class TimeManager:
    """Manages simulation time progression"""
    
    def __init__(self, start_date: datetime, end_date: datetime, timezone: str = "UTC"):
        self.start_date = start_date
        self.end_date = end_date
        self.timezone = pytz.timezone(timezone)
        self.current_date = start_date
        self.trading_days = []
        self._generate_trading_days()
        self.current_index = 0
        
    def _generate_trading_days(self):
        """Generate list of trading days (weekdays only for now)"""
        current = self.start_date
        # Ensure timezone-naive dates
        current = current.replace(tzinfo=None) if hasattr(current, 'tzinfo') else current
        while current <= self.end_date:
            # Skip weekends (simplified - real implementation would check market calendar)
            if current.weekday() < 5:  # Monday = 0, Friday = 4
                self.trading_days.append(current)
            current += timedelta(days=1)
            
    def has_next(self) -> bool:
        """Check if there are more trading days"""
        return self.current_index < len(self.trading_days)
        
    def next(self) -> Optional[datetime]:
        """Move to next trading day"""
        if self.has_next():
            self.current_index += 1
            if self.current_index < len(self.trading_days):
                self.current_date = self.trading_days[self.current_index]
                return self.current_date
        return None
        
    def get_progress(self) -> float:
        """Get simulation progress as percentage"""
        if not self.trading_days:
            return 0.0
        return self.current_index / len(self.trading_days)
        
    def get_elapsed_days(self) -> int:
        """Get number of elapsed trading days"""
        return self.current_index
        
    def get_total_days(self) -> int:
        """Get total number of trading days"""
        return len(self.trading_days)