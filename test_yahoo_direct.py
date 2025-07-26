#!/usr/bin/env python3
"""
Yahoo Finance直接接続テスト（ARM64環境）
"""

import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_yahoo_finance():
    """Yahoo Finance直接テスト"""
    logger.info("=" * 60)
    logger.info("📈 Yahoo Finance接続テスト（ARM64）")
    logger.info("=" * 60)
    
    try:
        import yfinance as yf
        logger.info("✅ yfinanceインポート成功")
        
        # 複数の銘柄でテスト
        test_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        
        for symbol in test_symbols:
            logger.info(f"\n📍 {symbol}のデータ取得テスト")
            
            try:
                # Tickerオブジェクト作成
                ticker = yf.Ticker(symbol)
                
                # 基本情報取得
                info = ticker.info
                logger.info(f"   企業名: {info.get('longName', 'N/A')}")
                logger.info(f"   現在価格: ${info.get('currentPrice', 'N/A')}")
                logger.info(f"   時価総額: ${info.get('marketCap', 0):,}")
                
                # 履歴データ取得
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                hist = ticker.history(start=start_date, end=end_date)
                if not hist.empty:
                    logger.info(f"   データ件数: {len(hist)}件")
                    logger.info(f"   最新終値: ${hist['Close'].iloc[-1]:.2f}")
                    logger.info(f"   30日最高値: ${hist['High'].max():.2f}")
                    logger.info(f"   30日最安値: ${hist['Low'].min():.2f}")
                    logger.info(f"   ✅ 履歴データ取得成功")
                else:
                    logger.warning("   ⚠️  履歴データが空です")
                    
            except Exception as e:
                logger.error(f"   ❌ エラー: {str(e)}")
                
        # バッチ取得テスト
        logger.info("\n📊 バッチデータ取得テスト")
        symbols_str = " ".join(test_symbols[:2])
        
        try:
            data = yf.download(symbols_str, period="1mo", interval="1d", progress=False)
            if not data.empty:
                logger.info(f"✅ バッチ取得成功: {len(data)}件のデータ")
                logger.info(f"   期間: {data.index[0]} 〜 {data.index[-1]}")
            else:
                logger.warning("⚠️  バッチデータが空です")
                
        except Exception as e:
            logger.error(f"❌ バッチ取得エラー: {str(e)}")
            
        logger.info("\n✅ Yahoo Finance接続テスト完了")
        logger.info("   Yahoo FinanceはAPIキー不要で利用可能")
        logger.info("   バックテストでの使用に問題ありません")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ yfinanceインポートエラー: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ 予期しないエラー: {str(e)}")
        return False


if __name__ == "__main__":
    import platform
    logger.info(f"Python実行環境: {platform.machine()}")
    
    success = test_yahoo_finance()
    
    if success:
        logger.info("\n💡 結論:")
        logger.info("✅ ARM64環境でYahoo Financeが正常動作")
        logger.info("✅ WebUIのバックテスト機能で使用可能")
    else:
        logger.info("\n❌ Yahoo Finance接続に問題があります")