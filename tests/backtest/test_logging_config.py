"""
Unit tests for logging_config module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import logging
import json
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtest.logging_config import (
    BacktestLogger, ColoredFormatter, StructuredLogger, 
    JSONFormatter, get_logger, get_structured_logger,
    configure_logging
)


class TestBacktestLogger(unittest.TestCase):
    """Test BacktestLogger class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        # Clear any existing handlers
        logging.getLogger('backtest').handlers.clear()
        logging.getLogger('backtest_test').handlers.clear()
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
        # Clear handlers
        logging.getLogger('backtest').handlers.clear()
        logging.getLogger('backtest_test').handlers.clear()
    
    def test_init_default(self):
        """Test initialization with defaults."""
        logger = BacktestLogger(name='backtest_test')
        
        self.assertEqual(logger.name, 'backtest_test')
        self.assertIsNotNone(logger.logger)
        self.assertIsNotNone(logger.log_dir)
    
    def test_init_custom_log_dir(self):
        """Test initialization with custom log directory."""
        custom_dir = Path(self.temp_dir) / "custom_logs"
        logger = BacktestLogger(name='backtest_test', log_dir=custom_dir)
        
        self.assertEqual(logger.log_dir, custom_dir)
        self.assertTrue(custom_dir.exists())
    
    def test_configure_logger_handlers(self):
        """Test that logger is configured with correct handlers."""
        logger = BacktestLogger(name='backtest_test', log_dir=Path(self.temp_dir))
        
        # Should have 4 handlers: console, info file, error file, debug file
        self.assertEqual(len(logger.logger.handlers), 4)
        
        # Check handler types
        handler_types = [type(h).__name__ for h in logger.logger.handlers]
        self.assertIn('StreamHandler', handler_types)
        self.assertEqual(handler_types.count('RotatingFileHandler'), 3)
    
    def test_no_duplicate_handlers(self):
        """Test that handlers are not duplicated on multiple calls."""
        logger = BacktestLogger(name='backtest_test', log_dir=Path(self.temp_dir))
        initial_count = len(logger.logger.handlers)
        
        # Configure again
        logger._configure_logger()
        
        # Should still have same number of handlers
        self.assertEqual(len(logger.logger.handlers), initial_count)
    
    def test_console_handler_level(self):
        """Test console handler log level."""
        logger = BacktestLogger(name='backtest_test', log_dir=Path(self.temp_dir))
        
        # Find console handler
        console_handler = next(h for h in logger.logger.handlers 
                             if isinstance(h, logging.StreamHandler))
        
        self.assertEqual(console_handler.level, logging.INFO)
    
    def test_file_handler_levels(self):
        """Test file handler log levels."""
        logger = BacktestLogger(name='backtest_test', log_dir=Path(self.temp_dir))
        
        # Get file handlers
        file_handlers = [h for h in logger.logger.handlers 
                        if hasattr(h, 'baseFilename')]
        
        # Check we have handlers for different levels
        levels = {h.level for h in file_handlers}
        self.assertIn(logging.DEBUG, levels)
        self.assertIn(logging.INFO, levels)
        self.assertIn(logging.ERROR, levels)


class TestColoredFormatter(unittest.TestCase):
    """Test ColoredFormatter class."""
    
    def test_format_with_colors(self):
        """Test formatting with color codes."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        
        # Test different log levels
        test_cases = [
            (logging.DEBUG, 'DEBUG', '\033[36m'),     # Cyan
            (logging.INFO, 'INFO', '\033[32m'),       # Green
            (logging.WARNING, 'WARNING', '\033[33m'), # Yellow
            (logging.ERROR, 'ERROR', '\033[31m'),     # Red
            (logging.CRITICAL, 'CRITICAL', '\033[35m') # Magenta
        ]
        
        for level, levelname, color_code in test_cases:
            record = logging.LogRecord(
                name='test', level=level, pathname='', lineno=0,
                msg='Test message', args=(), exc_info=None
            )
            
            formatted = formatter.format(record)
            
            # Check that color code is in the output
            self.assertIn(color_code, formatted)
            self.assertIn('\033[0m', formatted)  # Reset code
            
            # Check levelname is preserved after formatting
            self.assertEqual(record.levelname, levelname)
    
    def test_format_unknown_level(self):
        """Test formatting with unknown log level."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        
        # Create custom level
        custom_level = 25  # Between INFO and WARNING
        record = logging.LogRecord(
            name='test', level=custom_level, pathname='', lineno=0,
            msg='Test message', args=(), exc_info=None
        )
        record.levelname = 'CUSTOM'
        
        formatted = formatter.format(record)
        
        # Should not have color codes for unknown level
        self.assertNotIn('\033[', formatted)


