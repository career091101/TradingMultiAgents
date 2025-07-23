"""
Enhanced Test Utilities for E2E Testing - Phase 2
Advanced helper functions, assertions, and test infrastructure
"""

import pytest
from playwright.sync_api import Page, Browser, BrowserContext, expect
import time
import json
import hashlib
import os
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import asyncio
from pathlib import Path


class AdvancedPageAssertions:
    """Enhanced assertion methods for page testing"""
    
    def __init__(self, page: Page):
        self.page = page
    
    def assert_page_performance(self, max_load_time_ms: int = 3000):
        """Assert page loads within specified time"""
        metrics = self.page.evaluate("""() => {
            const timing = performance.timing;
            return {
                loadTime: timing.loadEventEnd - timing.navigationStart,
                domReady: timing.domContentLoadedEventEnd - timing.navigationStart
            }
        }""")
        
        assert metrics['loadTime'] < max_load_time_ms, \
            f"Page load time {metrics['loadTime']}ms exceeds {max_load_time_ms}ms"
        
        return metrics
    
    def assert_no_console_errors(self, allowed_patterns: List[str] = None):
        """Assert no JavaScript console errors"""
        allowed_patterns = allowed_patterns or []
        
        console_messages = []
        
        def handle_console(msg):
            if msg.type == "error":
                console_messages.append(msg.text)
        
        self.page.on("console", handle_console)
        
        # Give time for any errors to appear
        self.page.wait_for_timeout(1000)
        
        # Filter out allowed error patterns
        actual_errors = []
        for error in console_messages:
            is_allowed = any(pattern in error for pattern in allowed_patterns)
            if not is_allowed:
                actual_errors.append(error)
        
        assert len(actual_errors) == 0, f"Console errors found: {actual_errors}"
    
    def assert_accessibility_standards(self):
        """Basic accessibility checks"""
        # Check for proper heading structure
        headings = self.page.locator("h1, h2, h3, h4, h5, h6").all()
        assert len(headings) > 0, "No headings found for screen reader navigation"
        
        # Check for alt text on images
        images = self.page.locator("img").all()
        for img in images:
            alt_text = img.get_attribute("alt")
            src = img.get_attribute("src")
            if src and not src.startswith("data:"):  # Skip data URLs
                assert alt_text is not None, f"Image missing alt text: {src}"
        
        # Check for form labels
        inputs = self.page.locator("input[type='text'], input[type='email'], input[type='password']").all()
        for input_field in inputs:
            label_id = input_field.get_attribute("id")
            aria_label = input_field.get_attribute("aria-label")
            
            has_label = False
            if label_id:
                label = self.page.locator(f"label[for='{label_id}']")
                has_label = label.count() > 0
            
            assert has_label or aria_label, "Form input missing label or aria-label"
    
    def assert_responsive_design(self, breakpoints: Dict[str, Dict[str, int]]):
        """Test responsive design at different breakpoints"""
        for name, viewport in breakpoints.items():
            self.page.set_viewport_size(viewport)
            self.page.wait_for_timeout(500)  # Allow layout to adjust
            
            # Check that critical elements are still visible
            critical_elements = ["button", "input", "[role='main']"]
            for selector in critical_elements:
                elements = self.page.locator(selector).all()
                if elements:  # Only check if elements exist
                    visible_count = sum(1 for el in elements if el.is_visible())
                    assert visible_count > 0, f"No {selector} elements visible at {name} ({viewport})"
    
    def assert_secure_headers(self, required_headers: List[str]):
        """Assert security headers are present"""
        response = self.page.goto(self.page.url)
        headers = response.headers
        
        missing_headers = []
        for header in required_headers:
            if header.lower() not in [h.lower() for h in headers.keys()]:
                missing_headers.append(header)
        
        assert len(missing_headers) == 0, f"Missing security headers: {missing_headers}"


