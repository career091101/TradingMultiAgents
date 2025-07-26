#!/usr/bin/env python3
"""
バックテスト自動実行のテスト - モックデータ版
実際のWebUIに依存せずに機能をテストする
"""

import json
from datetime import datetime
from backtest_automation_advanced import BacktestAutomationAdvanced

class MockBacktestAutomation(BacktestAutomationAdvanced):
    """モックデータを使用したテスト用クラス"""
    
    def __init__(self):
        super().__init__()
        self.mock_mode = True
        
    def setup(self):
        """モック: ブラウザ起動"""
        print("=== モックモードで実行中 ===")
        self.log_event("ブラウザ起動", "成功")
        print("✓ ブラウザ起動成功（モック）")
        
    def login(self):
        """モック: ログイン"""
        self.log_event("ログイン", "成功")
        print("✓ ログイン成功（モック）")
        
    def navigate_to_backtest(self):
        """モック: バックテストページ遷移"""
        self.log_event("バックテストページ遷移", "成功")
        print("✓ バックテストページへ移動（モック）")
        
    def navigate_to_execution_tab(self):
        """モック: 実行タブへ移動"""
        self.log_event("実行タブ切り替え", "成功")
        print("✓ 実行タブに切り替え（モック）")
        
    def execute_backtest(self):
        """モック: バックテスト実行"""
        self.log_event("バックテスト実行開始", "成功")
        print("✓ 実行ボタンをクリック（モック）")
        return True
        
    def monitor_execution(self):
        """モック: 実行監視"""
        self.log_event("バックテスト完了", "成功")
        print("✓ バックテスト完了（モック）")
        return True
        
    def initial_validation(self):
        """モック: 初期検証 - 取引量0のケースを返す"""
        print("\n6. 実行結果の初期検証")
        
        # 取引量0のテストケース
        results = {
            "取引量": "0",
            "総リターン": "0.00",
            "シャープレシオ": "0.00",
            "最大ドローダウン": "0.00"
        }
        
        problems = []
        warnings = ["取引が0件です"]
        
        print(f"モック結果: 取引量={results['取引量']}")
        
        return results, problems, warnings
    
    def identify_errors(self):
        """モック: エラー特定"""
        return {
            "システムエラー": [],
            "データエラー": ["価格データの取得に失敗: API rate limit exceeded"],
            "設定エラー": [],
            "戦略エラー": ["エントリーシグナルが一度も発生しませんでした"]
        }
    
    def cleanup(self):
        """モック: クリーンアップ"""
        print("ブラウザを閉じました（モック）")
    
    def get_user_action(self):
        """モック: 自動的に0を返して終了"""
        print("\n=== モックモードのため、ユーザー入力をスキップします ===")
        return 0

def test_zero_trade_scenario():
    """取引量0のシナリオをテスト"""
    print("=" * 80)
    print("バックテスト自動実行テスト - 取引量0のシナリオ")
    print("=" * 80)
    
    automation = MockBacktestAutomation()
    
    try:
        # 基本的な実行フロー
        automation.setup()
        automation.login()
        automation.navigate_to_backtest()
        automation.navigate_to_execution_tab()
        
        if not automation.execute_backtest():
            print("実行失敗")
            return False
        
        # 初期検証
        results, problems, warnings = automation.initial_validation()
        
        # 取引量ゼロチェックと詳細分析
        zero_trade_analysis = None
        if results.get("取引量") == "0":
            print("\n7. 取引量ゼロチェックと詳細分析")
            zero_trade_analysis = automation.check_zero_trades_and_analyze(results, problems)
            
            print("\n=== 分析結果サマリー ===")
            print(f"エラータイプ: {list(zero_trade_analysis['error_analysis'].keys())}")
            print(f"根本原因: {zero_trade_analysis['rca_result']['なぜ5_根本原因']}")
            print(f"潜在的要因数: {len(zero_trade_analysis['potential_factors'])}")
        
        # レポート生成
        report = automation.generate_detailed_report(results, problems, warnings, zero_trade_analysis)
        
        # ユーザーアクション（モックなので自動終了）
        if problems or warnings or zero_trade_analysis:
            choice = automation.get_user_action()
            if choice > 0:
                automation.execute_user_action(choice)
        
        print("\n=== テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        automation.cleanup()

def test_successful_scenario():
    """成功シナリオをテスト"""
    print("\n" + "=" * 80)
    print("バックテスト自動実行テスト - 成功シナリオ")
    print("=" * 80)
    
    class SuccessMockAutomation(MockBacktestAutomation):
        def initial_validation(self):
            """成功ケースを返す"""
            results = {
                "取引量": "125",
                "総リターン": "15.32",
                "シャープレシオ": "1.85",
                "最大ドローダウン": "-8.54"
            }
            problems = []
            warnings = []
            return results, problems, warnings
    
    automation = SuccessMockAutomation()
    
    try:
        automation.setup()
        automation.login()
        automation.navigate_to_backtest()
        automation.navigate_to_execution_tab()
        automation.execute_backtest()
        
        results, problems, warnings = automation.initial_validation()
        zero_trade_analysis = None
        
        automation.generate_detailed_report(results, problems, warnings, zero_trade_analysis)
        
        print("\n=== テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"エラー: {e}")
        return False
    finally:
        automation.cleanup()

if __name__ == "__main__":
    print("高度なバックテスト自動実行機能のテスト\n")
    
    # 取引量0のシナリオをテスト
    test_zero_trade_scenario()
    
    # 成功シナリオをテスト
    test_successful_scenario()
    
    print("\n全テスト完了")