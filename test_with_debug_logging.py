#!/usr/bin/env python3
"""
Test with detailed debug logging to identify JSON serialization issues
"""

import asyncio
import logging
from datetime import datetime
from backtest2.core.config import BacktestConfig, LLMConfig, AgentConfig, TimeRange
from backtest2.core.engine import BacktestEngine

# Setup detailed debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_json_issues.log'),
        logging.StreamHandler()
    ]
)

# Focus on llm_client logging
logging.getLogger('backtest2.agents.llm_client').setLevel(logging.DEBUG)
logging.getLogger('backtest2.agents.orchestrator').setLevel(logging.DEBUG)

async def test_with_debug():
    print("=== JSONシリアライズ問題のデバッグテスト ===\n")
    
    # Create config
    llm_config = LLMConfig(
        deep_think_model="o3-2025-04-16",
        quick_think_model="o4-mini-2025-04-16",
        temperature=1.0
    )
    
    agent_config = AgentConfig(
        llm_config=llm_config,
        max_debate_rounds=1,
        max_risk_discuss_rounds=1
    )
    
    # Short date range for quick test
    time_range = TimeRange(
        start=datetime(2025, 7, 1),
        end=datetime(2025, 7, 2)  # Two days
    )
    
    config = BacktestConfig(
        symbols=["AAPL"],
        time_range=time_range,
        initial_capital=100000.0,
        agent_config=agent_config,
        debug=True
    )
    
    print("テスト設定:")
    print(f"  日付: {time_range.start}")
    print(f"  銘柄: AAPL")
    print(f"  モデル: {llm_config.deep_think_model} / {llm_config.quick_think_model}")
    print("\n実行中...\n")
    
    # Run test
    engine = BacktestEngine(config)
    
    try:
        result = await engine.run()
        print(f"\n=== 結果 ===")
        print(f"取引数: {result.metrics.total_trades}")
        print(f"最終価値: ${result.final_portfolio.total_value:,.2f}")
        
        if result.metrics.total_trades == 0:
            print("\n⚠️  取引が0件です - debug_json_issues.logを確認してください")
        else:
            print("\n✅ 取引が実行されました！")
            
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n詳細ログは debug_json_issues.log に保存されています")

if __name__ == "__main__":
    asyncio.run(test_with_debug())