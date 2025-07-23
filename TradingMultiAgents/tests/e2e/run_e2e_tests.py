#!/usr/bin/env python3
"""
E2Eテスト実行スクリプト
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime


def run_tests(args):
    """E2Eテストを実行"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Pytestコマンドの構築
    pytest_args = [
        "pytest",
        "tests/e2e/",
        "-v",  # 詳細出力
        "--tb=short",  # トレースバックを短縮
        f"--html=tests/reports/e2e_report_{timestamp}.html",
        "--self-contained-html",
        "--screenshot=only-on-failure",
    ]
    
    # ブラウザ指定
    if args.browser:
        pytest_args.extend(["--browser", args.browser])
    
    # スモークテストのみ
    if args.smoke:
        pytest_args.extend(["-m", "smoke"])
    
    # 並列実行
    if args.parallel:
        pytest_args.extend(["-n", str(args.parallel)])
    
    # ヘッドレスモード
    if args.headless:
        pytest_args.append("--headed")  # Playwrightのデフォルトはヘッドレス
    
    # 特定のテスト実行
    if args.test:
        pytest_args.extend(["-k", args.test])
    
    print("🧪 E2Eテストを実行中...")
    print(f"コマンド: {' '.join(pytest_args)}")
    
    # テスト実行
    result = subprocess.run(pytest_args)
    
    # レポートの場所を表示
    print(f"\n📊 テストレポート: tests/reports/e2e_report_{timestamp}.html")
    
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="E2Eテスト実行スクリプト")
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="使用するブラウザ"
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="スモークテストのみ実行"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        metavar="N",
        help="並列実行数"
    )
    parser.add_argument(
        "--headless",
        action="store_false",
        help="ヘッドレスモードで実行（デフォルト）"
    )
    parser.add_argument(
        "--test",
        help="特定のテストを実行（例: test_navigation）"
    )
    
    args = parser.parse_args()
    
    # 必要なパッケージの確認
    required_packages = ["playwright", "pytest", "pytest-playwright", "pytest-html"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 必要なパッケージがインストールされていません: {', '.join(missing_packages)}")
        print(f"インストール: pip install {' '.join(missing_packages)}")
        sys.exit(1)
    
    # Playwrightのブラウザがインストールされているか確認
    browser_check = subprocess.run(
        ["playwright", "install", "--dry-run"],
        capture_output=True,
        text=True
    )
    
    if "No browsers are installed" in browser_check.stdout:
        print("📥 Playwrightブラウザをインストール中...")
        subprocess.run(["playwright", "install"])
    
    # テスト実行
    exit_code = run_tests(args)
    
    if exit_code == 0:
        print("\n✅ すべてのテストが成功しました！")
    else:
        print(f"\n❌ テストが失敗しました（終了コード: {exit_code}）")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()