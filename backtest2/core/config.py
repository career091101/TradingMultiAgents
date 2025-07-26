"""Configuration classes for backtest system"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path


class RiskProfile(Enum):
    """Risk profile for position sizing"""
    AGGRESSIVE = "aggressive"
    NEUTRAL = "neutral"
    CONSERVATIVE = "conservative"


class ReflectionLevel(Enum):
    """Reflection level definitions"""
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    POSITION_CLOSE = "position"
    MILESTONE = "milestone"
    SYSTEM = "system"


@dataclass
class TimeRange:
    """Time range for backtesting"""
    start: datetime
    end: datetime
    
    def __post_init__(self):
        if self.start >= self.end:
            raise ValueError("Start date must be before end date")


@dataclass
class LLMConfig:
    """LLM configuration"""
    deep_think_model: str = "o3"  # Now we can use o3!
    quick_think_model: str = "o4-mini"  # And o4-mini!
    temperature: float = 0.0
    max_tokens: Optional[int] = 1000  # Default for most agents
    # Agent-specific token limits to prevent truncation
    agent_max_tokens: Optional[Dict[str, int]] = field(default_factory=lambda: {
        "Market Analyst": 1500,  # Needs more for technical analysis + markdown table
        "Fundamentals Analyst": 1200,  # Complex financial analysis
        "Research Manager": 1200,  # Detailed investment plans
        "Risk Manager": 1000,  # Final decision with rationale
    })
    timeout: int = 300  # 5 minutes


@dataclass
class AgentConfig:
    """Agent configuration"""
    max_debate_rounds: int = 1
    max_risk_discuss_rounds: int = 1
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    use_japanese_prompts: bool = True
    enable_memory: bool = True


@dataclass
class DataConfig:
    """Data source configuration"""
    primary_source: str = "TauricTradingDB"
    fallback_sources: List[str] = field(default_factory=lambda: ["YahooFinance"])
    cache_enabled: bool = True
    cache_ttl: int = 86400  # 1 day
    timezone: str = "UTC"
    force_refresh: bool = False


@dataclass
class RiskConfig:
    """Risk management configuration"""
    position_limits: Dict[RiskProfile, float] = field(default_factory=lambda: {
        RiskProfile.AGGRESSIVE: 0.8,  # 論文準拠: 80%
        RiskProfile.NEUTRAL: 0.5,     # 論文準拠: 50%
        RiskProfile.CONSERVATIVE: 0.3  # 論文準拠: 30%
    })
    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "high": 0.8,
        "medium": 0.5,
        "low": 0.3
    })
    stop_loss: float = 0.1  # 10%
    take_profit: float = 0.2  # 20%
    max_positions: int = 10
    min_trade_size: float = 100.0  # Reduced from 1000.0 for better trade execution


@dataclass
class ReflectionConfig:
    """Reflection configuration"""
    enabled: bool = True
    immediate_on_trade: bool = True
    daily_enabled: bool = True
    daily_hour: int = 17  # 5 PM
    weekly_enabled: bool = True
    weekly_day: str = "friday"
    consecutive_loss_threshold: int = 3
    drawdown_threshold: float = 0.15
    abnormal_return_threshold: float = 0.05
    trades_per_reflection: int = 10


@dataclass
class BacktestConfig:
    """Main backtest configuration"""
    # Basic settings
    name: str = "backtest"
    symbols: List[str] = field(default_factory=list)
    time_range: Optional[TimeRange] = None
    initial_capital: float = 10000.0
    random_seed: int = 42  # For reproducibility
    
    # Position management
    max_positions: int = 10
    position_limits: Dict[RiskProfile, float] = field(default_factory=lambda: {
        RiskProfile.AGGRESSIVE: 0.8,  # 論文準拠: 80%
        RiskProfile.NEUTRAL: 0.5,     # 論文準拠: 50%
        RiskProfile.CONSERVATIVE: 0.3  # 論文準拠: 30%
    })
    
    # LLM configuration
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    
    # Data sources
    data_sources: List[str] = field(default_factory=lambda: ["yahoo", "finnhub"])
    
    # Reflection configuration
    reflection_config: Optional[Dict[str, Any]] = None
    
    # Result directory
    result_dir: Optional[Path] = None
    
    # Trading costs
    slippage: float = 0.001  # 0.1%
    commission: float = 0.001  # 0.1%
    
    # Benchmark
    risk_free_rate: float = 0.02  # 2%
    benchmark: str = "SPY"  # S&P 500
    
    # Legacy fields for compatibility
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    agent_config: Optional[AgentConfig] = None
    data_config: Optional[DataConfig] = None
    risk_config: Optional[RiskConfig] = None
    
    # Performance settings
    enable_parallel: bool = True
    max_workers: int = 4
    cache_size: int = 1000
    
    # Logging and monitoring
    log_level: str = "INFO"
    save_results: bool = True
    results_path: str = "./results"
    enable_monitoring: bool = True
    debug: bool = False  # Debug mode for detailed logging
    
    def __post_init__(self):
        # Handle legacy date fields
        if self.time_range is None and self.start_date and self.end_date:
            self.time_range = TimeRange(start=self.start_date, end=self.end_date)
    
    def validate(self):
        """Validate configuration"""
        if not self.symbols:
            raise ValueError("At least one symbol must be specified")
        if self.initial_capital <= 0:
            raise ValueError("Initial capital must be positive")
        if self.time_range is None:
            raise ValueError("Time range must be specified")
        
        if not 0 <= self.slippage <= 0.1:
            raise ValueError("Slippage must be between 0 and 10%")
            
        if not 0 <= self.commission <= 0.1:
            raise ValueError("Commission must be between 0 and 10%")