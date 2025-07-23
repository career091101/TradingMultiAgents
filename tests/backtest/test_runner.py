"""
Unit tests for the CLI runner module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import argparse
import sys
import os
from io import StringIO
import json
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtest.runner import parse_arguments, run_single_backtest, save_trade_log, save_metrics_json, main
from backtest.simulator import BacktestResult, Trade
from backtest.metrics import PerformanceMetrics


class TestParseArguments(unittest.TestCase):
    """Test command line argument parsing."""
    
    def test_parse_single_ticker(self):
        """Test parsing with single ticker."""
        test_args = ['runner.py', 'AAPL', '--start', '2023-01-01', '--end', '2023-12-31']
        with patch.object(sys, 'argv', test_args):
            args = parse_arguments()
        
        self.assertEqual(args.tickers, ['AAPL'])
        self.assertEqual(args.start, '2023-01-01')
        self.assertEqual(args.end, '2023-12-31')
        self.assertEqual(args.capital, 10000.0)
        self.assertEqual(args.slippage, 0.0)
        self.assertFalse(args.fast)
        self.assertFalse(args.debug)
        self.assertEqual(args.output, './backtest/results')
        self.assertFalse(args.no_plots)
    
    def test_parse_multiple_tickers(self):
        """Test parsing with multiple tickers."""
        test_args = ['runner.py', 'AAPL', 'MSFT', 'GOOGL', '--start', '2023-01-01', '--end', '2023-12-31']
        with patch.object(sys, 'argv', test_args):
            args = parse_arguments()
        
        self.assertEqual(args.tickers, ['AAPL', 'MSFT', 'GOOGL'])
    
    def test_parse_all_options(self):
        """Test parsing with all options."""
        test_args = [
            'runner.py', 'AAPL', 
            '--start', '2023-01-01', 
            '--end', '2023-12-31',
            '--capital', '50000',
            '--slippage', '0.002',
            '--fast',
            '--debug',
            '--output', 'my_results',
            '--no-plots',
            '--save-trades',
            '--risk-free-rate', '0.03',
            '--config', 'custom_config.json'
        ]
        with patch.object(sys, 'argv', test_args):
            args = parse_arguments()
        
        self.assertEqual(args.capital, 50000.0)
        self.assertEqual(args.slippage, 0.002)
        self.assertTrue(args.fast)
        self.assertTrue(args.debug)
        self.assertEqual(args.output, 'my_results')
        self.assertTrue(args.no_plots)
        self.assertTrue(args.save_trades)
        self.assertEqual(args.risk_free_rate, 0.03)
        self.assertEqual(args.config, 'custom_config.json')
    
    def test_parse_missing_required_args(self):
        """Test parsing with missing required arguments."""
        # Missing --start
        test_args = ['runner.py', 'AAPL', '--end', '2023-12-31']
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit):
                parse_arguments()
        
        # Missing --end
        test_args = ['runner.py', 'AAPL', '--start', '2023-01-01']
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit):
                parse_arguments()


class TestLoadConfig(unittest.TestCase):
    """Test config loading function."""
    
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"key": "value"}')
    def test_load_config_success(self, mock_file):
        """Test successful config loading."""
        from backtest.runner import load_config
        
        config = load_config('config.json')
        
        self.assertEqual(config, {"key": "value"})
        mock_file.assert_called_once_with('config.json', 'r')
    
    @patch('builtins.open', side_effect=FileNotFoundError())
    @patch('backtest.runner.logger')
    def test_load_config_file_not_found(self, mock_logger, mock_file):
        """Test config loading with missing file."""
        from backtest.runner import load_config
        
        config = load_config('missing.json')
        
        self.assertIsNone(config)
        mock_logger.error.assert_called()
    
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='invalid json')
    @patch('backtest.runner.logger')
    def test_load_config_invalid_json(self, mock_logger, mock_file):
        """Test config loading with invalid JSON."""
        from backtest.runner import load_config
        
        config = load_config('invalid.json')
        
        self.assertIsNone(config)
        mock_logger.error.assert_called()


class TestSaveFunctions(unittest.TestCase):
    """Test save functions."""
    
    def setUp(self):
        """Set up test data."""
        self.result = BacktestResult(
            initial_capital=10000.0,
            ticker="AAPL",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        self.result.final_portfolio_value = 12000.0
        self.result.trades = [
            Trade(datetime(2023, 1, 1), "BUY", 100.0, 100, 10000, 0, 10000),
            Trade(datetime(2023, 6, 1), "SELL", 120.0, 0, 12000, 12000, 12000)
        ]
        
        self.metrics = PerformanceMetrics(
            total_return=20.0,
            annualized_return=20.0,
            max_drawdown=5.0,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            win_rate=100.0,
            total_trades=1,
            winning_trades=1,
            losing_trades=0,
            avg_win=20.0,
            avg_loss=0.0,
            profit_factor=0.0,
            calmar_ratio=4.0,
            volatility=15.0
        )
    
    @patch('pandas.DataFrame.to_csv')
    def test_save_trade_log(self, mock_to_csv):
        """Test saving trade log to CSV."""
        save_trade_log(self.result, 'trades.csv')
        
        mock_to_csv.assert_called_once_with('trades.csv', index=False)
        
        # Check DataFrame was created correctly
        call_args = mock_to_csv.call_args
        df_arg = mock_to_csv.call_args[1] if len(mock_to_csv.call_args) > 1 else None
        self.assertIsNotNone(df_arg)
    
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_save_metrics_json(self, mock_file):
        """Test saving metrics to JSON."""
        save_metrics_json(self.metrics, 'AAPL', '/output/dir')
        
        # Check that file was opened with correct pattern
        self.assertEqual(mock_file.call_count, 1)
        file_path = mock_file.call_args[0][0]
        self.assertIn('/output/dir/AAPL_metrics_', file_path)
        self.assertIn('.json', file_path)
        
        # Check JSON content
        written_data = ''.join(call.args[0] for call in mock_file().write.call_args_list)
        data = json.loads(written_data)
        
        self.assertEqual(data['ticker'], 'AAPL')
        self.assertEqual(data['total_return'], 20.0)
        self.assertEqual(data['sharpe_ratio'], 1.5)


class TestRunSingleBacktest(unittest.TestCase):
    """Test run_single_backtest function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_simulator = Mock()
        self.mock_result = Mock()
        self.mock_result.ticker = 'AAPL'
        self.mock_result.initial_capital = 10000.0
        self.mock_result.final_portfolio_value = 12000.0
        self.mock_result.total_return = 20.0
        self.mock_result.num_trades = 10
        self.mock_simulator.run_backtest.return_value = self.mock_result
        
        self.args = Mock(
            start='2023-01-01',
            end='2023-12-31',
            capital=10000.0,
            slippage=0.001,
            risk_free_rate=0.02,
            output='./results',
            save_trades=False,
            no_plots=True
        )
    
    @patch('backtest.runner.calculate_performance_metrics')
    @patch('backtest.runner.format_metrics_report')
    @patch('backtest.runner.save_metrics_json')
    @patch('backtest.runner.os.makedirs')
    @patch('builtins.print')
    def test_run_single_backtest_success(self, mock_print, mock_makedirs,
                                       mock_save_metrics, mock_format, mock_calc):
        """Test successful single backtest run."""
        mock_metrics = Mock()
        mock_calc.return_value = mock_metrics
        mock_format.return_value = "Test Report"
        
        run_single_backtest(self.mock_simulator, 'AAPL', self.args)
        
        # Verify calls
        self.mock_simulator.run_backtest.assert_called_once_with(
            ticker='AAPL', 
            start_date='2023-01-01', 
            end_date='2023-12-31', 
            initial_capital=10000.0, 
            slippage=0.001
        )
        mock_calc.assert_called_once_with(self.mock_result, 0.02)
        mock_format.assert_called_once_with(mock_metrics, 'AAPL')
        mock_save_metrics.assert_called_once()
        mock_print.assert_called()
    
    @patch('backtest.runner.calculate_performance_metrics')
    @patch('backtest.runner.save_trade_log')
    @patch('backtest.runner.create_backtest_report')
    @patch('backtest.runner.save_metrics_json')
    @patch('backtest.runner.format_metrics_report')
    @patch('backtest.runner.os.makedirs')
    @patch('builtins.print')
    def test_run_single_backtest_with_plots_and_trades(self, mock_print, mock_makedirs,
                                                      mock_format, mock_save_metrics,
                                                      mock_create_report, mock_save_trades,
                                                      mock_calc):
        """Test backtest with plots and trade saving enabled."""
        self.args.no_plots = False
        self.args.save_trades = True
        
        mock_metrics = Mock()
        mock_calc.return_value = mock_metrics
        mock_format.return_value = "Test Report"
        
        run_single_backtest(self.mock_simulator, 'AAPL', self.args)
        
        # Verify plots and trades were saved
        mock_create_report.assert_called_once()
        mock_save_trades.assert_called_once()
    
    @patch('backtest.runner.logger')
    @patch('builtins.print')
    def test_run_single_backtest_with_error(self, mock_print, mock_logger):
        """Test error handling in single backtest."""
        self.mock_simulator.run_backtest.side_effect = Exception("Test error")
        
        run_single_backtest(self.mock_simulator, 'AAPL', self.args)
        
        # Should log error
        mock_logger.error.assert_called()
        # Should print error message
        print_args = [str(call) for call in mock_print.call_args_list]
        error_found = any('Error' in arg or 'error' in arg.lower() for arg in print_args)
        self.assertTrue(error_found)