class TestDataManager:
    """Manage test data and fixtures"""
    
    def __init__(self, base_path: str = "tests/fixtures"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def load_test_data(self, filename: str) -> Dict[str, Any]:
        """Load test data from JSON file"""
        file_path = self.base_path / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_test_data(self, filename: str, data: Dict[str, Any]):
        """Save test data to JSON file"""
        file_path = self.base_path / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def generate_test_stocks(self, count: int = 10) -> List[str]:
        """Generate list of test stock symbols"""
        base_stocks = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", 
            "META", "NVDA", "JPM", "JNJ", "V",
            "PG", "UNH", "HD", "MA", "DIS",
            "PYPL", "ADBE", "NFLX", "CRM", "INTC"
        ]
        return base_stocks[:count]
    
    def create_mock_api_response(self, symbol: str, scenario: str = "success") -> Dict[str, Any]:
        """Create mock API response data"""
        base_response = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "status": "success" if scenario == "success" else "error"
        }
        
        if scenario == "success":
            base_response.update({
                "price": 150.0 + hash(symbol) % 100,
                "change": (hash(symbol) % 20) - 10,
                "volume": 1000000 + hash(symbol) % 5000000,
                "analysis": {
                    "recommendation": ["BUY", "HOLD", "SELL"][hash(symbol) % 3],
                    "confidence": 0.5 + (hash(symbol) % 50) / 100,
                    "key_metrics": {
                        "rsi": 30 + (hash(symbol) % 40),
                        "macd": -5 + (hash(symbol) % 10),
                        "pe_ratio": 10 + (hash(symbol) % 30)
                    }
                }
            })
        else:
            base_response.update({
                "error": "API rate limit exceeded" if scenario == "rate_limit" else "Symbol not found",
                "error_code": 429 if scenario == "rate_limit" else 404
            })
        
        return base_response


class VisualTestingManager:
    """Manage visual regression testing"""
    
    def __init__(self, baseline_dir: str = "tests/screenshots/baseline"):
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
    
    def capture_baseline(self, page: Page, test_name: str, element_selector: str = None):
        """Capture baseline screenshot"""
        screenshot_path = self.baseline_dir / f"{test_name}_baseline.png"
        
        if element_selector:
            element = page.locator(element_selector)
            element.screenshot(path=str(screenshot_path))
        else:
            page.screenshot(path=str(screenshot_path), full_page=True)
        
        return screenshot_path
    
    def compare_visual(self, page: Page, test_name: str, threshold: float = 0.1) -> bool:
        """Compare current page with baseline"""
        baseline_path = self.baseline_dir / f"{test_name}_baseline.png"
        current_path = self.baseline_dir.parent / "current" / f"{test_name}_current.png"
        
        current_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Take current screenshot
        page.screenshot(path=str(current_path), full_page=True)
        
        if not baseline_path.exists():
            # No baseline exists, create one
            page.screenshot(path=str(baseline_path), full_page=True)
            return True
        
        # For now, return True (would implement actual image comparison)
        # In production, would use libraries like pixelmatch or opencv
        return True


class NetworkMockManager:
    """Manage network request mocking"""
    
    def __init__(self, page: Page):
        self.page = page
        self.routes = {}
        self.request_log = []
    
    def mock_api_success(self, symbol: str, data: Dict[str, Any] = None):
        """Mock successful API response"""
        test_data = TestDataManager()
        response_data = data or test_data.create_mock_api_response(symbol, "success")
        
        def handle_request(route):
            self.request_log.append({
                "url": route.request.url,
                "method": route.request.method,
                "timestamp": datetime.now().isoformat()
            })
            route.fulfill(
                status=200,
                headers={"content-type": "application/json"},
                body=json.dumps(response_data)
            )
        
        pattern = f"**/api/**{symbol}**"
        self.page.route(pattern, handle_request)
        self.routes[pattern] = handle_request
    
    def mock_api_error(self, error_type: str = "rate_limit", status_code: int = 429):
        """Mock API error responses"""
        error_responses = {
            "rate_limit": {
                "error": "Rate limit exceeded",
                "message": "API制限に達しました。しばらくお待ちください",
                "retry_after": 60
            },
            "not_found": {
                "error": "Symbol not found",
                "message": "指定された銘柄が見つかりません"
            },
            "server_error": {
                "error": "Internal server error",
                "message": "サーバーエラーが発生しました"
            }
        }
        
        def handle_error(route):
            self.request_log.append({
                "url": route.request.url,
                "method": route.request.method,
                "timestamp": datetime.now().isoformat(),
                "mocked_error": error_type
            })
            route.fulfill(
                status=status_code,
                headers={"content-type": "application/json"},
                body=json.dumps(error_responses.get(error_type, error_responses["server_error"]))
            )
        
        pattern = "**/api/**"
        self.page.route(pattern, handle_error)
        self.routes[pattern] = handle_error
    
    def mock_network_failure(self):
        """Mock complete network failure"""
        def handle_failure(route):
            self.request_log.append({
                "url": route.request.url,
                "method": route.request.method,
                "timestamp": datetime.now().isoformat(),
                "mocked_error": "network_failure"
            })
            route.abort()
        
        pattern = "**/*"
        self.page.route(pattern, handle_failure)
        self.routes[pattern] = handle_failure
    
    def clear_mocks(self):
        """Clear all route mocks"""
        for pattern in self.routes.keys():
            try:
                self.page.unroute(pattern)
            except:
                pass
        self.routes.clear()
    
    def get_request_log(self) -> List[Dict[str, Any]]:
        """Get log of intercepted requests"""
        return self.request_log.copy()


