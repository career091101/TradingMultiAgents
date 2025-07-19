"""
Enhanced logging configuration for the backtesting module.

Provides structured logging with file rotation, formatting, and filtering.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

from .path_utils import get_project_paths


class BacktestLogger:
    """Enhanced logger for backtesting with structured logging support."""
    
    # Log format templates
    SIMPLE_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DETAILED_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    JSON_FORMAT = '%(json_message)s'
    
    def __init__(self, name: str = 'backtest', log_dir: Optional[Path] = None):
        """
        Initialize the backtest logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files (uses default if None)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        
        # Set log directory
        if log_dir is None:
            paths = get_project_paths()
            self.log_dir = paths['logs_dir']
        else:
            self.log_dir = Path(log_dir)
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure the logger
        self._configure_logger()
    
    def _configure_logger(self):
        """Configure the logger with handlers and formatters."""
        # Don't add handlers if already configured
        if self.logger.handlers:
            return
        
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = self._create_console_handler()
        self.logger.addHandler(console_handler)
        
        # File handlers
        info_handler = self._create_file_handler('info')
        error_handler = self._create_file_handler('error')
        debug_handler = self._create_file_handler('debug')
        
        self.logger.addHandler(info_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(debug_handler)
    
    def _create_console_handler(self) -> logging.StreamHandler:
        """Create console handler with colored output."""
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # Simple format for console
        formatter = ColoredFormatter(self.SIMPLE_FORMAT)
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_file_handler(self, level: str) -> logging.handlers.RotatingFileHandler:
        """
        Create rotating file handler for specific log level.
        
        Args:
            level: Log level ('debug', 'info', 'error')
            
        Returns:
            Configured file handler
        """
        # File paths
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = self.log_dir / f'backtest_{level}_{timestamp}.log'
        
        # Create rotating file handler (10MB max, keep 5 backups)
        handler = logging.handlers.RotatingFileHandler(
            filename,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        
        # Set level
        if level == 'debug':
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(self.DETAILED_FORMAT)
        elif level == 'error':
            handler.setLevel(logging.ERROR)
            formatter = logging.Formatter(self.DETAILED_FORMAT)
        else:  # info
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(self.SIMPLE_FORMAT)
        
        handler.setFormatter(formatter)
        return handler
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for console."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        """Format the log record with colors."""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Format the message
        formatted = super().format(record)
        
        # Reset levelname for file handlers
        record.levelname = levelname
        
        return formatted


class StructuredLogger:
    """Logger that outputs structured JSON logs for analysis."""
    
    def __init__(self, name: str = 'backtest_structured', log_dir: Optional[Path] = None):
        """Initialize structured logger."""
        self.name = name
        self.logger = logging.getLogger(name)
        
        if log_dir is None:
            paths = get_project_paths()
            self.log_dir = paths['logs_dir']
        else:
            self.log_dir = Path(log_dir)
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._configure_logger()
    
    def _configure_logger(self):
        """Configure logger for JSON output."""
        if self.logger.handlers:
            return
        
        self.logger.setLevel(logging.DEBUG)
        
        # JSON file handler
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.log_dir / f'backtest_structured_{timestamp}.jsonl'
        
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(JSONFormatter())
        
        self.logger.addHandler(handler)
    
    def log_trade(self, ticker: str, action: str, price: float, 
                  shares: float, portfolio_value: float, **kwargs):
        """Log a trade with structured data."""
        data = {
            'type': 'trade',
            'ticker': ticker,
            'action': action,
            'price': price,
            'shares': shares,
            'portfolio_value': portfolio_value,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        self.logger.info('', extra={'json_data': data})
    
    def log_metrics(self, ticker: str, metrics: Dict[str, Any]):
        """Log performance metrics."""
        data = {
            'type': 'metrics',
            'ticker': ticker,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        self.logger.info('', extra={'json_data': data})
    
    def log_backtest_start(self, config: Dict[str, Any]):
        """Log backtest start with configuration."""
        data = {
            'type': 'backtest_start',
            'config': config,
            'timestamp': datetime.now().isoformat()
        }
        self.logger.info('', extra={'json_data': data})
    
    def log_backtest_end(self, summary: Dict[str, Any]):
        """Log backtest completion with summary."""
        data = {
            'type': 'backtest_end',
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
        self.logger.info('', extra={'json_data': data})


class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""
    
    def format(self, record):
        """Format record as JSON line."""
        if hasattr(record, 'json_data'):
            # Use provided JSON data
            data = record.json_data
        else:
            # Create JSON from standard log record
            data = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
        
        return json.dumps(data, default=str)


# Global logger instances
_backtest_logger = None
_structured_logger = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger for backtesting.
    
    Args:
        name: Optional logger name (uses module name if provided)
        
    Returns:
        Configured logger instance
    """
    global _backtest_logger
    
    if _backtest_logger is None:
        _backtest_logger = BacktestLogger()
    
    if name:
        # Return child logger
        return logging.getLogger(f'backtest.{name}')
    
    return _backtest_logger.get_logger()


def get_structured_logger() -> StructuredLogger:
    """
    Get the structured logger for analysis.
    
    Returns:
        StructuredLogger instance
    """
    global _structured_logger
    
    if _structured_logger is None:
        _structured_logger = StructuredLogger()
    
    return _structured_logger


# Configure logging on import
def configure_logging(level: str = 'INFO', log_dir: Optional[str] = None):
    """
    Configure logging for the backtest module.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Optional log directory
    """
    # Create loggers
    backtest_logger = BacktestLogger(log_dir=Path(log_dir) if log_dir else None)
    
    # Set root logger level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger('backtest').setLevel(numeric_level)
    
    # Return logger for convenience
    return backtest_logger.get_logger()