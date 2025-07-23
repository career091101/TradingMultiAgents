"""
E2Eテスト用の高度なエラーハンドリングとレポート機能
詳細な診断情報とトラブルシューティングガイドを提供
"""

import traceback
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from playwright.sync_api import Page, Error as PlaywrightError
import re


class ErrorCategory:
    """エラーカテゴリの定義"""
    ELEMENT_NOT_FOUND = "element_not_found"
    TIMEOUT = "timeout"
    NETWORK = "network"
    ASSERTION = "assertion"
    STALE_ELEMENT = "stale_element"
    JAVASCRIPT = "javascript"
    AUTHENTICATION = "authentication"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class ErrorAnalyzer:
    """エラーを分析し、カテゴリ分類と解決策を提供"""
    
    # エラーパターンとカテゴリのマッピング
    ERROR_PATTERNS = {
        ErrorCategory.ELEMENT_NOT_FOUND: [
            r"element not found",
            r"no element matches selector",
            r"waiting for selector",
            r"locator.*not found"
        ],
        ErrorCategory.TIMEOUT: [
            r"timeout.*exceeded",
            r"waiting for.*timeout",
            r"timed out after",
            r"TimeoutError"
        ],
        ErrorCategory.NETWORK: [
            r"net::ERR_",
            r"failed to fetch",
            r"network error",
            r"connection refused"
        ],
        ErrorCategory.STALE_ELEMENT: [
            r"stale element",
            r"element is not attached",
            r"detached from.*DOM"
        ],
        ErrorCategory.JAVASCRIPT: [
            r"javascript error",
            r"uncaught.*exception",
            r"ReferenceError",
            r"TypeError"
        ],
        ErrorCategory.AUTHENTICATION: [
            r"401|403",
            r"unauthorized",
            r"forbidden",
            r"authentication.*failed"
        ],
        ErrorCategory.ASSERTION: [
            r"AssertionError",
            r"assert.*failed",
            r"expected.*but.*got"
        ]
    }
    
    # カテゴリ別の解決策
    SOLUTIONS = {
        ErrorCategory.ELEMENT_NOT_FOUND: [
            "セレクタが正しいか確認してください",
            "要素が動的に生成される場合は、適切な待機処理を追加してください",
            "ページが完全に読み込まれているか確認してください",
            "開発者ツールで実際のDOM構造を確認してください"
        ],
        ErrorCategory.TIMEOUT: [
            "タイムアウト時間を延長してください",
            "ネットワーク接続を確認してください",
            "サーバーの応答時間を確認してください",
            "page.wait_for_load_state('networkidle')を使用してください"
        ],
        ErrorCategory.NETWORK: [
            "インターネット接続を確認してください",
            "VPNやプロキシの設定を確認してください",
            "サーバーが起動しているか確認してください",
            "正しいURLを使用しているか確認してください"
        ],
        ErrorCategory.STALE_ELEMENT: [
            "要素を再取得してください",
            "RetryHandler.retry_on_stale_element()デコレーターを使用してください",
            "要素が更新される前に操作を完了してください",
            "page.wait_for_selector()で要素の安定を待ってください"
        ],
        ErrorCategory.JAVASCRIPT: [
            "ブラウザコンソールでJSエラーを確認してください",
            "page.on('pageerror')でエラーをキャプチャしてください",
            "JavaScriptが無効化されていないか確認してください",
            "必要な依存関係が読み込まれているか確認してください"
        ],
        ErrorCategory.AUTHENTICATION: [
            "APIキーや認証情報が正しく設定されているか確認してください",
            "環境変数が正しく読み込まれているか確認してください",
            "認証トークンの有効期限を確認してください",
            "必要な権限があるか確認してください"
        ],
        ErrorCategory.ASSERTION: [
            "期待値と実際の値を詳細に比較してください",
            "テストデータが最新か確認してください",
            "非同期処理が完了してから検証してください",
            "要素の状態（visible, enabled等）を確認してください"
        ]
    }
    
    @classmethod
    def categorize_error(cls, error: Exception) -> str:
        """エラーをカテゴリに分類"""
        error_message = str(error).lower()
        
        for category, patterns in cls.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_message, re.IGNORECASE):
                    return category
        
        return ErrorCategory.UNKNOWN
    
    @classmethod
    def get_solutions(cls, category: str) -> List[str]:
        """カテゴリに応じた解決策を取得"""
        return cls.SOLUTIONS.get(category, ["エラーの詳細を確認し、適切な対処を行ってください"])
    
    @classmethod
    def analyze_error(cls, error: Exception) -> Dict[str, Any]:
        """エラーを詳細に分析"""
        category = cls.categorize_error(error)
        solutions = cls.get_solutions(category)
        
        return {
            "category": category,
            "type": type(error).__name__,
            "message": str(error),
            "solutions": solutions,
            "stacktrace": traceback.format_exc()
        }


