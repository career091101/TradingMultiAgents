"""
Phase 2 Adapted Test Runner
実際のWebUI構造に適応したPhase 2テストの実行
"""

import subprocess
import sys
import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class Phase2AdaptedTestRunner:
    """適応されたPhase 2テストランナー"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.output_dir = Path("tests/reports/phase2_adapted")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_test_suite(self, 
                      categories: List[str] = None,
                      browser: str = "chromium") -> Dict[str, Any]:
        """適応されたPhase 2テストスイートを実行"""
        
        print("🚀 Starting Phase 2 Adapted E2E Test Suite")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Default categories if none specified
        if not categories:
            categories = ["error_handling", "performance", "security"]
        
        # Test file mapping for adapted tests
        test_files = {
            "error_handling": "test_error_handling_adapted.py",
            "performance": "test_performance_adapted.py",
            "security": "test_security_adapted.py"
        }
        
        # Run each test category
        for category in categories:
            if category not in test_files:
                print(f"⚠️ Unknown category: {category}")
                continue
                
            print(f"\n🔧 Running {category} tests...")
            result = self._run_category(category, test_files[category], browser)
            self.results[category] = result
            
            # Print immediate results
            if result["exit_code"] == 0:
                print(f"✅ {category} tests PASSED")
            else:
                print(f"❌ {category} tests FAILED")
        
        # Generate report
        report_path = self._generate_report()
        print(f"\n📊 Report generated: {report_path}")
        
        total_time = time.time() - self.start_time
        print(f"\n⏱️  Total execution time: {total_time:.1f}s")
        
        return self.results
    
    def _run_category(self, category: str, test_file: str, browser: str) -> Dict[str, Any]:
        """カテゴリ別のテスト実行"""
        
        # Build pytest command
        cmd = [
            "python", "-m", "pytest",
            f"tests/e2e/{test_file}",
            f"--browser={browser}",
            "--screenshot=on",
            f"--html=tests/reports/phase2_adapted/{category}_report.html",
            "--self-contained-html",
            "-v"
        ]
        
        start_time = time.time()
        
        try:
            # Set environment variables
            import os
            env = os.environ.copy()
            env["FINNHUB_API_KEY"] = "test_key_for_testing"
            env["OPENAI_API_KEY"] = "test_key_for_testing"
            
            # Run tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per category
                env=env
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
    
    def _generate_report(self) -> str:
        """包括的なレポート生成"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"phase2_adapted_report_{timestamp}.html"
        
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
    <title>Phase 2 Adapted E2E Test Report - {timestamp}</title>
    <style>
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }}
        .header h1 {{
            color: #667eea;
            margin: 0;
            font-size: 2.5em;
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
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
            font-weight: bold;
        }}
        .summary-card p {{
            margin: 0;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .category-result {{
            margin: 20px 0;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #ccc;
            background: #f9f9f9;
        }}
        .passed {{
            background: linear-gradient(135deg, #d4edda, #c3e6cb);
            border-left-color: #28a745;
        }}
        .failed {{
            background: linear-gradient(135deg, #f8d7da, #f5c6cb);
            border-left-color: #dc3545;
        }}
        .expandable {{
            cursor: pointer;
            user-select: none;
            padding: 10px;
            border-radius: 5px;
            transition: background-color 0.3s;
        }}
        .expandable:hover {{
            background-color: rgba(255,255,255,0.5);
        }}
        .test-output {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 10px;
            border: 1px solid #4a5568;
        }}
        .hidden {{
            display: none;
        }}
        .success-rate {{
            font-size: 1.5em;
            font-weight: bold;
            color: {('#28a745' if passed_categories == total_categories else '#dc3545')};
        }}
        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 10px;
        }}
        .badge-success {{
            background: #28a745;
            color: white;
        }}
        .badge-danger {{
            background: #dc3545;
            color: white;
        }}
        .features {{
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .features h3 {{
            color: #495057;
            margin-top: 0;
        }}
        .features ul {{
            columns: 2;
            column-gap: 30px;
        }}
        .features li {{
            margin: 5px 0;
            break-inside: avoid;
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
            <h1>🧪 Phase 2 Adapted E2E Test Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Adapted for TradingAgents WebUI Structure</p>
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
        
        <div style="text-align: center; margin: 20px 0;">
            <span class="success-rate">{(passed_categories/total_categories)*100:.1f}% Success Rate</span>
        </div>
        
        <div class="features">
            <h3>🎯 Phase 2 Adapted Features</h3>
            <ul>
                <li>✅ Real WebUI structure adaptation</li>
                <li>✅ Error handling validation</li>
                <li>✅ Performance monitoring</li>
                <li>✅ Security testing</li>
                <li>✅ Screenshot documentation</li>
                <li>✅ Streamlit-specific selectors</li>
                <li>✅ Navigation flow testing</li>
                <li>✅ Input validation</li>
            </ul>
        </div>
        
        <h2>📋 Category Results</h2>
"""
        
        for category, result in self.results.items():
            status_class = "passed" if result.get("exit_code") == 0 else "failed"
            status_icon = "✅" if result.get("exit_code") == 0 else "❌"
            badge_class = "badge-success" if result.get("exit_code") == 0 else "badge-danger"
            badge_text = "PASSED" if result.get("exit_code") == 0 else "FAILED"
            
            html_content += f"""
            <div class="category-result {status_class}">
                <div class="expandable" onclick="toggleSection('{category}_details')">
                    <h3>{status_icon} {category.replace('_', ' ').title()}
                        <span class="badge {badge_class}">{badge_text}</span>
                    </h3>
                    <p><strong>Execution Time:</strong> {result.get('execution_time', 0):.1f}s</p>
                    <p><strong>Exit Code:</strong> {result.get('exit_code', 'Unknown')}</p>
                    <small>📄 Click to expand details</small>
                </div>
                
                <div id="{category}_details" class="hidden">
                    <h4>Command Executed:</h4>
                    <div class="test-output">{self._escape_html(result.get('command', 'N/A'))}</div>
                    
                    <h4>Test Output:</h4>
                    <div class="test-output">{self._escape_html(result.get('stdout', 'No output'))}</div>
                    
                    {f'<h4>Errors:</h4><div class="test-output">{self._escape_html(result.get("stderr", ""))}</div>' if result.get('stderr') else ''}
                    {f'<h4>Error Details:</h4><div class="test-output">{self._escape_html(result.get("error", ""))}</div>' if result.get('error') else ''}
                </div>
            </div>
"""
        
        html_content += f"""
        
        <div class="features">
            <h3>🔍 Testing Insights</h3>
            <p>These adapted tests validate the actual WebUI implementation and provide:</p>
            <ul>
                <li><strong>Realistic Error Scenarios:</strong> Network failures, API timeouts, invalid inputs</li>
                <li><strong>Performance Benchmarks:</strong> Page load times, navigation speed, memory usage</li>
                <li><strong>Security Validation:</strong> Input sanitization, API key protection, session security</li>
                <li><strong>UI Compatibility:</strong> Tests work with actual Streamlit components and layout</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 10px;">
            <h3>🚀 Next Steps</h3>
            <p>Phase 2 adaptation complete! Ready for:</p>
            <ul style="list-style: none; padding: 0;">
                <li>📋 Enhanced test coverage</li>
                <li>🔄 CI/CD integration</li>
                <li>📊 Performance optimization</li>
                <li>🛡️ Security hardening</li>
            </ul>
        </div>
        
        <footer style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e9ecef; color: #6c757d; text-align: center;">
            <p><strong>TradingAgents E2E Testing Framework - Phase 2 Adapted</strong></p>
            <p>Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Also generate JSON report
        json_report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_categories": total_categories,
                "passed_categories": passed_categories,
                "failed_categories": total_categories - passed_categories,
                "total_execution_time": total_time,
                "success_rate": (passed_categories / total_categories) * 100 if total_categories > 0 else 0
            },
            "results": self.results
        }
        
        json_path = self.output_dir / f"phase2_adapted_results_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        
        return str(report_path)
    
    def _escape_html(self, text: str) -> str:
        """HTML特殊文字のエスケープ"""
        if not text:
            return ""
        
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(description="Run Phase 2 Adapted E2E Tests")
    parser.add_argument(
        "--categories", 
        nargs="+", 
        choices=["error_handling", "performance", "security"],
        help="Test categories to run"
    )
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Browser to use for testing"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = Phase2AdaptedTestRunner()
    
    # Run tests
    results = runner.run_test_suite(
        categories=args.categories,
        browser=args.browser
    )
    
    # Exit with appropriate code
    failed_categories = [cat for cat, result in results.items() 
                        if result.get("exit_code") != 0]
    
    if failed_categories:
        print(f"\n❌ Failed categories: {', '.join(failed_categories)}")
        sys.exit(1)
    else:
        print("\n✅ All Phase 2 Adapted tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()