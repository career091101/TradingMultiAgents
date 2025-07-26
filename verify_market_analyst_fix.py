#!/usr/bin/env python
"""Market Analystのエラー率改善確認テスト"""

import os
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
import random

# APIキー設定
bashrc_path = Path.home() / ".bashrc"
if bashrc_path.exists():
    with open(bashrc_path, 'r') as f:
        for line in f:
            if 'export OPENAI_API_KEY=' in line:
                key = line.strip().split('=', 1)[1].strip('"')
                os.environ['OPENAI_API_KEY'] = key
                break

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from backtest2.agents.llm_client import OpenAILLMClient
from backtest2.core.config import LLMConfig
from backtest2.core.types import MarketData

async def test_market_analyst_multiple():
    """複数回Market Analystを実行してエラー率を確認"""
    print("🧪 Market Analystエラー率改善テスト")
    print("=" * 50)
    
    config = LLMConfig(
        deep_think_model="gpt-3.5-turbo",
        quick_think_model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=1000,  # デフォルト
        agent_max_tokens={
            "Market Analyst": 1500,  # 増加した制限
        }
    )
    
    client = OpenAILLMClient(config)
    
    # Market Analystのスキーマ（簡略化後）
    schema = {
        "selected_indicators": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "price_trend": {"type": "string", "enum": ["bullish", "bearish", "neutral"]},
        "volume_analysis": {"type": "string", "maxLength": 200},
        "technical_analysis": {"type": "string", "maxLength": 300},
        "recommendation": {"type": "string", "enum": ["BUY", "HOLD", "SELL"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "rationale": {"type": "string", "maxLength": 200}
    }
    
    success_count = 0
    error_count = 0
    truncation_errors = 0
    
    # 10回テスト実行
    num_tests = 10
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    
    for i in range(num_tests):
        symbol = random.choice(symbols)
        base_price = random.uniform(100, 500)
        
        # より複雑なプロンプト（長い応答を誘発）
        prompt = f"""
        株価データ: {symbol}
        - 始値: ${base_price:.2f}
        - 高値: ${base_price * random.uniform(1.01, 1.05):.2f}
        - 安値: ${base_price * random.uniform(0.95, 0.99):.2f}
        - 終値: ${base_price * random.uniform(0.97, 1.03):.2f}
        - 出来高: {random.randint(10000000, 100000000):,}
        
        以下の技術指標を含む包括的な分析を提供してください：
        - 50日移動平均線と200日移動平均線のクロスオーバー
        - MACDのシグナルライン交差
        - RSIのオーバーボート/オーバーソールド状態
        - ボリンジャーバンドのスクイーズ状態
        - ATR（平均真の範囲）の変化
        
        各指標について詳細な説明を含めてください。
        """
        
        try:
            print(f"\nテスト {i+1}/{num_tests} - {symbol}...")
            result = await client.generate_structured(
                prompt=prompt,
                context={"test": True, "iteration": i},
                output_schema=schema,
                agent_name="Market Analyst",
                use_cache=False
            )
            
            # 結果検証
            if all(key in result for key in ["recommendation", "price_trend", "confidence"]):
                success_count += 1
                print(f"✅ 成功 - 推奨: {result['recommendation']}, トレンド: {result['price_trend']}")
            else:
                error_count += 1
                print(f"❌ エラー - 不完全な応答")
                
        except json.JSONDecodeError as e:
            error_count += 1
            if "Unterminated string" in str(e):
                truncation_errors += 1
                print(f"❌ 切り詰めエラー: {e}")
            else:
                print(f"❌ JSONエラー: {e}")
        except Exception as e:
            error_count += 1
            print(f"❌ その他のエラー: {e}")
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 テスト結果サマリー")
    print(f"総テスト数: {num_tests}")
    print(f"成功: {success_count} ({success_count/num_tests*100:.1f}%)")
    print(f"エラー: {error_count} ({error_count/num_tests*100:.1f}%)")
    print(f"  - 切り詰めエラー: {truncation_errors}")
    print(f"  - その他のエラー: {error_count - truncation_errors}")
    
    print("\n📈 改善効果")
    print(f"改善前のエラー率: 6.7% (主に切り詰め)")
    print(f"改善後のエラー率: {error_count/num_tests*100:.1f}%")
    
    if error_count == 0:
        print("🎉 すべてのテストが成功しました！")
    elif error_count/num_tests < 0.067:
        print("✅ エラー率が改善されました！")
    
    await client.cleanup()

async def main():
    """メインテスト実行"""
    await test_market_analyst_multiple()

if __name__ == "__main__":
    asyncio.run(main())