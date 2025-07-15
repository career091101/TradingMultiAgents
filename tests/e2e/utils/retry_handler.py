"""
E2Eテスト用のリトライハンドラー
フレーキーなテストを自動的にリトライし、安定性を向上させる
"""

import functools
import time
from typing import Callable, Any, Optional, Type, Tuple
import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeout, Error as PlaywrightError


class RetryHandler:
    """リトライロジックを提供するクラス"""
    
    # リトライ可能な例外のタイプ
    RETRYABLE_EXCEPTIONS = (
        PlaywrightTimeout,
        PlaywrightError,
        AssertionError,
        TimeoutError,
    )
    
    # デフォルトのリトライ設定
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_RETRY_DELAY = 2  # 秒
    DEFAULT_BACKOFF_FACTOR = 1.5
    
    @staticmethod
    def retry(
        max_attempts: int = DEFAULT_RETRY_COUNT,
        delay: float = DEFAULT_RETRY_DELAY,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        exceptions: Tuple[Type[Exception], ...] = RETRYABLE_EXCEPTIONS,
        condition: Optional[Callable[[Exception], bool]] = None
    ):
        """
        リトライデコレーター
        
        Args:
            max_attempts: 最大リトライ回数
            delay: リトライ間の初期遅延（秒）
            backoff_factor: 遅延の増加係数
            exceptions: リトライ対象の例外タイプ
            condition: リトライ条件を判定する関数
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                current_delay = delay
                
                for attempt in range(max_attempts):
                    try:
                        # テスト実行
                        result = func(*args, **kwargs)
                        
                        # 成功したらリトライ情報をログ
                        if attempt > 0:
                            print(f"✅ リトライ成功: {func.__name__} (試行 {attempt + 1}/{max_attempts})")
                        
                        return result
                        
                    except exceptions as e:
                        last_exception = e
                        
                        # カスタム条件チェック
                        if condition and not condition(e):
                            raise
                        
                        # 最後の試行の場合は例外を再発生
                        if attempt == max_attempts - 1:
                            print(f"❌ リトライ失敗: {func.__name__} (全{max_attempts}回失敗)")
                            raise
                        
                        # リトライログ
                        print(f"⚠️ リトライ中: {func.__name__} (試行 {attempt + 1}/{max_attempts})")
                        print(f"   エラー: {type(e).__name__}: {str(e)}")
                        print(f"   次回試行まで {current_delay:.1f} 秒待機...")
                        
                        # 待機
                        time.sleep(current_delay)
                        
                        # 次回の遅延を計算
                        current_delay *= backoff_factor
                        
                # 予期しない状況の場合
                if last_exception:
                    raise last_exception
                    
            return wrapper
        return decorator
    
    @staticmethod
    def retry_on_stale_element():
        """Stale element エラー専用のリトライデコレーター"""
        def is_stale_element_error(e: Exception) -> bool:
            error_messages = [
                "stale element",
                "element is not attached",
                "element not found",
                "detached from the DOM"
            ]
            return any(msg in str(e).lower() for msg in error_messages)
        
        return RetryHandler.retry(
            max_attempts=5,
            delay=1,
            condition=is_stale_element_error
        )
    
    @staticmethod
    def retry_on_timeout():
        """タイムアウトエラー専用のリトライデコレーター"""
        return RetryHandler.retry(
            max_attempts=3,
            delay=3,
            exceptions=(PlaywrightTimeout, TimeoutError)
        )
    
    @staticmethod
    def wait_and_retry(page, action: Callable, wait_condition: str = "networkidle"):
        """
        アクション実行前に待機してからリトライ
        
        Args:
            page: Playwright page オブジェクト
            action: 実行するアクション
            wait_condition: 待機条件
        """
        @RetryHandler.retry(max_attempts=3, delay=1)
        def execute_with_wait():
            page.wait_for_load_state(wait_condition)
            return action()
        
        return execute_with_wait()


class SmartWait:
    """インテリジェントな待機処理を提供するクラス"""
    
    @staticmethod
    def wait_for_element(page, selector: str, state: str = "visible", timeout: int = 30000):
        """
        要素の出現を賢く待機
        
        Args:
            page: Playwright page オブジェクト
            selector: 要素のセレクタ
            state: 期待する状態
            timeout: タイムアウト（ミリ秒）
        """
        @RetryHandler.retry(max_attempts=3, delay=1)
        def wait():
            # まず短いタイムアウトで試す
            try:
                page.wait_for_selector(selector, state=state, timeout=5000)
                return
            except PlaywrightTimeout:
                # 失敗したら、ページをリフレッシュして再試行
                print(f"⟳ 要素が見つからないため、待機中: {selector}")
                page.wait_for_timeout(1000)
                
                # 最終的に長いタイムアウトで待機
                page.wait_for_selector(selector, state=state, timeout=timeout)
        
        wait()
    
    @staticmethod
    def wait_for_stable_element(page, selector: str, stability_time: int = 500):
        """
        要素が安定するまで待機（位置やサイズが変化しなくなるまで）
        
        Args:
            page: Playwright page オブジェクト
            selector: 要素のセレクタ
            stability_time: 安定と判定する時間（ミリ秒）
        """
        element = page.locator(selector).first
        
        # 要素が表示されるまで待機
        element.wait_for(state="visible")
        
        # 要素の位置とサイズを監視
        prev_bbox = None
        stable_count = 0
        check_interval = 100  # ミリ秒
        
        while stable_count * check_interval < stability_time:
            current_bbox = element.bounding_box()
            
            if current_bbox and prev_bbox and current_bbox == prev_bbox:
                stable_count += 1
            else:
                stable_count = 0
            
            prev_bbox = current_bbox
            page.wait_for_timeout(check_interval)
        
        return element


# テスト用のカスタムマーカー
def flaky(max_runs: int = 3):
    """フレーキーなテストをマークし、自動的にリトライする"""
    return pytest.mark.flaky(max_runs=max_runs, min_passes=1)


def critical():
    """クリティカルなテストをマーク（リトライなし）"""
    return pytest.mark.critical


# 使用例
"""
from tests.e2e.utils.retry_handler import RetryHandler, SmartWait, flaky

class TestExample:
    
    @flaky(max_runs=3)
    def test_flaky_navigation(self, page):
        # フレーキーなテストは自動的に3回まで試行される
        page.goto("/unstable-page")
        assert page.title() == "Expected Title"
    
    @RetryHandler.retry_on_stale_element()
    def test_dynamic_content(self, page):
        # DOM要素が頻繁に更新されるページのテスト
        element = page.locator(".dynamic-element")
        element.click()
        assert element.text_content() == "Updated"
    
    def test_with_smart_wait(self, page):
        # インテリジェントな待機
        SmartWait.wait_for_element(page, "#slow-loading-element")
        SmartWait.wait_for_stable_element(page, ".animating-element")
        
        element = page.locator("#slow-loading-element")
        assert element.is_visible()
"""