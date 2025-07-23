"""
E2E Performance Tests - Phase 2 Implementation (Adapted)
現在のWebUI構造に合わせたパフォーマンステスト
"""

import pytest
from playwright.sync_api import Page, expect
import time
import json
from typing import Dict, List, Any
from utils.streamlit_selectors import StreamlitSelectors
from utils.streamlit_test_helpers import StreamlitTestHelpers, StreamlitAssertions

# Phase 2 マーカー
pytestmark = pytest.mark.performance


class TestPerformanceAdapted:
    """WebUI構造に適応したパフォーマンステスト"""
    
    def setup_method(self):
        """Set up selectors for testing"""
        self.selectors = StreamlitSelectors()

    def test_page_load_performance(self, page: Page, screenshot_dir):
        """ページロード性能テスト"""
        start_time = time.time()
        
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        load_time = time.time() - start_time
        
        page.screenshot(path=f"{screenshot_dir}/page_load_performance.png", full_page=True)
        
        print(f"Page load time: {load_time:.2f} seconds")
        
        # Basic performance assertion
        assert load_time < 10.0, f"Page load time {load_time:.2f}s exceeds 10 seconds"
        
        # Get JavaScript performance metrics
        metrics = page.evaluate("""() => {
            const timing = performance.timing;
            return {
                domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                loadComplete: timing.loadEventEnd - timing.navigationStart,
                navigationStart: timing.navigationStart
            }
        }""")
        
        print(f"DOM Content Loaded: {metrics['domContentLoaded']}ms")
        print(f"Load Complete: {metrics['loadComplete']}ms")

    def test_navigation_performance(self, page: Page, screenshot_dir):
        """ナビゲーション性能テスト"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        pages_to_test = ["settings", "execution", "results"]
        navigation_times = []
        
        for page_name in pages_to_test:
            start_time = time.time()
            
            page.click(self.selectors.nav_button(page_name))
            page.wait_for_load_state("networkidle")
            
            nav_time = time.time() - start_time
            navigation_times.append(nav_time)
            
            print(f"Navigation to {page_name}: {nav_time:.2f} seconds")
            
            page.screenshot(path=f"{screenshot_dir}/nav_{page_name}.png", full_page=True)
            
            # Assert reasonable navigation time
            assert nav_time < 5.0, f"Navigation to {page_name} took {nav_time:.2f}s"
        
        avg_nav_time = sum(navigation_times) / len(navigation_times)
        print(f"Average navigation time: {avg_nav_time:.2f} seconds")

    def test_memory_usage_monitoring(self, page: Page, screenshot_dir):
        """メモリ使用量監視テスト"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Initial memory measurement
        initial_memory = page.evaluate("""() => {
            if (performance.memory) {
                return {
                    used: performance.memory.usedJSHeapSize,
                    total: performance.memory.totalJSHeapSize,
                    limit: performance.memory.jsHeapSizeLimit
                }
            }
            return null;
        }""")
        
        if initial_memory:
            print(f"Initial memory usage: {initial_memory['used']/(1024*1024):.1f}MB")
        
        # Navigate through pages
        pages = ["settings", "execution", "results", "dashboard"]
        
        for page_name in pages:
            if page_name == "dashboard":
                page.goto("http://localhost:8501")  # Back to dashboard
            else:
                page.click(self.selectors.nav_button(page_name))
            
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)  # Wait for any animations
            
            # Measure memory after navigation
            current_memory = page.evaluate("""() => {
                if (performance.memory) {
                    return {
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize
                    }
                }
                return null;
            }""")
            
            if current_memory:
                memory_mb = current_memory['used'] / (1024 * 1024)
                print(f"Memory after {page_name}: {memory_mb:.1f}MB")
                
                # Assert reasonable memory usage
                assert memory_mb < 100, f"Memory usage {memory_mb:.1f}MB is too high"
        
        page.screenshot(path=f"{screenshot_dir}/memory_test_final.png", full_page=True)

    def test_responsive_design_performance(self, page: Page, screenshot_dir):
        """レスポンシブデザインの性能テスト（修正版）"""
        page.goto("http://localhost:8501")
        StreamlitTestHelpers.wait_for_streamlit_ready(page)
        
        viewports = [
            {"name": "desktop", "width": 1920, "height": 1080},
            {"name": "tablet", "width": 768, "height": 1024},
            {"name": "mobile", "width": 375, "height": 812}
        ]
        
        for viewport in viewports:
            start_time = time.time()
            
            page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
            page.wait_for_timeout(1000)  # Allow layout to adjust
            
            resize_time = time.time() - start_time
            
            print(f"Resize to {viewport['name']}: {resize_time:.2f} seconds")
            
            page.screenshot(path=f"{screenshot_dir}/responsive_{viewport['name']}.png", full_page=True)
            
            # Assert reasonable resize time
            assert resize_time < 2.0, f"Resize to {viewport['name']} took {resize_time:.2f}s"
            
            # レスポンシブサイドバーの適切な動作を確認
            StreamlitAssertions.assert_responsive_sidebar(page, viewport["width"])

    def test_repeated_interactions_performance(self, page: Page, screenshot_dir):
        """繰り返し操作の性能テスト"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Test repeated navigation
        interaction_times = []
        
        for i in range(5):
            start_time = time.time()
            
            # Navigate to settings and back
            page.click(self.selectors.nav_button("settings"))
            page.wait_for_load_state("networkidle")
            
            page.click(self.selectors.nav_button("dashboard"))
            page.wait_for_load_state("networkidle")
            
            interaction_time = time.time() - start_time
            interaction_times.append(interaction_time)
            
            print(f"Round trip {i+1}: {interaction_time:.2f} seconds")
        
        # Calculate statistics
        avg_time = sum(interaction_times) / len(interaction_times)
        max_time = max(interaction_times)
        
        print(f"Average round trip time: {avg_time:.2f} seconds")
        print(f"Maximum round trip time: {max_time:.2f} seconds")
        
        page.screenshot(path=f"{screenshot_dir}/repeated_interactions.png", full_page=True)
        
        # Assert performance doesn't degrade significantly
        assert max_time < avg_time * 2, "Performance degraded significantly"
        assert avg_time < 5.0, f"Average interaction time {avg_time:.2f}s is too slow"

    def test_concurrent_page_access_simulation(self, page: Page, screenshot_dir):
        """同時ページアクセスのシミュレーション（修正版）"""
        page.goto("http://localhost:8501")
        StreamlitTestHelpers.wait_for_streamlit_ready(page)
        
        # Create additional context to simulate multiple users
        context = page.context
        pages = [page]
        
        # Create 2 additional pages with proper session isolation
        for i in range(2):
            new_page = StreamlitTestHelpers.create_stable_page_session(
                context, "http://localhost:8501"
            )
            pages.append(new_page)
        
        # セッション間の競合を避けるための安定化処理
        StreamlitTestHelpers.handle_concurrent_sessions(pages, delay_between_actions=1.5)
        
        # Perform navigation sequentially to avoid session conflicts
        start_time = time.time()
        
        navigation_actions = ["settings", "execution", "results"]
        
        for i, test_page in enumerate(pages):
            if i < len(navigation_actions):
                StreamlitTestHelpers.safe_click_with_retry(
                    test_page, self.selectors.nav_button(navigation_actions[i])
                )
                StreamlitTestHelpers.wait_for_navigation_complete(test_page)
                
                # 個別の安定化待機
                time.sleep(0.5)
        
        concurrent_time = time.time() - start_time
        
        print(f"Sequential navigation time: {concurrent_time:.2f} seconds")
        
        # Take screenshots of all pages
        for i, test_page in enumerate(pages):
            test_page.screenshot(path=f"{screenshot_dir}/concurrent_page_{i}.png", full_page=True)
        
        # Assert reasonable performance
        assert concurrent_time < 15.0, f"Sequential operations took {concurrent_time:.2f}s"
        
        # Verify all pages are still functional using safe assertions
        StreamlitAssertions.assert_concurrent_pages_stable(pages)
        
        # Close additional pages
        for test_page in pages[1:]:
            test_page.close()

    def test_resource_loading_efficiency(self, page: Page, screenshot_dir):
        """リソース読み込み効率テスト"""
        resource_stats = {
            "total_requests": 0,
            "total_size": 0,
            "slow_requests": []
        }
        
        def track_request(request):
            resource_stats["total_requests"] += 1
        
        def track_response(response):
            try:
                if response.body():
                    size = len(response.body())
                    resource_stats["total_size"] += size
                    
                    # Check for slow responses (hypothetical timing)
                    if size > 1024 * 1024:  # > 1MB
                        resource_stats["slow_requests"].append({
                            "url": response.url,
                            "size": size
                        })
            except:
                pass
        
        page.on("request", track_request)
        page.on("response", track_response)
        
        # Load the page and navigate
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to a few pages to trigger resource loading
        page.click(self.selectors.nav_button("execution"))
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/resource_loading.png", full_page=True)
        
        # Report statistics
        print(f"Total requests: {resource_stats['total_requests']}")
        print(f"Total size: {resource_stats['total_size'] / 1024:.1f} KB")
        print(f"Large resources: {len(resource_stats['slow_requests'])}")
        
        # Assert reasonable resource usage
        assert resource_stats["total_size"] < 10 * 1024 * 1024, "Total resource size > 10MB"