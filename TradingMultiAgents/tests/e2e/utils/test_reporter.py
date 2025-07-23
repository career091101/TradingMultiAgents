"""
E2Eテスト用のカスタムレポーター
詳細なテスト結果とスクリーンショットを含むHTMLレポートを生成
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pytest
from _pytest.terminal import TerminalReporter
from playwright.sync_api import Page


class TestReporter:
    """テスト結果を収集し、レポートを生成するクラス"""
    
    def __init__(self, report_dir: str = "reports/e2e"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_results: List[Dict[str, Any]] = []
        self.start_time = datetime.datetime.now()
        self.screenshots: Dict[str, List[str]] = {}
        
    def add_test_result(self, test_data: Dict[str, Any]):
        """テスト結果を追加"""
        self.test_results.append(test_data)
    
    def add_screenshot(self, test_name: str, screenshot_path: str, description: str = ""):
        """スクリーンショットを追加"""
        if test_name not in self.screenshots:
            self.screenshots[test_name] = []
        
        self.screenshots[test_name].append({
            "path": screenshot_path,
            "description": description,
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    def generate_html_report(self, output_file: str = "e2e_test_report.html"):
        """HTMLレポートを生成"""
        output_path = self.report_dir / output_file
        
        # テスト統計を計算
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t["status"] == "passed")
        failed_tests = sum(1 for t in self.test_results if t["status"] == "failed")
        skipped_tests = sum(1 for t in self.test_results if t["status"] == "skipped")
        
        duration = (datetime.datetime.now() - self.start_time).total_seconds()
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradingAgents E2E Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
        }}
        
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .skipped {{ color: #ffc107; }}
        
        .test-results {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .test-result {{
            border-bottom: 1px solid #eee;
            padding: 15px;
        }}
        
        .test-result:last-child {{
            border-bottom: none;
        }}
        
        .test-result.passed {{
            border-left: 4px solid #28a745;
        }}
        
        .test-result.failed {{
            border-left: 4px solid #dc3545;
        }}
        
        .test-result.skipped {{
            border-left: 4px solid #ffc107;
        }}
        
        .test-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .test-name {{
            font-weight: bold;
            font-size: 1.1em;
        }}
        
        .test-status {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .test-status.passed {{
            background: #d4edda;
            color: #155724;
        }}
        
        .test-status.failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .test-status.skipped {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .test-details {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .error-message {{
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
        }}
        
        .screenshots {{
            margin-top: 15px;
        }}
        
        .screenshot {{
            display: inline-block;
            margin: 5px;
        }}
        
        .screenshot img {{
            max-width: 200px;
            border: 1px solid #ddd;
            border-radius: 5px;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        
        .screenshot img:hover {{
            transform: scale(1.05);
        }}
        
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
        }}
        
        .modal-content {{
            position: relative;
            margin: 50px auto;
            max-width: 90%;
            max-height: 80%;
        }}
        
        .modal-content img {{
            width: 100%;
            height: auto;
        }}
        
        .close {{
            position: absolute;
            top: 20px;
            right: 40px;
            color: white;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }}
        
        .filters {{
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .filter-btn:hover {{
            background: #f0f0f0;
        }}
        
        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 TradingAgents E2E Test Report</h1>
        <p>実行日時: {self.start_time.strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        <p>実行時間: {duration:.2f} 秒</p>
    </div>
    
    <div class="summary">
        <div class="summary-card">
            <h3>総テスト数</h3>
            <div class="value">{total_tests}</div>
        </div>
        <div class="summary-card">
            <h3>成功</h3>
            <div class="value passed">{passed_tests}</div>
        </div>
        <div class="summary-card">
            <h3>失敗</h3>
            <div class="value failed">{failed_tests}</div>
        </div>
        <div class="summary-card">
            <h3>スキップ</h3>
            <div class="value skipped">{skipped_tests}</div>
        </div>
        <div class="summary-card">
            <h3>成功率</h3>
            <div class="value">{(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%</div>
        </div>
    </div>
    
    <div class="filters">
        <button class="filter-btn active" onclick="filterTests('all')">すべて</button>
        <button class="filter-btn" onclick="filterTests('passed')">成功</button>
        <button class="filter-btn" onclick="filterTests('failed')">失敗</button>
        <button class="filter-btn" onclick="filterTests('skipped')">スキップ</button>
    </div>
    
    <div class="test-results">
"""
        
        # 各テスト結果を追加
        for test in self.test_results:
            test_name = test.get("name", "Unknown")
            status = test.get("status", "unknown")
            duration = test.get("duration", 0)
            error = test.get("error", "")
            
            html_content += f"""
        <div class="test-result {status}" data-status="{status}">
            <div class="test-header">
                <div class="test-name">{test_name}</div>
                <div>
                    <span class="test-status {status}">{status}</span>
                    <span class="test-details">{duration:.2f}秒</span>
                </div>
            </div>
"""
            
            if error:
                html_content += f"""
            <div class="error-message">{error}</div>
"""
            
            # スクリーンショットを追加
            if test_name in self.screenshots:
                html_content += """
            <div class="screenshots">
                <strong>スクリーンショット:</strong><br>
"""
                for screenshot in self.screenshots[test_name]:
                    html_content += f"""
                <div class="screenshot">
                    <img src="{screenshot['path']}" alt="{screenshot['description']}" 
                         onclick="openModal(this.src)" title="{screenshot['description']}">
                </div>
"""
                html_content += """
            </div>
"""
            
            html_content += """
        </div>
"""
        
        html_content += """
    </div>
    
    <!-- モーダル -->
    <div id="imageModal" class="modal" onclick="closeModal()">
        <span class="close">&times;</span>
        <div class="modal-content">
            <img id="modalImage" src="">
        </div>
    </div>
    
    <script>
        function filterTests(status) {
            const buttons = document.querySelectorAll('.filter-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            const tests = document.querySelectorAll('.test-result');
            tests.forEach(test => {
                if (status === 'all' || test.dataset.status === status) {
                    test.style.display = 'block';
                } else {
                    test.style.display = 'none';
                }
            });
        }
        
        function openModal(src) {
            document.getElementById('imageModal').style.display = 'block';
            document.getElementById('modalImage').src = src;
        }
        
        function closeModal() {
            document.getElementById('imageModal').style.display = 'none';
        }
    </script>
</body>
</html>
"""
        
        # HTMLファイルを保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n📊 テストレポートを生成しました: {output_path}")
        
        # JSON形式のレポートも生成
        json_path = self.report_dir / "test_results.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "start_time": self.start_time.isoformat(),
                "duration": duration,
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "skipped": skipped_tests
                },
                "tests": self.test_results,
                "screenshots": self.screenshots
            }, f, ensure_ascii=False, indent=2)


