#!/usr/bin/env python3
"""
シンプルなOpenAI API疎通テスト（.env対応版）
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
from pathlib import Path

# .envファイルを読み込む
def load_env():
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# .envを読み込む
load_env()

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
        ("gpt-4-turbo", "GPT-4 Turbo"),
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
            
        logger.info("\n💡 バックテスト推奨設定:")
        logger.info("   実際のLLMを使用する場合:")
        if "gpt-4o" in available_models:
            logger.info("     Deep Think Model: gpt-4o")
        elif "gpt-4-turbo" in available_models:
            logger.info("     Deep Think Model: gpt-4-turbo")
            
        if "gpt-4o-mini" in available_models:
            logger.info("     Quick Think Model: gpt-4o-mini")
        elif "gpt-3.5-turbo" in available_models:
            logger.info("     Quick Think Model: gpt-3.5-turbo")
            
        logger.info("\n   モックモードを使用する場合:")
        logger.info("     Deep Think Model: mock")
        logger.info("     Quick Think Model: mock")
            
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
            
    # 並行リクエストテスト
    if available_models:
        logger.info("\n🚀 並行リクエストテスト")
        logger.info("-" * 40)
        
        test_model = available_models[0]
        logger.info(f"使用モデル: {test_model}")
        logger.info("3つの並行リクエストを送信...")
        
        async def make_request(session, index):
            start = time.time()
            payload = {
                "model": test_model,
                "messages": [{"role": "user", "content": f"Request {index}. Reply with the number."}],
                "max_tokens": 10,
                "temperature": 0
            }
            
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    reply = data['choices'][0]['message']['content']
                    elapsed = time.time() - start
                    return index, elapsed, reply
                else:
                    return index, 0, "Error"
                    
        try:
            async with aiohttp.ClientSession() as session:
                start_total = time.time()
                results = await asyncio.gather(
                    make_request(session, 1),
                    make_request(session, 2),
                    make_request(session, 3)
                )
                total_time = time.time() - start_total
                
                logger.info(f"   ✅ 並行リクエスト完了")
                logger.info(f"   総実行時間: {total_time:.2f}秒")
                
                for index, elapsed, reply in results:
                    logger.info(f"   リクエスト{index}: {elapsed:.2f}秒 - {reply}")
                    
        except Exception as e:
            logger.error(f"   ❌ エラー: {str(e)}")
            
    logger.info("\n✅ API疎通テスト完了")
    
    # 結果をファイルに保存
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "api_key_masked": masked_key if api_key else None,
        "available_models": available_models,
        "recommended_settings": {
            "with_llm": {
                "deep_think_model": "gpt-4o" if "gpt-4o" in available_models else "gpt-4-turbo",
                "quick_think_model": "gpt-4o-mini" if "gpt-4o-mini" in available_models else "gpt-3.5-turbo"
            },
            "mock_mode": {
                "deep_think_model": "mock",
                "quick_think_model": "mock"
            }
        }
    }
    
    with open("api_test_results.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    logger.info(f"\n📁 テスト結果を保存しました: api_test_results.json")


if __name__ == "__main__":
    # 基本的な接続テスト
    asyncio.run(test_openai_connection())