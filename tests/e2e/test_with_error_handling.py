"""
Week 3の改善機能を使用したE2Eテスト例
エラーハンドリング、スクリーンショット、カスタムアサーションのデモ
"""

import pytest
from playwright.sync_api import Page
from utils.error_handler import EnhancedErrorReporter, ErrorContext, ErrorAnalyzer
from utils.screenshot_manager import ScreenshotManager
from utils.custom_assertions import CustomAssertions, assert_element_visible, assert_text_equals


class TestWithErrorHandling:
    """エラーハンドリング機能を活用したテスト"""
    
    def setup_method(self):
        """各テストの前に実行"""
        self.error_reporter = EnhancedErrorReporter()
        self.screenshot_manager = ScreenshotManager()
    
    def teardown_method(self):
        """各テストの後に実行"""
        # エラーサマリーレポートを生成
        if self.error_reporter.errors:
            report_path = self.error_reporter.generate_summary_report()
            print(f"\n📊 エラーレポート生成: {report_path}")
        
        # スクリーンショットギャラリーを生成
        gallery_path = self.screenshot_manager.generate_gallery()
        print(f"\n🖼️ スクリーンショットギャラリー: {gallery_path}")
    
    def test_with_comprehensive_error_handling(self, page: Page):
        """包括的なエラーハンドリングのテスト"""
        test_name = "comprehensive_error_handling"
        
        # エラーコンテキストを使用
        with ErrorContext(self.error_reporter, test_name, page) as ctx:
            ctx.add_context("test_phase", "navigation")
            ctx.add_context("expected_behavior", "ダッシュボードページへの遷移")
            
            # カスタムアサーションを使用
            assertions = CustomAssertions(page)
            
            # スクリーンショットを撮影（アノテーション付き）
            self.screenshot_manager.capture(
                page=page,
                name=f"{test_name}_initial",
                annotations=[{
                    "text": "テスト開始時の状態",
                    "position": (10, 10),
                    "color": "blue"
                }]
            )
            
            # ナビゲーションボタンの確認
            assertions.assert_element_visible(
                selector='[data-testid="stSidebar"] button:has-text("ダッシュボード")',
                message="ダッシュボードボタンが見つかりません",
                timeout=10000
            )
            
            # ボタンをハイライトしてスクリーンショット
            self.screenshot_manager.capture(
                page=page,
                name=f"{test_name}_button_highlight",
                highlight=['[data-testid="stSidebar"] button:has-text("ダッシュボード")']
            )
            
            # ボタンクリック
            page.locator('[data-testid="stSidebar"] button:has-text("ダッシュボード")').click()
            page.wait_for_load_state("networkidle")
            
            # ページ遷移後の確認
            assertions.assert_url_matches(
                pattern=r".*(\?.*)?$",  # クエリパラメータを許可
                message="URLが期待されるパターンに一致しません"
            )
            
            # メトリクスの確認
            assertions.assert_element_count(
                selector='[data-testid="stMetric"]',
                expected_count=4,
                operator="greater_equal",
                message="メトリクスが十分に表示されていません"
            )
            
            # テキスト内容の確認
            assertions.assert_text_contains(
                selector='[data-testid="stMetric"]',
                substring="総分析数",
                message="総分析数メトリクスが見つかりません"
            )
            
            # 要素の状態を複合的に確認
            assertions.assert_element_state(
                selector='button:has-text("SPY分析")',
                state={
                    "visible": True,
                    "enabled": True
                },
                message="SPY分析ボタンの状態が正しくありません"
            )
            
            # コンソールエラーの確認
            assertions.assert_no_console_errors(
                ignore_patterns=[
                    "ResizeObserver loop limit exceeded",  # 既知の無害なエラー
                    "Non-Error promise rejection captured"
                ],
                message="予期しないコンソールエラーが発生しました"
            )
            
            # 成功時のスクリーンショット
            self.screenshot_manager.capture(
                page=page,
                name=f"{test_name}_success",
                category="actual",
                annotations=[{
                    "text": "✅ テスト成功",
                    "position": (10, 10),
                    "color": "green"
                }]
            )
            
            # アサーションサマリーを取得
            summary = assertions.get_assertion_summary()
            print(f"\n📊 アサーションサマリー: {summary['passed']}/{summary['total']} passed")
    
    def test_element_screenshot_on_failure(self, page: Page):
        """失敗時の要素スクリーンショット"""
        test_name = "element_screenshot_failure"
        
        try:
            # 存在しない要素をクリックしようとする
            non_existent_selector = "#non-existent-element"
            
            # 要素の周辺をキャプチャ
            self.screenshot_manager.capture_element(
                page=page,
                selector='[data-testid="stSidebar"]',  # 実際に存在する要素
                name=f"{test_name}_context",
                padding=50
            )
            
            # エラーを発生させる
            page.locator(non_existent_selector).click(timeout=2000)
            
        except Exception as e:
            # エラーを分析
            error_analysis = ErrorAnalyzer.analyze_error(e)
            print(f"\n🔍 エラー分析: {error_analysis['category']}")
            print(f"推奨される解決策:")
            for i, solution in enumerate(error_analysis['solutions'], 1):
                print(f"  {i}. {solution}")
            
            # エラー時のスクリーンショット（複数の形式）
            self.screenshot_manager.capture(
                page=page,
                name=f"{test_name}_error_full",
                category="error",
                full_page=True
            )
            
            self.screenshot_manager.capture(
                page=page,
                name=f"{test_name}_error_viewport",
                category="error",
                full_page=False
            )
            
            # エラー情報をレポーターに記録
            self.error_reporter.capture_error(
                error=e,
                test_name=test_name,
                page=page,
                context={
                    "attempted_action": "click",
                    "selector": non_existent_selector
                }
            )
            
            # テストは失敗として扱う
            pytest.fail(f"要素が見つかりません: {non_existent_selector}")
    
    def test_responsive_screenshots_with_assertions(self, page: Page):
        """レスポンシブスクリーンショットとアサーション"""
        test_name = "responsive_assertions"
        
        # 複数のビューポートでスクリーンショットを撮影
        screenshots = self.screenshot_manager.capture_responsive(
            page=page,
            name=test_name
        )
        
        # 各ビューポートでアサーションを実行
        viewports = [
            {"width": 1920, "height": 1080, "name": "desktop"},
            {"width": 768, "height": 1024, "name": "tablet"},
            {"width": 375, "height": 812, "name": "mobile"}
        ]
        
        for viewport in viewports:
            page.set_viewport_size({
                "width": viewport["width"],
                "height": viewport["height"]
            })
            page.wait_for_timeout(500)
            
            with ErrorContext(self.error_reporter, f"{test_name}_{viewport['name']}", page) as ctx:
                ctx.add_context("viewport", viewport)
                
                assertions = CustomAssertions(page)
                
                # ビューポートに応じたアサーション
                if viewport["width"] >= 768:
                    # デスクトップ/タブレット: サイドバーが表示
                    assertions.assert_element_visible(
                        '[data-testid="stSidebar"]',
                        message=f"{viewport['name']}でサイドバーが表示されていません"
                    )
                else:
                    # モバイル: 特別な処理
                    print(f"モバイルビューでのテスト: {viewport['name']}")
                
                # 共通要素の確認
                assertions.assert_element_visible(
                    '[data-testid="stAppViewContainer"]',
                    message=f"{viewport['name']}でメインコンテンツが表示されていません"
                )
    
    def test_action_series_with_screenshots(self, page: Page):
        """一連のアクションとスクリーンショット"""
        test_name = "action_series"
        
        # アクションシーケンスを定義
        actions = [
            {
                "type": "click",
                "selector": 'button:has-text("分析設定")',
                "description": "設定ページへ移動"
            },
            {
                "type": "wait",
                "timeout": 1000,
                "description": "ページ読み込み待機"
            },
            {
                "type": "fill",
                "selector": 'input[type="text"]',
                "value": "AAPL",
                "description": "ティッカー入力"
            },
            {
                "type": "scroll",
                "y": 200,
                "description": "ページスクロール"
            }
        ]
        
        # アクションを実行しながらスクリーンショットを撮影
        screenshots = self.screenshot_manager.capture_series(
            page=page,
            name=test_name,
            actions=actions
        )
        
        print(f"\n📸 撮影されたスクリーンショット: {len(screenshots)}枚")
    
    @pytest.mark.skip(reason="アクセシビリティテストは必要に応じて実行")
    def test_accessibility_with_error_reporting(self, page: Page):
        """アクセシビリティテストとエラーレポート"""
        test_name = "accessibility_check"
        
        with ErrorContext(self.error_reporter, test_name, page) as ctx:
            ctx.add_context("test_type", "accessibility")
            
            assertions = CustomAssertions(page)
            
            # 全体的なアクセシビリティチェック
            assertions.assert_accessibility(
                rules=["color-contrast", "label", "image-alt"],
                message="アクセシビリティ違反が検出されました"
            )
            
            # 特定要素のアクセシビリティチェック
            assertions.assert_accessibility(
                selector='[data-testid="stSidebar"]',
                message="サイドバーにアクセシビリティ問題があります"
            )