#!/usr/bin/env python3
"""
WebUI経由でバックテストの状態を確認するスクリプト
"""

import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_webui_status():
    """WebUIの状態を確認"""
    try:
        # WebUIの健全性確認
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            logger.info("✓ WebUIは正常に稼働中")
            return True
        else:
            logger.error(f"✗ WebUI応答エラー: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ WebUI接続エラー: {e}")
        return False

def get_recent_results():
    """最新の実行結果を取得"""
    import os
    import glob
    
    # 結果ディレクトリを確認
    result_dirs = glob.glob("/Users/y-sato/TradingAgents2/results/backtest2_*")
    
    if result_dirs:
        latest_dir = max(result_dirs, key=os.path.getmtime)
        logger.info(f"最新の結果ディレクトリ: {latest_dir}")
        
        # 結果ファイルを確認
        result_files = glob.glob(f"{latest_dir}/**/*.json", recursive=True)
        
        for file in result_files:
            logger.info(f"結果ファイル: {file}")
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    if 'trades' in data:
                        logger.info(f"  取引数: {len(data['trades'])}")
                    if 'metrics' in data:
                        logger.info(f"  メトリクス: {data['metrics']}")
            except:
                pass
    else:
        logger.warning("結果ディレクトリが見つかりません")

def main():
    logger.info("=== WebUI状態確認 ===")
    
    # 1. WebUI状態確認
    if check_webui_status():
        logger.info("\nWebUIでバックテストを実行するには:")
        logger.info("1. ブラウザで http://localhost:8501 を開く")
        logger.info("2. 「バックテスト2」タブを選択")
        logger.info("3. 設定を入力して「バックテスト実行」をクリック")
        
        # 2. 既存の結果を確認
        logger.info("\n=== 既存の実行結果 ===")
        get_recent_results()
        
        # 3. 実行中のバックテストログを確認
        logger.info("\n=== 実行中のバックテストを確認 ===")
        try:
            with open("/Users/y-sato/TradingAgents2/auto_backtest.log", 'r') as f:
                lines = f.readlines()
                if lines:
                    logger.info("最新のログ:")
                    for line in lines[-10:]:
                        print(f"  {line.strip()}")
        except:
            logger.info("実行中のバックテストはありません")

if __name__ == "__main__":
    main()