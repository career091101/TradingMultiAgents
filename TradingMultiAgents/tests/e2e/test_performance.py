"""
E2E Performance Tests - Phase 2 Implementation
TC016: Page Load Time Testing
TC017: Large Data Processing Testing
Additional performance benchmarks
"""

import pytest
from playwright.sync_api import Page, expect, Browser
import time
import json
from typing import Dict, List, Any
import statistics

# Phase 2 マーカー
pytestmark = pytest.mark.performance


class TestPageLoadPerformance:
    """TC016: Test page loading performance"""

    # Performance thresholds (in milliseconds)
    PERFORMANCE_THRESHOLDS = {
        "dashboard": 3000,
        "settings": 2000,
        "execution": 2000,
        "results": 5000
    }

    def test_dashboard_load_time(self, page: Page, screenshot_dir):
        """Test dashboard page load performance"""
        start_time = time.time()
        
        # Navigate to dashboard
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle", timeout=10000)
        
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000
        
        # Get detailed performance metrics
        metrics = page.evaluate("""() => {
            const timing = performance.timing;
            const navigation = performance.getEntriesByType('navigation')[0];
            
            return {
                domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                loadComplete: timing.loadEventEnd - timing.navigationStart,
                firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0,
                firstContentfulPaint: performance.getEntriesByType('paint')[1]?.startTime || 0,
                navigationStart: timing.navigationStart,
                responseStart: timing.responseStart - timing.navigationStart,
                responseEnd: timing.responseEnd - timing.navigationStart,
                domInteractive: timing.domInteractive - timing.navigationStart,
                resourceCount: performance.getEntriesByType('resource').length
            }
        }""")
        
        # Take screenshot
        page.screenshot(path=f"{screenshot_dir}/dashboard_performance.png", full_page=True)
        
        # Log performance metrics
        print(f"Dashboard Load Performance:")
        print(f"  Total Load Time: {load_time_ms:.0f}ms")
        print(f"  DOM Content Loaded: {metrics['domContentLoaded']:.0f}ms")
        print(f"  Load Complete: {metrics['loadComplete']:.0f}ms")
        print(f"  First Paint: {metrics['firstPaint']:.0f}ms")
        print(f"  First Contentful Paint: {metrics['firstContentfulPaint']:.0f}ms")
        print(f"  Resources Loaded: {metrics['resourceCount']}")
        
        # Assert performance thresholds
        assert load_time_ms < self.PERFORMANCE_THRESHOLDS["dashboard"], \
            f"Dashboard load time {load_time_ms:.0f}ms exceeds threshold {self.PERFORMANCE_THRESHOLDS['dashboard']}ms"
        
        assert metrics['domContentLoaded'] < self.PERFORMANCE_THRESHOLDS["dashboard"] * 0.8, \
            f"DOM content loaded time {metrics['domContentLoaded']:.0f}ms is too slow"

    def test_settings_page_load_time(self, page: Page, screenshot_dir):
        """Test settings page load performance"""
        # Start from dashboard
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        start_time = time.time()
        
        # Navigate to settings
        page.click("text=分析設定")
        page.wait_for_load_state("networkidle", timeout=5000)
        
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000
        
        page.screenshot(path=f"{screenshot_dir}/settings_performance.png", full_page=True)
        
        print(f"Settings Page Load Time: {load_time_ms:.0f}ms")
        
        assert load_time_ms < self.PERFORMANCE_THRESHOLDS["settings"], \
            f"Settings load time {load_time_ms:.0f}ms exceeds threshold {self.PERFORMANCE_THRESHOLDS['settings']}ms"

    def test_execution_page_load_time(self, page: Page, screenshot_dir):
        """Test execution page load performance"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        start_time = time.time()
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle", timeout=5000)
        
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000
        
        page.screenshot(path=f"{screenshot_dir}/execution_performance.png", full_page=True)
        
        print(f"Execution Page Load Time: {load_time_ms:.0f}ms")
        
        assert load_time_ms < self.PERFORMANCE_THRESHOLDS["execution"], \
            f"Execution load time {load_time_ms:.0f}ms exceeds threshold {self.PERFORMANCE_THRESHOLDS['execution']}ms"

    def test_results_page_load_time(self, page: Page, screenshot_dir):
        """Test results page load performance"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        start_time = time.time()
        
        page.click("text=結果表示")
        page.wait_for_load_state("networkidle", timeout=8000)
        
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000
        
        page.screenshot(path=f"{screenshot_dir}/results_performance.png", full_page=True)
        
        print(f"Results Page Load Time: {load_time_ms:.0f}ms")
        
        assert load_time_ms < self.PERFORMANCE_THRESHOLDS["results"], \
            f"Results load time {load_time_ms:.0f}ms exceeds threshold {self.PERFORMANCE_THRESHOLDS['results']}ms"

    def test_resource_loading_optimization(self, page: Page, screenshot_dir):
        """Test resource loading optimization"""
        # Monitor network requests
        resource_stats = {
            "total_requests": 0,
            "total_size": 0,
            "slow_requests": [],
            "failed_requests": []
        }
        
        def track_request(request):
            resource_stats["total_requests"] += 1
        
        def track_response(response):
            try:
                if response.request.resource_type in ["stylesheet", "script", "image"]:
                    # Track resource loading time
                    load_time = response.request.timing["responseEnd"] - response.request.timing["requestStart"]
                    if load_time > 1000:  # Resources taking more than 1 second
                        resource_stats["slow_requests"].append({
                            "url": response.url,
                            "type": response.request.resource_type,
                            "load_time": load_time,
                            "size": len(response.body()) if response.body() else 0
                        })
                    
                    if response.body():
                        resource_stats["total_size"] += len(response.body())
            except:
                resource_stats["failed_requests"].append(response.url)
        
        page.on("request", track_request)
        page.on("response", track_response)
        
        # Load dashboard page
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle", timeout=10000)
        
        page.screenshot(path=f"{screenshot_dir}/resource_optimization.png")
        
        print(f"Resource Loading Stats:")
        print(f"  Total Requests: {resource_stats['total_requests']}")
        print(f"  Total Size: {resource_stats['total_size']/1024:.1f} KB")
        print(f"  Slow Requests: {len(resource_stats['slow_requests'])}")
        print(f"  Failed Requests: {len(resource_stats['failed_requests'])}")
        
        # Assert reasonable resource usage
        assert resource_stats["total_size"] < 5 * 1024 * 1024, "Total resource size exceeds 5MB"
        assert len(resource_stats["slow_requests"]) < 3, "Too many slow loading resources"
        assert len(resource_stats["failed_requests"]) == 0, "Some resources failed to load"


