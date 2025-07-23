"""Central configuration constants for backtest2 system"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RiskAnalysisConstants:
    """Constants for risk analysis"""
    # Time windows
    lookback_days: int = 30
    correlation_window: int = 60
    
    # Risk thresholds
    gap_threshold: float = 0.02  # 2% gap threshold
    var_confidence_level: float = 0.95
    
    # Risk adjustments
    slippage_multiplier: float = 0.5
    gap_risk_multiplier: float = 2.0
    correlation_risk_multiplier: float = 0.5
    
    # Risk floors (minimum values)
    min_gap_factor: float = 0.5
    min_correlation_factor: float = 0.7
    
    # Risk ceilings (maximum values)
    max_diversification_bonus: float = 1.2
    max_div_adjustment: float = 1.1
    
    # Risk scoring
    gap_score_weights: Dict[str, float] = None
    correlation_score_weights: Dict[str, float] = None
    concentration_score_weight: float = 40.0
    
    # Risk thresholds
    high_risk_threshold: float = 70.0
    moderate_risk_threshold: float = 50.0
    large_gap_threshold: float = 0.05
    frequent_gap_threshold: float = 0.1
    high_correlation_threshold: float = 0.7
    extreme_correlation_threshold: float = 0.9
    low_diversification_threshold: float = 1.2
    significant_slippage_threshold: float = 0.01
    portfolio_correlation_threshold: float = 0.6
    
    def __post_init__(self):
        if self.gap_score_weights is None:
            self.gap_score_weights = {
                "max_gap": 100.0,
                "frequency": 50.0,
                "slippage": 100.0
            }
        if self.correlation_score_weights is None:
            self.correlation_score_weights = {
                "portfolio": 30.0,
                "max_pair": 20.0,
                "diversification": 10.0
            }


@dataclass
class PositionManagementConstants:
    """Constants for position management"""
    # Buffer sizes
    closed_positions_buffer_size: int = 10000
    transaction_history_buffer_size: int = 50000
    portfolio_history_buffer_size: int = 10000
    
    # Confidence multipliers
    high_confidence_multiplier: float = 1.0
    medium_confidence_multiplier: float = 0.7
    low_confidence_multiplier: float = 0.4
    
    # Confidence thresholds
    high_confidence_threshold: float = 0.8
    medium_confidence_threshold: float = 0.5
    
    # Capital management
    min_cash_reserve_ratio: float = 0.1  # 10% of initial capital
    max_position_ratio: float = 0.9  # 90% of total capital
    min_position_ratio: float = 0.01  # 1% of portfolio
    cash_buffer_ratio: float = 0.95  # Leave 5% cash buffer
    
    # Holding period
    max_holding_days: int = 30
    
    # Validation ranges
    slippage_validation_max: float = 0.1
    commission_validation_max: float = 0.1


@dataclass
class CacheManagementConstants:
    """Constants for cache management"""
    # General cache settings
    max_entries: int = 10000
    default_ttl_minutes: int = 30
    cleanup_interval_minutes: int = 5
    
    # LLM specific cache
    llm_cache_max_entries: int = 5000
    llm_cache_ttl_hours: int = 1
    
    # TTL by cache type (in minutes)
    ttl_by_type: Dict[str, int] = None
    
    # Hash truncation lengths
    param_hash_length: int = 8
    prompt_hash_length: int = 16
    context_hash_length: int = 16
    
    # Memory estimates
    cache_entry_overhead_bytes: int = 200
    
    def __post_init__(self):
        if self.ttl_by_type is None:
            self.ttl_by_type = {
                "llm_result": 60,      # 1 hour
                "market_data": 5,      # 5 minutes
                "analysis_result": 30, # 30 minutes
                "decision": 120        # 2 hours
            }


@dataclass
class MemoryManagementConstants:
    """Constants for memory management"""
    # Circular buffer defaults
    default_circular_buffer_size: int = 10000
    
    # Memory limited dict
    default_max_items_per_key: int = 1000
    
    # Memory store
    default_memory_fetch_limit: int = 10
    default_memory_search_limit: int = 10


@dataclass
class RetryHandlerConstants:
    """Constants for retry handling"""
    # Circuit breaker
    failure_threshold: int = 5
    recovery_timeout_minutes: int = 1
    success_threshold: int = 3
    
    # Retry configuration
    max_retry_attempts: int = 3
    min_retry_wait_seconds: float = 1.0
    max_retry_wait_seconds: float = 60.0
    retry_multiplier: float = 2.0
    
    # LLM specific
    llm_failure_threshold: int = 5
    llm_recovery_timeout_minutes: int = 2
    llm_success_threshold: int = 2
    llm_min_wait_seconds: float = 2.0
    llm_max_wait_seconds: float = 30.0


@dataclass
class TransactionConstants:
    """Constants for transaction management"""
    # Buffer size
    transaction_buffer_size: int = 50000
    
    # Transaction log retention
    transaction_log_retention: int = 1000


# Default instances
RISK_ANALYSIS = RiskAnalysisConstants()
POSITION_MANAGEMENT = PositionManagementConstants()
CACHE_MANAGEMENT = CacheManagementConstants()
MEMORY_MANAGEMENT = MemoryManagementConstants()
RETRY_HANDLER = RetryHandlerConstants()
TRANSACTION = TransactionConstants()


def load_constants_from_env() -> None:
    """Load constants from environment variables if available"""
    import os
    
    # Example of loading from environment
    if "BACKTEST_MAX_HOLDING_DAYS" in os.environ:
        POSITION_MANAGEMENT.max_holding_days = int(os.environ["BACKTEST_MAX_HOLDING_DAYS"])
    
    if "BACKTEST_CACHE_MAX_ENTRIES" in os.environ:
        CACHE_MANAGEMENT.max_entries = int(os.environ["BACKTEST_CACHE_MAX_ENTRIES"])
    
    # Add more environment variable mappings as needed