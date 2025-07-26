#!/usr/bin/env python3
"""
OpenAI API疎通テスト（SSL証明書問題対応版）
"""

import os
import asyncio
import json
import time
import ssl
import certifi
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
    """OpenAI API接続テスト（SSL証明書対応版）"""
    
    logger.info("=" * 60)
    logger.info("🔑 OpenAI API 疎通テスト（SSL対応版）")
    logger.info("=" * 60)
    
    # APIキー確認
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error("❌ OPENAI_API_KEY環境変数が設定されていません")
        return
        
    masked_key = f"{api_key[:8]}...{api_key[-4:]}"
    logger.info(f"✅ APIキーが設定されています: {masked_key}")
    
    # SSL証明書のパスを確認
    cert_path = certifi.where()
    logger.info(f"📜 SSL証明書パス: {cert_path}")
    
    # aiohttp をインポート
    try:
        import aiohttp
    except ImportError:
        logger.error("❌ aiohttpがインストールされていません")
        return
        
    # SSL contextを作成
    ssl_context = ssl.create_default_context(cafile=cert_path)
    
    # テストするモデル（基本的なものだけ）
    models_to_test = [
        ("gpt-3.5-turbo", "GPT-3.5 Turbo"),
        ("gpt-4o-mini", "GPT-4o-mini"),
        ("gpt-4o", "GPT-4o"),
    ]
    
    logger.info("\n📍 モデル利用可能性テスト")
    logger.info("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # SSL contextを使用してセッションを作成
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        available_models = []
        
        for model_id, model_name in models_to_test:
            logger.info(f"\nテスト中: {model_name} ({model_id})")
            
            payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": "Test. Reply 'OK'."}],
                "max_tokens": 10,
                "temperature": 0
            }
            
            try:
                start_time = time.time()
                
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    elapsed = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        reply = data['choices'][0]['message']['content']
                        logger.info(f"   ✅ 利用可能")
                        logger.info(f"   応答時間: {elapsed:.2f}秒")
                        logger.info(f"   レスポンス: {reply}")
                        available_models.append(model_id)
                        
                    elif response.status == 401:
                        logger.error(f"   ❌ 認証エラー: APIキーが無効です")
                        break
                    elif response.status == 404:
                        logger.warning(f"   ⚠️  モデルが見つかりません")
                    else:
                        error_text = await response.text()
                        logger.error(f"   ❌ エラー (status={response.status}): {error_text[:200]}")
                            
            except asyncio.TimeoutError:
                logger.error(f"   ❌ タイムアウト")
            except Exception as e:
                logger.error(f"   ❌ エラー: {str(e)}")
                
    # もしSSL証明書の問題が続く場合は、SSL検証を無効化してテスト
    if not available_models:
        logger.info("\n🔄 SSL検証を無効化して再試行...")
        
        # SSL検証を無効化（開発環境のみ）
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            # 最小限のテスト
            model_id = "gpt-3.5-turbo"
            payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5,
                "temperature": 0
            }
            
            try:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("   ✅ SSL検証無効化でAPI接続成功")
                        logger.warning("   ⚠️  本番環境ではSSL検証を有効にしてください")
                        available_models.append(model_id)
                    else:
                        logger.error(f"   ❌ APIエラー: {response.status}")
                        
            except Exception as e:
                logger.error(f"   ❌ 接続エラー: {str(e)}")
    
    # サマリー
    logger.info("\n" + "=" * 60)
    logger.info("📊 テスト結果サマリー")
    logger.info("=" * 60)
    
    if available_models:
        logger.info(f"\n✅ API接続成功!")
        logger.info(f"利用可能なモデル: {', '.join(available_models)}")
        
        logger.info("\n💡 バックテスト設定の推奨:")
        logger.info("1. 実際のLLMを使用する場合:")
        logger.info(f"   Deep Think Model: {'gpt-4o' if 'gpt-4o' in available_models else 'gpt-3.5-turbo'}")
        logger.info(f"   Quick Think Model: {'gpt-4o-mini' if 'gpt-4o-mini' in available_models else 'gpt-3.5-turbo'}")
        logger.info("   Timeout: 600 (10分)")
        
        logger.info("\n2. モックモードを使用する場合（推奨）:")
        logger.info("   Deep Think Model: mock")
        logger.info("   Quick Think Model: mock")
        logger.info("   Mock Mode: ✅")
        
    else:
        logger.error("\n❌ API接続に失敗しました")
        logger.error("考えられる原因:")
        logger.error("1. APIキーが無効")
        logger.error("2. ネットワーク接続の問題")
        logger.error("3. SSL証明書の問題")
        logger.error("\n対処法:")
        logger.error("1. APIキーを確認: https://platform.openai.com/api-keys")
        logger.error("2. ネットワーク接続を確認")
        logger.error("3. Python証明書をアップデート: pip install --upgrade certifi")


# curlコマンドでの確認
def test_with_curl():
    """curlコマンドでAPI接続をテスト"""
    logger.info("\n" + "=" * 60)
    logger.info("🐚 curlコマンドでのテスト")
    logger.info("=" * 60)
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error("APIキーが設定されていません")
        return
        
    import subprocess
    
    curl_cmd = [
        'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
        'https://api.openai.com/v1/models',
        '-H', f'Authorization: Bearer {api_key}'
    ]
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        status_code = result.stdout.strip()
        
        if status_code == "200":
            logger.info("✅ curlでのAPI接続成功 (status=200)")
        elif status_code == "401":
            logger.error("❌ 認証エラー (status=401) - APIキーが無効です")
        else:
            logger.error(f"❌ エラー (status={status_code})")
            
    except Exception as e:
        logger.error(f"curlコマンドの実行に失敗: {e}")


if __name__ == "__main__":
    # curlでの接続テスト
    test_with_curl()
    
    # Pythonでの接続テスト
    asyncio.run(test_openai_connection())