class TestLargeDataProcessing:
    """TC017: Test handling of large datasets"""

    def test_large_dataset_rendering(self, page: Page, screenshot_dir):
        """Test performance with large datasets"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to results page
        page.click("text=結果表示")
        page.wait_for_load_state("networkidle")
        
        # Measure memory usage before loading large data
        initial_memory = page.evaluate("""() => {
            if (performance.memory) {
                return {
                    usedJSHeapSize: performance.memory.usedJSHeapSize,
                    totalJSHeapSize: performance.memory.totalJSHeapSize,
                    jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                }
            }
            return null;
        }""")
        
        # Simulate loading large dataset by scrolling through content
        start_time = time.time()
        
        # Scroll through the page to trigger any virtual scrolling or lazy loading
        for i in range(10):
            page.evaluate(f"window.scrollTo(0, {i * 500})")
            page.wait_for_timeout(200)
        
        # Scroll back to top
        page.evaluate("window.scrollTo(0, 0)")
        
        end_time = time.time()
        scroll_time_ms = (end_time - start_time) * 1000
        
        # Measure memory usage after data operations
        final_memory = page.evaluate("""() => {
            if (performance.memory) {
                return {
                    usedJSHeapSize: performance.memory.usedJSHeapSize,
                    totalJSHeapSize: performance.memory.totalJSHeapSize,
                    jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                }
            }
            return null;
        }""")
        
        page.screenshot(path=f"{screenshot_dir}/large_data_performance.png", full_page=True)
        
        if initial_memory and final_memory:
            memory_increase = final_memory["usedJSHeapSize"] - initial_memory["usedJSHeapSize"]
            memory_increase_mb = memory_increase / (1024 * 1024)
            
            print(f"Large Data Performance:")
            print(f"  Scroll Time: {scroll_time_ms:.0f}ms")
            print(f"  Memory Increase: {memory_increase_mb:.1f}MB")
            print(f"  Final Memory Usage: {final_memory['usedJSHeapSize']/(1024*1024):.1f}MB")
            
            # Assert memory usage is reasonable
            assert memory_increase_mb < 100, f"Memory usage increased by {memory_increase_mb:.1f}MB, which is too much"
        
        # Assert scrolling performance
        assert scroll_time_ms < 5000, f"Scrolling took {scroll_time_ms:.0f}ms, which is too slow"

    def test_table_rendering_performance(self, page: Page, screenshot_dir):
        """Test table rendering performance with many rows"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=結果表示")
        page.wait_for_load_state("networkidle")
        
        # Look for tables on the page
        tables = page.locator("table, .dataframe").all()
        
        for i, table in enumerate(tables):
            start_time = time.time()
            
            # Force table to be visible
            table.scroll_into_view_if_needed()
            
            # Wait for table to fully render
            page.wait_for_timeout(1000)
            
            end_time = time.time()
            render_time_ms = (end_time - start_time) * 1000
            
            # Count rows in table
            try:
                rows = table.locator("tr").all()
                row_count = len(rows)
            except:
                row_count = 0
            
            page.screenshot(path=f"{screenshot_dir}/table_performance_{i}.png")
            
            print(f"Table {i} Performance:")
            print(f"  Rows: {row_count}")
            print(f"  Render Time: {render_time_ms:.0f}ms")
            
            # Assert reasonable rendering time
            if row_count > 0:
                time_per_row = render_time_ms / row_count
                assert time_per_row < 10, f"Table rendering took {time_per_row:.1f}ms per row"

    def test_chart_rendering_performance(self, page: Page, screenshot_dir):
        """Test chart rendering performance"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=結果表示")
        page.wait_for_load_state("networkidle")
        
        # Look for chart containers
        chart_containers = page.locator(".plotly, canvas, svg[class*='chart']").all()
        
        for i, chart in enumerate(chart_containers):
            start_time = time.time()
            
            # Scroll to chart
            chart.scroll_into_view_if_needed()
            
            # Wait for chart to load
            page.wait_for_timeout(2000)
            
            end_time = time.time()
            render_time_ms = (end_time - start_time) * 1000
            
            page.screenshot(path=f"{screenshot_dir}/chart_performance_{i}.png")
            
            print(f"Chart {i} Render Time: {render_time_ms:.0f}ms")
            
            # Assert reasonable chart rendering time
            assert render_time_ms < 5000, f"Chart took {render_time_ms:.0f}ms to render"


class TestMemoryLeakDetection:
    """Test for memory leaks during navigation"""

    def test_memory_usage_during_navigation(self, page: Page, screenshot_dir):
        """Test memory usage during multiple page navigations"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        memory_readings = []
        
        pages_to_test = [
            ("ダッシュボード", "http://localhost:8501"),
            ("分析設定", None),
            ("分析実行", None),
            ("結果表示", None)
        ]
        
        for i, (page_name, url) in enumerate(pages_to_test):
            # Navigate to page
            if url:
                page.goto(url)
            else:
                page.click(f"text={page_name}")
            
            page.wait_for_load_state("networkidle", timeout=8000)
            
            # Measure memory
            memory = page.evaluate("""() => {
                if (performance.memory) {
                    return performance.memory.usedJSHeapSize;
                }
                return null;
            }""")
            
            if memory:
                memory_mb = memory / (1024 * 1024)
                memory_readings.append(memory_mb)
                print(f"{page_name} memory usage: {memory_mb:.1f}MB")
            
            page.screenshot(path=f"{screenshot_dir}/memory_test_{i}_{page_name}.png")
            
            # Force garbage collection
            page.evaluate("window.gc && window.gc()")
            page.wait_for_timeout(1000)
        
        if len(memory_readings) > 1:
            # Check for significant memory increases
            max_memory = max(memory_readings)
            min_memory = min(memory_readings)
            memory_increase = max_memory - min_memory
            
            print(f"Memory Analysis:")
            print(f"  Min Memory: {min_memory:.1f}MB")
            print(f"  Max Memory: {max_memory:.1f}MB")
            print(f"  Increase: {memory_increase:.1f}MB")
            
            # Assert no significant memory leaks
            assert memory_increase < 50, f"Memory increased by {memory_increase:.1f}MB during navigation"