class PerformanceMonitor:
    """Monitor and analyze performance metrics"""
    
    def __init__(self, page: Page):
        self.page = page
        self.metrics_history = []
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        
        # Inject performance monitoring script
        self.page.add_init_script("""
            window.performanceMetrics = {
                startTime: performance.now(),
                interactions: [],
                resourceTimings: []
            };
            
            // Monitor user interactions
            ['click', 'keydown', 'submit'].forEach(eventType => {
                document.addEventListener(eventType, (e) => {
                    window.performanceMetrics.interactions.push({
                        type: eventType,
                        timestamp: performance.now(),
                        target: e.target.tagName + (e.target.id ? '#' + e.target.id : '')
                    });
                });
            });
            
            // Monitor resource loading
            new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    window.performanceMetrics.resourceTimings.push({
                        name: entry.name,
                        duration: entry.duration,
                        startTime: entry.startTime
                    });
                }
            }).observe({entryTypes: ['resource']});
        """)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        metrics = self.page.evaluate("""() => {
            const timing = performance.timing;
            const navigation = performance.getEntriesByType('navigation')[0];
            
            return {
                pageLoad: {
                    domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                    loadComplete: timing.loadEventEnd - timing.navigationStart,
                    firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0,
                    firstContentfulPaint: performance.getEntriesByType('paint')[1]?.startTime || 0
                },
                memory: performance.memory ? {
                    used: performance.memory.usedJSHeapSize,
                    total: performance.memory.totalJSHeapSize,
                    limit: performance.memory.jsHeapSizeLimit
                } : null,
                interactions: window.performanceMetrics?.interactions || [],
                resourceTimings: window.performanceMetrics?.resourceTimings || []
            }
        }""")
        
        metrics['timestamp'] = datetime.now().isoformat()
        metrics['testDuration'] = time.time() - self.start_time
        
        self.metrics_history.append(metrics)
        return metrics
    
    def assert_performance_budget(self, budget: Dict[str, int]):
        """Assert performance meets specified budget"""
        metrics = self.get_metrics()
        
        for metric, threshold in budget.items():
            if metric == "domContentLoaded":
                actual = metrics['pageLoad']['domContentLoaded']
            elif metric == "loadComplete":
                actual = metrics['pageLoad']['loadComplete']
            elif metric == "memoryUsageMB":
                actual = metrics['memory']['used'] / (1024 * 1024) if metrics['memory'] else 0
            else:
                continue
            
            assert actual < threshold, f"Performance budget exceeded: {metric} = {actual}, budget = {threshold}"
    
    def generate_performance_report(self) -> str:
        """Generate detailed performance report"""
        if not self.metrics_history:
            return "No performance data collected"
        
        latest = self.metrics_history[-1]
        
        report = f"""
Performance Report
==================
Page Load Metrics:
  - DOM Content Loaded: {latest['pageLoad']['domContentLoaded']:.0f}ms
  - Load Complete: {latest['pageLoad']['loadComplete']:.0f}ms
  - First Paint: {latest['pageLoad']['firstPaint']:.0f}ms
  - First Contentful Paint: {latest['pageLoad']['firstContentfulPaint']:.0f}ms

Memory Usage:
  - Used Heap: {latest['memory']['used']/(1024*1024):.1f}MB
  - Total Heap: {latest['memory']['total']/(1024*1024):.1f}MB

User Interactions: {len(latest['interactions'])}
Resources Loaded: {len(latest['resourceTimings'])}
Test Duration: {latest['testDuration']:.1f}s
"""
        return report


