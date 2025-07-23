"""
Unit tests for the metrics module.
"""

import unittest
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtest.metrics import (
    calculate_returns, calculate_max_drawdown, calculate_sharpe_ratio,
    calculate_sortino_ratio, analyze_trades, PerformanceMetrics,
    calculate_performance_metrics, format_metrics_report
)
from backtest.simulator import Trade, BacktestResult
from backtest.constants import MAX_SHARPE_RATIO, MAX_SORTINO_RATIO, MAX_PROFIT_FACTOR, TRADING_DAYS_PER_YEAR


class TestReturnsCalculation(unittest.TestCase):
    """Test returns calculation functions."""
    
    def test_calculate_returns_normal(self):
        """Test normal returns calculation."""
        equity_curve = [10000, 10100, 10050, 10200]
        returns = calculate_returns(equity_curve)
        
        self.assertEqual(len(returns), 3)
        self.assertAlmostEqual(returns[0], 0.01, places=4)  # 1%
        self.assertAlmostEqual(returns[1], -0.00495, places=4)  # ~-0.5%
        self.assertAlmostEqual(returns[2], 0.01493, places=4)  # ~1.5%
    
    def test_calculate_returns_empty(self):
        """Test returns with empty or short equity curve."""
        self.assertEqual(len(calculate_returns([])), 0)
        self.assertEqual(len(calculate_returns([10000])), 0)
    
    def test_calculate_returns_no_change(self):
        """Test returns with no changes."""
        equity_curve = [10000, 10000, 10000]
        returns = calculate_returns(equity_curve)
        np.testing.assert_array_almost_equal(returns, [0, 0])


class TestDrawdownCalculation(unittest.TestCase):
    """Test drawdown calculation."""
    
    def test_max_drawdown_normal(self):
        """Test normal drawdown calculation."""
        # Equity curve with 20% drawdown
        equity_curve = [10000, 11000, 12000, 10000, 9600, 10500]
        max_dd, peak_idx, trough_idx = calculate_max_drawdown(equity_curve)
        
        self.assertAlmostEqual(max_dd, 20.0, places=1)  # 20% drawdown
        self.assertEqual(peak_idx, 2)  # Peak at 12000
        self.assertEqual(trough_idx, 4)  # Trough at 9600
    
    def test_max_drawdown_no_drawdown(self):
        """Test with no drawdown (always increasing)."""
        equity_curve = [10000, 11000, 12000, 13000]
        max_dd, peak_idx, trough_idx = calculate_max_drawdown(equity_curve)
        
        self.assertEqual(max_dd, 0.0)
    
    def test_max_drawdown_empty(self):
        """Test with empty equity curve."""
        max_dd, peak_idx, trough_idx = calculate_max_drawdown([])
        self.assertEqual(max_dd, 0.0)


class TestSharpeRatio(unittest.TestCase):
    """Test Sharpe ratio calculation."""
    
    def test_sharpe_ratio_normal(self):
        """Test normal Sharpe ratio calculation."""
        # Daily returns with positive Sharpe
        returns = np.array([0.01, -0.005, 0.015, 0.002, -0.003])
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.02)
        
        self.assertGreater(sharpe, 0)  # Should be positive
        self.assertLess(sharpe, MAX_SHARPE_RATIO)  # Should be capped
    
    def test_sharpe_ratio_zero_volatility(self):
        """Test Sharpe with zero volatility."""
        returns = np.array([0.01, 0.01, 0.01])  # Constant returns
        sharpe = calculate_sharpe_ratio(returns)
        
        # Should handle division by zero
        self.assertEqual(sharpe, 0.0)
    
    def test_sharpe_ratio_capped(self):
        """Test Sharpe ratio capping."""
        # Extremely high returns
        returns = np.array([0.1] * 100)  # 10% daily
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.0)
        
        self.assertEqual(sharpe, MAX_SHARPE_RATIO)


