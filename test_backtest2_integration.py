#!/usr/bin/env python3
"""
Test Backtest2 integration with all fixes applied
"""

import asyncio
import sys
sys.path.insert(0, '.')
sys.path.insert(0, './TradingMultiAgents')

async def test_backtest2():
    print("Testing Backtest2 Integration...")
    
    # Import after clearing cache
    from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper
    
    # Test configuration
    test_config = {
        'tickers': ['AAPL'],
        'start_date': '2024-01-01',
        'end_date': '2024-01-31',
        'initial_capital': 10000,
        'debug': True,  # Enable debug mode
        'use_mock': True,  # Use mock mode for testing
        'agent_config': {
            'llm_provider': 'openai',
            'max_debate_rounds': 1,
            'max_risk_rounds': 1
        }
    }
    
    # Create wrapper
    wrapper = Backtest2Wrapper()
    
    # Log callback
    logs = []
    def log_callback(msg):
        print(f"[LOG] {msg}")
        logs.append(msg)
    
    # Progress callback
    def progress_callback(progress, status, ticker):
        print(f"[PROGRESS] {progress:.1f}% - {status}")
    
    try:
        # Run backtest
        print("\nRunning backtest...")
        results = await wrapper.run_backtest_async(
            config=test_config,
            progress_callback=progress_callback,
            log_callback=log_callback
        )
        
        print("\n✓ Backtest completed successfully!")
        print(f"Results: {list(results.keys())}")
        
        # Check results
        for ticker, result in results.items():
            print(f"\n{ticker} Results:")
            if 'error' in result:
                print(f"  ✗ Error: {result['error']}")
            else:
                print(f"  ✓ Trades: {result.get('trade_count', 0)}")
                print(f"  ✓ Final value: ${result.get('final_value', 0):.2f}")
                
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    # Run test
    success = asyncio.run(test_backtest2())
    
    if success:
        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED - Backtest2 is working correctly!")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ TESTS FAILED - Please check the errors above")
        print("="*50)