class TestStructuredLogger(unittest.TestCase):
    """Test StructuredLogger class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        logging.getLogger('backtest_structured_test').handlers.clear()
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
        logging.getLogger('backtest_structured_test').handlers.clear()
    
    def test_init_creates_jsonl_file(self):
        """Test that initialization creates JSONL file."""
        logger = StructuredLogger(name='backtest_structured_test', 
                                log_dir=Path(self.temp_dir))
        
        # Check that a .jsonl file was created
        jsonl_files = list(Path(self.temp_dir).glob('*.jsonl'))
        self.assertEqual(len(jsonl_files), 1)
    
    def test_log_trade(self):
        """Test logging trade information."""
        log_file = Path(self.temp_dir) / 'test.jsonl'
        
        # Create logger with specific file
        logger = StructuredLogger(name='backtest_structured_test', 
                                log_dir=Path(self.temp_dir))
        
        # Log a trade
        logger.log_trade(
            ticker='AAPL',
            action='BUY',
            price=150.0,
            shares=10.0,
            portfolio_value=10000.0,
            custom_field='test'
        )
        
        # Find and read the log file
        jsonl_files = list(Path(self.temp_dir).glob('*.jsonl'))
        self.assertEqual(len(jsonl_files), 1)
        
        with open(jsonl_files[0], 'r') as f:
            line = f.readline()
            data = json.loads(line)
        
        self.assertEqual(data['type'], 'trade')
        self.assertEqual(data['ticker'], 'AAPL')
        self.assertEqual(data['action'], 'BUY')
        self.assertEqual(data['price'], 150.0)
        self.assertEqual(data['shares'], 10.0)
        self.assertEqual(data['portfolio_value'], 10000.0)
        self.assertEqual(data['custom_field'], 'test')
        self.assertIn('timestamp', data)
    
    def test_log_metrics(self):
        """Test logging metrics."""
        logger = StructuredLogger(name='backtest_structured_test', 
                                log_dir=Path(self.temp_dir))
        
        metrics = {
            'sharpe_ratio': 1.5,
            'max_drawdown': 10.0,
            'total_return': 25.0
        }
        
        logger.log_metrics('MSFT', metrics)
        
        # Read the log
        jsonl_files = list(Path(self.temp_dir).glob('*.jsonl'))
        with open(jsonl_files[0], 'r') as f:
            line = f.readline()
            data = json.loads(line)
        
        self.assertEqual(data['type'], 'metrics')
        self.assertEqual(data['ticker'], 'MSFT')
        self.assertEqual(data['metrics'], metrics)
    
    def test_log_backtest_start(self):
        """Test logging backtest start."""
        logger = StructuredLogger(name='backtest_structured_test', 
                                log_dir=Path(self.temp_dir))
        
        config = {
            'ticker': 'GOOGL',
            'start_date': '2023-01-01',
            'initial_capital': 10000
        }
        
        logger.log_backtest_start(config)
        
        # Read the log
        jsonl_files = list(Path(self.temp_dir).glob('*.jsonl'))
        with open(jsonl_files[0], 'r') as f:
            line = f.readline()
            data = json.loads(line)
        
        self.assertEqual(data['type'], 'backtest_start')
        self.assertEqual(data['config'], config)
    
    def test_log_backtest_end(self):
        """Test logging backtest end."""
        logger = StructuredLogger(name='backtest_structured_test', 
                                log_dir=Path(self.temp_dir))
        
        summary = {
            'total_return': 15.0,
            'num_trades': 20,
            'final_value': 11500.0
        }
        
        logger.log_backtest_end(summary)
        
        # Read the log
        jsonl_files = list(Path(self.temp_dir).glob('*.jsonl'))
        with open(jsonl_files[0], 'r') as f:
            line = f.readline()
            data = json.loads(line)
        
        self.assertEqual(data['type'], 'backtest_end')
        self.assertEqual(data['summary'], summary)


class TestJSONFormatter(unittest.TestCase):
    """Test JSONFormatter class."""
    
    def test_format_with_json_data(self):
        """Test formatting when record has json_data."""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='', args=(), exc_info=None
        )
        record.json_data = {'key': 'value', 'number': 42}
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        self.assertEqual(data['key'], 'value')
        self.assertEqual(data['number'], 42)
    
    def test_format_without_json_data(self):
        """Test formatting standard log record."""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name='test.module', level=logging.WARNING, 
            pathname='test.py', lineno=42,
            msg='Test warning message', args=(), exc_info=None
        )
        record.funcName = 'test_function'
        record.module = 'test'
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        self.assertEqual(data['level'], 'WARNING')
        self.assertEqual(data['logger'], 'test.module')
        self.assertEqual(data['message'], 'Test warning message')
        self.assertEqual(data['module'], 'test')
        self.assertEqual(data['function'], 'test_function')
        self.assertEqual(data['line'], 42)
        self.assertIn('timestamp', data)


class TestGlobalFunctions(unittest.TestCase):
    """Test global convenience functions."""
    
    def setUp(self):
        """Reset global variables."""
        import backtest.logging_config
        backtest.logging_config._backtest_logger = None
        backtest.logging_config._structured_logger = None
    
    def test_get_logger_singleton(self):
        """Test that get_logger returns singleton."""
        logger1 = get_logger()
        logger2 = get_logger()
        
        # Should be the same logger
        self.assertIs(logger1, logger2)
    
    def test_get_logger_with_name(self):
        """Test get_logger with module name."""
        logger = get_logger('test_module')
        
        self.assertEqual(logger.name, 'backtest.test_module')
    
    def test_get_structured_logger_singleton(self):
        """Test that get_structured_logger returns singleton."""
        logger1 = get_structured_logger()
        logger2 = get_structured_logger()
        
        # Should be the same instance
        self.assertIs(logger1, logger2)
    
    def test_configure_logging(self):
        """Test configure_logging function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = configure_logging(level='DEBUG', log_dir=temp_dir)
            
            self.assertIsInstance(logger, logging.Logger)
            self.assertEqual(logging.getLogger('backtest').level, logging.DEBUG)


