"""
Unit tests for the metrics module.
"""

import unittest
import numpy as np
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtest.metrics import (
    calculate_returns, calculate_max_drawdown, calculate_sharpe_ratio,
    calculate_sortino_ratio, analyze_trades, PerformanceMetrics
)
from backtest.simulator import Trade, BacktestResult
from backtest.constants import MAX_SHARPE_RATIO, MAX_SORTINO_RATIO, MAX_PROFIT_FACTOR


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


if __name__ == '__main__':
    unittest.main()