class TestConcurrentUserSimulation:
    """Test performance under concurrent load"""

    def test_concurrent_page_access(self, page: Page, screenshot_dir):
        """Simulate multiple users accessing the application"""
        # This test simulates concurrent access by rapidly switching pages
        start_time = time.time()
        
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Rapidly navigate between pages
        navigation_times = []
        
        for i in range(5):
            nav_start = time.time()
            
            # Navigate to different pages quickly
            page.click("text=分析設定")
            page.wait_for_load_state("networkidle", timeout=5000)
            
            page.click("text=分析実行")
            page.wait_for_load_state("networkidle", timeout=5000)
            
            page.click("text=結果表示")
            page.wait_for_load_state("networkidle", timeout=5000)
            
            nav_end = time.time()
            navigation_times.append((nav_end - nav_start) * 1000)
        
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        
        avg_navigation_time = statistics.mean(navigation_times)
        max_navigation_time = max(navigation_times)
        
        page.screenshot(path=f"{screenshot_dir}/concurrent_access_test.png")
        
        print(f"Concurrent Access Test:")
        print(f"  Total Time: {total_time_ms:.0f}ms")
        print(f"  Average Navigation: {avg_navigation_time:.0f}ms")
        print(f"  Max Navigation: {max_navigation_time:.0f}ms")
        
        # Assert reasonable performance under rapid navigation
        assert avg_navigation_time < 8000, f"Average navigation time {avg_navigation_time:.0f}ms is too slow"
        assert max_navigation_time < 15000, f"Max navigation time {max_navigation_time:.0f}ms is too slow"


