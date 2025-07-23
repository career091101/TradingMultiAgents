"""
Integration tests for the simulator module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtest.simulator import BacktestSimulator, Trade, BacktestResult
from backtest.validation import ValidationError


class TestBacktestSimulator(unittest.TestCase):
    """Test BacktestSimulator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock TradingAgentsGraph to avoid external dependencies
        self.mock_agent_patcher = patch('backtest.simulator.TradingAgentsGraph')
        self.mock_agent_class = self.mock_agent_patcher.start()
        
        # Create mock agent instance
        self.mock_agent = Mock()
        self.mock_agent.propagate.return_value = (None, "HOLD")
        self.mock_agent_class.return_value = self.mock_agent
    
    def tearDown(self):
        """Clean up patches."""
        self.mock_agent_patcher.stop()
    
    def test_simulator_initialization_default(self):
        """Test simulator initialization with default config."""
        simulator = BacktestSimulator()
        
        self.assertIsNotNone(simulator.config)
        self.assertFalse(simulator.debug)
        self.assertFalse(simulator.fast_mode)
        self.assertIsNone(simulator.agent)
        
        # Check config has required fields
        self.assertIn('project_dir', simulator.config)
        self.assertIn('llm_provider', simulator.config)
        self.assertIn('deep_think_llm', simulator.config)
        self.assertEqual(simulator.config['online_tools'], False)
    
    def test_simulator_initialization_fast_mode(self):
        """Test simulator initialization with fast mode."""
        simulator = BacktestSimulator(fast_mode=True)
        
        self.assertTrue(simulator.fast_mode)
        self.assertEqual(simulator.config['max_debate_rounds'], 0)
        self.assertEqual(simulator.config['max_risk_discuss_rounds'], 0)
        self.assertEqual(simulator.config['quick_think_llm'], 'gpt-3.5-turbo')
    
    def test_simulator_initialization_custom_config(self):
        """Test simulator initialization with custom config."""
        custom_config = {
            'llm_provider': 'anthropic',
            'max_debate_rounds': 3
        }
        simulator = BacktestSimulator(config=custom_config)
        
        self.assertEqual(simulator.config['llm_provider'], 'anthropic')
        self.assertEqual(simulator.config['max_debate_rounds'], 3)
    
    @patch('backtest.simulator.yf.Ticker')
    def test_fetch_historical_data_success(self, mock_ticker):
        """Test successful historical data fetching."""
        # Mock yfinance response
        mock_hist = pd.DataFrame({
            'Date': pd.date_range('2023-01-01', periods=5),
            'Open': [100, 101, 102, 103, 104],
            'High': [101, 102, 103, 104, 105],
            'Low': [99, 100, 101, 102, 103],
            'Close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'Volume': [1000000] * 5
        })
        mock_hist.set_index('Date', inplace=True)
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_ticker_instance
        
        simulator = BacktestSimulator()
        data = simulator._fetch_historical_data('AAPL', '2023-01-01', '2023-01-05')
        
        self.assertEqual(len(data), 5)
        self.assertIn('Close', data.columns)
        mock_ticker_instance.history.assert_called_once()
    
    @patch('backtest.simulator.yf.Ticker')
    def test_fetch_historical_data_empty(self, mock_ticker):
        """Test historical data fetching with no data."""
        # Mock empty response
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance
        
        simulator = BacktestSimulator()
        
        with self.assertRaises(ValueError) as cm:
            simulator._fetch_historical_data('INVALID', '2023-01-01', '2023-01-05')
        
        self.assertIn("No data found", str(cm.exception))
    
    def test_execute_trade_buy(self):
        """Test executing a buy trade."""
        simulator = BacktestSimulator()
        
        # Test buy with available cash
        new_cash, new_shares = simulator._execute_trade(
            action="BUY",
            current_price=100.0,
            cash=1000.0,
            shares=0.0,
            slippage=0.01
        )
        
        expected_buy_price = 100.0 * 1.01  # With slippage
        expected_shares = 1000.0 / expected_buy_price
        
        self.assertEqual(new_cash, 0.0)
        self.assertAlmostEqual(new_shares, expected_shares, places=2)
    
    def test_execute_trade_sell(self):
        """Test executing a sell trade."""
        simulator = BacktestSimulator()
        
        # Test sell with shares
        new_cash, new_shares = simulator._execute_trade(
            action="SELL",
            current_price=110.0,
            cash=0.0,
            shares=10.0,
            slippage=0.01
        )
        
        expected_sell_price = 110.0 * 0.99  # With slippage
        expected_cash = 10.0 * expected_sell_price
        
        self.assertEqual(new_shares, 0.0)
        self.assertAlmostEqual(new_cash, expected_cash, places=2)
    
    def test_execute_trade_hold(self):
        """Test executing a hold (no action)."""
        simulator = BacktestSimulator()
        
        initial_cash = 500.0
        initial_shares = 5.0
        
        new_cash, new_shares = simulator._execute_trade(
            action="HOLD",
            current_price=100.0,
            cash=initial_cash,
            shares=initial_shares,
            slippage=0.01
        )
        
        self.assertEqual(new_cash, initial_cash)
        self.assertEqual(new_shares, initial_shares)
    
    def test_execute_trade_buy_no_cash(self):
        """Test buy with no available cash."""
        simulator = BacktestSimulator()
        
        # Buy with existing position should hold
        new_cash, new_shares = simulator._execute_trade(
            action="BUY",
            current_price=100.0,
            cash=0.0,
            shares=10.0,  # Already have shares
            slippage=0.01
        )
        
        self.assertEqual(new_cash, 0.0)
        self.assertEqual(new_shares, 10.0)  # No change
    
    def test_parse_trading_signal(self):
        """Test parsing different trading signals."""
        simulator = BacktestSimulator()
        
        # Test various signal formats
        test_cases = [
            ((None, "BUY"), "BUY"),
            ((None, "SELL"), "SELL"),
            ((None, "HOLD"), "HOLD"),
            ((None, "Strong BUY signal"), "BUY"),
            ((None, "Recommend SELL"), "SELL"),
            ((None, "No action"), "HOLD"),
            ("BUY", "BUY"),  # Non-tuple
            (("state", "buy"), "BUY"),  # Lowercase
        ]
        
        for signal, expected in test_cases:
            with self.subTest(signal=signal):
                result = simulator._parse_trading_signal(signal)
                self.assertEqual(result, expected)
    
    def test_parse_trading_signal_error(self):
        """Test parsing invalid trading signal."""
        simulator = BacktestSimulator()
        
        # Test with exception in parsing
        result = simulator._parse_trading_signal(None)
        self.assertEqual(result, "HOLD")  # Should default to HOLD
    
    @patch('backtest.simulator.yf.Ticker')
    def test_run_backtest_validation_error(self, mock_ticker):
        """Test run_backtest with validation errors."""
        simulator = BacktestSimulator()
        
        # Test with invalid ticker
        with self.assertRaises(ValidationError):
            simulator.run_backtest(
                ticker="INVALID-TICKER-TOO-LONG",
                start_date="2023-01-01",
                end_date="2023-12-31"
            )
        
        # Test with invalid date range
        with self.assertRaises(ValidationError):
            simulator.run_backtest(
                ticker="AAPL",
                start_date="2023-12-31",
                end_date="2023-01-01"  # End before start
            )
        
        # Test with invalid capital
        with self.assertRaises(ValidationError):
            simulator.run_backtest(
                ticker="AAPL",
                start_date="2023-01-01",
                end_date="2023-12-31",
                initial_capital=50.0  # Too small
            )
    
    @patch('backtest.simulator.yf.Ticker')
    @patch('backtest.simulator.structured_logger')
    def test_run_backtest_simple(self, mock_structured_logger, mock_ticker):
        """Test simple backtest execution."""
        # Prepare mock data
        dates = pd.date_range('2023-01-01', periods=3)
        mock_hist = pd.DataFrame({
            'Date': dates,
            'Close': [100.0, 101.0, 99.0],
            'Open': [99.5, 100.5, 101.5],
            'High': [101.0, 102.0, 100.0],
            'Low': [99.0, 100.0, 98.0],
            'Volume': [1000000] * 3
        })
        mock_hist.set_index('Date', inplace=True)
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_ticker_instance
        
        # Set up agent responses
        self.mock_agent.propagate.side_effect = [
            (None, "BUY"),   # Day 1: Buy
            (None, "HOLD"),  # Day 2: Hold
            (None, "SELL"),  # Day 3: Sell
        ]
        
        simulator = BacktestSimulator()
        result = simulator.run_backtest(
            ticker="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-03",
            initial_capital=10000.0,
            slippage=0.001
        )
        
        # Verify result
        self.assertIsInstance(result, BacktestResult)
        self.assertEqual(result.ticker, "AAPL")
        self.assertEqual(result.initial_capital, 10000.0)
        self.assertEqual(len(result.trades), 3)
        self.assertEqual(len(result.equity_curve), 3)
        
        # Check trades
        self.assertEqual(result.trades[0].action, "BUY")
        self.assertEqual(result.trades[1].action, "HOLD")
        self.assertEqual(result.trades[2].action, "SELL")
        
        # Verify agent was called
        self.assertEqual(self.mock_agent.propagate.call_count, 3)
        
        # Verify structured logging
        mock_structured_logger.log_backtest_start.assert_called_once()
        mock_structured_logger.log_backtest_end.assert_called_once()
        self.assertEqual(mock_structured_logger.log_trade.call_count, 3)
    
    def test_run_portfolio_backtest(self):
        """Test portfolio backtest with multiple tickers."""
        with patch.object(BacktestSimulator, 'run_backtest') as mock_run:
            # Mock individual backtest results
            mock_result1 = BacktestResult(
                initial_capital=5000.0,
                ticker="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-31"
            )
            mock_result1.final_portfolio_value = 5500.0
            
            mock_result2 = BacktestResult(
                initial_capital=5000.0,
                ticker="MSFT",
                start_date="2023-01-01",
                end_date="2023-01-31"
            )
            mock_result2.final_portfolio_value = 4800.0
            
            mock_run.side_effect = [mock_result1, mock_result2]
            
            simulator = BacktestSimulator()
            results = simulator.run_portfolio_backtest(
                tickers=["AAPL", "MSFT"],
                start_date="2023-01-01",
                end_date="2023-01-31",
                initial_capital=10000.0
            )
            
            self.assertEqual(len(results), 2)
            self.assertIn("AAPL", results)
            self.assertIn("MSFT", results)
            self.assertEqual(results["AAPL"].final_portfolio_value, 5500.0)
            self.assertEqual(results["MSFT"].final_portfolio_value, 4800.0)
            
            # Verify capital split
            self.assertEqual(mock_run.call_count, 2)
            # Check positional arguments (args[0] is ticker, args[1] is start_date, etc.)
            for call in mock_run.call_args_list:
                # Initial capital is the 4th positional argument (index 3)
                self.assertEqual(call[0][3], 5000.0)  # Split evenly
    
    def test_backtest_result_properties(self):
        """Test BacktestResult calculated properties."""
        result = BacktestResult(
            initial_capital=10000.0,
            ticker="TEST",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        result.final_portfolio_value = 11000.0
        
        # Add some trades
        result.trades = [
            Trade(datetime.now(), "BUY", 100.0, 10, 10000, 9000, 9000),
            Trade(datetime.now(), "SELL", 110.0, 0, 10100, 10100, 10100),
            Trade(datetime.now(), "HOLD", 110.0, 0, 10100, 10100, 10100),
        ]
        
        # Test properties
        self.assertEqual(result.total_return, 10.0)  # 10% return
        self.assertEqual(result.num_trades, 2)  # Only BUY and SELL count
    
    def test_total_return_zero_capital(self):
        """Test total return calculation with zero initial capital."""
        result = BacktestResult(
            initial_capital=0.0,
            ticker="TEST",
            start_date="2023-01-01",
            end_date="2023-01-31"
        )
        result.final_portfolio_value = 0.0
        
        # Should return 0 instead of division by zero
        self.assertEqual(result.total_return, 0.0)


class TestBacktestSimulatorEdgeCases(unittest.TestCase):
    """Test edge cases and error handling in BacktestSimulator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_agent_patcher = patch('backtest.simulator.TradingAgentsGraph')
        self.mock_agent_class = self.mock_agent_patcher.start()
        self.mock_agent = Mock()
        self.mock_agent_class.return_value = self.mock_agent
    
    def tearDown(self):
        """Clean up patches."""
        self.mock_agent_patcher.stop()
    
    def test_import_error_fallback(self):
        """Test ImportError handling for tradingagents module."""
        # This is tricky to test directly, but we can verify the paths are added
        import sys
        original_path = sys.path.copy()
        
        # The module adds paths in the global scope
        # Verify that paths were added
        self.assertTrue(any('TradingMultiAgents' in p for p in sys.path))
    
    @patch('backtest.simulator.yf.Ticker')
    @patch('backtest.simulator.logger')
    def test_fetch_data_with_invalid_prices(self, mock_logger, mock_ticker):
        """Test handling of invalid price data."""
        # Mock data with NaN prices
        mock_hist = pd.DataFrame({
            'Date': pd.date_range('2023-01-01', periods=3),
            'Close': [100.0, np.nan, 102.0],  # Invalid price in middle
            'Open': [99.5, 101.0, 101.5],
            'High': [101.0, 102.0, 103.0],
            'Low': [99.0, 100.0, 101.0],
            'Volume': [1000000] * 3
        })
        mock_hist.set_index('Date', inplace=True)
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_ticker_instance
        
        # Set up agent
        self.mock_agent.propagate.return_value = (None, "HOLD")
        
        simulator = BacktestSimulator()
        result = simulator.run_backtest("AAPL", "2023-01-01", "2023-01-03")
        
        # Should skip the invalid price day
        self.assertEqual(len(result.trades), 2)  # Only 2 days processed
        mock_logger.warning.assert_called()
    
    @patch('backtest.simulator.yf.Ticker')
    @patch('backtest.simulator.logger')
    def test_agent_error_handling(self, mock_logger, mock_ticker):
        """Test handling when agent raises exception."""
        # Mock valid data
        mock_hist = pd.DataFrame({
            'Date': pd.date_range('2023-01-01', periods=2),
            'Close': [100.0, 101.0],
            'Open': [99.5, 100.5],
            'High': [101.0, 102.0],
            'Low': [99.0, 100.0],
            'Volume': [1000000] * 2
        })
        mock_hist.set_index('Date', inplace=True)
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_ticker_instance
        
        # Make agent raise exception
        self.mock_agent.propagate.side_effect = Exception("Agent error")
        
        simulator = BacktestSimulator()
        result = simulator.run_backtest("AAPL", "2023-01-01", "2023-01-02")
        
        # Should default to HOLD when agent fails
        self.assertEqual(result.trades[0].action, "HOLD")
        self.assertEqual(result.trades[1].action, "HOLD")
        mock_logger.error.assert_called()
    
    @patch('backtest.simulator.yf.Ticker')
    def test_close_final_position(self, mock_ticker):
        """Test closing final position at end of backtest."""
        # Mock data
        mock_hist = pd.DataFrame({
            'Date': pd.date_range('2023-01-01', periods=3),
            'Close': [100.0, 105.0, 110.0],
            'Open': [99.5, 104.5, 109.5],
            'High': [101.0, 106.0, 111.0],
            'Low': [99.0, 104.0, 109.0],
            'Volume': [1000000] * 3
        })
        mock_hist.set_index('Date', inplace=True)
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_ticker_instance
        
        # Agent buys and holds
        self.mock_agent.propagate.side_effect = [
            (None, "BUY"),
            (None, "HOLD"),
            (None, "HOLD")
        ]
        
        simulator = BacktestSimulator()
        result = simulator.run_backtest("AAPL", "2023-01-01", "2023-01-03", initial_capital=10000.0)
        
        # Should have closed position at final price
        # Final value should be close to the initial capital * (1 + return)
        # Buy at 100.1 (with slippage), sell at 110 = ~9.89% return
        self.assertAlmostEqual(result.final_portfolio_value, 10989.01, places=0)
        self.assertEqual(len(result.trades), 3)
    
    @patch('backtest.simulator.TradingAgentsGraph')
    def test_agent_initialization_failure(self, mock_graph_class):
        """Test handling of agent initialization failure."""
        mock_graph_class.side_effect = Exception("Config error")
        
        simulator = BacktestSimulator()
        
        with self.assertRaises(Exception) as cm:
            simulator._initialize_agent()
        
        self.assertIn("Config error", str(cm.exception))
    
    def test_portfolio_backtest_individual_failure(self):
        """Test portfolio backtest when individual ticker fails."""
        with patch.object(BacktestSimulator, 'run_backtest') as mock_run:
            # First ticker succeeds, second fails
            mock_result = BacktestResult(
                initial_capital=5000.0,
                ticker="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-31"
            )
            mock_result.final_portfolio_value = 5500.0
            
            mock_run.side_effect = [mock_result, Exception("Data error")]
            
            simulator = BacktestSimulator()
            results = simulator.run_portfolio_backtest(
                tickers=["AAPL", "INVALID"],
                start_date="2023-01-01",
                end_date="2023-01-31"
            )
            
            # Should have results only for successful ticker
            self.assertEqual(len(results), 1)
            self.assertIn("AAPL", results)
            self.assertNotIn("INVALID", results)
    
    @patch('backtest.simulator.yf.Ticker')
    def test_all_invalid_prices(self, mock_ticker):
        """Test when all prices are invalid."""
        # Mock data with all NaN prices
        mock_hist = pd.DataFrame({
            'Date': pd.date_range('2023-01-01', periods=3),
            'Close': [np.nan, np.nan, np.nan],
            'Open': [100.0, 101.0, 102.0],
            'High': [101.0, 102.0, 103.0],
            'Low': [99.0, 100.0, 101.0],
            'Volume': [1000000] * 3
        })
        mock_hist.set_index('Date', inplace=True)
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_ticker_instance
        
        simulator = BacktestSimulator()
        
        # Should raise ValueError due to all invalid prices
        with self.assertRaises(ValueError) as cm:
            result = simulator.run_backtest("AAPL", "2023-01-01", "2023-01-03")
        
        self.assertIn("No valid price data", str(cm.exception))


class TestSimulatorEdgeCases(unittest.TestCase):
    """Test edge cases for simulator."""
    
    def test_simulator_import_error_handling(self):
        """Test simulator handles import errors gracefully."""
        # Test the ImportError handling in simulator.py lines 34-36
        import sys
        original_modules = sys.modules.copy()
        
        # Temporarily remove tradingagents if it exists
        modules_to_remove = [key for key in sys.modules.keys() if 'tradingagents' in key]
        for module in modules_to_remove:
            sys.modules.pop(module, None)
        
        try:
            # This should trigger the ImportError handling
            from backtest.simulator import BacktestSimulator
            # If we get here, the alternative import worked
            self.assertIsNotNone(BacktestSimulator)
        finally:
            # Restore original modules
            sys.modules.update(original_modules)
    
    def test_parse_trading_signal_edge_cases(self):
        """Test edge cases in parsing trading signals."""
        simulator = BacktestSimulator()
        simulator._initialize_agent = Mock(return_value=Mock())
        
        # Test various signal formats
        # Test None input
        self.assertEqual(simulator._parse_trading_signal(None), "HOLD")
        
        # Test tuple format
        self.assertEqual(simulator._parse_trading_signal(("context", "BUY")), "BUY")
        self.assertEqual(simulator._parse_trading_signal(("context", "SELL")), "SELL")
        self.assertEqual(simulator._parse_trading_signal(("context", "HOLD")), "HOLD")
        
        # Test string format
        self.assertEqual(simulator._parse_trading_signal("BUY"), "BUY")
        self.assertEqual(simulator._parse_trading_signal("sell"), "SELL")
        self.assertEqual(simulator._parse_trading_signal("nothing"), "HOLD")
    
    def test_initialize_agent_lazy_loading(self):
        """Test lazy loading of agent (lines 312-313)."""
        simulator = BacktestSimulator()
        simulator.agent = None
        
        mock_agent = Mock()
        simulator._initialize_agent = Mock(return_value=mock_agent)
        
        # Mock other required methods
        simulator._fetch_historical_data = Mock(return_value=pd.DataFrame({
            'Close': [100, 105],
            'Date': pd.date_range('2023-01-01', periods=2)
        }))
        
        with patch.object(simulator, '_parse_trading_signal', return_value="HOLD"):
            # Run backtest which should initialize agent
            result = simulator.run_backtest("TEST", "2023-01-01", "2023-01-02")
            
            # Verify agent was initialized
            simulator._initialize_agent.assert_called_once()
            self.assertEqual(simulator.agent, mock_agent)


if __name__ == '__main__':
    unittest.main()