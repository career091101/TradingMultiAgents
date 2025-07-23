"""
Backtest simulator for TradingAgents framework.

This module provides the core backtesting functionality to simulate trading strategies
using the TradingAgents framework on historical data.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import yfinance as yf
from dataclasses import dataclass, field
import sys
import os

# Handle import based on execution context
try:
    # Try relative imports first (when run as module)
    from .constants import (
        DEFAULT_INITIAL_CAPITAL, DEFAULT_SLIPPAGE, 
        TRADING_DAYS_PER_YEAR
    )
    from .validation import (
        validate_ticker, validate_date_range, 
        validate_capital, validate_slippage, ValidationError
    )
    from .path_utils import get_tradingagents_config, get_project_paths
    from .logging_config import get_logger, get_structured_logger
except ImportError:
    # Fall back to absolute imports (when run directly)
    from constants import (
        DEFAULT_INITIAL_CAPITAL, DEFAULT_SLIPPAGE, 
        TRADING_DAYS_PER_YEAR
    )
    from validation import (
        validate_ticker, validate_date_range, 
        validate_capital, validate_slippage, ValidationError
    )
    from path_utils import get_tradingagents_config, get_project_paths
    from logging_config import get_logger, get_structured_logger

# Add parent directory to path to import tradingagents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG
except ImportError:
    # If direct import fails, try alternative paths
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'TradingMultiAgents'))
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG

# Configure logging
logger = get_logger('simulator')
structured_logger = get_structured_logger()


@dataclass
class Trade:
    """Represents a single trade in the backtest."""
    date: datetime
    action: str  # BUY, SELL, HOLD
    price: float
    shares: float
    cash_before: float
    cash_after: float
    portfolio_value: float
    signal_details: Optional[str] = None


@dataclass
class BacktestResult:
    """Contains the results of a backtest simulation."""
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    dates: List[datetime] = field(default_factory=list)
    final_portfolio_value: float = 0.0
    initial_capital: float = 0.0
    ticker: str = ""
    start_date: str = ""
    end_date: str = ""
    
    @property
    def total_return(self) -> float:
        """Calculate total return percentage."""
        if self.initial_capital == 0:
            return 0.0
        return ((self.final_portfolio_value - self.initial_capital) / self.initial_capital) * 100
    
    @property
    def num_trades(self) -> int:
        """Count number of actual trades (excluding HOLD)."""
        return sum(1 for trade in self.trades if trade.action in ['BUY', 'SELL'])


class BacktestSimulator:
    """
    Main backtesting simulator for TradingAgents strategies.
    
    This class handles the simulation of trading strategies using the TradingAgents
    framework on historical data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, debug: bool = False, fast_mode: bool = False):
        """
        Initialize the backtest simulator.
        
        Args:
            config: Configuration dictionary for TradingAgentsGraph (defaults to DEFAULT_CONFIG)
            debug: Enable debug mode for more verbose output
            fast_mode: Enable fast mode with reduced agents and no debates
        """
        # Create a safe default config for backtesting
        base_config = DEFAULT_CONFIG.copy()
        
        # Use centralized path resolution
        path_config = get_tradingagents_config()
        
        base_config.update({
            **path_config,
            "online_tools": False,  # Always use offline for backtesting
            # Ensure LLM settings are present with safe defaults
            "llm_provider": base_config.get("llm_provider", "openai"),
            "deep_think_llm": "gpt-4o-mini",  # Use standard model for backtesting
            "quick_think_llm": "gpt-4o-mini",  # Use standard model for backtesting
            "backend_url": base_config.get("backend_url", "https://api.openai.com/v1")
        })
        
        # Apply fast mode optimizations
        if fast_mode:
            logger.info("Fast mode enabled - using minimal agents and no debates")
            base_config.update({
                "max_debate_rounds": 0,  # Skip debates
                "max_risk_discuss_rounds": 0,  # Skip risk discussions
                "quick_think_llm": "gpt-3.5-turbo",  # Use faster model
                "deep_think_llm": "gpt-4o-mini",  # Use faster deep think model
                "temperature": 0  # Deterministic outputs
            })
        
        # Apply user config if provided
        if config:
            base_config.update(config)
            
        self.config = base_config
        self.debug = debug
        self.fast_mode = fast_mode
        self.agent = None
        
    def _initialize_agent(self) -> TradingAgentsGraph:
        """Initialize the TradingAgents graph with the given configuration."""
        logger.info("Initializing TradingAgents graph...")
        
        # Ensure offline mode for backtesting reproducibility
        backtest_config = self.config.copy()
        backtest_config['online_tools'] = False
        
        # Log configuration for debugging
        if self.debug:
            logger.debug(f"Initializing with config: {backtest_config}")
        
        try:
            return TradingAgentsGraph(debug=self.debug, config=backtest_config)
        except Exception as e:
            logger.error(f"Failed to initialize TradingAgentsGraph: {e}")
            logger.error(f"Config used: {backtest_config}")
            raise
    
    def _fetch_historical_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch historical price data for the given ticker and date range.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DataFrame with historical price data
        """
        logger.info(f"Fetching historical data for {ticker} from {start_date} to {end_date}")
        
        try:
            # Fetch data using yfinance
            stock = yf.Ticker(ticker)
            hist_data = stock.history(start=start_date, end=end_date)
            
            if hist_data.empty:
                raise ValueError(f"No data found for ticker {ticker} in the specified date range")
            
            # Validate data quality
            if 'Close' not in hist_data.columns or hist_data['Close'].isna().all():
                raise ValueError(f"No valid price data for ticker {ticker}")
            
            # Reset index to have date as a column
            hist_data.reset_index(inplace=True)
            
            return hist_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            raise
    
    def _execute_trade(self, action: str, current_price: float, cash: float, shares: float,
                      slippage: float = 0.0) -> Tuple[float, float]:
        """
        Execute a trade based on the signal.
        
        Args:
            action: Trading action (BUY, SELL, HOLD)
            current_price: Current stock price
            cash: Available cash
            shares: Current share holdings
            slippage: Slippage percentage (0.0 to 1.0)
            
        Returns:
            Tuple of (new_cash, new_shares)
        """
        if action == "BUY" and cash > 0 and shares == 0:
            # Apply slippage - buy at slightly higher price
            buy_price = current_price * (1 + slippage)
            
            # Calculate maximum shares we can buy
            max_shares = cash / buy_price
            
            # Execute purchase
            new_shares = max_shares
            new_cash = 0  # Use all available cash
            
            logger.info(f"Executing BUY: {new_shares:.2f} shares at ${buy_price:.2f}")
            
        elif action == "SELL" and shares > 0:
            # Apply slippage - sell at slightly lower price
            sell_price = current_price * (1 - slippage)
            
            # Sell all shares
            new_cash = cash + (shares * sell_price)
            new_shares = 0
            
            logger.info(f"Executing SELL: {shares:.2f} shares at ${sell_price:.2f}")
            
        else:
            # HOLD or no action possible
            new_cash = cash
            new_shares = shares
            
        return new_cash, new_shares
    
    def _parse_trading_signal(self, agent_output: Tuple[Any, str]) -> str:
        """
        Parse the agent output to extract the trading signal.
        
        Args:
            agent_output: Output from TradingAgentsGraph.propagate()
            
        Returns:
            Trading signal: "BUY", "SELL", or "HOLD"
        """
        try:
            # The output is typically (final_state, decision)
            if isinstance(agent_output, tuple) and len(agent_output) >= 2:
                decision = agent_output[1]
            else:
                decision = str(agent_output)
            
            # Convert to uppercase and look for keywords
            decision_upper = decision.upper()
            
            if "BUY" in decision_upper:
                return "BUY"
            elif "SELL" in decision_upper:
                return "SELL"
            else:
                return "HOLD"
                
        except Exception as e:
            logger.warning(f"Error parsing trading signal: {str(e)}. Defaulting to HOLD.")
            return "HOLD"
    
    def run_backtest(self, ticker: str, start_date: str, end_date: str,
                    initial_capital: float = DEFAULT_INITIAL_CAPITAL, 
                    slippage: float = DEFAULT_SLIPPAGE) -> BacktestResult:
        """
        Run a backtest for a single ticker over the specified date range.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            initial_capital: Starting cash amount
            slippage: Slippage percentage (e.g., 0.001 for 0.1%)
            
        Returns:
            BacktestResult object containing all simulation results
        """
        # Validate inputs
        try:
            ticker = validate_ticker(ticker)
            start_dt, end_dt = validate_date_range(start_date, end_date)
            initial_capital = validate_capital(initial_capital)
            slippage = validate_slippage(slippage)
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        
        logger.info(f"Starting backtest for {ticker}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Initial capital: ${initial_capital:,.2f}")
        logger.info(f"Slippage: {slippage*100:.2f}%")
        
        # Log backtest start with structured logger
        structured_logger.log_backtest_start({
            'ticker': ticker,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital,
            'slippage': slippage,
            'fast_mode': self.fast_mode,
            'config': {k: v for k, v in self.config.items() if k not in ['project_dir', 'data_dir', 'data_cache_dir']}
        })
        
        # Initialize agent
        if self.agent is None:
            self.agent = self._initialize_agent()
        
        # Fetch historical data
        hist_data = self._fetch_historical_data(ticker, start_date, end_date)
        
        # Initialize portfolio
        cash = initial_capital
        shares = 0.0
        
        # Initialize result container
        result = BacktestResult(
            initial_capital=initial_capital,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date
        )
        
        # Log expected duration
        total_days = len(hist_data)
        logger.info(f"Processing {total_days} trading days. This may take several minutes...")
        
        # Iterate through each trading day
        for idx, row in hist_data.iterrows():
            current_date = row['Date']
            current_price = row['Close']
            
            # Skip if price data is invalid
            if pd.isna(current_price) or current_price <= 0:
                logger.warning(f"Invalid price data for {current_date}, skipping")
                continue
            
            # Get agent's trading decision
            logger.debug(f"Getting agent decision for {ticker} on {current_date.strftime('%Y-%m-%d')}")
            
            try:
                # Call the agent's propagate method
                agent_output = self.agent.propagate(ticker, current_date.strftime('%Y-%m-%d'))
                signal = self._parse_trading_signal(agent_output)
                
            except Exception as e:
                logger.error(f"Error getting agent decision: {str(e)}. Defaulting to HOLD.")
                signal = "HOLD"
            
            # Record portfolio value before trade
            portfolio_value_before = cash + (shares * current_price)
            
            # Execute trade
            new_cash, new_shares = self._execute_trade(
                signal, current_price, cash, shares, slippage
            )
            
            # Update portfolio
            cash = new_cash
            shares = new_shares
            
            # Calculate portfolio value after trade
            portfolio_value_after = cash + (shares * current_price)
            
            # Record trade
            trade = Trade(
                date=current_date,
                action=signal,
                price=current_price,
                shares=shares,
                cash_before=portfolio_value_before,
                cash_after=cash,
                portfolio_value=portfolio_value_after
            )
            result.trades.append(trade)
            
            # Log trade with structured logger
            structured_logger.log_trade(
                ticker=ticker,
                action=signal,
                price=current_price,
                shares=shares,
                portfolio_value=portfolio_value_after,
                date=current_date.strftime('%Y-%m-%d'),
                cash=cash
            )
            
            # Update equity curve
            result.equity_curve.append(portfolio_value_after)
            result.dates.append(current_date)
            
            logger.info(f"{current_date.strftime('%Y-%m-%d')}: {signal} @ ${current_price:.2f}, "
                       f"Portfolio: ${portfolio_value_after:,.2f}")
        
        # Close any remaining position at the end
        if shares > 0 and len(hist_data) > 0:
            final_price = hist_data.iloc[-1]['Close']
            cash += shares * final_price
            shares = 0
            logger.info(f"Closing final position at ${final_price:.2f}")
        
        # Set final portfolio value
        result.final_portfolio_value = cash
        
        logger.info(f"Backtest completed. Final value: ${result.final_portfolio_value:,.2f}")
        logger.info(f"Total return: {result.total_return:.2f}%")
        
        # Log backtest completion
        structured_logger.log_backtest_end({
            'ticker': ticker,
            'initial_capital': initial_capital,
            'final_value': result.final_portfolio_value,
            'total_return': result.total_return,
            'num_trades': result.num_trades,
            'duration_days': len(hist_data)
        })
        
        return result
    
    def run_portfolio_backtest(self, tickers: List[str], start_date: str, end_date: str,
                             initial_capital: float = 10000.0, slippage: float = 0.0) -> Dict[str, BacktestResult]:
        """
        Run backtests for multiple tickers independently.
        
        Each ticker gets an equal allocation of the initial capital.
        
        Args:
            tickers: List of stock ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            initial_capital: Total starting cash amount
            slippage: Slippage percentage
            
        Returns:
            Dictionary mapping ticker to BacktestResult
        """
        results = {}
        capital_per_ticker = initial_capital / len(tickers)
        
        logger.info(f"Running portfolio backtest for {len(tickers)} tickers")
        logger.info(f"Capital per ticker: ${capital_per_ticker:,.2f}")
        
        for ticker in tickers:
            try:
                result = self.run_backtest(
                    ticker, start_date, end_date, capital_per_ticker, slippage
                )
                results[ticker] = result
                
            except Exception as e:
                logger.error(f"Failed to backtest {ticker}: {str(e)}")
                continue
        
        return results