# Pytest フック
def pytest_configure(config):
    """pytest 設定時に呼ばれる"""
    config._test_reporter = TestReporter()


def pytest_runtest_logreport(report):
    """各テストの結果を記録"""
    if report.when == "call":
        reporter = pytest.config._test_reporter
        
        test_data = {
            "name": report.nodeid,
            "status": report.outcome,
            "duration": report.duration,
        }
        
        if report.failed:
            test_data["error"] = str(report.longrepr)
        
        reporter.add_test_result(test_data)


@pytest.fixture
def test_reporter():
    """テストレポーターを提供するフィクスチャ"""
    return pytest.config._test_reporter


@pytest.fixture
def enhanced_screenshot(page: Page, test_reporter, request):
    """拡張スクリーンショット機能を提供するフィクスチャ"""
    def take_screenshot(name: str, full_page: bool = True, description: str = ""):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{request.node.name}_{name}_{timestamp}.png"
        filepath = test_reporter.report_dir / "screenshots" / filename
        filepath.parent.mkdir(exist_ok=True)
        
        # スクリーンショットを撮影
        page.screenshot(path=str(filepath), full_page=full_page)
        
        # レポーターに記録
        test_reporter.add_screenshot(
            request.node.name,
            f"screenshots/{filename}",
            description or name
        )
        
        return str(filepath)
    
    return take_screenshot