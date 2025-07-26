#!/usr/bin/env python3
"""バックテスト2の実行状況を確認するスクリプト"""

import os
import json
import glob
from datetime import datetime, timedelta

def check_status():
    print("=== バックテスト2 実行状況確認 ===")
    print(f"確認時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. ログファイルの最終更新時刻
    log_file = "/Users/y-sato/TradingAgents2/auto_backtest.log"
    if os.path.exists(log_file):
        mtime = os.path.getmtime(log_file)
        last_update = datetime.fromtimestamp(mtime)
        time_diff = datetime.now() - last_update
        print(f"ログファイル最終更新: {last_update.strftime('%Y-%m-%d %H:%M:%S')} ({time_diff.seconds//60}分前)")
        
        # 最後の5行を表示
        with open(log_file, 'r') as f:
            lines = f.readlines()
            print("\n最新のログ:")
            for line in lines[-5:]:
                print(f"  {line.strip()}")
    
    # 2. 結果ディレクトリの確認
    print("\n結果ファイル:")
    result_dirs = glob.glob("/Users/y-sato/TradingAgents2/results/backtest*")
    if result_dirs:
        latest_dir = max(result_dirs, key=os.path.getmtime)
        print(f"最新の結果ディレクトリ: {latest_dir}")
        
        # 結果ファイルを確認
        result_files = glob.glob(f"{latest_dir}/**/*.json", recursive=True)
        for file in result_files[:5]:
            print(f"  - {os.path.basename(file)}")
    else:
        print("  結果ディレクトリが見つかりません")
    
    # 3. プロセス状態
    print("\nプロセス状態:")
    import subprocess
    result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    python_processes = [line for line in result.stdout.split('\n') if 'python' in line and 'backtest' in line]
    
    if python_processes:
        print("  実行中のバックテストプロセス:")
        for proc in python_processes:
            print(f"    {proc[:100]}...")
    else:
        print("  実行中のバックテストプロセスなし")
    
    # 4. 実行サマリー
    print("\n実行サマリー:")
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            content = f.read()
            
        # 実行した銘柄を確認
        executed_symbols = []
        if "Executed BUY" in content:
            lines = content.split('\n')
            for line in lines:
                if "Executed BUY" in line and "shares of" in line:
                    parts = line.split("shares of")
                    if len(parts) > 1:
                        symbol = parts[1].split()[0]
                        executed_symbols.append(symbol)
        
        print(f"  実行済み銘柄: {', '.join(executed_symbols) if executed_symbols else 'なし'}")
        
        # 最終決定を確認
        decisions = []
        for line in content.split('\n'):
            if "Final decision for" in line:
                decisions.append(line.strip())
        
        if decisions:
            print("  最終決定:")
            for decision in decisions[-3:]:
                print(f"    {decision}")

if __name__ == "__main__":
    check_status()