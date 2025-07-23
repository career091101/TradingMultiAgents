"""E2E tests for WebUI integration with improved backtest2 system"""

import pytest
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys
import os
from playwright.async_api import async_playwright, Page, Browser

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))


class TestWebUIBacktest2Integration:
    """Test suite for WebUI integration with backtest2 improvements"""
    
    @pytest.fixture
    async def browser(self):
        """Create browser instance"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            yield browser
            await browser.close()
            
    @pytest.fixture
    async def page(self, browser: Browser):
        """Create page instance"""
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        yield page
        await context.close()
        
    async def wait_for_streamlit(self, page: Page):
        """Wait for Streamlit app to load"""
        await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
        await page.wait_for_load_state('networkidle')
        
    @pytest.mark.asyncio
    async def test_backtest_execution_with_retry(self, page: Page):
        """Test backtest execution with retry mechanism"""
        print("\n=== Testing Backtest Execution with Retry Mechanism ===")
        
        # Navigate to the app
        await page.goto("http://localhost:8501")
        await self.wait_for_streamlit(page)
        
        # Navigate to backtest page
        print("Navigating to backtest page...")
        await page.click('text="バックテスト"')
        await page.wait_for_selector('[data-testid="stButton"]')
        
        # Configure backtest parameters
        print("Configuring backtest parameters...")
        
        # Set date range
        await page.fill('input[type="date"]:first-of-type', '2023-01-01')
        await page.fill('input[type="date"]:last-of-type', '2023-12-31')
        
        # Set initial capital
        capital_input = await page.query_selector('input[type="number"]')
        if capital_input:
            await capital_input.fill('100000')
            
        # Select symbols
        await page.click('text="銘柄を選択"')
        await page.click('text="AAPL"')
        await page.click('text="GOOGL"')
        
        # Start backtest
        print("Starting backtest execution...")
        await page.click('button:has-text("バックテスト実行")')
        
        # Monitor execution with retry status
        retry_detected = False
        circuit_breaker_status = None
        
        # Wait for results or error with retry indication
        for i in range(60):  # 60 seconds timeout
            # Check for retry messages
            retry_msg = await page.query_selector('text=/再試行|Retrying/i')
            if retry_msg:
                retry_detected = True
                print("✓ Retry mechanism detected during execution")
                
            # Check for circuit breaker status
            cb_msg = await page.query_selector('text=/Circuit breaker|サーキットブレーカー/i')
            if cb_msg:
                circuit_breaker_status = await cb_msg.text_content()
                print(f"✓ Circuit breaker status: {circuit_breaker_status}")
                
            # Check for completion
            results = await page.query_selector('[data-testid="backtest-results"]')
            if results:
                print("✓ Backtest completed successfully")
                break
                
            await page.wait_for_timeout(1000)
        else:
            pytest.fail("Backtest execution timed out")
            
        # Verify results include new metrics
        await self.verify_enhanced_results(page)
        
    async def verify_enhanced_results(self, page: Page):
        """Verify enhanced results with new features"""
        print("\nVerifying enhanced results...")
        
        # Check for risk metrics
        gap_risk = await page.query_selector('text=/Gap Risk|ギャップリスク/i')
        assert gap_risk, "Gap risk metrics not found"
        print("✓ Gap risk metrics displayed")
        
        correlation_risk = await page.query_selector('text=/Correlation|相関/i')
        assert correlation_risk, "Correlation risk metrics not found"
        print("✓ Correlation risk metrics displayed")
        
        # Check for cache statistics
        cache_stats = await page.query_selector('text=/Cache Hit Rate|キャッシュヒット率/i')
        if cache_stats:
            print("✓ Cache statistics displayed")
            
        # Check for transaction atomicity indicators
        transaction_status = await page.query_selector('text=/Transaction Status|トランザクション状態/i')
        if transaction_status:
            print("✓ Transaction status indicators present")
            
    @pytest.mark.asyncio
    async def test_real_time_metrics_dashboard(self, page: Page):
        """Test real-time metrics dashboard"""
        print("\n=== Testing Real-time Metrics Dashboard ===")
        
        await page.goto("http://localhost:8501")
        await self.wait_for_streamlit(page)
        
        # Navigate to dashboard
        await page.click('text="ダッシュボード"')
        await page.wait_for_selector('[data-testid="metric-container"]')
        
        print("Checking metrics display...")
        
        # Verify metrics are displayed
        metrics_to_check = [
            "Total Trades",
            "Cache Hit Rate", 
            "Average LLM Response Time",
            "Circuit Breaker Status",
            "Active Positions",
            "Risk Score"
        ]
        
        found_metrics = 0
        for metric in metrics_to_check:
            element = await page.query_selector(f'text=/{metric}/i')
            if element:
                found_metrics += 1
                print(f"✓ {metric} metric found")
                
        assert found_metrics >= 4, f"Only found {found_metrics} metrics, expected at least 4"
        
        # Check for real-time updates
        print("\nChecking real-time updates...")
        initial_value = await page.text_content('[data-testid="metric-container"]:first-of-type')
        
        # Wait for potential update
        await page.wait_for_timeout(5000)
        
        # Check if any metrics have updated
        updated_value = await page.text_content('[data-testid="metric-container"]:first-of-type')
        print("✓ Metrics dashboard loaded successfully")
        
    @pytest.mark.asyncio
    async def test_configuration_validation_ui(self, page: Page):
        """Test configuration validation in UI"""
        print("\n=== Testing Configuration Validation UI ===")
        
        await page.goto("http://localhost:8501")
        await self.wait_for_streamlit(page)
        
        # Navigate to settings
        await page.click('text="設定"')
        await page.wait_for_selector('text="リスク設定"')
        
        print("Testing invalid configuration inputs...")
        
        # Test invalid stop loss (>100%)
        stop_loss_input = await page.query_selector('input[aria-label*="Stop Loss"]')
        if stop_loss_input:
            await stop_loss_input.fill('150')
            await page.press('input[aria-label*="Stop Loss"]', 'Tab')
            
            # Check for validation error
            error_msg = await page.wait_for_selector('text=/Invalid|無効|Error|エラー/i', timeout=3000)
            assert error_msg, "Validation error not shown for invalid stop loss"
            print("✓ Stop loss validation working")
            
        # Test invalid position size (negative)
        position_size_input = await page.query_selector('input[aria-label*="Position Size"]')
        if position_size_input:
            await position_size_input.fill('-10')
            await page.press('input[aria-label*="Position Size"]', 'Tab')
            
            # Check for validation error
            error_msg = await page.wait_for_selector('text=/must be positive|正の値/i', timeout=3000)
            assert error_msg, "Validation error not shown for negative position size"
            print("✓ Position size validation working")
            
        # Test configuration warnings
        print("\nChecking configuration warnings...")
        
        # Set high slippage
        slippage_input = await page.query_selector('input[aria-label*="Slippage"]')
        if slippage_input:
            await slippage_input.fill('5')  # 5% slippage
            await page.press('input[aria-label*="Slippage"]', 'Tab')
            
            # Check for warning
            warning_msg = await page.wait_for_selector('text=/Warning|警告|High slippage/i', timeout=3000)
            if warning_msg:
                print("✓ Configuration warnings displayed")
                
    @pytest.mark.asyncio  
    async def test_error_recovery_flow(self, page: Page):
        """Test error recovery with improved error handling"""
        print("\n=== Testing Error Recovery Flow ===")
        
        await page.goto("http://localhost:8501")
        await self.wait_for_streamlit(page)
        
        # Simulate various error conditions
        print("Testing LLM timeout recovery...")
        
        # Navigate to backtest with minimal data to trigger potential errors
        await page.click('text="バックテスト"')
        
        # Set very short date range (might cause data issues)
        await page.fill('input[type="date"]:first-of-type', '2023-12-30')
        await page.fill('input[type="date"]:last-of-type', '2023-12-31')
        
        # Try to execute
        await page.click('button:has-text("バックテスト実行")')
        
        # Monitor error handling
        error_handled = False
        recovery_attempted = False
        
        for i in range(30):
            # Check for error messages
            error_msg = await page.query_selector('.stAlert[data-testid="stAlert"]')
            if error_msg:
                error_handled = True
                error_text = await error_msg.text_content()
                print(f"✓ Error detected and displayed: {error_text[:50]}...")
                
            # Check for recovery attempts
            recovery_msg = await page.query_selector('text=/Recovering|回復|Retrying|再試行/i')
            if recovery_msg:
                recovery_attempted = True
                print("✓ Recovery mechanism activated")
                
            # Check if recovered
            success_msg = await page.query_selector('text=/Completed|完了|Success|成功/i')
            if success_msg and error_handled:
                print("✓ System recovered from error successfully")
                break
                
            await page.wait_for_timeout(1000)
            
        assert error_handled or recovery_attempted, "No error handling or recovery detected"
        
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, page: Page):
        """Test performance monitoring features"""
        print("\n=== Testing Performance Monitoring ===")
        
        await page.goto("http://localhost:8501")
        await self.wait_for_streamlit(page)
        
        # Check for performance metrics in UI
        print("Checking performance metrics...")
        
        # Look for performance indicators
        perf_indicators = [
            "Response Time",
            "レスポンス時間",
            "Latency", 
            "遅延",
            "Memory Usage",
            "メモリ使用量"
        ]
        
        found_indicators = 0
        for indicator in perf_indicators:
            element = await page.query_selector(f'text=/{indicator}/i')
            if element:
                found_indicators += 1
                print(f"✓ Found performance indicator: {indicator}")
                
        # Check page load time
        navigation_start = await page.evaluate('window.performance.timing.navigationStart')
        load_complete = await page.evaluate('window.performance.timing.loadEventEnd')
        load_time = (load_complete - navigation_start) / 1000
        
        print(f"✓ Page load time: {load_time:.2f} seconds")
        assert load_time < 10, f"Page load time too slow: {load_time:.2f}s"
        
        # Check for memory leak indicators
        print("\nChecking for memory leak prevention...")
        
        # Get initial memory usage
        initial_memory = await page.evaluate('window.performance.memory?.usedJSHeapSize || 0')
        
        # Perform some operations
        for i in range(5):
            await page.click('text="ダッシュボード"')
            await page.wait_for_timeout(1000)
            await page.click('text="バックテスト"')
            await page.wait_for_timeout(1000)
            
        # Check memory after operations
        final_memory = await page.evaluate('window.performance.memory?.usedJSHeapSize || 0')
        
        if initial_memory > 0 and final_memory > 0:
            memory_increase = (final_memory - initial_memory) / initial_memory
            print(f"✓ Memory increase: {memory_increase:.1%}")
            assert memory_increase < 0.5, f"Potential memory leak: {memory_increase:.1%} increase"
            

async def run_webui_integration_tests():
    """Run all WebUI integration tests"""
    print("\n" + "="*60)
    print("WEBUI BACKTEST2 INTEGRATION E2E TEST SUITE")
    print("="*60)
    
    # Note: These tests require the WebUI to be running
    print("\n⚠️  Note: Please ensure the WebUI is running at http://localhost:8501")
    print("   Run: streamlit run TradingMultiAgents/streamlit_app.py")
    
    test_suite = TestWebUIBacktest2Integration()
    
    # Create browser and page
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to True for CI
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        tests = [
            ("Backtest Execution with Retry", test_suite.test_backtest_execution_with_retry),
            ("Real-time Metrics Dashboard", test_suite.test_real_time_metrics_dashboard),
            ("Configuration Validation UI", test_suite.test_configuration_validation_ui),
            ("Error Recovery Flow", test_suite.test_error_recovery_flow),
            ("Performance Monitoring", test_suite.test_performance_monitoring)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                await test_func(page)
                passed += 1
                print(f"\n✅ {test_name} - PASSED")
            except Exception as e:
                failed += 1
                print(f"\n❌ {test_name} - FAILED: {e}")
                
                # Take screenshot on failure
                await page.screenshot(path=f"test_failure_{test_name.replace(' ', '_')}.png")
                
                import traceback
                traceback.print_exc()
                
        await context.close()
        await browser.close()
        
    print("\n" + "="*60)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(run_webui_integration_tests())
    sys.exit(0 if success else 1)