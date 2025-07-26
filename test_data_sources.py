#!/usr/bin/env python3
"""
バックテストで使用するデータソースの接続テスト
- Yahoo Finance
- FinnHub
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_yahoo_finance():
    """Yahoo Finance接続テスト"""
    logger.info("=" * 60)
    logger.info("📈 Yahoo Finance接続テスト")
    logger.info("=" * 60)
    
    try:
        # プロジェクトルートからインポート
        sys.path.insert(0, '/Users/y-sato/TradingAgents2')
        from backtest2.data.yahoo_source import YahooDataSource
        
        logger.info("✅ YahooDataSourceモジュールのインポート成功")
        
        # データソースを初期化
        yahoo_source = YahooDataSource()
        
        # テストシンボルでデータ取得
        test_symbol = "AAPL"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        logger.info(f"\n📍 {test_symbol}の過去30日間のデータを取得中...")
        
        try:
            # get_historical_dataメソッドを使用
            data = yahoo_source.get_historical_data(
                symbol=test_symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if data is not None and not data.empty:
                logger.info(f"✅ データ取得成功")
                logger.info(f"   データ件数: {len(data)}件")
                logger.info(f"   期間: {data.index[0]} 〜 {data.index[-1]}")
                logger.info(f"   最新終値: ${data['Close'].iloc[-1]:.2f}")
                logger.info(f"   最高値: ${data['High'].max():.2f}")
                logger.info(f"   最安値: ${data['Low'].min():.2f}")
                
                return True
            else:
                logger.warning("⚠️  データが空です")
                return False
                
        except Exception as e:
            logger.error(f"❌ データ取得エラー: {str(e)}")
            return False
            
    except ImportError as e:
        logger.error(f"❌ モジュールインポートエラー: {str(e)}")
        
        # 直接yfinanceを試す
        logger.info("\n🔄 yfinanceを直接テスト...")
        try:
            import subprocess
            result = subprocess.run(
                ["python", "-c", "import yfinance as yf; print(yf.Ticker('AAPL').info.get('currentPrice', 'N/A'))"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info(f"✅ yfinance直接実行成功: 現在価格 ${result.stdout.strip()}")
            else:
                logger.error(f"❌ yfinance実行エラー: {result.stderr}")
        except Exception as e2:
            logger.error(f"❌ 直接実行エラー: {str(e2)}")
            
        return False


def test_finnhub_connection():
    """FinnHub接続確認（簡易版）"""
    logger.info("\n" + "=" * 60)
    logger.info("🌐 FinnHub接続確認")
    logger.info("=" * 60)
    
    # APIキー確認
    finnhub_key = os.environ.get('FINNHUB_API_KEY')
    
    # .envファイルを確認
    if not finnhub_key:
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if 'FINNHUB_API_KEY=' in line:
                        finnhub_key = line.split('=', 1)[1].strip()
                        break
    
    if finnhub_key:
        logger.info("✅ FinnHub APIキーが設定されています")
        logger.info("   バックテストでFinnHubデータソースを使用可能")
    else:
        logger.info("⚠️  FinnHub APIキーが設定されていません")
        logger.info("   設定方法:")
        logger.info("   1. https://finnhub.io/register で無料アカウント作成")
        logger.info("   2. .envファイルに追加: FINNHUB_API_KEY=your-key-here")
        logger.info("\n📌 注: FinnHubなしでもYahoo Financeのみで動作可能")
        
    return finnhub_key is not None


def print_backtest_data_config():
    """バックテストのデータ設定推奨事項"""
    logger.info("\n" + "=" * 60)
    logger.info("💡 バックテストのデータソース設定")
    logger.info("=" * 60)
    
    yahoo_ok = test_yahoo_finance()
    finnhub_ok = test_finnhub_connection()
    
    logger.info("\n📊 利用可能なデータソース:")
    if yahoo_ok:
        logger.info("✅ Yahoo Finance - 利用可能（推奨）")
    else:
        logger.info("❌ Yahoo Finance - エラー")
        
    if finnhub_ok:
        logger.info("✅ FinnHub - APIキー設定済み")
    else:
        logger.info("⚠️  FinnHub - APIキー未設定（オプション）")
        
    logger.info("\n📝 推奨設定:")
    if yahoo_ok:
        logger.info("1. WebUIのバックテスト設定:")
        logger.info("   - データソース: Yahoo Finance（デフォルト）")
        logger.info("   - APIキー不要で即座に使用可能")
        
        if finnhub_ok:
            logger.info("\n2. FinnHubも併用する場合:")
            logger.info("   - 追加のニュースデータや詳細な財務データが利用可能")
            logger.info("   - レート制限に注意（無料: 60req/分）")
    else:
        logger.info("⚠️  データソースに問題があります")
        logger.info("以下を確認してください:")
        logger.info("1. インターネット接続")
        logger.info("2. Pythonパッケージの再インストール:")
        logger.info("   pip install yfinance pandas numpy")
        
    # 結果を保存
    results = {
        "timestamp": datetime.now().isoformat(),
        "yahoo_finance": "available" if yahoo_ok else "error",
        "finnhub": "configured" if finnhub_ok else "not_configured",
        "recommendation": "Yahoo Finance is ready for use" if yahoo_ok else "Check installation"
    }
    
    with open("data_source_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"\n📁 テスト結果を保存: data_source_test_results.json")


if __name__ == "__main__":
    print_backtest_data_config()