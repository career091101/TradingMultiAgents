#!/usr/bin/env python3
"""
Test Backtest2 with mock mode and improved settings
"""

import asyncio
import sys
sys.path.insert(0, '.')
sys.path.insert(0, './TradingMultiAgents')

async def test_mock_backtest():
    print("Testing Backtest2 with Mock Mode and Optimized Settings...")
    
    from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper
    
    # Test configuration with improvements
    test_config = {
        'tickers': ['AAPL'],
        'start_date': '2024-01-01',  # Past date
        'end_date': '2024-01-31',     # Past date
        'initial_capital': 100000,
        'debug': True,
        'use_mock': True,  # Use mock LLM
        'agent_config': {
            'llm_provider': 'openai',
            'max_debate_rounds': 1,
            'max_risk_rounds': 1
        },
        # Adjust position sizing
        'min_trade_size': 100,  # Lower minimum
        'aggressive_limit': 0.3,
        'neutral_limit': 0.2,
        'conservative_limit': 0.1,
    }
    
    # Create wrapper
    wrapper = Backtest2Wrapper()
    
    # Callbacks
    logs = []
    def log_callback(msg):
        print(f"[LOG] {msg}")
        logs.append(msg)
    
    def progress_callback(progress, status, ticker):
        print(f"[PROGRESS] {progress:.1f}% - {status}")
    
    try:
        print("\nRunning backtest with optimized settings...")
        results = await wrapper.run_backtest_async(
            config=test_config,
            progress_callback=progress_callback,
            log_callback=log_callback
        )
        
        print("\n✓ Backtest completed!")
        
        # Analyze results
        for ticker, result in results.items():
            print(f"\n{ticker} Results:")
            if 'error' in result:
                print(f"  ✗ Error: {result['error']}")
            else:
                trades = result.get('trade_count', 0)
                final_value = result.get('final_value', 0)
                metrics = result.get('metrics', {})
                total_return = metrics.get('total_return', 0)
                
                print(f"  ✓ Trades: {trades}")
                print(f"  ✓ Final value: ${final_value:.2f}")
                print(f"  ✓ Total return: {total_return:.2f}%")
                
                if trades == 0:
                    print("\n  ⚠️  No trades executed. Possible causes:")
                    print("     - Agent decisions are too conservative")
                    print("     - Position sizing below minimum")
                    print("     - Data not available for date range")
                
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mock_backtest())
    
    if success:
        print("\n" + "="*50)
        print("✅ Mock test completed - Check results above")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ Mock test failed")
        print("="*50)