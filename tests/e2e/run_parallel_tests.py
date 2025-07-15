#!/usr/bin/env python3
"""
E2Eテストの並列実行スクリプト
Week 2の改善: 効率的な並列実行とレポート生成
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse
import json
from datetime import datetime


def run_parallel_tests(args):
    """並列でE2Eテストを実行"""
    
    # 基本のpytestコマンド
    cmd = ["python", "-m", "pytest"]
    
    # 並列実行の設定
    if args.workers:
        cmd.extend(["-n", str(args.workers)])
    else:
        cmd.extend(["-n", "auto"])  # CPU数に応じて自動設定
    
    # テストの種類を指定
    if args.smoke:
        cmd.extend(["-m", "smoke"])
    elif args.slow:
        cmd.extend(["-m", "slow"])
    elif args.critical:
        cmd.extend(["-m", "critical"])
    
    # 詳細度の設定
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    # HTMLレポートの生成
    if args.html_report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"reports/e2e/test_report_{timestamp}.html"
        cmd.extend(["--html", report_path, "--self-contained-html"])
    
    # JUnitXMLレポート（CI用）
    if args.junit_xml:
        cmd.extend(["--junit-xml", args.junit_xml])
    
    # カバレッジ測定
    if args.coverage:
        cmd.extend([
            "--cov=webui",
            "--cov-report=html:reports/coverage",
            "--cov-report=term-missing"
        ])
    
    # 失敗時の動作
    if args.fail_fast:
        cmd.append("-x")  # 最初の失敗で停止
    else:
        cmd.extend(["--maxfail", str(args.max_failures)])
    
    # 特定のテストファイルまたはディレクトリ
    if args.tests:
        cmd.extend(args.tests)
    else:
        cmd.append("tests/e2e")
    
    # 環境変数の設定
    env = os.environ.copy()
    
    if args.headless is not None:
        env["E2E_HEADLESS"] = str(args.headless).lower()
    
    if args.browser:
        env["E2E_BROWSER"] = args.browser
    
    if args.base_url:
        env["E2E_BASE_URL"] = args.base_url
    
    if args.timeout:
        env["E2E_TIMEOUT"] = str(args.timeout)
    
    # テスト実行
    print("🚀 E2Eテストを並列実行中...")
    print(f"コマンド: {' '.join(cmd)}")
    print(f"ワーカー数: {args.workers or 'auto'}")
    
    try:
        result = subprocess.run(cmd, env=env)
        
        if result.returncode == 0:
            print("\n✅ すべてのテストが成功しました！")
        else:
            print(f"\n❌ テストが失敗しました (終了コード: {result.returncode})")
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️ テストが中断されました")
        return 1
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        return 1


def create_test_groups():
    """テストをグループ化して並列実行を最適化"""
    groups = {
        "fast": [
            "test_navigation.py::TestNavigation::test_main_page_loads",
            "test_dashboard.py::TestDashboard::test_statistics_display",
            "test_settings.py::TestSettings::test_navigate_to_settings",
        ],
        "medium": [
            "test_execution.py::TestExecution::test_symbol_validation",
            "test_results.py::TestResults::test_result_selection",
        ],
        "slow": [
            "test_execution.py::TestExecution::test_analysis_execution",
            "test_results.py::TestResults::test_pdf_generation",
        ],
        "visual": [
            "test_dashboard.py::TestDashboard::test_dashboard_layout",
            "test_settings.py::TestSettings::test_settings_responsive_layout",
            "test_execution.py::TestExecution::test_execution_responsive",
            "test_results.py::TestResults::test_results_responsive",
        ]
    }
    
    return groups


def run_test_suite(suite_name):
    """特定のテストスイートを実行"""
    suites = {
        "smoke": {
            "markers": "smoke",
            "workers": 4,
            "timeout": 30000,
            "description": "基本機能の高速テスト"
        },
        "regression": {
            "markers": "not slow",
            "workers": 2,
            "timeout": 60000,
            "description": "全機能の回帰テスト"
        },
        "performance": {
            "markers": "slow",
            "workers": 1,
            "timeout": 120000,
            "description": "パフォーマンステスト"
        },
        "visual": {
            "markers": "visual",
            "workers": 2,
            "timeout": 60000,
            "description": "ビジュアルレグレッションテスト"
        }
    }
    
    if suite_name not in suites:
        print(f"❌ 不明なテストスイート: {suite_name}")
        print(f"利用可能なスイート: {', '.join(suites.keys())}")
        return 1
    
    suite = suites[suite_name]
    print(f"\n🎯 {suite['description']}を実行中...")
    
    args = argparse.Namespace(
        workers=suite["workers"],
        smoke=False,
        slow=False,
        critical=False,
        verbose=True,
        html_report=True,
        junit_xml=None,
        coverage=False,
        fail_fast=False,
        max_failures=10,
        tests=[],
        headless=True,
        browser="chromium",
        base_url=None,
        timeout=suite["timeout"]
    )
    
    # マーカーに基づいてテストを実行
    cmd = ["python", "-m", "pytest", "-m", suite["markers"]]
    result = subprocess.run(cmd)
    
    return result.returncode


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="E2Eテストを並列実行するスクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # すべてのテストを並列実行
  python run_parallel_tests.py
  
  # スモークテストのみを4ワーカーで実行
  python run_parallel_tests.py -n 4 --smoke
  
  # 特定のテストファイルを実行
  python run_parallel_tests.py test_navigation.py test_dashboard.py
  
  # ヘッドレスモードを無効化してデバッグ
  python run_parallel_tests.py --no-headless --workers 1
  
  # テストスイートを実行
  python run_parallel_tests.py --suite smoke
"""
    )
    
    # 並列実行オプション
    parser.add_argument("-n", "--workers", type=int,
                        help="並列実行のワーカー数（デフォルト: auto）")
    
    # テストフィルタリング
    parser.add_argument("--smoke", action="store_true",
                        help="スモークテストのみ実行")
    parser.add_argument("--slow", action="store_true",
                        help="時間のかかるテストのみ実行")
    parser.add_argument("--critical", action="store_true",
                        help="クリティカルパステストのみ実行")
    
    # レポート生成
    parser.add_argument("--html-report", action="store_true", default=True,
                        help="HTMLレポートを生成（デフォルト: True）")
    parser.add_argument("--junit-xml", type=str,
                        help="JUnit XMLレポートのパス")
    parser.add_argument("--coverage", action="store_true",
                        help="カバレッジを測定")
    
    # 実行制御
    parser.add_argument("-x", "--fail-fast", action="store_true",
                        help="最初の失敗で停止")
    parser.add_argument("--max-failures", type=int, default=10,
                        help="最大失敗数（デフォルト: 10）")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="詳細な出力")
    
    # ブラウザ設定
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"],
                        help="使用するブラウザ")
    parser.add_argument("--no-headless", dest="headless", action="store_false",
                        help="ヘッドレスモードを無効化")
    parser.add_argument("--base-url", type=str,
                        help="ベースURL")
    parser.add_argument("--timeout", type=int,
                        help="タイムアウト（ミリ秒）")
    
    # テストスイート
    parser.add_argument("--suite", choices=["smoke", "regression", "performance", "visual"],
                        help="事前定義されたテストスイートを実行")
    
    # テストファイル
    parser.add_argument("tests", nargs="*",
                        help="実行するテストファイルまたはディレクトリ")
    
    args = parser.parse_args()
    
    # テストスイートの実行
    if args.suite:
        return run_test_suite(args.suite)
    
    # 通常のテスト実行
    return run_parallel_tests(args)


if __name__ == "__main__":
    sys.exit(main())