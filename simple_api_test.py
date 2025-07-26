#!/usr/bin/env python3
"""
シンプルなOpenAI API疎通テスト
- 基本的な接続確認
- モデル利用可能性チェック
- エラーハンドリング確認
"""

import os
import asyncio
import json
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_openai_connection():
    """OpenAI API接続テスト（純粋なHTTPリクエスト版）"""
    
    logger.info("=" * 60)
    logger.info("🔑 OpenAI API 疎通テスト")
    logger.info("=" * 60)
    
    # APIキー確認
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error("❌ OPENAI_API_KEY環境変数が設定されていません")
        logger.error("設定方法: export OPENAI_API_KEY='your-api-key-here'")
        return
        
    masked_key = f"{api_key[:8]}...{api_key[-4:]}"
    logger.info(f"✅ APIキーが設定されています: {masked_key}")
    
    # aiohttp をインポート
    try:
        import aiohttp
    except ImportError:
        logger.error("❌ aiohttpがインストールされていません")
        logger.error("インストール: pip install aiohttp")
        return
        
    # テストするモデル
    models_to_test = [
        ("gpt-4o-mini", "GPT-4o-mini (Quick thinking)"),
        ("gpt-4o", "GPT-4o (Deep thinking)"),
        ("gpt-3.5-turbo", "GPT-3.5 Turbo"),
        ("o3", "O3 (Advanced reasoning)"),
        ("o4-mini", "O4-mini (Fast reasoning)"),
    ]
    
    logger.info("\n📍 モデル利用可能性テスト")
    logger.info("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        available_models = []
        
        for model_id, model_name in models_to_test:
            logger.info(f"\nテスト中: {model_name} ({model_id})")
            
            # リクエストボディ
            if model_id.startswith(('o3', 'o4')):
                # o-series models
                payload = {
                    "model": model_id,
                    "messages": [{"role": "user", "content": "Test. Reply with 'OK'."}],
                    "max_completion_tokens": 10,
                    "temperature": 1.0
                }
            else:
                # Standard models
                payload = {
                    "model": model_id,
                    "messages": [{"role": "user", "content": "Test. Reply with 'OK'."}],
                    "max_tokens": 10,
                    "temperature": 0
                }
            
            try:
                start_time = time.time()
                
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    elapsed = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        reply = data['choices'][0]['message']['content']
                        logger.info(f"   ✅ 利用可能")
                        logger.info(f"   応答時間: {elapsed:.2f}秒")
                        logger.info(f"   レスポンス: {reply}")
                        available_models.append(model_id)
                        
                    else:
                        error_text = await response.text()
                        error_data = json.loads(error_text) if error_text else {}
                        error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                        
                        if "model_not_found" in error_msg or "does not exist" in error_msg:
                            logger.warning(f"   ⚠️  モデルが見つかりません")
                        else:
                            logger.error(f"   ❌ エラー: {error_msg}")
                            
            except asyncio.TimeoutError:
                logger.error(f"   ❌ タイムアウト (30秒)")
            except Exception as e:
                logger.error(f"   ❌ エラー: {str(e)}")
                
    # サマリー
    logger.info("\n" + "=" * 60)
    logger.info("📊 テスト結果サマリー")
    logger.info("=" * 60)
    
    if available_models:
        logger.info(f"\n✅ 利用可能なモデル ({len(available_models)}個):")
        for model in available_models:
            logger.info(f"   - {model}")
            
        logger.info("\n💡 推奨設定:")
        if "gpt-4o" in available_models:
            logger.info("   Deep Think Model: gpt-4o")
        elif "gpt-4" in available_models:
            logger.info("   Deep Think Model: gpt-4")
            
        if "gpt-4o-mini" in available_models:
            logger.info("   Quick Think Model: gpt-4o-mini")
        elif "gpt-3.5-turbo" in available_models:
            logger.info("   Quick Think Model: gpt-3.5-turbo")
            
    else:
        logger.error("\n❌ 利用可能なモデルがありません")
        logger.error("APIキーまたはネットワーク接続を確認してください")
        
    # JSON形式のレスポンステスト
    if available_models:
        logger.info("\n📋 JSON形式レスポンステスト")
        logger.info("-" * 40)
        
        test_model = available_models[0]
        logger.info(f"使用モデル: {test_model}")
        
        json_prompt = """Please respond with JSON format:
{
  "action": "HOLD",
  "confidence": 0.7,
  "reason": "Test response"
}"""
        
        payload = {
            "model": test_model,
            "messages": [{"role": "user", "content": json_prompt}],
            "max_tokens": 100,
            "temperature": 0
        }
        
        if test_model in ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]:
            payload["response_format"] = {"type": "json_object"}
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        reply = data['choices'][0]['message']['content']
                        
                        # JSONパース試行
                        try:
                            parsed = json.loads(reply)
                            logger.info("   ✅ JSON形式レスポンス成功")
                            logger.info(f"   パース結果: {json.dumps(parsed, ensure_ascii=False)}")
                        except json.JSONDecodeError:
                            logger.warning("   ⚠️  JSONパース失敗")
                            logger.info(f"   レスポンス: {reply}")
                            
        except Exception as e:
            logger.error(f"   ❌ エラー: {str(e)}")
            
    logger.info("\n✅ API疎通テスト完了")


async def test_with_backtest_llm():
    """バックテストで使用されるLLMクライアントのテスト"""
    logger.info("\n" + "=" * 60)
    logger.info("🔗 Backtest2 LLMクライアント互換性テスト")
    logger.info("=" * 60)
    
    try:
        # backtest2のLLMクライアントをインポート
        import sys
        sys.path.insert(0, '/Users/y-sato/TradingAgents2')
        
        from backtest2.agents.llm_client import OpenAILLMClient
        from backtest2.core.config import LLMConfig
        
        # 通常モデルのテスト
        logger.info("\n📍 通常モデルでのテスト")
        normal_config = LLMConfig(
            deep_think_model="gpt-4o",
            quick_think_model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=100,
            timeout=30
        )
        
        client = OpenAILLMClient(normal_config)
        
        # 簡単なテスト
        response = await client.generate(
            prompt="Test connection. Reply with 'Backtest LLM OK'.",
            context={},
            use_deep_thinking=False,
            agent_name="test_agent"
        )
        
        logger.info(f"   ✅ LLMクライアント接続成功")
        logger.info(f"   レスポンス: {response[:100]}")
        
        # モックモードのテスト
        logger.info("\n📍 モックモードでのテスト")
        mock_config = LLMConfig(
            deep_think_model="mock",
            quick_think_model="mock",
            temperature=0.0,
            timeout=30
        )
        
        mock_client = OpenAILLMClient(mock_config)
        mock_response = await mock_client.generate(
            prompt="Test mock mode",
            context={},
            agent_name="market_analyst"
        )
        
        logger.info(f"   ✅ モックモード動作確認")
        logger.info(f"   モックレスポンス: {mock_response[:200]}")
        
    except ImportError as e:
        logger.warning(f"   ⚠️  Backtest2モジュールのインポートエラー: {e}")
        logger.info("   （これは環境依存の問題です）")
    except Exception as e:
        logger.error(f"   ❌ エラー: {str(e)}")


if __name__ == "__main__":
    # 基本的な接続テスト
    asyncio.run(test_openai_connection())
    
    # Backtest LLMクライアントのテスト
    asyncio.run(test_with_backtest_llm())