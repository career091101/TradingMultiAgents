#!/usr/bin/env python3
"""
バックテスト自動実行スクリプト
Seleniumを使用してWebUIを自動操作し、バックテストを実行
"""

import time
import sys
import os
from datetime import datetime
import json
import logging
from typing import Dict, Any, Optional

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_backtest.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Streamlit APIを使用した直接実行
def run_backtest_directly():
    """StreamlitのAPIを使わずに直接バックテストを実行"""
    logger.info("=== バックテスト自動実行開始 ===")
    
    # 環境変数を設定
    os.environ['OPENAI_API_KEY'] = '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'
    
    try:
        # backtest2モジュールをインポート
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from backtest2.core.config import BacktestConfig, LLMConfig
        from backtest2.core.engine import BacktestEngine
        from datetime import datetime, timedelta
        
        # 1. バックテスト設定
        logger.info("1. バックテスト設定を準備")
        
        # デフォルト設定
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        config = BacktestConfig(
            name="AutoBacktest_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            symbols=["AAPL", "MSFT"],
            start_date=start_date,
            end_date=end_date,
            initial_capital=100000.0,
            llm_config=LLMConfig(
                deep_think_model="o3",
                quick_think_model="o4-mini",
                temperature=0.0,
                max_tokens=5000
            )
        )
        
        logger.info(f"設定内容: {config.name}")
        logger.info(f"銘柄: {config.symbols}")
        logger.info(f"期間: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        # 2. バックテスト実行
        logger.info("2. バックテストエンジンを初期化")
        engine = BacktestEngine(config)
        
        logger.info("3. バックテスト実行開始")
        start_time = time.time()
        
        # 非同期実行を同期的に実行
        import asyncio
        result = asyncio.run(engine.run())
        
        execution_time = time.time() - start_time
        logger.info(f"4. バックテスト完了 (実行時間: {execution_time:.2f}秒)")
        
        # 5. 結果分析
        logger.info("5. 実行結果を分析")
        
        # エラーチェック
        errors = []
        warnings = []
        
        if hasattr(result, 'trades'):
            trade_count = len(result.trades)
            logger.info(f"取引数: {trade_count}")
            if trade_count == 0:
                warnings.append("取引が0件です")
        else:
            errors.append("取引データが見つかりません")
        
        if hasattr(result, 'metrics'):
            logger.info(f"メトリクス: {result.metrics}")
        else:
            warnings.append("メトリクスデータがありません")
        
        # 6. 結果レポート
        logger.info("6. 実行結果レポート")
        
        report = {
            "execution_time": datetime.now().isoformat(),
            "status": "error" if errors else ("warning" if warnings else "success"),
            "execution_duration": f"{execution_time:.2f}秒",
            "errors": errors,
            "warnings": warnings,
            "config": {
                "symbols": config.symbols,
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "initial_capital": config.initial_capital
            }
        }
        
        if hasattr(result, 'trades'):
            report["trades"] = len(result.trades)
        
        if hasattr(result, 'metrics') and result.metrics:
            report["metrics"] = {
                "total_return": getattr(result.metrics, 'total_return', None),
                "sharpe_ratio": getattr(result.metrics, 'sharpe_ratio', None),
                "max_drawdown": getattr(result.metrics, 'max_drawdown', None)
            }
        
        # レポート保存
        report_file = f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"レポート保存: {report_file}")
        
        # 問題判定
        if errors:
            logger.error("=== エラーが発生しました ===")
            for error in errors:
                logger.error(f"- {error}")
            logger.error("\n根本原因分析:")
            logger.error("1. APIキーが正しく設定されていない可能性")
            logger.error("2. データソースへの接続エラー")
            logger.error("3. バックテストエンジンの初期化エラー")
            logger.error("\n推奨対処法:")
            logger.error("- 環境変数OPENAI_API_KEYを確認")
            logger.error("- ネットワーク接続を確認")
            logger.error("- ログファイルを詳細に確認")
            return False
        
        elif warnings:
            logger.warning("=== 警告があります ===")
            for warning in warnings:
                logger.warning(f"- {warning}")
            logger.warning("\n考えられる原因:")
            logger.warning("1. 市場が休場日")
            logger.warning("2. エージェントの判断がすべてHOLD")
            logger.warning("3. リスク設定が厳しすぎる")
        
        else:
            logger.info("=== バックテスト正常完了 ===")
            
        return True
        
    except Exception as e:
        logger.error(f"=== 予期しないエラーが発生しました ===")
        logger.error(f"エラー: {str(e)}")
        logger.error(f"エラータイプ: {type(e).__name__}")
        logger.error(f"発生時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # システム情報
        try:
            import psutil
            logger.error(f"\nシステム状態:")
            logger.error(f"- メモリ使用率: {psutil.virtual_memory().percent}%")
            logger.error(f"- CPU使用率: {psutil.cpu_percent(interval=1)}%")
            logger.error(f"- 利用可能メモリ: {psutil.virtual_memory().available / (1024**3):.2f} GB")
        except:
            logger.error("システム情報取得失敗")
        
        import traceback
        logger.error("\nスタックトレース:")
        logger.error(traceback.format_exc())
        
        logger.error("\n根本原因分析:")
        if "ModuleNotFoundError" in str(type(e)):
            logger.error("- 必要なモジュールがインストールされていません")
            logger.error("推奨: pip install -r requirements.txt")
        elif "401" in str(e) or "API" in str(e):
            logger.error("- APIキーの問題です")
            logger.error("推奨: 環境変数OPENAI_API_KEYを確認")
        elif "timeout" in str(e).lower():
            logger.error("- タイムアウトエラーです")
            logger.error("推奨: ネットワーク接続を確認、タイムアウト値を増加")
        elif "memory" in str(e).lower():
            logger.error("- メモリ不足の可能性があります")
            logger.error("推奨: 不要なプロセスを終了、バッチサイズを削減")
        else:
            logger.error("- システムエラーの可能性があります")
            logger.error("推奨: ログを確認して開発者に報告")
        
        return False

if __name__ == "__main__":
    # 直接実行
    success = run_backtest_directly()
    sys.exit(0 if success else 1)