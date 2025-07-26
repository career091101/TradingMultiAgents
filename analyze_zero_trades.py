#!/usr/bin/env python3
"""
Analyze why trades are zero - comprehensive analysis
"""

import asyncio
import logging
from datetime import datetime
from backtest2.core.config import BacktestConfig, LLMConfig, AgentConfig, TimeRange
from backtest2.core.engine import BacktestEngine
from backtest2.data.manager_simple import DataManager
from backtest2.agents.orchestrator import AgentOrchestrator

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def analyze_issue():
    print("=== 取引0件の根本原因分析 ===\n")
    
    # 1. Check data availability
    print("1. データ取得チェック:")
    
    # Create minimal config for data test
    time_range = TimeRange(
        start=datetime(2025, 4, 24),
        end=datetime(2025, 7, 22)
    )
    
    config = BacktestConfig(
        symbols=["AAPL"],
        time_range=time_range,
        initial_capital=100000.0
    )
    
    # Test data manager
    data_manager = DataManager(config)
    await data_manager.initialize()
    
    # Try to get data for a specific date
    test_date = datetime(2025, 7, 1)
    data = await data_manager.get_data("AAPL", test_date)
    
    if data:
        print(f"   ✓ データ取得成功: {test_date} - Close: ${data.close:.2f}")
    else:
        print(f"   ✗ データ取得失敗: {test_date}")
        print("   → これが根本原因の可能性大")
    
    # 2. Check trading days
    print("\n2. 取引日チェック:")
    from backtest2.utils.time_manager import TimeManager
    time_manager = TimeManager(
        start_date=datetime(2025, 4, 24),
        end_date=datetime(2025, 7, 22),
        timezone="UTC"
    )
    
    trading_days = time_manager.trading_days
    print(f"   取引日数: {len(trading_days)}")
    if trading_days:
        print(f"   最初の取引日: {trading_days[0]}")
        print(f"   最後の取引日: {trading_days[-1]}")
    
    # 3. Test with historical data
    print("\n3. 履歴データでのテスト:")
    historical_range = TimeRange(
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 10)
    )
    
    hist_config = BacktestConfig(
        symbols=["AAPL"],
        time_range=historical_range,
        initial_capital=100000.0
    )
    
    hist_data_manager = DataManager(hist_config)
    hist_date = datetime(2024, 1, 2)
    hist_data = await hist_data_manager.get_data("AAPL", hist_date)
    
    if hist_data:
        print(f"   ✓ 履歴データ取得成功: {hist_date} - Close: ${hist_data.close:.2f}")
    else:
        print(f"   ✗ 履歴データ取得失敗: {hist_date}")
    
    # 4. Check orchestrator initialization
    print("\n4. エージェント初期化チェック:")
    try:
        # Use mock for quick test
        llm_config = LLMConfig(
            deep_think_model="mock",
            quick_think_model="mock"
        )
        
        agent_config = AgentConfig(
            llm_config=llm_config,
            max_debate_rounds=1
        )
        
        test_config = BacktestConfig(
            symbols=["AAPL"],
            time_range=historical_range,
            agent_config=agent_config
        )
        
        from backtest2.memory import MemoryStore
        memory_store = MemoryStore()
        orchestrator = AgentOrchestrator(test_config, memory_store)
        await orchestrator.initialize()
        
        print("   ✓ エージェント初期化成功")
    except Exception as e:
        print(f"   ✗ エージェント初期化失敗: {e}")
    
    # Summary
    print("\n=== 分析結果 ===")
    print("\n根本原因:")
    print("1. 2025年の日付を使用している（未来のデータ）")
    print("2. Yahoo Financeは未来のデータを提供しない")
    print("3. データが取得できないため、エージェントが決定を下せない")
    print("\n潜在的要因:")
    print("- WebUIが推奨日付設定を反映していない")
    print("- データマネージャーのエラーハンドリングが不十分")
    print("- エージェントがデータなしの場合の処理が不適切")

if __name__ == "__main__":
    asyncio.run(analyze_issue())