class TestSortinoRatio(unittest.TestCase):
    """Test Sortino ratio calculation."""
    
    def test_sortino_ratio_normal(self):
        """Test normal Sortino ratio calculation."""
        # Returns with some downside
        returns = np.array([0.01, -0.005, 0.015, -0.002, 0.008])
        sortino = calculate_sortino_ratio(returns, risk_free_rate=0.02)
        
        self.assertGreater(sortino, 0)
        self.assertLess(sortino, MAX_SORTINO_RATIO)
    
    def test_sortino_ratio_no_downside(self):
        """Test Sortino with no downside risk."""
        # All positive returns
        returns = np.array([0.01, 0.02, 0.015, 0.005])
        sortino = calculate_sortino_ratio(returns, risk_free_rate=0.0)
        
        self.assertEqual(sortino, MAX_SORTINO_RATIO)
    
    def test_sortino_ratio_all_negative(self):
        """Test Sortino with all negative returns."""
        returns = np.array([-0.01, -0.02, -0.015])
        sortino = calculate_sortino_ratio(returns)
        
        self.assertLess(sortino, 0)  # Should be negative
    
    def test_sortino_ratio_zero_downside_std(self):
        """Test Sortino with returns that have zero downside standard deviation."""
        # Create returns where some are below risk-free rate but all have same downside
        risk_free_rate = 0.02
        daily_rate = risk_free_rate / TRADING_DAYS_PER_YEAR
        
        # All returns are below risk-free rate by the same amount
        # This creates non-zero downside returns but zero downside std
        below_rate = daily_rate - 0.001
        returns = np.array([below_rate, below_rate, below_rate])
        
        sortino = calculate_sortino_ratio(returns, risk_free_rate=risk_free_rate)
        
        # Should return 0.0 when downside std is zero
        self.assertEqual(sortino, 0.0)


class TestTradeAnalysis(unittest.TestCase):
    """Test trade analysis functions."""
    
    def setUp(self):
        """Set up test trades."""
        self.trades = [
            Trade(datetime(2023, 1, 1), "BUY", 100.0, 10, 1000, 0, 1000),
            Trade(datetime(2023, 1, 2), "SELL", 110.0, 0, 1100, 1100, 1100),
            Trade(datetime(2023, 1, 3), "BUY", 105.0, 10, 1100, 50, 1100),
            Trade(datetime(2023, 1, 4), "SELL", 102.0, 0, 1020, 1070, 1070),
        ]
    
    def test_analyze_trades_normal(self):
        """Test normal trade analysis."""
        analysis = analyze_trades(self.trades)
        
        self.assertEqual(analysis['total_trades'], 2)  # 2 round trips
        self.assertEqual(analysis['winning_trades'], 1)
        self.assertEqual(analysis['losing_trades'], 1)
        self.assertEqual(analysis['win_rate'], 50.0)
        self.assertGreater(analysis['avg_win'], 0)
        self.assertGreater(analysis['avg_loss'], 0)
        self.assertGreater(analysis['profit_factor'], 0)
    
    def test_analyze_trades_empty(self):
        """Test with no trades."""
        analysis = analyze_trades([])
        
        self.assertEqual(analysis['total_trades'], 0)
        self.assertEqual(analysis['win_rate'], 0.0)
        self.assertEqual(analysis['profit_factor'], 0.0)
    
    def test_analyze_trades_only_buys(self):
        """Test with only buy trades (no sells)."""
        buy_only = [
            Trade(datetime(2023, 1, 1), "BUY", 100.0, 10, 1000, 0, 1000),
            Trade(datetime(2023, 1, 2), "BUY", 110.0, 20, 0, 0, 2200),
        ]
        analysis = analyze_trades(buy_only)
        
        self.assertEqual(analysis['total_trades'], 0)  # No complete trades


