"""
WebUIの全ページをナビゲートしてスクリーンショットを取得
"""

import os
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

# 環境変数を設定（UIテスト用のダミー値）
os.environ["FINNHUB_API_KEY"] = "test_dummy_key"
os.environ["OPENAI_API_KEY"] = "test_dummy_key"

def capture_all_pages():
    # スクリーンショット保存ディレクトリ
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = Path(f"webui_screenshots_{timestamp}")
    screenshot_dir.mkdir(exist_ok=True)
    
    with sync_playwright() as p:
        # ブラウザを起動
        browser = p.chromium.launch(headless=False)  # headless=Falseで画面表示
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="ja-JP"
        )
        page = context.new_page()
        
        # WebUIにアクセス
        print("🌐 WebUIにアクセス中...")
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # ページ情報とスクリーンショット取得
        pages = [
            ("dashboard", "ダッシュボード", '[data-testid="stSidebar"] button:has-text("ダッシュボード")'),
            ("settings", "分析設定", '[data-testid="stSidebar"] button:has-text("分析設定")'),
            ("execution", "分析実行", '[data-testid="stSidebar"] button:has-text("分析実行")'),
            ("results", "結果表示", '[data-testid="stSidebar"] button:has-text("結果表示")')
        ]
        
        ui_issues = []
        
        for page_id, page_name, selector in pages:
            print(f"\n📸 {page_name}ページをキャプチャ中...")
            
            try:
                # サイドバーが閉じている場合は開く
                sidebar = page.locator('[data-testid="stSidebar"]')
                if not sidebar.is_visible():
                    # ハンバーガーメニューをクリック
                    hamburger = page.locator('button[kind="header"]').first
                    if hamburger.is_visible():
                        hamburger.click()
                        time.sleep(1)
                
                # ナビゲーションボタンをクリック
                nav_button = page.locator(selector)
                if nav_button.is_visible():
                    nav_button.click()
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)
                else:
                    # セレクタが見つからない場合の代替手段
                    print(f"⚠️ {page_name}ボタンが見つかりません。代替セレクタを試行...")
                    # テキストベースで検索
                    alt_button = page.get_by_text(page_name.replace("ダッシュボード", "Dashboard"))
                    if alt_button.is_visible():
                        alt_button.click()
                        page.wait_for_load_state("networkidle")
                        time.sleep(2)
                    else:
                        ui_issues.append(f"{page_name}ページへのナビゲーションボタンが見つかりません")
                        continue
                
                # フルページスクリーンショット
                screenshot_path = screenshot_dir / f"{page_id}_full.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"✅ フルページスクリーンショット保存: {screenshot_path}")
                
                # ビューポートスクリーンショット
                viewport_path = screenshot_dir / f"{page_id}_viewport.png"
                page.screenshot(path=str(viewport_path), full_page=False)
                print(f"✅ ビューポートスクリーンショット保存: {viewport_path}")
                
                # ページ内のスクロール可能な要素をチェック
                scrollable_elements = page.locator('[data-testid="stVerticalBlock"]').all()
                if scrollable_elements:
                    print(f"📜 {len(scrollable_elements)}個のスクロール可能な要素を検出")
                    
                    for i, element in enumerate(scrollable_elements[:3]):  # 最初の3つまで
                        try:
                            # 要素までスクロール
                            element.scroll_into_view_if_needed()
                            time.sleep(0.5)
                            
                            # スクロール後のスクリーンショット
                            scroll_path = screenshot_dir / f"{page_id}_scroll_{i}.png"
                            page.screenshot(path=str(scroll_path))
                            print(f"✅ スクロール位置{i+1}のスクリーンショット保存: {scroll_path}")
                        except Exception as e:
                            print(f"⚠️ スクロール要素{i+1}の処理中にエラー: {e}")
                
                # ページ固有のUI要素をチェック
                if page_id == "dashboard":
                    # メトリクスカードの確認
                    metrics = page.locator('[data-testid="stMetric"]').all()
                    if not metrics:
                        ui_issues.append("ダッシュボードページにメトリクスカードが表示されていません")
                    else:
                        print(f"✅ {len(metrics)}個のメトリクスカードを検出")
                
                elif page_id == "settings":
                    # 入力フィールドの確認
                    inputs = page.locator('input[type="text"]').all()
                    if not inputs:
                        ui_issues.append("分析設定ページに入力フィールドが表示されていません")
                    else:
                        print(f"✅ {len(inputs)}個の入力フィールドを検出")
                
                elif page_id == "execution":
                    # 実行ボタンの確認
                    run_button = page.locator('button:has-text("分析実行")')
                    if not run_button.is_visible():
                        ui_issues.append("分析実行ページに実行ボタンが表示されていません")
                    else:
                        print("✅ 分析実行ボタンを検出")
                
                elif page_id == "results":
                    # 結果表示エリアの確認
                    results_area = page.locator('[data-testid="stContainer"]').all()
                    if len(results_area) < 2:
                        ui_issues.append("結果表示ページに十分なコンテナが表示されていません")
                    else:
                        print(f"✅ {len(results_area)}個のコンテナを検出")
                        
            except Exception as e:
                print(f"❌ {page_name}ページの処理中にエラー: {e}")
                ui_issues.append(f"{page_name}ページの処理中にエラー: {str(e)}")
        
        # レスポンシブテスト
        print("\n📱 レスポンシブテスト実施中...")
        viewports = [
            ("mobile", 375, 667),
            ("tablet", 768, 1024),
            ("desktop", 1920, 1080)
        ]
        
        for device, width, height in viewports:
            print(f"\n🖥️ {device}サイズ ({width}x{height}) でテスト...")
            page.set_viewport_size({"width": width, "height": height})
            time.sleep(1)
            
            # ダッシュボードページでテスト
            dashboard_button = page.locator('[data-testid="stSidebar"] button').first
            if dashboard_button.is_visible():
                dashboard_button.click()
                time.sleep(1)
            
            responsive_path = screenshot_dir / f"responsive_{device}.png"
            page.screenshot(path=str(responsive_path))
            print(f"✅ {device}スクリーンショット保存: {responsive_path}")
            
            # サイドバーの表示状態をチェック
            sidebar = page.locator('[data-testid="stSidebar"]')
            if device == "mobile" and sidebar.is_visible():
                ui_issues.append(f"{device}サイズでサイドバーが常時表示されています（折りたたみ推奨）")
        
        browser.close()
        
        # UI課題のレポート出力
        print("\n" + "="*50)
        print("📋 UI課題レポート")
        print("="*50)
        
        if ui_issues:
            print(f"\n⚠️ 検出された課題 ({len(ui_issues)}件):")
            for i, issue in enumerate(ui_issues, 1):
                print(f"{i}. {issue}")
        else:
            print("\n✅ 重大なUI課題は検出されませんでした")
        
        # サマリー
        print(f"\n📊 スクリーンショット保存先: {screenshot_dir.absolute()}")
        print(f"📸 保存されたスクリーンショット数: {len(list(screenshot_dir.glob('*.png')))}枚")
        
        return ui_issues

if __name__ == "__main__":
    capture_all_pages()