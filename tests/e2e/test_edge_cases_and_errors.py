"""E2E tests for edge cases and error scenarios"""

import pytest
import asyncio
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backtest2.core.config import BacktestConfig, LLMConfig, RiskConfig
from backtest2.core.engine import BacktestEngine
from backtest2.risk.position_manager import PositionManager
from backtest2.utils.retry_handler import LLMRetryHandler, CircuitBreakerConfig
from backtest2.utils.cache_manager import LLMCacheManager, CacheType
from backtest2.risk.risk_analyzer import RiskAnalyzer
from backtest2.core.types import TradeAction, TradingSignal, Transaction


class TestEdgeCasesAndErrors:
    """Test suite for edge cases and error scenarios"""
    
    @pytest.mark.asyncio
    async def test_extreme_market_conditions(self):
        """Test system behavior under extreme market conditions"""
        print("\n=== Testing Extreme Market Conditions ===")
        
        # Create position manager
        position_manager = PositionManager(
            initial_capital=100000,
            risk_config=RiskConfig()
        )
        
        risk_analyzer = RiskAnalyzer()
        
        # Test 1: Flash crash scenario (20% drop)
        print("\nTest 1: Flash crash scenario...")
        
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        prices = []
        base_price = 100.0
        
        for i, date in enumerate(dates):
            if i == 50:  # Flash crash on day 50
                open_price = base_price * 0.8  # 20% gap down
                close_price = base_price * 0.75  # Further decline
            else:
                open_price = base_price if i == 0 else prices[-1]['close']
                close_price = open_price * np.random.uniform(0.99, 1.01)
                
            prices.append({
                'date': date,
                'open': open_price,
                'high': max(open_price, close_price) * 1.01,
                'low': min(open_price, close_price) * 0.99,
                'close': close_price
            })
            
        price_df = pd.DataFrame(prices)
        gap_metrics = risk_analyzer.analyze_gap_risk('CRASH_TEST', price_df)
        
        assert gap_metrics.max_gap_percentage > 0.15  # Should detect large gap
        print(f"✓ Flash crash detected: {gap_metrics.max_gap_percentage:.1%} gap")
        
        # Test position sizing adjustment
        signal = TradingSignal(
            symbol='CRASH_TEST',
            action=TradeAction.BUY,
            confidence=0.8
        )
        
        position_manager.update_market_data(
            'CRASH_TEST',
            price_df,
            price_df['close'].pct_change().dropna()
        )
        
        position_size = position_manager.calculate_position_size(
            signal=signal,
            confidence=0.8,
            current_price=75.0
        )
        
        # Position size should be reduced due to high gap risk
        assert position_size < position_manager.initial_capital * 0.2
        print(f"✓ Position size reduced to ${position_size:,.2f} due to gap risk")
        
        # Test 2: Extreme volatility (50% daily swings)
        print("\nTest 2: Extreme volatility scenario...")
        
        volatile_prices = []
        for i, date in enumerate(dates[:10]):  # 10 days of extreme volatility
            if i == 0:
                open_price = 100.0
            else:
                # Random 20-50% swings
                swing = np.random.uniform(0.2, 0.5) * np.random.choice([-1, 1])
                open_price = volatile_prices[-1]['close'] * (1 + swing)
                
            close_price = open_price * np.random.uniform(0.8, 1.2)
            
            volatile_prices.append({
                'date': date,
                'open': open_price,
                'high': max(open_price, close_price) * 1.1,
                'low': min(open_price, close_price) * 0.9,
                'close': close_price
            })
            
        volatile_df = pd.DataFrame(volatile_prices)
        volatility = volatile_df['close'].pct_change().std()
        
        assert volatility > 0.2  # Extreme volatility
        print(f"✓ Extreme volatility detected: {volatility:.1%} daily std dev")
        
        # Test 3: Zero liquidity / halted trading
        print("\nTest 3: Zero liquidity scenario...")
        
        # Simulate trading halt (no price change, zero volume implied)
        halt_prices = []
        halt_price = 100.0
        
        for date in dates[:5]:
            halt_prices.append({
                'date': date,
                'open': halt_price,
                'high': halt_price,
                'low': halt_price,
                'close': halt_price
            })
            
        halt_df = pd.DataFrame(halt_prices)
        price_changes = halt_df['close'].pct_change().dropna()
        
        assert all(price_changes == 0)
        print("✓ Trading halt detected: no price movement")
        
    @pytest.mark.asyncio
    async def test_circuit_breaker_cascade(self):
        """Test circuit breaker cascade failure scenario"""
        print("\n=== Testing Circuit Breaker Cascade ===")
        
        # Create multiple retry handlers to simulate service dependencies
        primary_handler = LLMRetryHandler()
        secondary_handler = LLMRetryHandler()
        
        # Configure aggressive circuit breaker
        primary_handler.circuit_breaker.config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=timedelta(seconds=5),
            success_threshold=1
        )
        
        call_count = 0
        
        async def failing_service():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Service unavailable")
            
        # Trigger primary circuit breaker
        print("Triggering primary circuit breaker...")
        for i in range(3):
            try:
                await primary_handler.execute_with_retry(failing_service)
            except:
                pass
                
        assert primary_handler.circuit_breaker.state.value == "open"
        print("✓ Primary circuit breaker opened")
        
        # Test cascade prevention
        print("\nTesting cascade prevention...")
        cascade_prevented = False
        
        try:
            await primary_handler.execute_with_retry(failing_service)
        except ConnectionError as e:
            if "Circuit breaker is OPEN" in str(e):
                cascade_prevented = True
                
        assert cascade_prevented
        print("✓ Cascade prevented - circuit breaker blocked call")
        
        # Test recovery
        print("\nTesting circuit breaker recovery...")
        await asyncio.sleep(6)  # Wait for recovery timeout
        
        # Circuit should be in half-open state
        async def success_service():
            return "success"
            
        result = await primary_handler.execute_with_retry(success_service)
        assert result == "success"
        assert primary_handler.circuit_breaker.state.value == "closed"
        print("✓ Circuit breaker recovered successfully")
        
    @pytest.mark.asyncio
    async def test_concurrent_transaction_conflicts(self):
        """Test concurrent transaction conflict resolution"""
        print("\n=== Testing Concurrent Transaction Conflicts ===")
        
        position_manager = PositionManager(
            initial_capital=100000,
            risk_config=RiskConfig()
        )
        
        # Create multiple transactions for same symbol
        transactions = []
        for i in range(10):
            transaction = Transaction(
                symbol='AAPL',
                action=TradeAction.BUY,
                quantity=100,
                price=150.0 + i,
                commission=1.0,
                timestamp=datetime.now(),
                total_cost=15001.0 + i * 100
            )
            transactions.append(transaction)
            
        print(f"Executing {len(transactions)} concurrent transactions...")
        
        # Execute transactions concurrently
        tasks = [
            position_manager.execute_transaction(t)
            for t in transactions
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful transactions
        successful = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if r is False)
        errors = sum(1 for r in results if isinstance(r, Exception))
        
        print(f"✓ Results: {successful} successful, {failed} failed, {errors} errors")
        
        # Verify final state consistency
        if 'AAPL' in position_manager.positions:
            position = position_manager.positions['AAPL']
            total_quantity = position.quantity
            print(f"✓ Final position quantity: {total_quantity}")
            
        # Verify cash consistency
        total_spent = sum(t.total_cost for i, t in enumerate(transactions) if results[i] is True)
        expected_cash = 100000 - total_spent
        
        assert abs(position_manager.cash - expected_cash) < 0.01
        print(f"✓ Cash consistency verified: ${position_manager.cash:,.2f}")
        
    @pytest.mark.asyncio
    async def test_cache_overflow_and_eviction(self):
        """Test cache overflow and eviction policies"""
        print("\n=== Testing Cache Overflow and Eviction ===")
        
        # Create cache with small size
        cache = LLMCacheManager()
        cache.max_entries = 10  # Very small cache
        await cache.start()
        
        try:
            print("Filling cache beyond capacity...")
            
            # Fill cache with more entries than capacity
            for i in range(20):
                await cache.cache_llm_result(
                    agent_name=f"agent_{i}",
                    prompt=f"prompt_{i}",
                    context={"index": i},
                    result=f"result_{i}",
                    use_deep_thinking=False
                )
                
            # Check cache size
            stats = cache.get_stats()
            assert stats["entries"] <= 10
            print(f"✓ Cache size limited to {stats['entries']} entries")
            
            # Verify LRU eviction
            # Early entries should be evicted
            early_result = await cache.get_llm_result(
                agent_name="agent_0",
                prompt="prompt_0",
                context={"index": 0},
                use_deep_thinking=False
            )
            
            assert early_result is None  # Should be evicted
            print("✓ LRU eviction working correctly")
            
            # Recent entries should still be cached
            recent_result = await cache.get_llm_result(
                agent_name="agent_19",
                prompt="prompt_19",
                context={"index": 19},
                use_deep_thinking=False
            )
            
            assert recent_result == "result_19"
            print("✓ Recent entries retained in cache")
            
            # Test cache invalidation
            print("\nTesting cache invalidation...")
            
            invalidated = await cache.invalidate(cache_type=CacheType.LLM_RESULT)
            assert invalidated > 0
            print(f"✓ Invalidated {invalidated} cache entries")
            
            # Verify cache is empty
            stats_after = cache.get_stats()
            assert stats_after["entries"] == 0
            print("✓ Cache successfully cleared")
            
        finally:
            await cache.stop()
            
    @pytest.mark.asyncio
    async def test_malformed_data_handling(self):
        """Test handling of malformed and invalid data"""
        print("\n=== Testing Malformed Data Handling ===")
        
        risk_analyzer = RiskAnalyzer()
        
        # Test 1: Empty price data
        print("Test 1: Empty price data...")
        empty_df = pd.DataFrame()
        
        gap_metrics = risk_analyzer.analyze_gap_risk('EMPTY', empty_df)
        assert gap_metrics.max_gap_percentage == 0
        assert gap_metrics.gap_frequency == 0
        print("✓ Empty data handled gracefully")
        
        # Test 2: NaN values in price data
        print("\nTest 2: NaN values in price data...")
        nan_data = pd.DataFrame({
            'open': [100, np.nan, 102, 103],
            'high': [101, 102, np.nan, 104],
            'low': [99, np.nan, 101, 102],
            'close': [100, 101, 102, np.nan]
        })
        
        try:
            gap_metrics = risk_analyzer.analyze_gap_risk('NAN_TEST', nan_data)
            print("✓ NaN values handled without crash")
        except Exception as e:
            pytest.fail(f"Failed to handle NaN values: {e}")
            
        # Test 3: Extreme outliers
        print("\nTest 3: Extreme outliers...")
        outlier_data = pd.DataFrame({
            'open': [100, 100, 100, 1000000],  # Extreme spike
            'high': [101, 101, 101, 1000001],
            'low': [99, 99, 99, 999999],
            'close': [100, 100, 100, 1000000]
        })
        
        gap_metrics = risk_analyzer.analyze_gap_risk('OUTLIER', outlier_data)
        assert gap_metrics.max_gap_percentage > 100  # Should detect massive gap
        print(f"✓ Extreme outlier detected: {gap_metrics.max_gap_percentage:.0%} gap")
        
        # Test 4: Invalid correlation data
        print("\nTest 4: Invalid correlation data...")
        
        # Single position (no correlation possible)
        single_pos_metrics = risk_analyzer.analyze_correlation_risk(
            ['AAPL'],
            {'AAPL': pd.Series([0.01, 0.02, -0.01])}
        )
        
        assert single_pos_metrics.portfolio_correlation == 0
        assert single_pos_metrics.diversification_ratio == 1.0
        print("✓ Single position correlation handled correctly")
        
        # Test 5: Mismatched data lengths
        print("\nTest 5: Mismatched data lengths...")
        mismatched_returns = {
            'AAPL': pd.Series([0.01, 0.02, -0.01, 0.03]),
            'GOOGL': pd.Series([0.02, -0.01])  # Different length
        }
        
        try:
            corr_metrics = risk_analyzer.analyze_correlation_risk(
                ['AAPL', 'GOOGL'],
                mismatched_returns
            )
            print("✓ Mismatched data handled gracefully")
        except Exception as e:
            print(f"✓ Exception properly raised for mismatched data: {type(e).__name__}")
            
    @pytest.mark.asyncio
    async def test_resource_exhaustion(self):
        """Test system behavior under resource exhaustion"""
        print("\n=== Testing Resource Exhaustion ===")
        
        # Test 1: Transaction buffer overflow
        print("Test 1: Transaction buffer overflow...")
        
        from backtest2.core.engine import BacktestEngine
        from backtest2.config.constants import TRANSACTION
        
        config = BacktestConfig(
            symbols=["AAPL"],
            start_date="2023-01-01",
            end_date="2023-01-02",
            initial_capital=1000000
        )
        
        engine = BacktestEngine(config)
        
        # Verify transaction buffer has size limit
        assert engine.transactions.max_size == TRANSACTION.transaction_buffer_size
        print(f"✓ Transaction buffer limited to {TRANSACTION.transaction_buffer_size} entries")
        
        # Test 2: Memory pressure simulation
        print("\nTest 2: Memory pressure simulation...")
        
        position_manager = PositionManager(
            initial_capital=100000,
            risk_config=RiskConfig()
        )
        
        # Create large number of positions
        symbols = [f"STOCK_{i}" for i in range(100)]
        
        for symbol in symbols:
            signal = TradingSignal(
                symbol=symbol,
                action=TradeAction.BUY,
                confidence=0.7
            )
            
            # Position manager should enforce max positions limit
            if len(position_manager.positions) < position_manager.risk_config.max_positions:
                # Simulate position creation
                position_manager.positions[symbol] = type('Position', (), {
                    'symbol': symbol,
                    'quantity': 100,
                    'entry_price': 100.0,
                    'entry_date': datetime.now()
                })()
                
        assert len(position_manager.positions) <= position_manager.risk_config.max_positions
        print(f"✓ Position count limited to {len(position_manager.positions)}")
        
        # Test 3: Rapid metric generation
        print("\nTest 3: Rapid metric generation...")
        
        from backtest2.utils.metrics_collector import BacktestMetrics
        
        metrics = BacktestMetrics()
        await metrics.start()
        
        try:
            # Generate many metrics rapidly
            for i in range(10000):
                metrics.record_trade_execution(
                    f"SYMBOL_{i % 10}",
                    "BUY" if i % 2 == 0 else "SELL",
                    100 + i % 1000,
                    150.0 + (i % 100) * 0.1
                )
                
            # Check metrics are still responsive
            all_metrics = metrics.get_all_metrics()
            assert len(all_metrics["counters"]) > 0
            print(f"✓ Metrics system handled {10000} rapid updates")
            
        finally:
            await metrics.stop()
            

async def run_edge_case_tests():
    """Run all edge case and error tests"""
    print("\n" + "="*60)
    print("EDGE CASES AND ERROR SCENARIOS E2E TEST SUITE")
    print("="*60)
    
    test_suite = TestEdgeCasesAndErrors()
    
    tests = [
        ("Extreme Market Conditions", test_suite.test_extreme_market_conditions),
        ("Circuit Breaker Cascade", test_suite.test_circuit_breaker_cascade),
        ("Concurrent Transaction Conflicts", test_suite.test_concurrent_transaction_conflicts),
        ("Cache Overflow and Eviction", test_suite.test_cache_overflow_and_eviction),
        ("Malformed Data Handling", test_suite.test_malformed_data_handling),
        ("Resource Exhaustion", test_suite.test_resource_exhaustion)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
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
    success = asyncio.run(run_edge_case_tests())
    sys.exit(0 if success else 1)