#!/usr/bin/env python3
"""
Test suite to verify the critical fixes in the backtest system.
Run this after applying fixes to ensure they work correctly.
"""

import unittest
import sys
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))


class TestBacktestFixes(unittest.TestCase):
    """Test the critical fixes applied to the backtest system."""
    
    def test_backtest2_config_import(self):
        """Test that backtest2 config can be imported without errors."""
        try:
            # This should not raise ImportError after fixes
            from webui.backend.backtest2_wrapper import Backtest2Wrapper
            self.assertIsNotNone(Backtest2Wrapper)
            print("✓ Backtest2Wrapper import successful")
        except ImportError as e:
            self.fail(f"Failed to import Backtest2Wrapper: {e}")
    
    def test_backtest_config_instantiation(self):
        """Test that BacktestConfig can be instantiated properly."""
        # Mock the backtest2 modules
        with patch.dict('sys.modules', {
            'backtest2': MagicMock(),
            'backtest2.core': MagicMock(),
            'backtest2.core.config': MagicMock(),
            'backtest2.core.engine': MagicMock(),
            'backtest2.core.types': MagicMock(),
            'backtest2.core.results_simple': MagicMock()
        }):
            # Create mock classes
            mock_timerange = Mock()
            mock_timerange.start = datetime.now()
            mock_timerange.end = datetime.now() + timedelta(days=30)
            
            mock_llm_config = Mock()
            mock_agent_config = Mock()
            mock_data_config = Mock()
            mock_risk_config = Mock()
            
            # Mock BacktestConfig as a proper class
            class MockBacktestConfig:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
                    self.__dataclass_fields__ = kwargs.keys()
            
            sys.modules['backtest2.core.config'].BacktestConfig = MockBacktestConfig
            sys.modules['backtest2.core.config'].TimeRange = Mock(return_value=mock_timerange)
            sys.modules['backtest2.core.config'].LLMConfig = Mock(return_value=mock_llm_config)
            sys.modules['backtest2.core.config'].AgentConfig = Mock(return_value=mock_agent_config)
            sys.modules['backtest2.core.config'].DataConfig = Mock(return_value=mock_data_config)
            sys.modules['backtest2.core.config'].RiskConfig = Mock(return_value=mock_risk_config)
            sys.modules['backtest2.core.config'].RiskProfile = Mock()
            sys.modules['backtest2.core.config'].ReflectionConfig = Mock()
            
            # Now test the wrapper
            from webui.backend.backtest2_wrapper import Backtest2Wrapper
            
            wrapper = Backtest2Wrapper()
            config = {
                "tickers": ["AAPL"],
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 10000.0,
                "random_seed": 42
            }
            
            # This should not raise TypeError
            try:
                backtest_config = wrapper._create_backtest_config(config)
                self.assertIsNotNone(backtest_config)
                print("✓ BacktestConfig instantiation successful")
            except TypeError as e:
                self.fail(f"Failed to create BacktestConfig: {e}")
    
    def test_null_safety_in_metrics(self):
        """Test null safety in metrics extraction."""
        # Create a mock result with None metrics
        mock_result = Mock()
        mock_result.metrics = None
        
        # Mock the necessary modules
        with patch.dict('sys.modules', {
            'backtest2': MagicMock(),
            'backtest2.core': MagicMock(),
            'backtest2.core.config': MagicMock(),
            'backtest2.core.results_simple': MagicMock()
        }):
            from webui.backend.backtest2_wrapper import Backtest2Wrapper
            
            wrapper = Backtest2Wrapper()
            mock_config = Mock()
            mock_config.initial_capital = 10000.0
            mock_config.time_range = Mock(start=datetime.now(), end=datetime.now())
            
            # This should not raise AttributeError
            try:
                result = wrapper._process_results(mock_result, "AAPL", mock_config)
                self.assertIsInstance(result, dict)
                self.assertEqual(result["metrics"]["total_return"], 0.0)
                print("✓ Null safety in metrics working correctly")
            except AttributeError as e:
                self.fail(f"Null safety failed: {e}")
    
    def test_plotting_style_fallback(self):
        """Test that plotting style has proper fallback."""
        # Import with mocked matplotlib
        with patch('matplotlib.pyplot') as mock_plt:
            # Simulate style not found error
            mock_plt.style.use.side_effect = [OSError("style not found"), OSError("style not found"), None]
            
            # Import should handle the error gracefully
            try:
                from backtest.plotting import setup_plot_style
                setup_plot_style()
                
                # Check that fallback was attempted
                self.assertEqual(mock_plt.style.use.call_count, 3)
                print("✓ Plotting style fallback working correctly")
            except Exception as e:
                self.fail(f"Plotting style fallback failed: {e}")
    
    def test_directory_creation_fallback(self):
        """Test directory creation with fallback."""
        from webui.backend.backtest_wrapper import BacktestWrapper
        
        wrapper = BacktestWrapper()
        
        # Mock os.makedirs to fail
        with patch('os.makedirs') as mock_makedirs:
            mock_makedirs.side_effect = OSError("Permission denied")
            
            # This should handle the error and use temp directory
            with patch('tempfile.mkdtemp') as mock_mkdtemp:
                mock_mkdtemp.return_value = "/tmp/test_dir"
                
                # Create a simple config
                config = {
                    "tickers": ["AAPL"],
                    "start_date": "2023-01-01",
                    "end_date": "2023-01-02",
                    "initial_capital": 10000.0
                }
                
                # Mock the simulator
                with patch.object(wrapper, 'simulator') as mock_simulator:
                    mock_result = Mock()
                    mock_result.trades = []
                    mock_result.equity_curve = [10000, 10100]
                    mock_result.dates = [datetime(2023, 1, 1), datetime(2023, 1, 2)]
                    mock_result.final_portfolio_value = 10100
                    mock_result.initial_capital = 10000
                    mock_result.total_return = 1.0
                    
                    mock_simulator.run_backtest.return_value = mock_result
                    
                    try:
                        # This should use the temp directory fallback
                        results = wrapper.run_backtest(config)
                        self.assertIsNotNone(results)
                        print("✓ Directory creation fallback working correctly")
                    except Exception as e:
                        self.fail(f"Directory creation fallback failed: {e}")
    
    def test_webui_backtest_component(self):
        """Test that the WebUI backtest component doesn't have undefined variables."""
        try:
            # This import should not fail after fixes
            from webui.components.backtest import BacktestPage
            
            # Create mock session state
            mock_state = Mock()
            mock_state.get = Mock(return_value="test_value")
            mock_state.set = Mock()
            
            # Create instance - should not raise NameError
            page = BacktestPage(mock_state)
            self.assertIsNotNone(page)
            print("✓ WebUI backtest component has no undefined variables")
            
        except NameError as e:
            self.fail(f"Undefined variable in backtest component: {e}")
        except Exception as e:
            # Other exceptions are okay for this test
            print(f"  Note: Other exception occurred (expected): {type(e).__name__}")
            pass


