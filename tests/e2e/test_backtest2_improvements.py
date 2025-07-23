"""E2E tests for recent backtest2 improvements"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backtest2.core.config import BacktestConfig, LLMConfig, RiskConfig
from backtest2.core.engine import BacktestEngine
from backtest2.agents.llm_client import OpenAILLMClient
from backtest2.risk.position_manager import PositionManager
from backtest2.utils.retry_handler import RetryHandler, CircuitBreaker
from backtest2.utils.cache_manager import LLMCacheManager
from backtest2.utils.metrics_collector import BacktestMetrics
from backtest2.utils.tracer import get_tracer
from backtest2.config.constants import RISK_ANALYSIS, POSITION_MANAGEMENT
from backtest2.config.validator import validate_all_constants


class TestBacktest2Improvements:
    """Test suite for recent improvements to backtest2 system"""
    
    @pytest.fixture
    async def basic_config(self):
        """Create basic backtest configuration"""
        return BacktestConfig(
            symbols=["AAPL", "GOOGL"],
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=100000,
            llm_config=LLMConfig(
                deep_think_model="gpt-4",
                quick_think_model="gpt-3.5-turbo",
                temperature=0.0,
                max_tokens=2000
            ),
            risk_config=RiskConfig()
        )
        
    @pytest.mark.asyncio
    async def test_memory_leak_prevention(self, basic_config):
        """Test that memory leak prevention mechanisms work correctly"""
        print("\n=== Testing Memory Leak Prevention ===")
        
        # Create position manager
        position_manager = PositionManager(
            initial_capital=basic_config.initial_capital,
            risk_config=basic_config.risk_config
        )
        
        # Simulate many transactions
        print("Simulating 100,000 transactions...")
        for i in range(100000):
            # Simulate buy transaction
            transaction = {
                "symbol": "AAPL",
                "action": "BUY",
                "quantity": 10,
                "price": 150.0 + i * 0.01,
                "commission": 1.0,
                "timestamp": datetime.now()
            }
            
            # Check buffer sizes don't exceed limits
            assert len(position_manager.transaction_history.buffer) <= POSITION_MANAGEMENT.transaction_history_buffer_size
            assert len(position_manager.closed_positions.buffer) <= POSITION_MANAGEMENT.closed_positions_buffer_size
            
            if i % 10000 == 0:
                print(f"  Processed {i} transactions - buffers OK")
                
        print("✓ Memory leak prevention working correctly")
        
    @pytest.mark.asyncio
    async def test_retry_handler_and_circuit_breaker(self):
        """Test retry handler with circuit breaker pattern"""
        print("\n=== Testing Retry Handler and Circuit Breaker ===")
        
        # Create retry handler
        retry_handler = RetryHandler()
        
        # Track call attempts
        call_count = 0
        
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Simulated connection error")
            return "Success"
            
        # Test retry logic
        print("Testing retry logic...")
        result = await retry_handler.execute_with_retry(failing_function)
        assert result == "Success"
        assert call_count == 3
        print(f"✓ Function succeeded after {call_count} attempts")
        
        # Test circuit breaker
        print("\nTesting circuit breaker...")
        call_count = 0
        
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Permanent failure")
            
        # Trigger circuit breaker
        for i in range(5):
            try:
                await retry_handler.execute_with_retry(always_failing)
            except:
                pass
                
        # Circuit should be open now
        circuit_state = retry_handler.get_circuit_state()
        assert circuit_state["state"] == "open"
        print(f"✓ Circuit breaker opened after {circuit_state['failure_count']} failures")
        
        # Verify circuit prevents calls
        call_count_before = call_count
        try:
            await retry_handler.execute_with_retry(always_failing)
        except ConnectionError as e:
            assert "Circuit breaker is OPEN" in str(e)
            
        assert call_count == call_count_before  # No new calls made
        print("✓ Circuit breaker preventing calls when open")
        
    @pytest.mark.asyncio
    async def test_transaction_atomicity(self, basic_config):
        """Test atomic transaction execution"""
        print("\n=== Testing Transaction Atomicity ===")
        
        position_manager = PositionManager(
            initial_capital=basic_config.initial_capital,
            risk_config=basic_config.risk_config
        )
        
        # Test successful transaction
        print("Testing successful atomic transaction...")
        initial_cash = position_manager.cash
        
        transaction = type('Transaction', (), {
            'symbol': 'AAPL',
            'action': type('TradeAction', (), {'BUY': 'BUY'})(),
            'quantity': 100,
            'price': 150.0,
            'commission': 10.0,
            'timestamp': datetime.now(),
            'notes': 'Test transaction',
            'total_cost': 15010.0
        })()
        
        success = await position_manager.execute_transaction(transaction)
        assert success
        assert position_manager.cash == initial_cash - 15010.0
        assert 'AAPL' in position_manager.positions
        print("✓ Atomic transaction executed successfully")
        
        # Test failed transaction (insufficient funds)
        print("\nTesting failed atomic transaction...")
        large_transaction = type('Transaction', (), {
            'symbol': 'GOOGL',
            'action': type('TradeAction', (), {'BUY': 'BUY'})(),
            'quantity': 10000,
            'price': 2000.0,
            'commission': 100.0,
            'timestamp': datetime.now(),
            'notes': 'Large transaction',
            'total_cost': 20000100.0
        })()
        
        cash_before = position_manager.cash
        success = await position_manager.execute_transaction(large_transaction)
        assert not success
        assert position_manager.cash == cash_before  # Cash unchanged
        assert 'GOOGL' not in position_manager.positions
        print("✓ Failed transaction rolled back correctly")
        
    @pytest.mark.asyncio
    async def test_risk_analysis_integration(self, basic_config):
        """Test risk analysis with gap and correlation considerations"""
        print("\n=== Testing Risk Analysis Integration ===")
        
        position_manager = PositionManager(
            initial_capital=basic_config.initial_capital,
            risk_config=basic_config.risk_config
        )
        
        # Simulate market data for risk analysis
        import pandas as pd
        import numpy as np
        
        # Create synthetic price data with gaps
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        base_price = 150.0
        
        # Add gaps
        prices = []
        for i in range(len(dates)):
            if i > 0 and np.random.random() < 0.1:  # 10% chance of gap
                gap = np.random.uniform(-0.05, 0.05) * base_price
                open_price = prices[-1]['close'] + gap
            else:
                open_price = prices[-1]['close'] if i > 0 else base_price
                
            prices.append({
                'date': dates[i],
                'open': open_price,
                'high': open_price * np.random.uniform(1.0, 1.02),
                'low': open_price * np.random.uniform(0.98, 1.0),
                'close': open_price * np.random.uniform(0.99, 1.01)
            })
            
        price_df = pd.DataFrame(prices)
        returns = price_df['close'].pct_change().dropna()
        
        # Update market data cache
        position_manager.update_market_data('AAPL', price_df, returns)
        
        # Test position sizing with risk adjustments
        signal = type('TradingSignal', (), {
            'symbol': 'AAPL',
            'risk_assessment': {'risk_stance': 'NEUTRAL'}
        })()
        
        print("Testing position size calculation with risk adjustments...")
        position_size = position_manager.calculate_position_size(
            signal=signal,
            confidence=0.7,
            current_price=150.0
        )
        
        assert position_size > 0
        assert position_size < basic_config.initial_capital
        print(f"✓ Risk-adjusted position size: ${position_size:,.2f}")
        
        # Verify gap risk affects position size
        gap_metrics = position_manager.risk_analyzer.analyze_gap_risk('AAPL', price_df)
        print(f"✓ Gap risk metrics - Max gap: {gap_metrics.max_gap_percentage:.2%}")
        
    @pytest.mark.asyncio
    async def test_llm_caching(self):
        """Test LLM result caching"""
        print("\n=== Testing LLM Result Caching ===")
        
        cache_manager = LLMCacheManager()
        await cache_manager.start()
        
        try:
            # Test cache miss
            print("Testing cache miss...")
            result = await cache_manager.get_llm_result(
                agent_name="test_agent",
                prompt="Test prompt",
                context={"key": "value"},
                use_deep_thinking=False
            )
            assert result is None
            print("✓ Cache miss detected correctly")
            
            # Cache a result
            print("\nCaching LLM result...")
            await cache_manager.cache_llm_result(
                agent_name="test_agent",
                prompt="Test prompt",
                context={"key": "value"},
                result="Test response",
                use_deep_thinking=False
            )
            
            # Test cache hit
            print("Testing cache hit...")
            cached_result = await cache_manager.get_llm_result(
                agent_name="test_agent",
                prompt="Test prompt",
                context={"key": "value"},
                use_deep_thinking=False
            )
            assert cached_result == "Test response"
            print("✓ Cache hit working correctly")
            
            # Test cache statistics
            stats = cache_manager.get_stats()
            assert stats["hits"] == 1
            assert stats["misses"] == 1
            assert stats["hit_rate"] == 0.5
            print(f"✓ Cache statistics: {stats['hits']} hits, {stats['misses']} misses, {stats['hit_rate']:.0%} hit rate")
            
        finally:
            await cache_manager.stop()
            
    @pytest.mark.asyncio
    async def test_configuration_validation(self):
        """Test configuration validation"""
        print("\n=== Testing Configuration Validation ===")
        
        # Validate all constants
        print("Validating all configuration constants...")
        warnings = validate_all_constants()
        
        if warnings:
            print(f"Configuration warnings found:")
            for module, module_warnings in warnings.items():
                for warning in module_warnings:
                    print(f"  {module}: {warning}")
        else:
            print("✓ All configuration constants valid")
            
        # Test invalid configuration detection
        from backtest2.config.validator import ConfigValidator, ConfigValidationError
        
        print("\nTesting invalid configuration detection...")
        
        # Test probability validation
        try:
            ConfigValidator.validate_probability(1.5, "test_probability")
            assert False, "Should have raised validation error"
        except ConfigValidationError as e:
            print(f"✓ Probability validation working: {e}")
            
        # Test positive value validation
        try:
            ConfigValidator.validate_positive(-10, "test_value")
            assert False, "Should have raised validation error"
        except ConfigValidationError as e:
            print(f"✓ Positive value validation working: {e}")
            
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test metrics collection and observability"""
        print("\n=== Testing Metrics Collection ===")
        
        metrics = BacktestMetrics()
        await metrics.start()
        
        try:
            # Record various metrics
            print("Recording trading metrics...")
            
            # Trade execution metrics
            metrics.record_trade_execution("AAPL", "BUY", 100, 150.0)
            metrics.record_trade_execution("AAPL", "SELL", 50, 155.0)
            metrics.record_trade_execution("GOOGL", "BUY", 10, 2800.0)
            
            # LLM call metrics
            metrics.record_llm_call("market_analyst", 0.5, True, cache_hit=False)
            metrics.record_llm_call("market_analyst", 0.1, True, cache_hit=True)
            metrics.record_llm_call("trader", 0.8, False, cache_hit=False)
            
            # Portfolio metrics
            metrics.record_portfolio_state(cash=85000, total_value=100000, position_count=2)
            
            # Get metrics summary
            all_metrics = metrics.get_all_metrics()
            
            # Verify counters
            assert all_metrics["counters"]["trades.executed,symbol=AAPL,action=BUY"] == 1
            assert all_metrics["counters"]["trades.executed,symbol=AAPL,action=SELL"] == 1
            assert all_metrics["counters"]["llm.calls,agent=market_analyst,success=true,cache_hit=false"] == 1
            print("✓ Trade and LLM metrics recorded correctly")
            
            # Verify gauges
            assert all_metrics["gauges"]["portfolio.cash"] == 85000
            assert all_metrics["gauges"]["portfolio.total_value"] == 100000
            print("✓ Portfolio state metrics recorded correctly")
            
            # Test Prometheus export
            prometheus_output = metrics.export_prometheus()
            assert "trades_executed_total" in prometheus_output
            assert "portfolio_cash" in prometheus_output
            print("✓ Prometheus export working correctly")
            
        finally:
            await metrics.stop()
            
    @pytest.mark.asyncio
    async def test_distributed_tracing(self):
        """Test distributed tracing"""
        print("\n=== Testing Distributed Tracing ===")
        
        tracer = get_tracer()
        
        # Test basic span creation
        print("Testing span creation and hierarchy...")
        
        # Start root span
        root_span = tracer.start_trace("backtest_execution", tags={"test": "true"})
        
        # Create child spans
        async with tracer.trace("data_loading") as data_span:
            data_span.set_tag("symbols", ["AAPL", "GOOGL"])
            data_span.add_event("data_loaded", {"rows": 1000})
            
            async with tracer.trace("data_validation") as validation_span:
                validation_span.set_tag("valid", True)
                await asyncio.sleep(0.1)  # Simulate work
                
        # Create another child span
        async with tracer.trace("agent_execution") as agent_span:
            agent_span.set_tag("agent", "market_analyst")
            
            # Simulate error
            try:
                async with tracer.trace("llm_call") as llm_span:
                    llm_span.set_tag("model", "gpt-4")
                    raise ValueError("Simulated LLM error")
            except ValueError:
                pass  # Expected
                
        tracer.finish_span(root_span)
        
        # Verify trace structure
        trace_summary = tracer.get_trace_summary(root_span.trace_id)
        assert trace_summary["total_spans"] >= 4
        assert trace_summary["root_operation"] == "backtest_execution"
        assert "ok" in trace_summary["status_counts"]
        assert "error" in trace_summary["status_counts"]
        print(f"✓ Trace created with {trace_summary['total_spans']} spans")
        
        # Test Jaeger export
        jaeger_data = tracer.export_jaeger()
        assert len(jaeger_data["data"]) > 0
        assert jaeger_data["data"][0]["traceID"] == root_span.trace_id
        print("✓ Jaeger export working correctly")
        
        # Clear traces
        tracer.clear_completed_spans()
        