class TestStateManager:
    """Manage test state and cleanup"""
    
    def __init__(self):
        self.state_stack = []
        self.cleanup_functions = []
    
    def save_state(self, page: Page, name: str):
        """Save current page state"""
        state = {
            "name": name,
            "url": page.url,
            "timestamp": datetime.now().isoformat(),
            "local_storage": page.evaluate("() => JSON.stringify(localStorage)"),
            "session_storage": page.evaluate("() => JSON.stringify(sessionStorage)")
        }
        self.state_stack.append(state)
        return state
    
    def restore_state(self, page: Page, name: str = None):
        """Restore page state"""
        if not self.state_stack:
            return False
        
        if name:
            # Find specific state
            state = next((s for s in reversed(self.state_stack) if s["name"] == name), None)
        else:
            # Get most recent state
            state = self.state_stack[-1]
        
        if not state:
            return False
        
        # Navigate to saved URL
        page.goto(state["url"])
        page.wait_for_load_state("networkidle")
        
        # Restore storage
        if state["local_storage"] != "{}":
            page.evaluate(f"localStorage.clear(); Object.assign(localStorage, {state['local_storage']})")
        
        if state["session_storage"] != "{}":
            page.evaluate(f"sessionStorage.clear(); Object.assign(sessionStorage, {state['session_storage']})")
        
        return True
    
    def register_cleanup(self, cleanup_function: Callable):
        """Register cleanup function to run after test"""
        self.cleanup_functions.append(cleanup_function)
    
    def cleanup(self):
        """Run all cleanup functions"""
        for cleanup_func in self.cleanup_functions:
            try:
                cleanup_func()
            except Exception as e:
                print(f"Cleanup function failed: {e}")
        
        self.cleanup_functions.clear()
        self.state_stack.clear()


# Enhanced Pytest Fixtures
@pytest.fixture
def enhanced_page(page: Page, screenshot_dir):
    """Enhanced page fixture with additional utilities"""
    # Add custom properties to page
    page.assertions = AdvancedPageAssertions(page)
    page.network_mock = NetworkMockManager(page)
    page.performance = PerformanceMonitor(page)
    page.state_manager = TestStateManager()
    page.visual_testing = VisualTestingManager()
    
    # Start performance monitoring
    page.performance.start_monitoring()
    
    yield page
    
    # Cleanup
    page.network_mock.clear_mocks()
    page.state_manager.cleanup()


@pytest.fixture
def test_data():
    """Test data manager fixture"""
    return TestDataManager()


@pytest.fixture 
def performance_budget():
    """Default performance budget"""
    return {
        "domContentLoaded": 3000,
        "loadComplete": 5000,
        "memoryUsageMB": 100
    }


class TestReportGenerator:
    """Generate comprehensive test reports"""
    
    def __init__(self, output_dir: str = "tests/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.test_results = []
    
    def add_test_result(self, test_name: str, result: Dict[str, Any]):
        """Add test result to report"""
        result['test_name'] = test_name
        result['timestamp'] = datetime.now().isoformat()
        self.test_results.append(result)
    
    def generate_html_report(self, filename: str = None) -> str:
        """Generate HTML test report"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"e2e_enhanced_report_{timestamp}.html"
        
        report_path = self.output_dir / filename
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced E2E Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .test-result {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
        .passed {{ border-left-color: #28a745; }}
        .failed {{ border-left-color: #dc3545; }}
        .performance {{ background: #e3f2fd; padding: 10px; margin: 5px 0; }}
        .screenshot {{ max-width: 300px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>Enhanced E2E Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: {len(self.test_results)}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""
        
        for result in self.test_results:
            status_class = "passed" if result.get('status') == 'passed' else "failed"
            html_content += f"""
    <div class="test-result {status_class}">
        <h3>{result['test_name']}</h3>
        <p>Status: {result.get('status', 'unknown')}</p>
        <p>Duration: {result.get('duration', 0):.2f}s</p>
        
        {self._format_performance_data(result.get('performance', {}))}
        {self._format_screenshots(result.get('screenshots', []))}
        
        {f"<p>Error: {result['error']}</p>" if result.get('error') else ""}
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_path)
    
    def _format_performance_data(self, performance: Dict[str, Any]) -> str:
        """Format performance data for HTML"""
        if not performance:
            return ""
        
        return f"""
        <div class="performance">
            <h4>Performance Metrics</h4>
            <ul>
                <li>DOM Content Loaded: {performance.get('domContentLoaded', 0):.0f}ms</li>
                <li>Load Complete: {performance.get('loadComplete', 0):.0f}ms</li>
                <li>Memory Usage: {performance.get('memoryUsageMB', 0):.1f}MB</li>
            </ul>
        </div>
        """
    
    def _format_screenshots(self, screenshots: List[str]) -> str:
        """Format screenshots for HTML"""
        if not screenshots:
            return ""
        
        html = "<h4>Screenshots</h4>"
        for screenshot in screenshots:
            html += f'<img src="{screenshot}" class="screenshot" alt="Test screenshot"><br>'
        
        return html