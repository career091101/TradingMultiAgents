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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, debug: bool = False):
        """
        Initialize the backtest simulator.
        
        Args:
            config: Configuration dictionary for TradingAgentsGraph (defaults to DEFAULT_CONFIG)
            debug: Enable debug mode for more verbose output
        """
        self.config = config or DEFAULT_CONFIG.copy()
        self.debug = debug
        self.agent = None
        
    def _initialize_agent(self) -> TradingAgentsGraph:
        """Initialize the TradingAgents graph with the given configuration."""
        logger.info("Initializing TradingAgents graph...")
        
        # Ensure offline mode for backtesting reproducibility
        backtest_config = self.config.copy()
        backtest_config['online_tools'] = False
        
        return TradingAgentsGraph(debug=self.debug, config=backtest_config)
    
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
                    initial_capital: float = 10000.0, slippage: float = 0.0) -> BacktestResult:
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
        logger.info(f"Starting backtest for {ticker}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Initial capital: ${initial_capital:,.2f}")
        logger.info(f"Slippage: {slippage*100:.2f}%")
        
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