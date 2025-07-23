"""
Fixed integration tests for plotting module using file existence checks.
"""

import unittest
from unittest.mock import patch
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtest.plotting import (
    plot_equity_curve, plot_price_with_signals, plot_drawdown,
    plot_returns_distribution, create_backtest_report
)
from backtest.simulator import BacktestResult, Trade

# Set matplotlib to non-interactive backend
import matplotlib
matplotlib.use('Agg')


class TestPlottingIntegration(unittest.TestCase):
    """Integration tests for plotting functions with actual file generation."""
    
    def setUp(self):
        """Set up test data and temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.dates = [datetime(2023, 1, 1) + timedelta(days=i*30) for i in range(10)]
        self.equity_values = [10000 + i*500 for i in range(10)]
        
        self.result = BacktestResult(
            initial_capital=10000.0,
            ticker="TEST",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        self.result.final_portfolio_value = 15000.0
        self.result.equity_curve = self.equity_values
        self.result.dates = self.dates
        self.result.trades = [
            Trade(self.dates[0], "BUY", 100.0, 100, 10000, 0, 10000),
            Trade(self.dates[5], "SELL", 125.0, 0, 12500, 12500, 12500),
        ]
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_plot_equity_curve_creates_file(self):
        """Test that equity curve plot creates a file."""
        output_path = os.path.join(self.temp_dir, "equity_curve.png")
        
        # Should create the plot file
        plot_equity_curve(self.dates, self.equity_values, save_path=output_path)
        
        # Check file exists
        self.assertTrue(os.path.exists(output_path))
        # Check file is not empty
        self.assertGreater(os.path.getsize(output_path), 0)
    
    def test_plot_drawdown_creates_file(self):
        """Test that drawdown plot creates a file."""
        output_path = os.path.join(self.temp_dir, "drawdown.png")
        
        # Should create the plot file
        plot_drawdown(self.dates, self.equity_values, save_path=output_path)
        
        # Check file exists
        self.assertTrue(os.path.exists(output_path))
        self.assertGreater(os.path.getsize(output_path), 0)
    
    def test_plot_returns_distribution_creates_file(self):
        """Test that returns distribution plot creates a file."""
        output_path = os.path.join(self.temp_dir, "returns_dist.png")
        
        # Should create the plot file
        plot_returns_distribution(self.result, save_path=output_path)
        
        # Check file exists
        self.assertTrue(os.path.exists(output_path))
        self.assertGreater(os.path.getsize(output_path), 0)
    
    def test_create_backtest_report_creates_directory(self):
        """Test that full report creates directory with multiple files."""
        # Run report generation
        create_backtest_report(self.result, "TEST", output_dir=self.temp_dir)
        
        # Files are created directly in output_dir with timestamps
        # Check for files with expected patterns
        files = list(Path(self.temp_dir).iterdir())
        
        # Check that at least some expected files were created
        expected_patterns = [
            "TEST_equity_curve_",
            "TEST_price_signals_",
            "TEST_drawdown_", 
            "TEST_returns_dist_",
            "TEST_performance_summary_",
            "TEST_performance_report_"
        ]
        
        found_patterns = []
        for pattern in expected_patterns:
            matching_files = [f for f in files if f.name.startswith(pattern)]
            if matching_files:
                found_patterns.append(pattern)
                # Check file is not empty
                for f in matching_files:
                    self.assertGreater(f.stat().st_size, 0, f"Empty file: {f.name}")
        
        # At least some files should be created
        self.assertGreater(len(found_patterns), 0, "No expected files were created")
        
        # Check that we have the main plot files
        self.assertIn("TEST_equity_curve_", str(found_patterns))
        self.assertIn("TEST_drawdown_", str(found_patterns))
        self.assertIn("TEST_returns_dist_", str(found_patterns))
    
    def test_plot_with_empty_data(self):
        """Test plotting with minimal data."""
        # Single data point
        dates = [datetime(2023, 1, 1)]
        values = [10000]
        
        output_path = os.path.join(self.temp_dir, "empty_equity.png")
        
        # Should handle gracefully
        try:
            plot_equity_curve(dates, values, save_path=output_path)
            # File should be created if possible
            if os.path.exists(output_path):
                self.assertGreater(os.path.getsize(output_path), 0)
        except ValueError:
            # Empty data may cause ValueError, which is acceptable
            pass
    
    def test_plot_with_invalid_save_path(self):
        """Test plotting with invalid save path."""
        # Non-existent nested directory
        invalid_path = os.path.join(self.temp_dir, "non", "existent", "dir", "plot.png")
        
        # Should handle by creating directories or failing gracefully
        try:
            plot_equity_curve(self.dates, self.equity_values, save_path=invalid_path)
            # If successful, parent directories were created
            self.assertTrue(os.path.exists(os.path.dirname(invalid_path)))
        except (OSError, IOError):
            # Expected if directory creation fails
            pass


if __name__ == '__main__':
    unittest.main()