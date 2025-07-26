#!/usr/bin/env python
"""トークン制限修正のテスト"""

import os
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

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

async def test_market_analyst():
    """Market Analystのトークン制限テスト"""
    print("🧪 Market Analystトークン制限テスト")
    print("=" * 50)
    
    config = LLMConfig(
        deep_think_model="gpt-3.5-turbo",
        quick_think_model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=1000,  # デフォルト
        agent_max_tokens={
            "Market Analyst": 1500,  # 増加した制限
            "Fundamentals Analyst": 1200
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
    
    # 長い分析を要求するプロンプト
    prompt = """
    株価データ: AAPL
    - 始値: $214.50
    - 高値: $215.20
    - 安値: $213.80
    - 終値: $214.15
    - 出来高: 50,000,000
    
    50日移動平均、200日移動平均、MACD、RSI、ボリンジャーバンドを含む
    包括的な技術分析を提供してください。
    """
    
    try:
        print("\n1. 通常のMarket Analyst実行...")
        result = await client.generate_structured(
            prompt=prompt,
            context={"test": True, "market_data": {"symbol": "AAPL", "price": 214.15}},
            output_schema=schema,
            agent_name="Market Analyst",
            use_cache=False
        )
        
        print("✅ 成功!")
        print(f"  - selected_indicators: {len(result.get('selected_indicators', []))} items")
        print(f"  - price_trend: {result.get('price_trend')}")
        print(f"  - recommendation: {result.get('recommendation')}")
        print(f"  - volume_analysis length: {len(result.get('volume_analysis', ''))}")
        print(f"  - technical_analysis length: {len(result.get('technical_analysis', ''))}")
        
        # JSON復旧機能のテスト
        print("\n2. JSON復旧機能テスト...")
        truncated_json = '''{"selected_indicators": ["close_50_sma", "close_200_sma", "macd"], "price_trend": "bullish", "volume_analysis": "High volume indicates strong'''
        
        recovered = client._attempt_json_recovery(truncated_json)
        if recovered:
            print("✅ JSON復旧成功!")
            parsed = json.loads(recovered)
            print(f"  復旧されたデータ: {list(parsed.keys())}")
        else:
            print("❌ JSON復旧失敗")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.cleanup()

async def test_all_agents():
    """全エージェントの簡易テスト"""
    print("\n\n🧪 全エージェントトークン設定確認")
    print("=" * 50)
    
    config = LLMConfig(
        deep_think_model="gpt-3.5-turbo",
        quick_think_model="gpt-3.5-turbo",
        agent_max_tokens={
            "Market Analyst": 1500,
            "Fundamentals Analyst": 1200,
            "Research Manager": 1200,
            "Risk Manager": 1000
        }
    )
    
    agents = [
        "Market Analyst",
        "News Analyst",
        "Fundamentals Analyst",
        "Research Manager",
        "Risk Manager",
        "Trader"
    ]
    
    print("\nエージェント別max_tokens設定:")
    for agent in agents:
        tokens = config.agent_max_tokens.get(agent, config.max_tokens)
        status = "✅ カスタム" if agent in config.agent_max_tokens else "📝 デフォルト"
        print(f"  {agent:20}: {tokens:4} tokens {status}")

async def main():
    """メインテスト実行"""
    print("🎯 トークン制限修正テスト")
    print("改善内容:")
    print("- Market Analystのmax_tokensを1500に増加")
    print("- 出力スキーマを簡略化")
    print("- JSON復旧機能を追加")
    print()
    
    await test_market_analyst()
    await test_all_agents()
    
    print("\n✅ テスト完了")

if __name__ == "__main__":
    asyncio.run(main())