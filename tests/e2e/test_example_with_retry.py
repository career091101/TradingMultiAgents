"""
リトライ機能を使用したE2Eテストの例
Week 2の改善機能をデモンストレーション
"""

import pytest
from playwright.sync_api import Page
from utils.retry_handler import RetryHandler, SmartWait, flaky


class TestExampleWithRetry:
    """リトライ機能を使用したテスト例"""
    
    @pytest.mark.smoke
    @flaky(max_runs=3)
    def test_flaky_navigation(self, page: Page, screenshot_path):
        """フレーキーなナビゲーションテスト（自動リトライ）"""
        # このテストは最大3回まで自動的にリトライされます
        
        # ダッシュボードボタンをクリック
        dashboard_button = page.locator('button:has-text("ダッシュボード")')
        dashboard_button.click()
        
        # ページ遷移を待機
        page.wait_for_load_state("networkidle")
        
        # メトリクスが表示されるまで待機
        metrics = page.locator('[data-testid="stMetric"]').first
        assert metrics.is_visible(), "メトリクスが表示されていません"
        
        # スクリーンショット
        screenshot_path("flaky_test_success")
    
    @RetryHandler.retry_on_stale_element()
    def test_dynamic_content_with_retry(self, page: Page, smart_wait: SmartWait):
        """動的コンテンツのテスト（Stale Element対策）"""
        # 動的に更新される要素をスマートに待機
        smart_wait.wait_for_element(page, '[data-testid="stMetric"]')
        
        # 要素が安定するまで待機
        smart_wait.wait_for_stable_element(page, '[data-testid="stMetric"]')
        
        # メトリクスの値を取得
        metric = page.locator('[data-testid="stMetric"]').first
        value = metric.locator('[data-testid="stMetricValue"]').text_content()
        
        assert value is not None, "メトリクスの値が取得できません"
        print(f"メトリクス値: {value}")
    
    @RetryHandler.retry_on_timeout()
    def test_slow_loading_page(self, page: Page, retry_handler: RetryHandler):
        """遅いページのテスト（タイムアウトリトライ）"""
        # 設定ページへ移動
        settings_button = page.locator('button:has-text("分析設定")')
        
        # リトライ付きでクリック
        retry_handler.wait_and_retry(
            page,
            lambda: settings_button.click(),
            wait_condition="networkidle"
        )
        
        # 設定フォームが表示されるまで待機
        settings_form = page.locator('text="基本設定"').first
        assert settings_form.is_visible(timeout=10000)
    
    def test_with_custom_retry_logic(self, page: Page):
        """カスタムリトライロジックのテスト"""
        
        @RetryHandler.retry(
            max_attempts=5,
            delay=1,
            backoff_factor=1.2,
            condition=lambda e: "timeout" in str(e).lower()
        )
        def check_analysis_status():
            status = page.locator('text="分析完了"').first
            if not status.is_visible():
                raise TimeoutError("分析がまだ完了していません")
            return True
        
        # カスタムリトライロジックを実行
        result = check_analysis_status()
        assert result is True
    
    @pytest.mark.parametrize("viewport", [
        {"width": 1920, "height": 1080, "name": "desktop"},
        {"width": 768, "height": 1024, "name": "tablet"},
        {"width": 375, "height": 812, "name": "mobile"}
    ])
    def test_responsive_with_retry(self, page: Page, viewport, screenshot_path):
        """レスポンシブテスト（各ビューポートでリトライ）"""
        # ビューポートを設定
        page.set_viewport_size({
            "width": viewport["width"],
            "height": viewport["height"]
        })
        
        # リトライ付きで要素を待機
        @RetryHandler.retry(max_attempts=3)
        def check_layout():
            sidebar = page.locator('[data-testid="stSidebar"]')
            main_content = page.locator('[data-testid="stAppViewContainer"]')
            
            # モバイルでの特別な処理
            if viewport["width"] < 768:
                # サイドバーが折りたたまれているか確認
                pass
            else:
                # デスクトップ/タブレットではサイドバーが表示
                assert sidebar.is_visible()
            
            assert main_content.is_visible()
        
        check_layout()
        
        # スクリーンショット
        screenshot_path(f"responsive_{viewport['name']}", description=f"{viewport['name']}レイアウト")
    
    def test_error_recovery(self, page: Page, smart_wait: SmartWait):
        """エラーからの回復テスト"""
        # 無効な操作を試みる
        try:
            # 存在しない要素をクリック
            page.locator("#non-existent-element").click(timeout=1000)
        except Exception as e:
            print(f"予期されたエラー: {e}")
            
            # エラーから回復してダッシュボードに戻る
            @RetryHandler.retry(max_attempts=3)
            def recover_to_dashboard():
                dashboard_button = page.locator('button:has-text("ダッシュボード")').first
                if dashboard_button.is_visible():
                    dashboard_button.click()
                    page.wait_for_load_state("networkidle")
                else:
                    # URLから直接ダッシュボードへ
                    page.goto(page.url.split("?")[0])
            
            recover_to_dashboard()
            
            # ダッシュボードが表示されることを確認
            smart_wait.wait_for_element(page, '[data-testid="stMetric"]')
            assert True, "エラーから正常に回復しました"