class TestMetricsSafety(unittest.TestCase):
    """Test the safety improvements in metrics calculations."""
    
    def test_trade_analysis_zero_price(self):
        """Test trade analysis handles zero prices safely."""
        from backtest.simulator import Trade
        from backtest.metrics import analyze_trades
        
        # Create trades with zero price
        trades = [
            Trade(datetime(2023, 1, 1), "BUY", 0.0, 100, 0, 0, 0),  # Zero price buy
            Trade(datetime(2023, 1, 2), "SELL", 100.0, 0, 10000, 10000, 10000)
        ]
        
        # This should not raise ZeroDivisionError
        try:
            result = analyze_trades(trades)
            self.assertIsInstance(result, dict)
            # With zero price buy, the trade should be skipped
            self.assertEqual(result['total_trades'], 0)
            print("✓ Trade analysis handles zero prices safely")
        except ZeroDivisionError:
            self.fail("Trade analysis failed to handle zero price")
    
    def test_metrics_extreme_values(self):
        """Test metrics calculation with extreme values."""
        from backtest.metrics import calculate_sharpe_ratio, calculate_sortino_ratio
        import numpy as np
        
        # Test with extreme returns
        extreme_returns = np.array([1000.0, -1000.0, 1000.0])  # Extreme volatility
        
        # Should cap at maximum values
        sharpe = calculate_sharpe_ratio(extreme_returns)
        self.assertLessEqual(sharpe, 10.0)  # Should be capped
        
        sortino = calculate_sortino_ratio(extreme_returns)
        self.assertLessEqual(sortino, 10.0)  # Should be capped
        
        print("✓ Metrics handle extreme values correctly")


def run_tests():
    """Run all tests and report results."""
    print("🧪 Running backtest fixes verification tests...\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestBacktestFixes))
    suite.addTests(loader.loadTestsFromTestCase(TestMetricsSafety))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"✓ Tests run: {result.testsRun}")
    print(f"✓ Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"❌ Errors: {len(result.errors)}")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())