class EnhancedErrorReporter:
    """拡張エラーレポート機能"""
    
    def __init__(self, report_dir: str = "reports/e2e/errors"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.errors: List[Dict[str, Any]] = []
    
    def capture_error(self, 
                     error: Exception,
                     test_name: str,
                     page: Optional[Page] = None,
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """エラー情報をキャプチャ"""
        
        # エラー分析
        error_analysis = ErrorAnalyzer.analyze_error(error)
        
        # 基本エラー情報
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "error": error_analysis,
            "context": context or {},
            "environment": {
                "python_version": os.sys.version,
                "platform": os.sys.platform,
                "cwd": os.getcwd()
            }
        }
        
        # ページ情報を追加
        if page:
            try:
                error_info["page_info"] = {
                    "url": page.url,
                    "title": page.title(),
                    "viewport": page.viewport_size,
                    "console_messages": []
                }
                
                # コンソールメッセージを収集
                page.on("console", lambda msg: error_info["page_info"]["console_messages"].append({
                    "type": msg.type,
                    "text": msg.text,
                    "location": msg.location
                }))
                
                # スクリーンショットを撮影
                screenshot_path = self.capture_screenshot(page, test_name, "error")
                if screenshot_path:
                    error_info["screenshot"] = str(screenshot_path)
                
                # HTMLソースを保存
                html_path = self.save_html_source(page, test_name)
                if html_path:
                    error_info["html_source"] = str(html_path)
                
                # ネットワークログを取得
                error_info["network_info"] = self.get_network_info(page)
                
            except Exception as e:
                error_info["page_capture_error"] = str(e)
        
        # エラーをリストに追加
        self.errors.append(error_info)
        
        # 個別のエラーファイルを保存
        self.save_error_report(error_info, test_name)
        
        return error_info
    
    def capture_screenshot(self, page: Page, test_name: str, suffix: str = "") -> Optional[Path]:
        """エラー時のスクリーンショットを撮影"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{test_name}_{suffix}_{timestamp}.png"
            filepath = self.report_dir / "screenshots" / filename
            filepath.parent.mkdir(exist_ok=True)
            
            page.screenshot(path=str(filepath), full_page=True)
            
            # ビューポートのスクリーンショットも撮影
            viewport_path = filepath.with_stem(f"{filepath.stem}_viewport")
            page.screenshot(path=str(viewport_path), full_page=False)
            
            return filepath
            
        except Exception as e:
            print(f"スクリーンショット撮影エラー: {e}")
            return None
    
    def save_html_source(self, page: Page, test_name: str) -> Optional[Path]:
        """ページのHTMLソースを保存"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{test_name}_source_{timestamp}.html"
            filepath = self.report_dir / "html" / filename
            filepath.parent.mkdir(exist_ok=True)
            
            html_content = page.content()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return filepath
            
        except Exception as e:
            print(f"HTMLソース保存エラー: {e}")
            return None
    
    def get_network_info(self, page: Page) -> Dict[str, Any]:
        """ネットワーク情報を取得"""
        try:
            # ネットワークリクエストの情報を収集
            network_info = {
                "failed_requests": [],
                "slow_requests": [],
                "console_errors": []
            }
            
            # JavaScriptでネットワーク情報を取得
            network_data = page.evaluate("""
                () => {
                    const entries = performance.getEntriesByType('resource');
                    return entries.map(entry => ({
                        name: entry.name,
                        duration: entry.duration,
                        size: entry.transferSize,
                        status: entry.responseStatus
                    }));
                }
            """)
            
            # 遅いリクエストを特定
            for entry in network_data:
                if entry.get('duration', 0) > 1000:  # 1秒以上
                    network_info["slow_requests"].append(entry)
            
            return network_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def save_error_report(self, error_info: Dict[str, Any], test_name: str):
        """個別のエラーレポートを保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_name}_error_{timestamp}.json"
        filepath = self.report_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, ensure_ascii=False, indent=2)
    
    def generate_summary_report(self) -> Path:
        """エラーサマリーレポートを生成"""
        # エラーをカテゴリ別に集計
        category_summary = {}
        for error in self.errors:
            category = error["error"]["category"]
            if category not in category_summary:
                category_summary[category] = []
            category_summary[category].append(error)
        
        # HTMLレポートを生成
        html_content = self._generate_html_report(category_summary)
        
        # レポートを保存
        report_path = self.report_dir / "error_summary.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path
    
    def _generate_html_report(self, category_summary: Dict[str, List[Dict]]) -> str:
        """HTMLエラーレポートを生成"""
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E2E Test Error Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: #dc3545;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .category {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .category-title {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #dc3545;
        }}
        .error-item {{
            border-left: 4px solid #dc3545;
            padding-left: 15px;
            margin-bottom: 15px;
        }}
        .error-message {{
            font-family: monospace;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            white-space: pre-wrap;
            word-break: break-all;
        }}
        .solutions {{
            background: #e7f3ff;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }}
        .solution-item {{
            margin: 5px 0;
            padding-left: 20px;
            position: relative;
        }}
        .solution-item:before {{
            content: "💡";
            position: absolute;
            left: 0;
        }}
        .screenshot {{
            margin-top: 10px;
        }}
        .screenshot img {{
            max-width: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
        }}
        .stacktrace {{
            font-family: monospace;
            font-size: 0.85em;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            max-height: 200px;
            overflow-y: auto;
            margin-top: 10px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #dc3545;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 E2E Test Error Report</h1>
        <p>生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        <p>総エラー数: {len(self.errors)}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{len(self.errors)}</div>
            <div class="stat-label">総エラー数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(category_summary)}</div>
            <div class="stat-label">カテゴリ数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(set(e['test_name'] for e in self.errors))}</div>
            <div class="stat-label">影響テスト数</div>
        </div>
    </div>
"""
        
        # カテゴリ別のエラー表示
        for category, errors in category_summary.items():
            html += f"""
    <div class="category">
        <div class="category-title">
            {category.replace('_', ' ').title()} ({len(errors)}件)
        </div>
"""
            
            for error in errors[:5]:  # 各カテゴリ最大5件表示
                html += f"""
        <div class="error-item">
            <strong>テスト:</strong> {error['test_name']}<br>
            <strong>時刻:</strong> {error['timestamp']}<br>
            <strong>エラータイプ:</strong> {error['error']['type']}<br>
            
            <div class="error-message">{error['error']['message']}</div>
            
            <div class="solutions">
                <strong>推奨される解決策:</strong>
"""
                for solution in error['error']['solutions']:
                    html += f'<div class="solution-item">{solution}</div>'
                
                html += "</div>"
                
                if 'screenshot' in error:
                    html += f"""
            <div class="screenshot">
                <strong>スクリーンショット:</strong><br>
                <img src="{error['screenshot']}" onclick="window.open(this.src)">
            </div>
"""
                
                html += """
            <details>
                <summary>スタックトレース</summary>
                <div class="stacktrace">{}</div>
            </details>
        </div>
""".format(error['error'].get('stacktrace', 'N/A'))
            
            html += "</div>"
        
        html += """
</body>
</html>
"""
        
        return html


# カスタム例外クラス
class TestConfigurationError(Exception):
    """テスト設定エラー"""
    pass


class ElementNotFoundError(Exception):
    """要素が見つからないエラー"""
    pass


class TestDataError(Exception):
    """テストデータエラー"""
    pass


# エラーコンテキストマネージャー
class ErrorContext:
    """エラーコンテキストを管理"""
    
    def __init__(self, reporter: EnhancedErrorReporter, test_name: str, page: Optional[Page] = None):
        self.reporter = reporter
        self.test_name = test_name
        self.page = page
        self.context = {}
    
    def add_context(self, key: str, value: Any):
        """コンテキスト情報を追加"""
        self.context[key] = value
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.reporter.capture_error(
                error=exc_val,
                test_name=self.test_name,
                page=self.page,
                context=self.context
            )
        return False  # 例外を再発生させる