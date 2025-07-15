"""
E2Eテスト用の共通フィクスチャと設定
拡張版: リトライ、レポート、設定管理を統合
"""

import pytest
import subprocess
import time
import os
import signal
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import json
import datetime
from typing import Dict, Any, Generator
import requests

# カスタムモジュール
from config import get_test_config
from utils.retry_handler import RetryHandler, SmartWait
from utils.path_compat import safe_relative_to
from utils.test_reporter import TestReporter
from utils.error_handler import EnhancedErrorReporter, ErrorContext
from utils.screenshot_manager import ScreenshotManager
from utils.custom_assertions import CustomAssertions

# テスト設定を取得
config = get_test_config()

# ディレクトリの作成
SCREENSHOT_DIR = Path(config.screenshot_dir)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

if config.video_on_failure:
    VIDEO_DIR = Path(config.video_dir)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# グローバルなレポーターとマネージャー
test_reporter = TestReporter(config.report_dir)
error_reporter = EnhancedErrorReporter()
screenshot_manager = ScreenshotManager()


@pytest.fixture(scope="session")
def webui_server():
    """WebUIサーバーを起動するフィクスチャ（改善版）"""
    print("🚀 WebUIサーバーを起動中...")
    
    # すでに起動しているか確認
    try:
        response = requests.get(config.base_url, timeout=1)
        if response.status_code == 200:
            print("ℹ️ WebUIサーバーはすでに起動しています")
            yield None
            return
    except:
        pass
    
    # サーバープロセスを起動
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    
    process = subprocess.Popen(
        ["streamlit", "run", "webui/app.py", "--server.port", str(config.webui_port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        preexec_fn=os.setsid if os.name != 'nt' else None
    )
    
    # サーバーの起動を待機（リトライ付き）
    @RetryHandler.retry(max_attempts=config.webui_startup_timeout, delay=1)
    def wait_for_server():
        response = requests.get(config.base_url, timeout=1)
        if response.status_code != 200:
            raise RuntimeError("サーバーが応答しません")
    
    try:
        wait_for_server()
        print(f"✅ WebUIサーバーが起動しました (PID: {process.pid})")
    except Exception as e:
        process.terminate()
        raise RuntimeError(f"WebUIサーバーの起動に失敗: {e}")
    
    yield process
    
    # クリーンアップ
    print("🛑 WebUIサーバーを停止中...")
    if process:
        if os.name == 'nt':
            process.terminate()
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        
        process.wait(timeout=5)


@pytest.fixture(scope="session")
def browser_context_args():
    """ブラウザコンテキストの設定を提供"""
    return config.get_browser_context_args()


@pytest.fixture(scope="session")
def browser():
    """Playwrightのブラウザインスタンスを提供"""
    with sync_playwright() as p:
        # ブラウザの選択
        if config.browser == "firefox":
            browser = p.firefox.launch(headless=config.headless)
        elif config.browser == "webkit":
            browser = p.webkit.launch(headless=config.headless)
        else:
            browser = p.chromium.launch(headless=config.headless)
        
        yield browser
        browser.close()


@pytest.fixture
def context(browser: Browser, browser_context_args: dict, request) -> Generator[BrowserContext, None, None]:
    """ブラウザコンテキストを作成（拡張版）"""
    # ビデオ録画の設定（失敗時のみ）
    if config.video_on_failure:
        video_path = VIDEO_DIR / f"{request.node.name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        browser_context_args["record_video_dir"] = str(video_path)
    
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext, webui_server, request) -> Generator[Page, None, None]:
    """Playwrightのページオブジェクトを提供するフィクスチャ（拡張版）"""
    page = context.new_page()
    
    # ページ読み込みのリトライ
    @RetryHandler.retry(max_attempts=3, delay=2)
    def goto_with_retry():
        page.goto(config.base_url)
        page.wait_for_load_state("networkidle")
    
    goto_with_retry()
    
    # テスト実行
    yield page
    
    # 失敗時のスクリーンショット
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed and config.screenshot_on_failure:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_name = f"failure_{request.node.name}_{timestamp}.png"
        screenshot_path = SCREENSHOT_DIR / screenshot_name
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n💾 失敗時のスクリーンショット: {screenshot_path}")
        
        # レポーターに追加
        try:
            # report_dirが存在しない場合は作成
            report_base = Path(config.report_dir)
            if not report_base.exists():
                report_base.mkdir(parents=True, exist_ok=True)
            
            # スクリーンショットパスを適切に処理
            relative_path = safe_relative_to(screenshot_path, report_base.parent)
            
            test_reporter.add_screenshot(
                request.node.name,
                relative_path,
                "テスト失敗時のスクリーンショット"
            )
        except Exception as e:
            print(f"⚠️ スクリーンショットレポート記録エラー: {e}")
    
    # クリーンアップ
    page.close()


@pytest.fixture
def screenshot_path(page, request):
    """スクリーンショットのパスを生成するフィクスチャ（拡張版）"""
    def _screenshot_path(name, full_page=True, description=""):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{request.node.name}_{name}_{timestamp}.png"
        filepath = SCREENSHOT_DIR / filename
        
        # スクリーンショットを撮影
        page.screenshot(path=str(filepath), full_page=full_page)
        
        # レポーターに記録
        try:
            report_base = Path(config.report_dir)
            if not report_base.exists():
                report_base.mkdir(parents=True, exist_ok=True)
            
            relative_path = safe_relative_to(filepath, report_base.parent)
            
            test_reporter.add_screenshot(
                request.node.name,
                relative_path,
                description or name
            )
        except Exception as e:
            print(f"⚠️ スクリーンショットレポート記録エラー: {e}")
        
        return str(filepath)
    
    return _screenshot_path


@pytest.fixture
def test_data():
    """テストデータを提供するフィクスチャ"""
    test_data_path = config.get_test_data_path("test_data.json")
    
    if test_data_path.exists():
        with open(test_data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # デフォルトのテストデータ
        return {
            "test_tickers": ["AAPL", "MSFT", "GOOGL"],
            "api_keys": {
                "finnhub": "test_finnhub_key",
                "openai": "test_openai_key"
            },
            "models": {
                "deep_thinking": ["o3-2025-04-16", "o3", "DeepResearch (o3)"],
                "fast_thinking": ["gpt-4o-mini", "claude-3-haiku"]
            },
            "popular_stocks": [
                {"symbol": "NVDA", "name": "NVIDIA"},
                {"symbol": "TSLA", "name": "Tesla"},
                {"symbol": "AAPL", "name": "Apple"}
            ]
        }


# Pytest フック関数

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """テスト結果をitemに保存"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


def pytest_runtest_logreport(report):
    """テスト結果をレポーターに記録"""
    if report.when == "call":
        test_data = {
            "name": report.nodeid,
            "status": report.outcome,
            "duration": report.duration,
        }
        
        if report.failed:
            test_data["error"] = str(report.longrepr)
        
        test_reporter.add_test_result(test_data)


def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時にレポートを生成"""
    if config.generate_html_report:
        test_reporter.generate_html_report()
    
    # エラーレポートも生成
    if error_reporter.errors:
        error_report_path = error_reporter.generate_summary_report()
        print(f"\n🚨 エラーレポート: {error_report_path}")
    
    # スクリーンショットギャラリーを生成
    for category in ["actual", "error", "debug"]:
        try:
            gallery_path = screenshot_manager.generate_gallery(category)
            print(f"\n🖼️ {category}ギャラリー: {gallery_path}")
        except:
            pass


def pytest_configure(config):
    """Pytest設定のカスタマイズ"""
    # カスタムマーカーの登録
    config.addinivalue_line("markers", "smoke: 基本的な動作確認テスト（高速）")
    config.addinivalue_line("markers", "slow: 時間のかかるテスト（分析実行など）")
    config.addinivalue_line("markers", "visual: ビジュアルレグレッションテスト")
    config.addinivalue_line("markers", "critical: クリティカルパステスト")
    config.addinivalue_line("markers", "flaky: フレーキーなテスト（自動リトライ）")
    # Phase 2 マーカー
    config.addinivalue_line("markers", "error_handling: エラーハンドリングテスト")
    config.addinivalue_line("markers", "security: セキュリティテスト")
    config.addinivalue_line("markers", "performance: パフォーマンステスト")
    config.addinivalue_line("markers", "accessibility: アクセシビリティテスト")
    config.addinivalue_line("markers", "network: ネットワーク依存テスト")
    config.addinivalue_line("markers", "api: API連携テスト")


# 追加のフィクスチャ

@pytest.fixture
def smart_wait():
    """インテリジェントな待機機能を提供"""
    return SmartWait


@pytest.fixture
def retry_handler():
    """リトライハンドラーを提供"""
    return RetryHandler


@pytest.fixture(autouse=True)
def test_info(request):
    """各テストの情報を記録"""
    test_start = time.time()
    
    yield
    
    # テスト実行時間を記録
    duration = time.time() - test_start
    print(f"\n⏱️ テスト実行時間: {duration:.2f}秒")


@pytest.fixture
def mobile_page(browser: Browser, webui_server) -> Generator[Page, None, None]:
    """モバイル用ページを作成"""
    context = browser.new_context(
        viewport={"width": 375, "height": 812},
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
        has_touch=True,
        is_mobile=True,
    )
    page = context.new_page()
    page.goto(config.base_url)
    yield page
    context.close()


@pytest.fixture
def error_context(request, page):
    """エラーコンテキストを提供するフィクスチャ"""
    def _error_context(**kwargs):
        return ErrorContext(
            reporter=error_reporter,
            test_name=request.node.name,
            page=page,
            **kwargs
        )
    return _error_context


@pytest.fixture
def custom_assertions(page):
    """カスタムアサーションを提供するフィクスチャ"""
    return CustomAssertions(page)


@pytest.fixture
def enhanced_screenshot(page, request):
    """拡張スクリーンショット機能を提供するフィクスチャ"""
    def _capture(**kwargs):
        return screenshot_manager.capture(
            page=page,
            name=kwargs.get('name', request.node.name),
            **kwargs
        )
    return _capture


@pytest.fixture
def screenshot_dir(request):
    """スクリーンショットディレクトリを提供するフィクスチャ"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    test_name = request.node.name
    dir_path = SCREENSHOT_DIR / f"{test_name}_{timestamp}"
    dir_path.mkdir(parents=True, exist_ok=True)
    return str(dir_path)