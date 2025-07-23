"""
TradingAgents WebUI 包括的E2Eテスト
全機能を網羅したテストスイート
"""

import pytest
from playwright.sync_api import Page, expect
from utils.streamlit_advanced import create_streamlit_manager
from utils.custom_assertions import CustomAssertions
import time
import re

class TestWebUIComprehensive:
    """TradingAgents WebUI包括的テスト"""
    
    def setup_class(cls):
        """クラス全体の初期設定"""
        print("\n🚀 TradingAgents WebUI E2Eテスト開始")
        cls.test_results = {
            "passed": [],
            "failed": [],
            "screenshots": [],
            "performance": {}
        }
    
    def teardown_class(cls):
        """クラス全体の終了処理"""
        print(f"\n📊 E2Eテスト完了")
        print(f"✅ 成功: {len(cls.test_results['passed'])}")
        print(f"❌ 失敗: {len(cls.test_results['failed'])}")
        print(f"📸 スクリーンショット: {len(cls.test_results['screenshots'])}")
    
    def test_01_application_startup(self, page: Page):
        """1. アプリケーション起動テスト"""
        print("\n🔄 1. アプリケーション起動テスト")
        
        manager = create_streamlit_manager(page)
        assertions = CustomAssertions(page)
        
        start_time = time.time()
        
        # アプリケーションの準備完了を待つ
        ready = manager.wait_for_app_ready()
        
        startup_time = time.time() - start_time
        self.__class__.test_results["performance"]["startup_time"] = startup_time
        
        assert ready, "アプリケーションの起動に失敗"
        
        # 基本要素の確認
        page_info = manager.get_current_page_info()
        
        assert "TradingAgents" in page_info["title"], "アプリタイトルが正しくない"
        
        # スクリーンショット
        screenshot_path = "screenshots/01_startup.png"
        page.screenshot(path=screenshot_path, full_page=True)
        self.__class__.test_results["screenshots"].append(screenshot_path)
        
        print(f"✅ アプリケーション起動成功 ({startup_time:.2f}秒)")
        self.__class__.test_results["passed"].append("application_startup")
    
    def test_02_dashboard_functionality(self, page: Page):
        """2. ダッシュボード機能テスト"""
        print("\n📊 2. ダッシュボード機能テスト")
        
        manager = create_streamlit_manager(page)
        
        # ダッシュボードに移動
        success = manager.safe_navigate_to_page("dashboard")
        assert success, "ダッシュボードへの移動失敗"
        
        # ダッシュボードコンテンツの確認
        page_info = manager.get_current_page_info()
        
        # メトリクスカードの確認
        metrics = page.locator('[data-testid="stMetric"]').all()
        assert len(metrics) >= 3, f"メトリクスカードが不足: {len(metrics)}個"
        
        # 統計情報の確認
        stats_section = page.locator('text="統計情報"')
        if stats_section.count() > 0:
            print("✅ 統計情報セクション確認")
        
        # クイックアクションの確認
        quick_action = page.locator('text="クイックアクション"')
        if quick_action.count() > 0:
            print("✅ クイックアクションセクション確認")
        
        # 人気銘柄分析の確認
        popular_stocks = page.locator('text="人気銘柄分析"')
        if popular_stocks.count() > 0:
            print("✅ 人気銘柄分析セクション確認")
        
        # スクリーンショット
        screenshot_path = "screenshots/02_dashboard.png"
        page.screenshot(path=screenshot_path, full_page=True)
        self.__class__.test_results["screenshots"].append(screenshot_path)
        
        print("✅ ダッシュボード機能テスト成功")
        self.__class__.test_results["passed"].append("dashboard_functionality")
    
    def test_03_settings_configuration(self, page: Page):
        """3. 分析設定機能テスト"""
        print("\n⚙️ 3. 分析設定機能テスト")
        
        manager = create_streamlit_manager(page)
        
        # 設定ページに移動
        success = manager.safe_navigate_to_page("settings")
        assert success, "設定ページへの移動失敗"
        
        # 基本設定セクションの確認
        basic_settings = page.locator('text="基本設定"')
        assert basic_settings.count() > 0, "基本設定セクションが見つかりません"
        
        # ティッカーシンボル入力の確認
        ticker_inputs = page.locator('input[type="text"]').all()
        assert len(ticker_inputs) >= 1, "ティッカー入力フィールドがありません"
        
        # クイック選択ボタンの確認
        quick_buttons = page.locator('button').all()
        button_texts = []
        for btn in quick_buttons[:10]:  # 最初の10個をチェック
            if btn.is_visible():
                try:
                    text = btn.inner_text()
                    if text and len(text) <= 10:  # 短いテキストのボタン
                        button_texts.append(text)
                except:
                    pass
        
        assert len(button_texts) >= 3, f"クイック選択ボタンが不足: {button_texts}"
        
        # アナリストチーム選択の確認
        analyst_section = page.locator('text="アナリストチーム選択"')
        assert analyst_section.count() > 0, "アナリストチーム選択セクションがありません"
        
        # チェックボックスの確認
        checkboxes = page.locator('input[type="checkbox"]').all()
        visible_checkboxes = [cb for cb in checkboxes if cb.is_visible()]
        assert len(visible_checkboxes) >= 3, f"アナリスト選択チェックボックスが不足: {len(visible_checkboxes)}"
        
        # 簡単な設定操作テスト
        if len(ticker_inputs) > 0 and ticker_inputs[0].is_visible():
            try:
                ticker_inputs[0].fill("AAPL")
                time.sleep(0.5)
                print("✅ ティッカーシンボル入力テスト成功")
            except Exception as e:
                print(f"⚠️ ティッカー入力テストでエラー: {e}")
        
        # スクリーンショット
        screenshot_path = "screenshots/03_settings.png"
        page.screenshot(path=screenshot_path, full_page=True)
        self.__class__.test_results["screenshots"].append(screenshot_path)
        
        print("✅ 分析設定機能テスト成功")
        self.__class__.test_results["passed"].append("settings_configuration")
    
    def test_04_execution_preparation(self, page: Page):
        """4. 分析実行準備テスト"""
        print("\n🚀 4. 分析実行準備テスト")
        
        manager = create_streamlit_manager(page)
        
        # 実行ページに移動
        success = manager.safe_navigate_to_page("execution")
        assert success, "実行ページへの移動失敗"
        
        # 実行設定確認セクション
        execution_settings = page.locator('text="実行設定確認"')
        assert execution_settings.count() > 0, "実行設定確認セクションがありません"
        
        # 基本設定の表示確認
        basic_info = page.locator('text="基本設定"')
        if basic_info.count() > 0:
            print("✅ 基本設定情報表示確認")
        
        # 選択アナリストの表示確認
        selected_analysts = page.locator('text="選択アナリスト"')
        if selected_analysts.count() > 0:
            print("✅ 選択アナリスト情報表示確認")
        
        # LLM設定の表示確認
        llm_settings = page.locator('text="LLM設定"')
        if llm_settings.count() > 0:
            print("✅ LLM設定情報表示確認")
        
        # 予想実行時間の確認
        estimated_time = page.locator('text="予想実行時間"')
        if estimated_time.count() > 0:
            print("✅ 予想実行時間表示確認")
        
        # 実行制御ボタンの確認
        execution_control = page.locator('text="実行制御"')
        assert execution_control.count() > 0, "実行制御セクションがありません"
        
        # 分析開始ボタンの確認
        start_button = page.locator('button:has-text("分析開始")')
        if start_button.count() > 0:
            print("✅ 分析開始ボタン確認")
            # ボタンがクリック可能かテスト（実際には実行しない）
            assert start_button.is_visible(), "分析開始ボタンが見えません"
        
        # スクリーンショット
        screenshot_path = "screenshots/04_execution.png"
        page.screenshot(path=screenshot_path, full_page=True)
        self.__class__.test_results["screenshots"].append(screenshot_path)
        
        print("✅ 分析実行準備テスト成功")
        self.__class__.test_results["passed"].append("execution_preparation")
    
    def test_05_results_display(self, page: Page):
        """5. 結果表示機能テスト"""
        print("\n📈 5. 結果表示機能テスト")
        
        manager = create_streamlit_manager(page)
        
        # 結果ページに移動
        success = manager.safe_navigate_to_page("results")
        assert success, "結果ページへの移動失敗"
        
        # 結果選択セクション
        result_selection = page.locator('text="結果選択"')
        assert result_selection.count() > 0, "結果選択セクションがありません"
        
        # ティッカー選択ドロップダウン
        ticker_dropdown = page.locator('select').first
        if ticker_dropdown.count() > 0 and ticker_dropdown.is_visible():
            print("✅ ティッカー選択ドロップダウン確認")
        
        # 分析日選択
        date_inputs = page.locator('input[type="date"]').all()
        if len(date_inputs) > 0:
            print("✅ 分析日選択フィールド確認")
        
        # ステータス表示
        status_indicators = page.locator('text="completed"').all()
        if len(status_indicators) > 0:
            print("✅ ステータス表示確認")
        
        # レポート数表示
        report_count = page.locator('[data-testid="stMetric"]').all()
        if len(report_count) >= 1:
            print("✅ レポート数メトリクス確認")
        
        # 分析サマリーセクション
        analysis_summary = page.locator('text="分析サマリー"')
        if analysis_summary.count() > 0:
            print("✅ 分析サマリーセクション確認")
        
        # PDF出力ボタン
        pdf_button = page.locator('button:has-text("PDF出力")')
        if pdf_button.count() > 0:
            print("✅ PDF出力ボタン確認")
        
        # タブ表示の確認
        tabs = page.locator('[data-testid="stTabs"]').all()
        if len(tabs) > 0:
            print("✅ タブ表示確認")
        
        # スクリーンショット
        screenshot_path = "screenshots/05_results.png"
        page.screenshot(path=screenshot_path, full_page=True)
        self.__class__.test_results["screenshots"].append(screenshot_path)
        
        print("✅ 結果表示機能テスト成功")
        self.__class__.test_results["passed"].append("results_display")
    
    def test_06_navigation_flow(self, page: Page):
        """6. ナビゲーションフローテスト"""
        print("\n🧭 6. ナビゲーションフローテスト")
        
        manager = create_streamlit_manager(page)
        
        # 典型的なユーザーフローをテスト
        flow_steps = [
            ("dashboard", "ダッシュボード"),
            ("settings", "設定"),
            ("execution", "実行"),
            ("results", "結果"),
            ("dashboard", "ダッシュボード（戻り）")
        ]
        
        for i, (page_name, description) in enumerate(flow_steps):
            print(f"  {i+1}. {description}へ移動")
            
            success = manager.safe_navigate_to_page(page_name)
            assert success, f"{description}への移動に失敗"
            
            # 各ステップでのページ情報確認
            page_info = manager.get_current_page_info()
            assert page_info["main_content"] or page_info["title"], f"{description}でコンテンツが空"
            
            # 短い安定化待機
            time.sleep(1)
            
            # 各ステップのスクリーンショット
            screenshot_path = f"screenshots/06_flow_step_{i+1:02d}_{page_name}.png"
            page.screenshot(path=screenshot_path)
            self.__class__.test_results["screenshots"].append(screenshot_path)
        
        print("✅ ナビゲーションフローテスト成功")
        self.__class__.test_results["passed"].append("navigation_flow")
    
    def test_07_responsive_design(self, page: Page):
        """7. レスポンシブデザインテスト"""
        print("\n📱 7. レスポンシブデザインテスト")
        
        manager = create_streamlit_manager(page)
        
        # 各種デバイスサイズでテスト
        viewports = [
            {"width": 375, "height": 667, "name": "mobile"},
            {"width": 768, "height": 1024, "name": "tablet"},
            {"width": 1920, "height": 1080, "name": "desktop"}
        ]
        
        for viewport in viewports:
            print(f"  📏 {viewport['name']}サイズテスト ({viewport['width']}x{viewport['height']})")
            
            # ビューポート設定
            page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
            time.sleep(1)
            
            # アプリの準備
            manager.wait_for_app_ready()
            
            # 基本表示確認
            page_info = manager.get_current_page_info()
            assert page_info["title"] or page_info["main_content"], f"{viewport['name']}で表示エラー"
            
            # サイドバーの確認
            sidebar = page.locator('[data-testid="stSidebar"]')
            if viewport["width"] <= 768:
                # モバイルビューでの確認
                print(f"    📱 モバイルビュー確認")
            else:
                # デスクトップビューでの確認
                assert sidebar.is_visible(), f"{viewport['name']}でサイドバーが見えません"
                print(f"    🖥️ デスクトップビュー確認")
            
            # スクリーンショット
            screenshot_path = f"screenshots/07_responsive_{viewport['name']}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            self.__class__.test_results["screenshots"].append(screenshot_path)
        
        # デスクトップサイズに戻す
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        print("✅ レスポンシブデザインテスト成功")
        self.__class__.test_results["passed"].append("responsive_design")
    
    def test_08_error_handling(self, page: Page):
        """8. エラーハンドリングテスト"""
        print("\n🛡️ 8. エラーハンドリングテスト")
        
        manager = create_streamlit_manager(page)
        
        # 存在しないページへの移動テスト
        result = manager.safe_navigate_to_page("nonexistent_page")
        print(f"  📍 存在しないページへの移動結果: {result}")
        
        # アプリが正常状態を維持しているか確認
        page_info = manager.get_current_page_info()
        assert page_info["title"] or page_info["main_content"], "エラー後にアプリが不安定"
        
        # エラーチェック
        errors = manager._check_for_errors()
        if errors:
            print(f"  ⚠️ 検出されたエラー: {len(errors)}件")
            for error in errors[:3]:  # 最初の3件まで表示
                print(f"    - {error[:100]}...")
        else:
            print("  ✅ エラーなし")
        
        # 正常なページに戻れることを確認
        recovery_success = manager.safe_navigate_to_page("dashboard")
        assert recovery_success, "エラー後の復旧に失敗"
        
        # スクリーンショット
        screenshot_path = "screenshots/08_error_handling.png"
        page.screenshot(path=screenshot_path, full_page=True)
        self.__class__.test_results["screenshots"].append(screenshot_path)
        
        print("✅ エラーハンドリングテスト成功")
        self.__class__.test_results["passed"].append("error_handling")
    
    def test_09_performance_validation(self, page: Page):
        """9. パフォーマンス検証テスト"""
        print("\n⚡ 9. パフォーマンス検証テスト")
        
        manager = create_streamlit_manager(page)
        
        # ページ読み込み時間測定
        load_times = {}
        
        pages_to_test = ["dashboard", "settings", "execution", "results"]
        
        for page_name in pages_to_test:
            start_time = time.time()
            success = manager.safe_navigate_to_page(page_name)
            load_time = time.time() - start_time
            
            load_times[page_name] = load_time
            
            assert success, f"{page_name}ページの読み込み失敗"
            assert load_time < 10.0, f"{page_name}ページの読み込みが遅すぎます: {load_time:.2f}秒"
            
            print(f"  📊 {page_name}ページ読み込み時間: {load_time:.2f}秒")
        
        # 全体的なパフォーマンス評価
        avg_load_time = sum(load_times.values()) / len(load_times)
        max_load_time = max(load_times.values())
        
        self.__class__.test_results["performance"]["page_load_times"] = load_times
        self.__class__.test_results["performance"]["avg_load_time"] = avg_load_time
        self.__class__.test_results["performance"]["max_load_time"] = max_load_time
        
        print(f"  📈 平均読み込み時間: {avg_load_time:.2f}秒")
        print(f"  📈 最大読み込み時間: {max_load_time:.2f}秒")
        
        # パフォーマンス基準の確認
        assert avg_load_time < 5.0, f"平均読み込み時間が基準を超過: {avg_load_time:.2f}秒"
        assert max_load_time < 8.0, f"最大読み込み時間が基準を超過: {max_load_time:.2f}秒"
        
        # スクリーンショット
        screenshot_path = "screenshots/09_performance.png"
        page.screenshot(path=screenshot_path, full_page=True)
        self.__class__.test_results["screenshots"].append(screenshot_path)
        
        print("✅ パフォーマンス検証テスト成功")
        self.__class__.test_results["passed"].append("performance_validation")
    
    def test_10_integration_validation(self, page: Page):
        """10. 統合検証テスト"""
        print("\n🔗 10. 統合検証テスト")
        
        manager = create_streamlit_manager(page)
        
        # 設定→実行→結果の統合フロー確認
        print("  🔄 統合フローテスト開始")
        
        # 1. 設定ページで設定
        success = manager.safe_navigate_to_page("settings")
        assert success, "設定ページへの移動失敗"
        
        # 設定の確認（実際の変更はしない）
        ticker_inputs = page.locator('input[type="text"]').all()
        if len(ticker_inputs) > 0 and ticker_inputs[0].is_visible():
            current_value = ticker_inputs[0].input_value()
            print(f"    📋 現在のティッカー設定: {current_value}")
        
        # 2. 実行ページで準備確認
        success = manager.safe_navigate_to_page("execution")
        assert success, "実行ページへの移動失敗"
        
        # 実行準備状態の確認
        start_button = page.locator('button:has-text("分析開始")')
        if start_button.count() > 0:
            print("    ✅ 分析開始ボタン準備完了")
        
        # 3. 結果ページで表示確認
        success = manager.safe_navigate_to_page("results")
        assert success, "結果ページへの移動失敗"
        
        # 結果表示機能の確認
        result_sections = page.locator('[data-testid="stContainer"]').all()
        print(f"    📊 結果表示セクション数: {len(result_sections)}")
        
        # サイドバーの環境変数表示確認
        env_check = page.locator('text="FINNHUB_API_KEY"')
        if env_check.count() > 0:
            print("    🔑 API設定確認済み")
        
        # 最終状態の確認
        final_info = manager.get_current_page_info()
        assert final_info["main_content"] or final_info["title"], "統合テスト後の状態が不正"
        
        # スクリーンショット
        screenshot_path = "screenshots/10_integration.png"
        page.screenshot(path=screenshot_path, full_page=True)
        self.__class__.test_results["screenshots"].append(screenshot_path)
        
        print("✅ 統合検証テスト成功")
        self.__class__.test_results["passed"].append("integration_validation")
    
    def test_11_final_verification(self, page: Page):
        """11. 最終検証テスト"""
        print("\n🎯 11. 最終検証テスト")
        
        manager = create_streamlit_manager(page)
        
        # ダッシュボードに戻って全体確認
        success = manager.safe_navigate_to_page("dashboard")
        assert success, "最終ダッシュボード移動失敗"
        
        # アプリケーション全体の状態確認
        page_info = manager.get_current_page_info()
        
        # 重要な要素の最終確認
        checks = {
            "title": "TradingAgents" in page_info["title"],
            "sidebar": page.locator('[data-testid="stSidebar"]').is_visible(),
            "main_content": bool(page_info["main_content"]),
            "navigation": "ダッシュボード" in page_info.get("sidebar_active", "")
        }
        
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}: {result}")
            if not result:
                self.__class__.test_results["failed"].append(f"final_check_{check_name}")
        
        # すべてのチェックが通ることを確認
        all_passed = all(checks.values())
        assert all_passed, f"最終チェック失敗: {checks}"
        
        # 最終スクリーンショット
        screenshot_path = "screenshots/11_final_verification.png"
        page.screenshot(path=screenshot_path, full_page=True)
        self.__class__.test_results["screenshots"].append(screenshot_path)
        
        # 最終レポート生成
        self._generate_final_report(page)
        
        print("✅ 最終検証テスト成功")
        self.__class__.test_results["passed"].append("final_verification")
    
    def _generate_final_report(self, page: Page):
        """最終レポートの生成"""
        print("\n📋 最終テストレポート生成中...")
        
        results = self.__class__.test_results
        
        # レポート内容
        report = f"""
# TradingAgents WebUI E2Eテスト 最終レポート

## 📊 テスト結果サマリー
- ✅ 成功したテスト: {len(results['passed'])}
- ❌ 失敗したテスト: {len(results['failed'])}
- 📸 取得したスクリーンショット: {len(results['screenshots'])}

## 🎯 成功したテスト一覧
{chr(10).join(f"- {test}" for test in results['passed'])}

## ⚡ パフォーマンス結果
"""
        
        if results['performance']:
            perf = results['performance']
            if 'startup_time' in perf:
                report += f"- アプリ起動時間: {perf['startup_time']:.2f}秒\n"
            if 'avg_load_time' in perf:
                report += f"- 平均ページ読み込み時間: {perf['avg_load_time']:.2f}秒\n"
            if 'max_load_time' in perf:
                report += f"- 最大ページ読み込み時間: {perf['max_load_time']:.2f}秒\n"
        
        if results['failed']:
            report += f"\n## ❌ 失敗したテスト\n"
            report += "\n".join(f"- {test}" for test in results['failed'])
        
        report += f"\n\n## 📸 スクリーンショット一覧\n"
        report += "\n".join(f"- {path}" for path in results['screenshots'])
        
        # レポートファイルに保存
        try:
            with open("screenshots/E2E_TEST_FINAL_REPORT.md", "w", encoding="utf-8") as f:
                f.write(report)
            print("📄 最終レポート保存: screenshots/E2E_TEST_FINAL_REPORT.md")
        except Exception as e:
            print(f"⚠️ レポート保存エラー: {e}")
        
        print(report)