class TestLoggingIntegration(unittest.TestCase):
    """Integration tests for logging functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        # Clear all backtest loggers
        for name in ['backtest', 'backtest_structured', 'backtest.test']:
            logging.getLogger(name).handlers.clear()
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_logging_workflow(self):
        """Test complete logging workflow."""
        # Configure logging
        logger = configure_logging(level='DEBUG', log_dir=self.temp_dir)
        
        # Create structured logger with same log dir
        import backtest.logging_config
        backtest.logging_config._structured_logger = None  # Reset
        structured = StructuredLogger(log_dir=Path(self.temp_dir))
        
        # Log various messages
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Log structured data
        structured.log_backtest_start({'ticker': 'TEST'})
        structured.log_trade('TEST', 'BUY', 100.0, 10, 1000.0)
        structured.log_backtest_end({'total_return': 10.0})
        
        # Check that log files were created
        log_files = list(Path(self.temp_dir).glob('*'))
        self.assertGreater(len(log_files), 0)
        
        # Check for different log file types
        file_names = [f.name for f in log_files]
        self.assertTrue(any('debug' in name for name in file_names))
        self.assertTrue(any('info' in name for name in file_names))
        self.assertTrue(any('error' in name for name in file_names))
        self.assertTrue(any('structured' in name for name in file_names))


if __name__ == '__main__':
    unittest.main()