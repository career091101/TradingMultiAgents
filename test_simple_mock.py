#!/usr/bin/env python3
"""
Simple test with mock mode to verify the fix works
"""

import asyncio
from datetime import datetime
from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper

async def test_mock():
    print("=== モックモードでの動作確認 ===\n")
    
    config = {
        "tickers": ["AAPL"],
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
        "initial_capital": 100000.0,
        "use_mock": True,  # Mock mode
        "debug": True,
        "agent_config": {
            "llm_provider": "custom",
            "deep_model": "mock",
            "fast_model": "mock",
            "max_debate_rounds": 1,
            "max_risk_rounds": 1
        }
    }
    
    wrapper = Backtest2Wrapper()
    
    print("実行中...")
    
    try:
        results = await wrapper.run_backtest_async(config)
        
        print("\n=== 結果 ===")
        for ticker, result in results.items():
            print(f"{ticker}:")
            print(f"  取引数: {result['metrics']['total_trades']}")
            print(f"  リターン: {result['metrics']['total_return']:.2%}")
            
            if result['metrics']['total_trades'] > 0:
                print("\n✅ モックモードで取引が実行されました")
            else:
                print("\n⚠️  モックモードでも取引が0件です")
                
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mock())