class TestTradeStatistics(unittest.TestCase):
    """Test trade statistics calculation."""
    
    def test_analyze_trades_no_recent_buy_for_sell(self):
        """Test edge case where sell has no recent buy (line 189->186)."""
        trades = [
            Trade(datetime(2022, 12, 31), "SELL", 95.0, 100, 0, 9500, 9500),  # Early sell with no buy
            Trade(datetime(2023, 1, 1), "BUY", 100.0, 100, 10000, 0, 10000),
            Trade(datetime(2023, 1, 2), "SELL", 110.0, 100, 0, 11000, 11000)
        ]
        
        stats = analyze_trades(trades)
        
        # Only one valid buy-sell pair (first sell ignored)
        self.assertEqual(stats['total_trades'], 1)
        self.assertEqual(stats['winning_trades'], 1)
    
    def test_analyze_trades_sell_without_buy(self):
        """Test trade statistics with sell trade without matching buy."""
        trades = [
            Trade(datetime(2023, 1, 1), "SELL", 100.0, 0, 10000, 10000, 10000),
            Trade(datetime(2023, 1, 2), "BUY", 90.0, 100, 9000, 0, 9000),
            Trade(datetime(2023, 1, 3), "SELL", 95.0, 0, 9500, 9500, 9500)
        ]
        
        stats = analyze_trades(trades)
        
        # First sell has no matching buy, should be ignored
        self.assertEqual(stats['total_trades'], 1)
        self.assertEqual(stats['winning_trades'], 1)
        self.assertEqual(stats['losing_trades'], 0)
    
    def test_analyze_trades_multiple_sells_one_buy(self):
        """Test multiple sell orders after single buy."""
        trades = [
            Trade(datetime(2023, 1, 1), "BUY", 100.0, 200, 20000, 0, 20000),
            Trade(datetime(2023, 1, 2), "SELL", 110.0, 100, 11000, 11000, 22000),
            Trade(datetime(2023, 1, 3), "SELL", 105.0, 100, 10500, 21500, 21500)
        ]
        
        stats = analyze_trades(trades)
        
        # Both sells should match with the same buy
        self.assertEqual(stats['total_trades'], 2)
        self.assertEqual(stats['winning_trades'], 2)
        self.assertEqual(stats['losing_trades'], 0)
    
    def test_analyze_trades_complex_ordering(self):
        """Test complex buy/sell ordering."""
        trades = [
            Trade(datetime(2023, 1, 1), "BUY", 100.0, 100, 10000, 0, 10000),
            Trade(datetime(2023, 1, 2), "BUY", 95.0, 100, 9500, 0, 19000),
            Trade(datetime(2023, 1, 3), "SELL", 98.0, 200, 0, 19600, 19600),
            Trade(datetime(2023, 1, 4), "BUY", 102.0, 100, 10200, 9400, 19600),
            Trade(datetime(2023, 1, 5), "SELL", 105.0, 100, 0, 19900, 19900)
        ]
        
        stats = analyze_trades(trades)
        
        # Should have 2 complete trades
        self.assertEqual(stats['total_trades'], 2)




