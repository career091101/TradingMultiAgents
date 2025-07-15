"""
E2Eテスト用のPytest設定とフィクスチャ
"""

import pytest
import os
import json
from datetime import datetime
from playwright.sync_api import Browser, BrowserContext, Page
import subprocess
import time
from typing import Generator

# テスト設定
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8501")
SCREENSHOTS_DIR = "tests/screenshots"
REPORTS_DIR = "tests/reports"


@pytest.fixture(scope="session")
def webui_server():
    """WebUIサーバーを起動"""
    print("🚀 WebUIサーバーを起動中...")
    process = subprocess.Popen(
        ["python", "run_webui.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # サーバー起動を待機
    time.sleep(8)
    
    yield process
    
    # テスト終了後にサーバーを停止
    print("🛑 WebUIサーバーを停止中...")
    process.terminate()
    process.wait()


@pytest.fixture(scope="session")
def browser_context_args():
    """ブラウザコンテキストの設定"""
    return {
        "viewport": {"width": 1920, "height": 1080},
        "locale": "ja-JP",
        "timezone_id": "Asia/Tokyo",
        "record_video_dir": "tests/videos" if os.getenv("RECORD_VIDEO") else None,
    }


@pytest.fixture
def context(browser: Browser, browser_context_args: dict) -> Generator[BrowserContext, None, None]:
    """ブラウザコンテキストを作成"""
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext, webui_server) -> Generator[Page, None, None]:
    """新しいページを作成"""
    page = context.new_page()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    yield page
    page.close()


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
    page.goto(BASE_URL)
    yield page
    context.close()


@pytest.fixture
def screenshot_path(request):
    """スクリーンショットのパスを生成"""
    test_name = request.node.name.replace("[", "_").replace("]", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _path(name: str) -> str:
        dir_path = f"{SCREENSHOTS_DIR}/{test_name}_{timestamp}"
        os.makedirs(dir_path, exist_ok=True)
        return f"{dir_path}/{name}.png"
    
    return _path


@pytest.fixture
def test_data():
    """テストデータを読み込み"""
    with open("tests/fixtures/test_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def setup_teardown(request):
    """各テストの前後処理"""
    # テスト前の処理
    yield
    
    # テスト後の処理（テスト結果はpytest_runtest_makereportで処理）


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """テスト結果をレポートに追加"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def pytest_configure(config):
    """Pytest設定"""
    config.addinivalue_line(
        "markers", "smoke: スモークテスト（基本機能の確認）"
    )
    config.addinivalue_line(
        "markers", "slow: 実行時間の長いテスト"
    )
    config.addinivalue_line(
        "markers", "visual: ビジュアルリグレッションテスト"
    )