class TestMainFunction(unittest.TestCase):
    """Test main function integration."""
    
    @patch('backtest.runner.parse_arguments')
    @patch('backtest.runner.BacktestSimulator')
    @patch('backtest.runner.run_single_backtest')
    def test_main_single_ticker(self, mock_run_single, mock_simulator_class, mock_parse):
        """Test main with single ticker."""
        args = Mock(
            tickers=['AAPL'],
            config=None,
            debug=False,
            fast=False,
            start='2023-01-01',
            end='2023-12-31'
        )
        mock_parse.return_value = args
        
        mock_simulator = Mock()
        mock_simulator_class.return_value = mock_simulator
        
        main()
        
        mock_simulator_class.assert_called_once_with(
            config=None,
            debug=False,
            fast_mode=False
        )
        mock_run_single.assert_called_once_with(mock_simulator, 'AAPL', args)
    
    @patch('backtest.runner.parse_arguments')
    @patch('backtest.runner.BacktestSimulator')
    @patch('backtest.runner.run_single_backtest')
    @patch('backtest.runner.load_config')
    def test_main_with_config(self, mock_load_config, mock_run_single,
                             mock_simulator_class, mock_parse):
        """Test main with custom config."""
        args = Mock(
            tickers=['AAPL'],
            config='custom.json',
            debug=True,
            fast=True,
            start='2023-01-01',
            end='2023-12-31'
        )
        mock_parse.return_value = args
        
        mock_config = {'key': 'value'}
        mock_load_config.return_value = mock_config
        
        mock_simulator = Mock()
        mock_simulator_class.return_value = mock_simulator
        
        main()
        
        mock_load_config.assert_called_once_with('custom.json')
        mock_simulator_class.assert_called_once_with(
            config=mock_config,
            debug=True,
            fast_mode=True
        )
    
    @patch('backtest.runner.parse_arguments')
    @patch('backtest.runner.BacktestSimulator')
    @patch('backtest.runner.run_single_backtest')
    def test_main_multiple_tickers(self, mock_run_single, mock_simulator_class, mock_parse):
        """Test main with multiple tickers."""
        args = Mock(
            tickers=['AAPL', 'MSFT', 'GOOGL'],
            config=None,
            debug=False,
            fast=False,
            start='2023-01-01',
            end='2023-12-31'
        )
        mock_parse.return_value = args
        
        mock_simulator = Mock()
        mock_simulator_class.return_value = mock_simulator
        
        main()
        
        # Should run backtest for each ticker
        self.assertEqual(mock_run_single.call_count, 3)
        calls = mock_run_single.call_args_list
        self.assertEqual(calls[0][0][1], 'AAPL')
        self.assertEqual(calls[1][0][1], 'MSFT')
        self.assertEqual(calls[2][0][1], 'GOOGL')


