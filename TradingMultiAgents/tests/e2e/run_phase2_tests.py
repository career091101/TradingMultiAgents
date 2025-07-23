"""
Phase 2 E2E Test Runner
Orchestrates advanced testing scenarios with comprehensive reporting
"""

import subprocess
import sys
import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import shutil

from config.phase2_config import Phase2TestConfig, TEST_CATEGORIES


class Phase2TestRunner:
    """Advanced test runner for Phase 2 E2E tests"""
    
    def __init__(self, config_env: str = "local"):
        self.config = Phase2TestConfig.get_config(config_env)
        self.results = {}
        self.start_time = None
        self.output_dir = Path("tests/reports/phase2")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_test_suite(self, 
                      categories: List[str] = None,
                      parallel: bool = True,
                      generate_report: bool = True,
                      browser: str = "chromium") -> Dict[str, Any]:
        """Run Phase 2 test suite"""
        
        print("🚀 Starting Phase 2 E2E Test Suite")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Default categories if none specified
        if not categories:
            categories = ["error_handling", "security", "performance", "advanced_scenarios"]
        
        # Run each test category
        for category in categories:
            print(f"\n🔧 Running {category} tests...")
            result = self._run_category(category, browser, parallel)
            self.results[category] = result
            
            # Print immediate results
            if result["exit_code"] == 0:
                print(f"✅ {category} tests PASSED")
            else:
                print(f"❌ {category} tests FAILED")
        
        # Generate comprehensive report
        if generate_report:
            report_path = self._generate_final_report()
            print(f"\n📊 Report generated: {report_path}")
        
        total_time = time.time() - self.start_time
        print(f"\n⏱️  Total execution time: {total_time:.1f}s")
        
        return self.results
    
    def _run_category(self, category: str, browser: str, parallel: bool) -> Dict[str, Any]:
        """Run tests for a specific category"""
        
        test_files = {
            "error_handling": "test_error_handling.py",
            "security": "test_security.py", 
            "performance": "test_performance.py",
            "advanced_scenarios": "test_advanced_scenarios.py"
        }
        
        if category not in test_files:
            return {"exit_code": 1, "error": f"Unknown category: {category}"}
        
        test_file = test_files[category]
        
        # Build pytest command
        cmd = [
            "python", "-m", "pytest",
            f"tests/e2e/{test_file}",
            f"--browser={browser}",
            "--screenshot=on",
            f"--html=tests/reports/phase2/{category}_report.html",
            "--self-contained-html",
            "-v"
        ]
        
        # Add parallel execution
        if parallel and category != "performance":  # Performance tests should run sequentially
            cmd.extend(["-n", "2"])
        
        # Add category-specific options
        category_config = TEST_CATEGORIES.get(category, {})
        if category_config.get("retry_count", 0) > 0:
            cmd.extend(["--maxfail", str(category_config["retry_count"])])
        
        # Add markers
        cmd.extend(["-m", category])
        
        start_time = time.time()
        
        try:
            # Run tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout per category
            )
            
            execution_time = time.time() - start_time
            
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": execution_time,
                "command": " ".join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "exit_code": 1,
                "error": "Test execution timed out",
                "execution_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "exit_code": 1,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def _generate_final_report(self) -> str:
        """Generate comprehensive Phase 2 test report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"phase2_comprehensive_report_{timestamp}.html"
        
        # Calculate summary statistics
        total_categories = len(self.results)
        passed_categories = sum(1 for r in self.results.values() if r.get("exit_code") == 0)
        total_time = sum(r.get("execution_time", 0) for r in self.results.values())
        
        # Generate HTML report
        html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phase 2 E2E Test Report - {timestamp}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 2em;
        }}
        .category-result {{
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #ccc;
        }}
        .passed {{
            background-color: #d4edda;
            border-left-color: #28a745;
        }}
        .failed {{
            background-color: #f8d7da;
            border-left-color: #dc3545;
        }}
        .test-output {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 10px;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .section {{
            margin: 30px 0;
        }}
        .expandable {{
            cursor: pointer;
            user-select: none;
        }}
        .expandable:hover {{
            background-color: #f8f9fa;
        }}
        .hidden {{
            display: none;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
            transition: width 0.3s ease;
        }}
    </style>
    <script>
        function toggleSection(id) {{
            const element = document.getElementById(id);
            element.classList.toggle('hidden');
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Phase 2 E2E Test Report</h1>
            <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>{total_categories}</h3>
                <p>Test Categories</p>
            </div>
            <div class="summary-card">
                <h3>{passed_categories}</h3>
                <p>Passed</p>
            </div>
            <div class="summary-card">
                <h3>{total_categories - passed_categories}</h3>
                <p>Failed</p>
            </div>
            <div class="summary-card">
                <h3>{total_time:.1f}s</h3>
                <p>Total Time</p>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {(passed_categories/total_categories)*100:.1f}%"></div>
        </div>
        
        <div class="section">
            <h2>📋 Test Categories Results</h2>
"""
        
        for category, result in self.results.items():
            status_class = "passed" if result.get("exit_code") == 0 else "failed"
            status_icon = "✅" if result.get("exit_code") == 0 else "❌"
            
            html_content += f"""
            <div class="category-result {status_class}">
                <div class="expandable" onclick="toggleSection('{category}_details')">
                    <h3>{status_icon} {category.replace('_', ' ').title()}</h3>
                    <p>Execution Time: {result.get('execution_time', 0):.1f}s</p>
                    <p>Exit Code: {result.get('exit_code', 'Unknown')}</p>
                    <small>Click to expand details</small>
                </div>
                
                <div id="{category}_details" class="hidden">
                    <h4>Command Executed:</h4>
                    <div class="test-output">{result.get('command', 'N/A')}</div>
                    
                    <h4>Standard Output:</h4>
                    <div class="test-output">{self._escape_html(result.get('stdout', 'No output'))}</div>
                    
                    {f'<h4>Errors:</h4><div class="test-output">{self._escape_html(result.get("stderr", ""))}</div>' if result.get('stderr') else ''}
                    {f'<h4>Error Details:</h4><div class="test-output">{self._escape_html(result.get("error", ""))}</div>' if result.get('error') else ''}
                </div>
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="section">
            <h2>📊 Phase 2 Testing Overview</h2>
            <p>This Phase 2 testing focused on advanced scenarios including:</p>
            <ul>
                <li><strong>Error Handling:</strong> Network failures, API timeouts, rate limiting</li>
                <li><strong>Security Testing:</strong> XSS prevention, input validation, API key protection</li>
                <li><strong>Performance Testing:</strong> Load times, memory usage, concurrent access</li>
                <li><strong>Advanced Scenarios:</strong> Complex workflows, edge cases, accessibility</li>
            </ul>
            
            <h3>🎯 Test Coverage Achieved</h3>
            <ul>
                <li>Comprehensive error scenarios (TC014-TC015)</li>
                <li>Security vulnerability testing (TC018-TC019)</li>
                <li>Performance benchmarking (TC016-TC017)</li>
                <li>Edge case validation</li>
                <li>Accessibility compliance</li>
                <li>Cross-browser compatibility</li>
                <li>Mobile responsiveness</li>
            </ul>
            
            <h3>🔍 Key Improvements from Phase 2</h3>
            <ul>
                <li>Enhanced error handling and user feedback</li>
                <li>Robust security measures implementation</li>
                <li>Performance optimization validation</li>
                <li>Comprehensive test utilities and helpers</li>
                <li>Advanced test reporting and analytics</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>📈 Next Steps</h2>
            <p>Based on Phase 2 results, consider:</p>
            <ul>
                <li>Address any failed test categories</li>
                <li>Implement CI/CD integration (Phase 3)</li>
                <li>Expand visual regression testing</li>
                <li>Add API integration tests</li>
                <li>Enhance performance monitoring</li>
            </ul>
        </div>
        
        <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #6c757d; text-align: center;">
            <p>TradingAgents E2E Testing Framework - Phase 2</p>
            <p>Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Also generate JSON report for programmatic access
        json_report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_categories": total_categories,
                "passed_categories": passed_categories,
                "failed_categories": total_categories - passed_categories,
                "total_execution_time": total_time,
                "success_rate": (passed_categories / total_categories) * 100 if total_categories > 0 else 0
            },
            "results": self.results,
            "config": self.config
        }
        
        json_path = self.output_dir / f"phase2_results_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        
        return str(report_path)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return ""
        
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run Phase 2 E2E Tests")
    parser.add_argument(
        "--categories", 
        nargs="+", 
        choices=["error_handling", "security", "performance", "advanced_scenarios"],
        help="Test categories to run"
    )
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Browser to use for testing"
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run tests sequentially instead of in parallel"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating the final report"
    )
    parser.add_argument(
        "--environment",
        choices=["local", "ci", "staging", "production"],
        default="local",
        help="Test environment configuration"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = Phase2TestRunner(config_env=args.environment)
    
    # Run tests
    results = runner.run_test_suite(
        categories=args.categories,
        parallel=not args.sequential,
        generate_report=not args.no_report,
        browser=args.browser
    )
    
    # Exit with appropriate code
    failed_categories = [cat for cat, result in results.items() 
                        if result.get("exit_code") != 0]
    
    if failed_categories:
        print(f"\n❌ Failed categories: {', '.join(failed_categories)}")
        sys.exit(1)
    else:
        print("\n✅ All Phase 2 tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()