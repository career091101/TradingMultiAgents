#!/usr/bin/env python3
"""
OpenAI API疎通テストスクリプト
- API接続の確認
- 各モデルのレスポンステスト
- エラーハンドリングの確認
"""

import os
import sys
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# OpenAI imports
from openai import AsyncOpenAI, OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIConnectionTester:
    """OpenAI API接続テスター"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.test_results = {}
        
    def check_api_key(self) -> bool:
        """APIキーの存在確認"""
        logger.info("=" * 60)
        logger.info("🔑 APIキー確認")
        logger.info("=" * 60)
        
        if not self.api_key:
            logger.error("❌ OPENAI_API_KEY環境変数が設定されていません")
            return False
            
        # マスクして表示
        masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}"
        logger.info(f"✅ APIキーが設定されています: {masked_key}")
        return True
        
    async def test_basic_connection(self) -> bool:
        """基本的なAPI接続テスト"""
        logger.info("\n" + "=" * 60)
        logger.info("🌐 基本接続テスト")
        logger.info("=" * 60)
        
        try:
            client = AsyncOpenAI(api_key=self.api_key)
            
            # シンプルなテストリクエスト
            start_time = time.time()
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello, this is a test. Reply with 'OK'."}],
                max_tokens=10,
                temperature=0
            )
            elapsed = time.time() - start_time
            
            reply = response.choices[0].message.content
            logger.info(f"✅ API接続成功")
            logger.info(f"   レスポンス: {reply}")
            logger.info(f"   応答時間: {elapsed:.2f}秒")
            
            self.test_results['basic_connection'] = {
                'status': 'success',
                'response_time': elapsed,
                'response': reply
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ API接続失敗: {str(e)}")
            self.test_results['basic_connection'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
            
    async def test_model_availability(self) -> Dict[str, bool]:
        """各モデルの利用可能性テスト"""
        logger.info("\n" + "=" * 60)
        logger.info("🤖 モデル利用可能性テスト")
        logger.info("=" * 60)
        
        models_to_test = {
            "gpt-4o": "GPT-4o (Deep thinking)",
            "gpt-4o-mini": "GPT-4o-mini (Quick thinking)",
            "o3": "O3 (Advanced reasoning)",
            "o4-mini": "O4-mini (Fast reasoning)",
            "gpt-4-turbo": "GPT-4 Turbo",
            "gpt-3.5-turbo": "GPT-3.5 Turbo"
        }
        
        results = {}
        client = AsyncOpenAI(api_key=self.api_key)
        
        for model_id, model_name in models_to_test.items():
            logger.info(f"\n📍 テスト中: {model_name} ({model_id})")
            
            try:
                start_time = time.time()
                
                # o3/o4モデルの特別な設定
                if model_id.startswith(('o3', 'o4')):
                    response = await client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "user", "content": "Test connection. Reply with model name."}],
                        max_completion_tokens=50,  # o-seriesはmax_completion_tokens
                        temperature=1.0  # o-seriesは1.0固定
                    )
                else:
                    response = await client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "user", "content": "Test connection. Reply with model name."}],
                        max_tokens=50,
                        temperature=0
                    )
                
                elapsed = time.time() - start_time
                reply = response.choices[0].message.content
                
                logger.info(f"   ✅ 利用可能")
                logger.info(f"   応答時間: {elapsed:.2f}秒")
                logger.info(f"   レスポンス: {reply[:100]}")
                
                results[model_id] = {
                    'available': True,
                    'response_time': elapsed,
                    'response': reply
                }
                
            except Exception as e:
                error_msg = str(e)
                if "model_not_found" in error_msg or "does not exist" in error_msg:
                    logger.warning(f"   ⚠️  モデルが見つかりません")
                else:
                    logger.error(f"   ❌ エラー: {error_msg[:100]}")
                    
                results[model_id] = {
                    'available': False,
                    'error': error_msg
                }
                
        self.test_results['model_availability'] = results
        return results
        
    async def test_langchain_integration(self) -> bool:
        """LangChain統合のテスト"""
        logger.info("\n" + "=" * 60)
        logger.info("🔗 LangChain統合テスト")
        logger.info("=" * 60)
        
        try:
            # 通常のモデル
            logger.info("\n📍 通常モデル (gpt-4o-mini) テスト")
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=50,
                timeout=30
            )
            
            messages = [
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content="Reply with 'LangChain OK'")
            ]
            
            start_time = time.time()
            response = await llm.ainvoke(messages)
            elapsed = time.time() - start_time
            
            logger.info(f"   ✅ LangChain通常モデル接続成功")
            logger.info(f"   応答時間: {elapsed:.2f}秒")
            logger.info(f"   レスポンス: {response.content}")
            
            self.test_results['langchain_normal'] = {
                'status': 'success',
                'response_time': elapsed
            }
            
            # o-seriesモデルのテスト
            logger.info("\n📍 O-seriesモデル互換性テスト")
            
            # o3モデルの設定をテスト（実際には使わない）
            try:
                o_series_llm = ChatOpenAI(
                    model="gpt-4o",  # o3の代わりにgpt-4oを使用
                    temperature=1.0,
                    max_completion_tokens=50,
                    timeout=60
                )
                
                # ユーザーメッセージのみ（o-seriesスタイル）
                o_messages = [
                    HumanMessage(content="Test o-series compatibility. Reply with 'OK'.")
                ]
                
                start_time = time.time()
                response = await o_series_llm.ainvoke(o_messages)
                elapsed = time.time() - start_time
                
                logger.info(f"   ✅ O-series互換設定で接続成功")
                logger.info(f"   応答時間: {elapsed:.2f}秒")
                
                self.test_results['langchain_o_series'] = {
                    'status': 'success',
                    'response_time': elapsed
                }
                
            except Exception as e:
                logger.warning(f"   ⚠️  O-series互換テスト失敗: {str(e)}")
                self.test_results['langchain_o_series'] = {
                    'status': 'failed',
                    'error': str(e)
                }
            
            return True
            
        except Exception as e:
            logger.error(f"❌ LangChain統合テスト失敗: {str(e)}")
            self.test_results['langchain_integration'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
            
    async def test_json_response(self) -> bool:
        """JSON形式レスポンスのテスト"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 JSON形式レスポンステスト")
        logger.info("=" * 60)
        
        try:
            client = AsyncOpenAI(api_key=self.api_key)
            
            prompt = """
            Please respond with a JSON object containing:
            - action: "BUY", "SELL", or "HOLD"
            - confidence: a number between 0 and 1
            - reason: a brief explanation
            
            Example format:
            {"action": "HOLD", "confidence": 0.7, "reason": "Market conditions unclear"}
            """
            
            start_time = time.time()
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0,
                response_format={"type": "json_object"}  # JSON mode
            )
            elapsed = time.time() - start_time
            
            reply = response.choices[0].message.content
            logger.info(f"✅ JSONレスポンス取得成功")
            logger.info(f"   応答時間: {elapsed:.2f}秒")
            
            # JSONパース確認
            parsed_json = json.loads(reply)
            logger.info(f"   パース成功: {json.dumps(parsed_json, ensure_ascii=False)}")
            
            self.test_results['json_response'] = {
                'status': 'success',
                'response_time': elapsed,
                'parsed_json': parsed_json
            }
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSONパースエラー: {e}")
            logger.error(f"   レスポンス: {reply}")
            self.test_results['json_response'] = {
                'status': 'parse_error',
                'error': str(e)
            }
            return False
            
        except Exception as e:
            logger.error(f"❌ JSONレスポンステスト失敗: {str(e)}")
            self.test_results['json_response'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
            
    async def test_concurrent_requests(self) -> bool:
        """並行リクエストのテスト"""
        logger.info("\n" + "=" * 60)
        logger.info("🚀 並行リクエストテスト")
        logger.info("=" * 60)
        
        try:
            client = AsyncOpenAI(api_key=self.api_key)
            
            async def make_request(index: int):
                start = time.time()
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": f"Test request {index}. Reply with the number."}],
                    max_tokens=10,
                    temperature=0
                )
                elapsed = time.time() - start
                return index, elapsed, response.choices[0].message.content
            
            # 5つの並行リクエスト
            logger.info("   5つの並行リクエストを送信中...")
            start_time = time.time()
            tasks = [make_request(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            logger.info(f"✅ 並行リクエスト完了")
            logger.info(f"   総実行時間: {total_time:.2f}秒")
            
            for index, elapsed, response in results:
                logger.info(f"   リクエスト{index}: {elapsed:.2f}秒 - {response}")
                
            self.test_results['concurrent_requests'] = {
                'status': 'success',
                'total_time': total_time,
                'request_count': len(results)
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ 並行リクエストテスト失敗: {str(e)}")
            self.test_results['concurrent_requests'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
            
    def print_summary(self):
        """テスト結果のサマリー表示"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 テスト結果サマリー")
        logger.info("=" * 60)
        
        # 基本接続
        if 'basic_connection' in self.test_results:
            status = self.test_results['basic_connection']['status']
            if status == 'success':
                logger.info("✅ 基本接続: 成功")
            else:
                logger.info("❌ 基本接続: 失敗")
                
        # モデル利用可能性
        if 'model_availability' in self.test_results:
            models = self.test_results['model_availability']
            available = [m for m, r in models.items() if r['available']]
            unavailable = [m for m, r in models.items() if not r['available']]
            
            logger.info(f"\n📍 利用可能なモデル ({len(available)}個):")
            for model in available:
                logger.info(f"   ✅ {model}")
                
            if unavailable:
                logger.info(f"\n📍 利用不可のモデル ({len(unavailable)}個):")
                for model in unavailable:
                    logger.info(f"   ❌ {model}")
                    
        # 推奨設定
        logger.info("\n💡 推奨設定:")
        if 'gpt-4o' in available:
            logger.info("   Deep Think Model: gpt-4o")
        if 'gpt-4o-mini' in available:
            logger.info("   Quick Think Model: gpt-4o-mini")
            
        # 結果をファイルに保存
        result_file = "api_test_results.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        logger.info(f"\n📁 詳細な結果を保存しました: {result_file}")


async def main():
    """メイン実行関数"""
    tester = APIConnectionTester()
    
    # APIキー確認
    if not tester.check_api_key():
        logger.error("\n⚠️  APIキーを設定してください:")
        logger.error("export OPENAI_API_KEY='your-api-key-here'")
        return
        
    # 各種テスト実行
    await tester.test_basic_connection()
    await tester.test_model_availability()
    await tester.test_langchain_integration()
    await tester.test_json_response()
    await tester.test_concurrent_requests()
    
    # サマリー表示
    tester.print_summary()
    
    logger.info("\n✅ API疎通テスト完了")


if __name__ == "__main__":
    # イベントループの実行
    asyncio.run(main())