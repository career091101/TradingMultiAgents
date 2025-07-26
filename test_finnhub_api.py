#!/usr/bin/env python3
"""
FinnHub API疎通テストスクリプト
- API接続の確認
- 各エンドポイントのテスト
- データ取得の確認
"""

import os
import sys
import asyncio
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


class FinnHubAPITester:
    """FinnHub API接続テスター"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = "https://finnhub.io/api/v1"
        self.test_results = {}
        
    def load_api_key(self) -> bool:
        """APIキーを環境変数または.envファイルから読み込む"""
        logger.info("=" * 60)
        logger.info("🔑 FinnHub APIキー確認")
        logger.info("=" * 60)
        
        # まず環境変数をチェック
        self.api_key = os.environ.get('FINNHUB_API_KEY')
        
        # 環境変数にない場合は.envファイルを確認
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
            logger.warning("❌ FINNHUB_API_KEYが設定されていません")
            logger.info("\n📝 FinnHub APIキーの取得方法:")
            logger.info("1. https://finnhub.io/register にアクセス")
            logger.info("2. 無料アカウントを作成")
            logger.info("3. ダッシュボードからAPIキーを取得")
            logger.info("4. 以下のコマンドで設定:")
            logger.info("   export FINNHUB_API_KEY='your-api-key'")
            logger.info("   または .env ファイルに追加:")
            logger.info("   FINNHUB_API_KEY=your-api-key")
            
            # デモ用のサンプルキーを使用
            logger.info("\n🔄 デモ用サンプルキーでテストを実行します...")
            self.api_key = "sandbox_api_key"  # これは実際には動作しません
            return False
            
        masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "****"
        logger.info(f"✅ APIキーが設定されています: {masked_key}")
        return True
        
    async def test_basic_connection(self) -> bool:
        """基本的なAPI接続テスト"""
        logger.info("\n" + "=" * 60)
        logger.info("🌐 基本接続テスト")
        logger.info("=" * 60)
        
        try:
            import aiohttp
        except ImportError:
            logger.error("❌ aiohttpがインストールされていません")
            logger.error("インストール: pip install aiohttp")
            return False
            
        try:
            # 株価クォートエンドポイントでテスト
            url = f"{self.base_url}/quote"
            params = {
                "symbol": "AAPL",
                "token": self.api_key
            }
            
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    elapsed = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ API接続成功")
                        logger.info(f"   応答時間: {elapsed:.2f}秒")
                        logger.info(f"   AAPL現在価格: ${data.get('c', 'N/A')}")
                        
                        self.test_results['basic_connection'] = {
                            'status': 'success',
                            'response_time': elapsed,
                            'data': data
                        }
                        return True
                    elif response.status == 401:
                        logger.error("❌ 認証エラー: APIキーが無効です")
                    elif response.status == 429:
                        logger.error("❌ レート制限エラー: APIリクエスト上限に達しました")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ エラー (status={response.status}): {error_text}")
                        
        except Exception as e:
            logger.error(f"❌ 接続エラー: {str(e)}")
            
        self.test_results['basic_connection'] = {'status': 'failed'}
        return False
        
    async def test_endpoints(self):
        """主要エンドポイントのテスト"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 エンドポイントテスト")
        logger.info("=" * 60)
        
        import aiohttp
        
        endpoints_to_test = [
            {
                "name": "株価クォート",
                "endpoint": "/quote",
                "params": {"symbol": "AAPL"}
            },
            {
                "name": "企業プロファイル",
                "endpoint": "/stock/profile2", 
                "params": {"symbol": "AAPL"}
            },
            {
                "name": "マーケットニュース",
                "endpoint": "/news",
                "params": {"category": "general"}
            },
            {
                "name": "企業ニュース",
                "endpoint": "/company-news",
                "params": {
                    "symbol": "AAPL",
                    "from": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                    "to": datetime.now().strftime("%Y-%m-%d")
                }
            },
            {
                "name": "基本的な財務指標",
                "endpoint": "/stock/metric",
                "params": {"symbol": "AAPL", "metric": "all"}
            },
            {
                "name": "株価ローソク足データ",
                "endpoint": "/stock/candle",
                "params": {
                    "symbol": "AAPL",
                    "resolution": "D",
                    "from": str(int((datetime.now() - timedelta(days=30)).timestamp())),
                    "to": str(int(datetime.now().timestamp()))
                }
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for test in endpoints_to_test:
                logger.info(f"\n📍 テスト中: {test['name']}")
                
                url = f"{self.base_url}{test['endpoint']}"
                params = {**test['params'], "token": self.api_key}
                
                try:
                    start_time = time.time()
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        elapsed = time.time() - start_time
                        
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"   ✅ 成功")
                            logger.info(f"   応答時間: {elapsed:.2f}秒")
                            
                            # データのサンプルを表示
                            if isinstance(data, list) and len(data) > 0:
                                logger.info(f"   データ件数: {len(data)}件")
                                if test['name'] == "マーケットニュース":
                                    logger.info(f"   最新ニュース: {data[0].get('headline', 'N/A')[:50]}...")
                            elif isinstance(data, dict):
                                if test['name'] == "株価クォート":
                                    logger.info(f"   現在価格: ${data.get('c', 'N/A')}")
                                    logger.info(f"   前日終値: ${data.get('pc', 'N/A')}")
                                    logger.info(f"   変化率: {data.get('dp', 'N/A')}%")
                                elif test['name'] == "企業プロファイル":
                                    logger.info(f"   企業名: {data.get('name', 'N/A')}")
                                    logger.info(f"   業界: {data.get('finnhubIndustry', 'N/A')}")
                                    
                            self.test_results[test['endpoint']] = {
                                'status': 'success',
                                'response_time': elapsed
                            }
                            
                        else:
                            logger.warning(f"   ⚠️  エラー (status={response.status})")
                            self.test_results[test['endpoint']] = {
                                'status': 'failed',
                                'status_code': response.status
                            }
                            
                except Exception as e:
                    logger.error(f"   ❌ エラー: {str(e)}")
                    self.test_results[test['endpoint']] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    
    async def test_rate_limits(self):
        """APIレート制限のテスト"""
        logger.info("\n" + "=" * 60)
        logger.info("⏱️  レート制限テスト")
        logger.info("=" * 60)
        
        import aiohttp
        
        # 無料プランのレート制限を確認
        logger.info("FinnHub無料プランのレート制限:")
        logger.info("- 60リクエスト/分")
        logger.info("- 30リクエスト/秒")
        
        # 5つの並行リクエストをテスト
        logger.info("\n5つの並行リクエストを送信...")
        
        async def make_request(session, index):
            url = f"{self.base_url}/quote"
            params = {"symbol": f"AAPL", "token": self.api_key}
            
            try:
                start = time.time()
                async with session.get(url, params=params) as response:
                    elapsed = time.time() - start
                    return index, response.status, elapsed
            except Exception as e:
                return index, 0, str(e)
                
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            results = await asyncio.gather(*[make_request(session, i) for i in range(5)])
            total_time = time.time() - start_time
            
            logger.info(f"   総実行時間: {total_time:.2f}秒")
            
            success_count = sum(1 for _, status, _ in results if status == 200)
            logger.info(f"   成功: {success_count}/5")
            
            for index, status, elapsed in results:
                if isinstance(elapsed, float):
                    logger.info(f"   リクエスト{index}: status={status}, {elapsed:.2f}秒")
                else:
                    logger.info(f"   リクエスト{index}: エラー - {elapsed}")
                    
    def print_summary(self):
        """テスト結果のサマリー表示"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 テスト結果サマリー")
        logger.info("=" * 60)
        
        # 基本接続
        if self.test_results.get('basic_connection', {}).get('status') == 'success':
            logger.info("✅ FinnHub API接続: 成功")
        else:
            logger.info("❌ FinnHub API接続: 失敗")
            
        # 成功したエンドポイント
        successful_endpoints = [ep for ep, result in self.test_results.items() 
                              if result.get('status') == 'success' and ep != 'basic_connection']
        
        if successful_endpoints:
            logger.info(f"\n✅ 利用可能なエンドポイント ({len(successful_endpoints)}個):")
            for ep in successful_endpoints:
                logger.info(f"   - {ep}")
                
        # バックテストでの使用について
        logger.info("\n💡 バックテストでの使用:")
        if self.test_results.get('basic_connection', {}).get('status') == 'success':
            logger.info("✅ FinnHubをデータソースとして使用可能")
            logger.info("\n推奨設定:")
            logger.info("1. .envファイルにFINNHUB_API_KEYを追加")
            logger.info("2. バックテスト設定でdata_sourcesに'finnhub'を含める")
            logger.info("3. 無料プランの場合はレート制限に注意")
        else:
            logger.info("⚠️  FinnHub APIキーが必要です")
            logger.info("代替案: Yahoo Financeをメインデータソースとして使用")
            
        # 結果をファイルに保存
        result_file = "finnhub_test_results.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        logger.info(f"\n📁 詳細な結果を保存しました: {result_file}")


async def main():
    """メイン実行関数"""
    tester = FinnHubAPITester()
    
    # APIキー確認
    has_api_key = tester.load_api_key()
    
    if has_api_key:
        # 各種テスト実行
        if await tester.test_basic_connection():
            await tester.test_endpoints()
            await tester.test_rate_limits()
    else:
        logger.info("\n⚠️  FinnHub APIキーなしでのテスト")
        logger.info("実際のデータは取得できませんが、接続性のみ確認します")
        await tester.test_basic_connection()
    
    # サマリー表示
    tester.print_summary()
    
    logger.info("\n✅ FinnHub API疎通テスト完了")


if __name__ == "__main__":
    asyncio.run(main())