class TestRunnerMissingCoverage(unittest.TestCase):
    """Test missing coverage in runner module."""
    
    @patch('backtest.runner.BacktestSimulator')
    @patch('backtest.runner.run_single_backtest')
    @patch('logging.getLogger')
    @patch('backtest.runner.parse_arguments')
    def test_main_debug_mode_sets_logging(self, mock_parse, mock_get_logger,
                                        mock_run_single, mock_simulator_class):
        """Test debug mode sets logging level (line 237)."""
        import logging
        
        args = Mock(
            tickers=['AAPL'],
            start='2023-01-01',
            end='2023-12-31',
            debug=True,  # Enable debug mode
            config=None
        )
        mock_parse.return_value = args
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        mock_simulator = Mock()
        mock_simulator_class.return_value = mock_simulator
        
        main()
        
        # Should set debug level
        mock_logger.setLevel.assert_called_with(logging.DEBUG)
    
    @patch('backtest.runner.calculate_performance_metrics')
    @patch('backtest.runner.save_trade_log')
    @patch('backtest.runner.save_metrics_json')
    @patch('backtest.runner.format_metrics_report')
    @patch('backtest.runner.os.makedirs')
    @patch('backtest.runner.logger')
    @patch('builtins.print')
    def test_run_single_backtest_validation_error(self, mock_print, mock_logger,
                                                 mock_makedirs, mock_format,
                                                 mock_save_metrics, mock_save_trades,
                                                 mock_calc):
        """Test handling of ValidationError (lines 221-223)."""
        from backtest.validation import ValidationError
        
        mock_simulator = Mock()
        mock_simulator.run_backtest.side_effect = ValidationError("Invalid ticker")
        
        args = Mock(
            start='2023-01-01',
            end='2023-12-31',
            capital=10000.0,
            slippage=0.001,
            risk_free_rate=0.02,
            output='./results',
            save_trades=False,
            no_plots=True,
            debug=False
        )
        
        run_single_backtest(mock_simulator, 'INVALID', args)
        
        # Should log error but not print traceback
        mock_logger.error.assert_called_with("Validation error for INVALID: Invalid ticker")
        # Should not call traceback
        self.assertEqual(mock_print.call_count, 0)
    
    @patch('backtest.runner.calculate_performance_metrics')
    @patch('backtest.runner.logger')
    @patch('builtins.print')
    @patch('traceback.print_exc')
    def test_run_single_backtest_debug_mode(self, mock_traceback, mock_print,
                                           mock_logger, mock_calc):
        """Test debug mode prints traceback (lines 226-228)."""
        mock_simulator = Mock()
        mock_simulator.run_backtest.side_effect = Exception("Test error")
        
        args = Mock(
            start='2023-01-01',
            end='2023-12-31',
            capital=10000.0,
            slippage=0.001,
            risk_free_rate=0.02,
            output='./results',
            save_trades=False,
            no_plots=True,
            debug=True  # Enable debug mode
        )
        
        run_single_backtest(mock_simulator, 'TEST', args)
        
        # Should print traceback in debug mode
        mock_traceback.assert_called_once()
    
    @patch('sys.exit')
    @patch('backtest.runner.logger')
    @patch('backtest.runner.parse_arguments')
    def test_main_invalid_date_format(self, mock_parse, mock_logger, mock_exit):
        """Test invalid date format handling (lines 248-250)."""
        args = Mock(
            tickers=['AAPL'],
            start='invalid-date',
            end='2023-12-31',
            debug=False,
            config=None
        )
        mock_parse.return_value = args
        
        main()
        
        # Check that error was logged (exact message may vary)
        mock_logger.error.assert_called()
        error_msg = mock_logger.error.call_args[0][0]
        self.assertIn("Invalid date format", error_msg)
        mock_exit.assert_called_with(1)
    
    @patch('sys.exit')
    @patch('backtest.runner.logger')
    @patch('backtest.runner.parse_arguments')
    def test_main_start_after_end(self, mock_parse, mock_logger, mock_exit):
        """Test start date after end date (lines 244-246)."""
        args = Mock(
            tickers=['AAPL'],
            start='2023-12-31',
            end='2023-01-01',
            debug=False,
            config=None
        )
        mock_parse.return_value = args
        
        main()
        
        # Check that error was logged (exact message may vary)
        mock_logger.error.assert_called()
        error_msg = mock_logger.error.call_args[0][0]
        self.assertIn("Start date must be before end date", error_msg)
        mock_exit.assert_called_with(1)
    
    @patch('backtest.runner.BacktestSimulator')
    @patch('backtest.runner.run_single_backtest')
    @patch('backtest.runner.load_config')
    @patch('backtest.runner.logger')
    @patch('backtest.runner.parse_arguments')
    def test_main_config_load_failure(self, mock_parse, mock_logger, mock_load_config,
                                    mock_run_single, mock_simulator_class):
        """Test config load failure handling (line 257)."""
        args = Mock(
            tickers=['AAPL'],
            start='2023-01-01',
            end='2023-12-31',
            debug=False,
            fast=False,
            config='custom.json'
        )
        mock_parse.return_value = args
        
        # Config load fails
        mock_load_config.return_value = None
        
        mock_simulator = Mock()
        mock_simulator_class.return_value = mock_simulator
        
        main()
        
        # Should log warning about failed config
        mock_logger.warning.assert_called()
        warning_msg = mock_logger.warning.call_args[0][0]
        self.assertIn("Failed to load custom config", warning_msg)
        # Should still create simulator with None config
        mock_simulator_class.assert_called_once_with(config=None, debug=False, fast_mode=False)


if __name__ == '__main__':
    unittest.main()