class TestMobilePerformance:
    """Test performance on mobile devices"""

    @pytest.fixture
    def mobile_page(self, browser: Browser, screenshot_dir):
        """Create a mobile context for testing"""
        mobile_context = browser.new_context(
            viewport={"width": 375, "height": 812},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True
        )
        page = mobile_context.new_page()
        yield page
        mobile_context.close()

    def test_mobile_page_load_performance(self, mobile_page: Page, screenshot_dir):
        """Test page load performance on mobile"""
        start_time = time.time()
        
        mobile_page.goto("http://localhost:8501")
        mobile_page.wait_for_load_state("networkidle", timeout=10000)
        
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000
        
        mobile_page.screenshot(path=f"{screenshot_dir}/mobile_performance.png", full_page=True)
        
        print(f"Mobile Load Time: {load_time_ms:.0f}ms")
        
        # Mobile should load within 5 seconds
        assert load_time_ms < 5000, f"Mobile load time {load_time_ms:.0f}ms exceeds 5 second threshold"

    def test_mobile_scrolling_performance(self, mobile_page: Page, screenshot_dir):
        """Test scrolling performance on mobile"""
        mobile_page.goto("http://localhost:8501")
        mobile_page.wait_for_load_state("networkidle")
        
        start_time = time.time()
        
        # Simulate mobile scrolling
        for i in range(20):
            mobile_page.evaluate(f"window.scrollTo(0, {i * 100})")
            mobile_page.wait_for_timeout(50)
        
        end_time = time.time()
        scroll_time_ms = (end_time - start_time) * 1000
        
        mobile_page.screenshot(path=f"{screenshot_dir}/mobile_scrolling.png")
        
        print(f"Mobile Scrolling Time: {scroll_time_ms:.0f}ms")
        
        # Scrolling should be smooth (under 2 seconds for 20 scrolls)
        assert scroll_time_ms < 2000, f"Mobile scrolling took {scroll_time_ms:.0f}ms"