#!/usr/bin/env python3
"""
Test Yahoo Finance and FinnHub API connectivity
"""

import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== API CONNECTIVITY TEST ===\n")

# Check environment variables
print("1. Environment Variables:")
openai_key = os.getenv('OPENAI_API_KEY')
finnhub_key = os.getenv('FINNHUB_API_KEY')

print(f"OPENAI_API_KEY: {'✓ Set' if openai_key else '✗ Not Set'}")
print(f"FINNHUB_API_KEY: {'✓ Set' if finnhub_key else '✗ Not Set'}")

# Test Yahoo Finance
print("\n2. Testing Yahoo Finance API:")
try:
    import yfinance as yf
    ticker = yf.Ticker("AAPL")
    
    # Get recent data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"   Fetching AAPL data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    hist = ticker.history(start=start_date, end=end_date)
    
    if not hist.empty:
        print(f"   ✓ Success: Retrieved {len(hist)} days of data")
        print(f"   Latest close price: ${hist['Close'].iloc[-1]:.2f}")
        print(f"   Date range: {hist.index[0].strftime('%Y-%m-%d')} to {hist.index[-1].strftime('%Y-%m-%d')}")
    else:
        print("   ✗ Failed: No data returned")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test FinnHub
print("\n3. Testing FinnHub API:")
try:
    import finnhub
    
    if not finnhub_key:
        print("   ✗ FINNHUB_API_KEY not set")
    else:
        # Setup client
        finnhub_client = finnhub.Client(api_key=finnhub_key)
        
        # Test quote endpoint
        quote = finnhub_client.quote('AAPL')
        if quote and 'c' in quote:
            print(f"   ✓ Success: Connected to FinnHub")
            print(f"   AAPL current price: ${quote['c']:.2f}")
            print(f"   Today's change: {quote['dp']:.2f}%")
        else:
            print("   ✗ Failed: No data returned")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test data source implementations
print("\n4. Testing Backtest2 Data Sources:")
try:
    from backtest2.data.sources import YahooFinanceSource, FinnHubSource
    from backtest2.core.config import DataConfig
    
    data_config = DataConfig()
    
    # Test Yahoo source
    print("   Yahoo Finance Source:")
    yahoo_source = YahooFinanceSource(data_config)
    test_date = datetime(2024, 1, 2)
    
    # Run async test
    async def test_yahoo():
        try:
            data = await yahoo_source.get_market_data("AAPL", test_date)
            if data:
                print(f"   ✓ Retrieved data for {test_date.strftime('%Y-%m-%d')}")
                print(f"   Close price: ${data.close:.2f}")
            else:
                print("   ✗ No data returned")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    asyncio.run(test_yahoo())
    
    # Test FinnHub source
    if finnhub_key:
        print("\n   FinnHub Source:")
        finnhub_source = FinnHubSource(data_config)
        
        async def test_finnhub():
            try:
                data = await finnhub_source.get_market_data("AAPL", test_date)
                if data:
                    print(f"   ✓ Retrieved data")
                else:
                    print("   ✗ No data returned")
            except Exception as e:
                print(f"   ✗ Error: {e}")
        
        asyncio.run(test_finnhub())
    
except Exception as e:
    print(f"   ✗ Import Error: {e}")

print("\n=== SUMMARY ===")
print("If Yahoo Finance works but returns no data for recent dates,")
print("it's likely because the requested dates are too recent or in the future.")
print("\nRecommendation: Use historical dates (e.g., 2024-01-01 to 2024-06-30)")