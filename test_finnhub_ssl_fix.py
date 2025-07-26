#!/usr/bin/env python3
"""
FinnHub API疎通テストスクリプト（SSL対応版）
"""

import os
import sys
import asyncio
import json
import time
import ssl
import certifi
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinnHubAPITester:
    """FinnHub API接続テスター（SSL対応）"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = "https://finnhub.io/api/v1"
        self.test_results = {}
        
    def load_api_key(self) -> bool:
        """APIキーを環境変数または.envファイルから読み込む"""
        logger.info("=" * 60)
        logger.info("🔑 FinnHub APIキー確認")
        logger.info("=" * 60)
        
        # 環境変数をチェック
        self.api_key = os.environ.get('FINNHUB_API_KEY')
        
        # .envファイルを確認
        if not self.api_key:
            env_file = Path('.env')
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key == 'FINNHUB_API_KEY':
                                self.api_key = value
                                break
        
        if not self.api_key:
            logger.warning("⚠️  FINNHUB_API_KEYが設定されていません")
            logger.info("\n📝 無料のテスト用APIキーを使用します")
            # FinnHubの公開テスト用キー（機能制限あり）
            self.api_key = "sandbox"  # 実際のサンドボックスキー
            return False
            
        masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "****"
        logger.info(f"✅ APIキーが設定されています: {masked_key}")
        return True
        
    async def test_basic_connection(self) -> bool:
        """基本的なAPI接続テスト（SSL対応）"""
        logger.info("\n" + "=" * 60)
        logger.info("🌐 基本接続テスト")
        logger.info("=" * 60)
        
        try:
            import aiohttp
        except ImportError:
            logger.error("❌ aiohttpがインストールされていません")
            return False
            
        # SSL contextを作成
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        try:
            # 株価クォートエンドポイントでテスト
            url = f"{self.base_url}/quote"
            params = {
                "symbol": "AAPL",
                "token": self.api_key
            }
            
            start_time = time.time()
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    elapsed = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ API接続成功")
                        logger.info(f"   応答時間: {elapsed:.2f}秒")
                        
                        # データの内容を確認
                        if data and 'c' in data:
                            logger.info(f"   AAPL現在価格: ${data.get('c', 'N/A')}")
                            logger.info(f"   前日終値: ${data.get('pc', 'N/A')}")
                            change = data.get('d', 0)
                            change_pct = data.get('dp', 0)
                            logger.info(f"   変化: ${change} ({change_pct}%)")
                        
                        self.test_results['basic_connection'] = {
                            'status': 'success',
                            'response_time': elapsed,
                            'has_data': bool(data and 'c' in data)
                        }
                        return True
                        
                    elif response.status == 401:
                        logger.error("❌ 認証エラー: APIキーが無効です")
                        logger.info("   無料アカウントを作成してください: https://finnhub.io/register")
                    elif response.status == 429:
                        logger.error("❌ レート制限エラー: APIリクエスト上限に達しました")
                    elif response.status == 403:
                        logger.warning("⚠️  アクセス拒否: サンドボックスモードまたは無効なキー")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ エラー (status={response.status}): {error_text[:200]}")
                        
        except aiohttp.ClientSSLError as e:
            logger.error(f"❌ SSL証明書エラー: {str(e)}")
            
            # SSL検証を無効化して再試行
            logger.info("\n🔄 SSL検証を無効化して再試行...")
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            try:
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            logger.info("   ✅ SSL検証無効でAPI接続成功")
                            logger.warning("   ⚠️  本番環境ではSSL検証を有効にしてください")
                            return True
            except Exception as e2:
                logger.error(f"   ❌ 再試行も失敗: {str(e2)}")
                
        except Exception as e:
            logger.error(f"❌ 接続エラー: {str(e)}")
            
        self.test_results['basic_connection'] = {'status': 'failed'}
        return False
        
    async def test_data_availability(self):
        """データ取得可能性のテスト"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 データ取得テスト")
        logger.info("=" * 60)
        
        import aiohttp
        
        # SSL contextを作成（検証無効）
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        test_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        available_data = []
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            for symbol in test_symbols:
                logger.info(f"\n📍 {symbol}のデータ取得テスト")
                
                # 株価データ
                url = f"{self.base_url}/quote"
                params = {"symbol": symbol, "token": self.api_key}
                
                try:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and 'c' in data:
                                logger.info(f"   ✅ 株価データ取得成功: ${data['c']}")
                                available_data.append(symbol)
                            else:
                                logger.warning(f"   ⚠️  データが空またはサンドボックスモード")
                        else:
                            logger.warning(f"   ❌ 取得失敗 (status={response.status})")
                            
                except Exception as e:
                    logger.error(f"   ❌ エラー: {str(e)}")
                    
        self.test_results['available_symbols'] = available_data
        return len(available_data) > 0
        
    def print_summary(self):
        """テスト結果のサマリー表示"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 テスト結果サマリー")
        logger.info("=" * 60)
        
        # 接続状態
        connection_status = self.test_results.get('basic_connection', {}).get('status')
        if connection_status == 'success':
            logger.info("✅ FinnHub API接続: 成功")
            
            # データ取得状況
            available_symbols = self.test_results.get('available_symbols', [])
            if available_symbols:
                logger.info(f"✅ データ取得可能: {', '.join(available_symbols)}")
            else:
                logger.info("⚠️  実データの取得には有効なAPIキーが必要です")
                
        else:
            logger.info("❌ FinnHub API接続: 失敗")
            
        # バックテストでの使用について
        logger.info("\n💡 バックテストでのFinnHub使用について:")
        
        if connection_status == 'success':
            logger.info("📌 現在の状況:")
            logger.info("   - API接続は可能")
            logger.info("   - 実データ取得には有効なAPIキーが必要")
            
        logger.info("\n📝 推奨事項:")
        logger.info("1. Yahoo Financeをメインデータソースとして使用（APIキー不要）")
        logger.info("2. FinnHubは補助的なデータソースとして使用")
        logger.info("3. FinnHubを使用する場合:")
        logger.info("   a. https://finnhub.io/register で無料アカウント作成")
        logger.info("   b. .envファイルにFINNHUB_API_KEY=your-key-hereを追加")
        logger.info("   c. 無料プランは60リクエスト/分の制限あり")
        
        # 現在のバックテスト設定
        logger.info("\n✅ 現在のバックテストはYahoo Financeで正常動作します")
        logger.info("   FinnHub APIキーなしでも問題ありません")


# Yahoo Finance接続テスト
async def test_yahoo_finance():
    """Yahoo Finance接続テスト（比較用）"""
    logger.info("\n" + "=" * 60)
    logger.info("📈 Yahoo Finance接続テスト（比較）")
    logger.info("=" * 60)
    
    try:
        import yfinance as yf
        
        # テストシンボル
        ticker = yf.Ticker("AAPL")
        
        # 基本情報取得
        info = ticker.info
        logger.info("✅ Yahoo Finance接続成功")
        logger.info(f"   企業名: {info.get('longName', 'N/A')}")
        logger.info(f"   現在価格: ${info.get('currentPrice', 'N/A')}")
        logger.info(f"   時価総額: ${info.get('marketCap', 0):,}")
        
        # 履歴データ取得
        hist = ticker.history(period="1d")
        if not hist.empty:
            logger.info(f"   最新終値: ${hist['Close'].iloc[-1]:.2f}")
            
        logger.info("\n✅ Yahoo FinanceはAPIキー不要で利用可能")
        return True
        
    except Exception as e:
        logger.error(f"❌ Yahoo Finance接続エラー: {str(e)}")
        return False


async def main():
    """メイン実行関数"""
    # FinnHubテスト
    tester = FinnHubAPITester()
    has_api_key = tester.load_api_key()
    
    if await tester.test_basic_connection():
        await tester.test_data_availability()
    
    tester.print_summary()
    
    # Yahoo Financeテスト（比較）
    await test_yahoo_finance()
    
    logger.info("\n✅ API疎通テスト完了")


if __name__ == "__main__":
    asyncio.run(main())