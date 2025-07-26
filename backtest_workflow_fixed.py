#!/usr/bin/env python3
"""
WebUIバックテスト実行ワークフロー
AppleScriptを使用してブラウザを操作
"""

import subprocess
import time
import logging
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def execute_applescript(script):
    """AppleScriptを実行"""
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"AppleScript実行エラー: {e}")
        return None

def click_element_by_text(text):
    """指定されたテキストを含む要素をクリック"""
    script = f'''
    tell application "Google Chrome"
        tell active tab of window 1
            execute javascript "
                const elements = Array.from(document.querySelectorAll('*'));
                const target = elements.find(el => el.textContent.includes('{text}'));
                if (target) {{
                    target.click();
                    'clicked';
                }} else {{
                    'not found';
                }}
            "
        end tell
    end tell
    '''
    return execute_applescript(script)

def fill_input(selector, value):
    """入力フィールドに値を入力"""
    script = f'''
    tell application "Google Chrome"
        tell active tab of window 1
            execute javascript "
                const input = document.querySelector('{selector}');
                if (input) {{
                    input.value = '{value}';
                    input.dispatchEvent(new Event('input', {{bubbles: true}}));
                    'filled';
                }} else {{
                    'not found';
                }}
            "
        end tell
    end tell
    '''
    return execute_applescript(script)

def check_page_content():
    """ページの内容を確認"""
    script = '''
    tell application "Google Chrome"
        tell active tab of window 1
            execute javascript "document.body.innerText"
        end tell
    end tell
    '''
    return execute_applescript(script)

def take_screenshot(filename):
    """スクリーンショットを撮影"""
    subprocess.run(['screencapture', '-x', filename])
    logger.info(f"スクリーンショット保存: {filename}")

def main():
    logger.info("=== バックテスト自動実行ワークフロー開始 ===")
    
    # 2. ログイン処理
    logger.info("2. WebUI接続 - ログイン確認")
    time.sleep(2)
    
    page_content = check_page_content()
    if page_content and ("Password" in page_content or "password" in page_content):
        logger.info("ログイン画面を検出 - ログイン処理を実行")
        
        # ユーザー名入力
        fill_input('input[type="text"]', 'user')
        time.sleep(1)
        
        # パスワード入力
        fill_input('input[type="password"]', 'user123')
        time.sleep(1)
        
        # ログインボタンクリック
        click_element_by_text('Login')
        time.sleep(3)
        logger.info("ログイン完了")
    else:
        logger.info("既にログイン済み")
    
    # 3. バックテストページへの遷移
    logger.info("3. バックテストページへの遷移")
    
    # バックテスト2タブを探してクリック
    result = click_element_by_text('バックテスト2')
    if result == 'clicked':
        logger.info("バックテスト2タブをクリック")
        time.sleep(2)
    else:
        logger.warning("バックテスト2タブが見つからない - 既に表示されている可能性")
    
    # 4. バックテスト実行タブへの移動
    logger.info("4. バックテスト実行タブへの移動")
    time.sleep(1)
    
    # 5. バックテスト実行
    logger.info("5. バックテスト実行")
    
    # 実行ボタンを探してクリック
    execution_started = False
    for button_text in ['バックテスト実行', '実行', 'Run Backtest', 'Execute']:
        result = click_element_by_text(button_text)
        if result == 'clicked':
            logger.info(f"実行ボタン「{button_text}」をクリック")
            execution_started = True
            break
    
    if not execution_started:
        logger.warning("実行ボタンが見つかりません")
        take_screenshot('backtest_no_button.png')
    else:
        time.sleep(3)
        take_screenshot('backtest_execution_started.png')
    
    # 6. ログ確認・問題判定
    logger.info("6. ログ確認・問題判定")
    
    # 実行状態を監視（最大5分）
    start_time = time.time()
    timeout = 300  # 5分
    
    problems = []
    warnings = []
    
    while time.time() - start_time < timeout:
        page_content = check_page_content()
        
        if page_content:
            # エラーチェック
            if "ERROR" in page_content or "エラー" in page_content:
                problems.append("エラーメッセージを検出")
                take_screenshot('backtest_error.png')
                break
            
            # 完了チェック
            if any(word in page_content for word in ['完了', 'Complete', 'Finished', '結果']):
                logger.info("バックテスト完了を確認")
                take_screenshot('backtest_completed.png')
                
                # 結果確認
                if "取引数: 0" in page_content or "Trades: 0" in page_content:
                    warnings.append("取引が0件です")
                
                break
        
        time.sleep(5)
    
    # 7. 結果処理
    logger.info("7. 結果処理")
    
    report = {
        "execution_time": datetime.now().isoformat(),
        "status": "error" if problems else ("warning" if warnings else "success"),
        "problems": problems,
        "warnings": warnings,
        "execution_duration": f"{time.time() - start_time:.2f}秒"
    }
    
    if problems:
        logger.error("=== エラーが発生しました ===")
        for problem in problems:
            logger.error(f"- {problem}")
        logger.error("\n根本原因分析:")
        logger.error("1. APIキー設定の問題")
        logger.error("2. データ取得エラー")
        logger.error("3. モデル呼び出しエラー")
        logger.error("\n推奨対処法:")
        logger.error("- ログファイルを確認")
        logger.error("- 環境変数を再確認")
        logger.error("- WebUIを再起動")
    elif warnings:
        logger.warning("=== 警告ありで完了 ===")
        for warning in warnings:
            logger.warning(f"- {warning}")
    else:
        logger.info("=== 正常完了 ===")
    
    # レポート保存
    report_file = f"backtest_workflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"レポート保存: {report_file}")
    return len(problems) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)