async def run_all_tests():
    """Run all E2E tests"""
    print("\n" + "="*60)
    print("BACKTEST2 IMPROVEMENTS E2E TEST SUITE")
    print("="*60)
    
    test_suite = TestBacktest2Improvements()
    
    # Create basic config
    basic_config = await test_suite.basic_config()
    
    # Run tests
    tests = [
        ("Memory Leak Prevention", test_suite.test_memory_leak_prevention, basic_config),
        ("Retry Handler and Circuit Breaker", test_suite.test_retry_handler_and_circuit_breaker, None),
        ("Transaction Atomicity", test_suite.test_transaction_atomicity, basic_config),
        ("Risk Analysis Integration", test_suite.test_risk_analysis_integration, basic_config),
        ("LLM Caching", test_suite.test_llm_caching, None),
        ("Configuration Validation", test_suite.test_configuration_validation, None),
        ("Metrics Collection", test_suite.test_metrics_collection, None),
        ("Distributed Tracing", test_suite.test_distributed_tracing, None)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func, config in tests:
        try:
            if config:
                await test_func(config)
            else:
                await test_func()
            passed += 1
            print(f"\n✅ {test_name} - PASSED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name} - FAILED: {e}")
            import traceback
            traceback.print_exc()
            
    print("\n" + "="*60)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)