"""
Constants for the backtesting module.
"""

# Time periods
TRADING_DAYS_PER_YEAR = 252
MONTHS_PER_YEAR = 12
DAYS_PER_YEAR = 365.25

# Default values
DEFAULT_INITIAL_CAPITAL = 10000.0
DEFAULT_RISK_FREE_RATE = 0.02
DEFAULT_SLIPPAGE = 0.001

# Maximum values (instead of float('inf'))
MAX_SHARPE_RATIO = 999.99
MAX_SORTINO_RATIO = 999.99
MAX_PROFIT_FACTOR = 999.99
MAX_CALMAR_RATIO = 999.99

# Minimum values
MIN_INITIAL_CAPITAL = 100.0
MIN_SLIPPAGE = 0.0
MAX_SLIPPAGE = 0.10  # 10%

# Validation patterns
TICKER_PATTERN = r'^[A-Z0-9\.\-]{1,10}$'  # Allows dots and dashes for international tickers
DATE_FORMAT = '%Y-%m-%d'