class TestPerformanceMetricsCalculation(unittest.TestCase):
    """Test the main performance metrics calculation function."""
    
    def setUp(self):
        """Set up test data."""
        # Create a sample BacktestResult
        from backtest.simulator import BacktestResult
        
        self.result = BacktestResult(
            initial_capital=10000.0,
            ticker="TEST",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        # Add equity curve data
        self.result.equity_curve = [
            10000, 10500, 10200, 10800, 11000,
            10500, 10300, 10700, 11200, 11500
        ]
        self.result.dates = [
            datetime(2023, 1, 1) + timedelta(days=i*30) 
            for i in range(10)
        ]
        self.result.final_portfolio_value = 11500.0
        
        # Add sample trades
        self.result.trades = [
            Trade(datetime(2023, 1, 1), "BUY", 100.0, 100, 10000, 0, 10000),
            Trade(datetime(2023, 2, 1), "SELL", 105.0, 0, 10500, 10500, 10500),
            Trade(datetime(2023, 3, 1), "BUY", 102.0, 100, 10500, 300, 10500),
            Trade(datetime(2023, 4, 1), "SELL", 108.0, 0, 10800, 11100, 11100),
        ]
    
    def test_calculate_performance_metrics_normal(self):
        """Test normal performance metrics calculation."""
        from backtest.metrics import calculate_performance_metrics
        
        metrics = calculate_performance_metrics(self.result)
        
        # Check all metrics are calculated
        self.assertIsInstance(metrics, PerformanceMetrics)
        self.assertAlmostEqual(metrics.total_return, 15.0, places=1)
        self.assertGreater(metrics.annualized_return, 0)
        self.assertGreater(metrics.max_drawdown, 0)
        self.assertIsInstance(metrics.sharpe_ratio, float)
        self.assertIsInstance(metrics.sortino_ratio, float)
        self.assertEqual(metrics.total_trades, 2)  # 2 complete buy-sell pairs
        self.assertEqual(metrics.win_rate, 100.0)  # Both trades profitable
        self.assertGreater(metrics.volatility, 0)
    
    def test_calculate_performance_metrics_with_losses(self):
        """Test metrics calculation with losing trades."""
        # Modify to include losses
        self.result.equity_curve = [10000, 9500, 9800, 9200, 9700, 10200]
        self.result.dates = [
            datetime(2023, 1, 1) + timedelta(days=i*60)
            for i in range(6)
        ]
        self.result.final_portfolio_value = 10200.0
        
        self.result.trades = [
            Trade(datetime(2023, 1, 1), "BUY", 100.0, 100, 10000, 0, 10000),
            Trade(datetime(2023, 3, 1), "SELL", 95.0, 0, 9500, 9500, 9500),  # Loss
            Trade(datetime(2023, 5, 1), "BUY", 92.0, 103, 9500, 0, 9476),
            Trade(datetime(2023, 7, 1), "SELL", 99.0, 0, 10197, 10197, 10197),  # Gain
        ]
        
        from backtest.metrics import calculate_performance_metrics
        metrics = calculate_performance_metrics(self.result)
        
        self.assertEqual(metrics.total_return, 2.0)  # 2% total return
        self.assertLess(metrics.win_rate, 100.0)
        self.assertGreater(metrics.max_drawdown, 0)
        self.assertEqual(metrics.winning_trades, 1)
        self.assertEqual(metrics.losing_trades, 1)
    
    def test_calculate_performance_metrics_empty_data(self):
        """Test metrics calculation with minimal data."""
        # Empty result
        empty_result = BacktestResult(
            initial_capital=10000.0,
            ticker="TEST",
            start_date="2023-01-01",
            end_date="2023-01-01"
        )
        empty_result.final_portfolio_value = 10000.0
        empty_result.equity_curve = [10000.0]
        empty_result.dates = [datetime(2023, 1, 1)]
        empty_result.trades = []
        
        from backtest.metrics import calculate_performance_metrics
        metrics = calculate_performance_metrics(empty_result)
        
        self.assertEqual(metrics.total_return, 0.0)
        self.assertEqual(metrics.annualized_return, 0.0)
        self.assertEqual(metrics.total_trades, 0)
        self.assertEqual(metrics.volatility, 0.0)


class TestMetricsFormatting(unittest.TestCase):
    """Test metrics report formatting."""
    
    def test_format_metrics_report(self):
        """Test formatting of metrics report."""
        from backtest.metrics import format_metrics_report
        
        metrics = PerformanceMetrics(
            total_return=25.5,
            annualized_return=12.3,
            max_drawdown=8.7,
            sharpe_ratio=1.45,
            sortino_ratio=2.10,
            win_rate=65.0,
            total_trades=20,
            winning_trades=13,
            losing_trades=7,
            avg_win=3.2,
            avg_loss=1.8,
            profit_factor=2.5,
            calmar_ratio=1.41,
            volatility=18.5
        )
        
        report = format_metrics_report(metrics, "AAPL")
        
        # Check report contains key information
        self.assertIn("AAPL", report)
        self.assertIn("25.50%", report)  # Total return
        self.assertIn("12.30%", report)  # Annualized return
        self.assertIn("8.70%", report)   # Max drawdown
        self.assertIn("1.45", report)    # Sharpe ratio
        self.assertIn("65.00%", report)  # Win rate
        self.assertIn("20", report)      # Total trades
        
        # Check formatting structure
        self.assertIn("Performance Report", report)
        self.assertIn("Returns:", report)
        self.assertIn("Risk Metrics:", report)
        self.assertIn("Trading Statistics:", report)
    
    def test_format_metrics_report_no_ticker(self):
        """Test formatting without ticker name."""
        from backtest.metrics import format_metrics_report
        
        metrics = PerformanceMetrics(
            total_return=10.0,
            annualized_return=10.0,
            max_drawdown=5.0,
            sharpe_ratio=1.0,
            sortino_ratio=1.5,
            win_rate=50.0,
            total_trades=10,
            winning_trades=5,
            losing_trades=5,
            avg_win=2.0,
            avg_loss=2.0,
            profit_factor=1.0,
            calmar_ratio=2.0,
            volatility=15.0
        )
        
        report = format_metrics_report(metrics)
        
        self.assertIn("Performance Report", report)
        # Check that ticker is not mentioned (no "for" in header line)
        header_line = report.strip().split('\n')[0]
        self.assertEqual(header_line, "Performance Report")


if __name__ == '__main__':
    unittest.main()