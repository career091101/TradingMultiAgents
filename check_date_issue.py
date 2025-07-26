#!/usr/bin/env python3
"""
Check date issue - using future dates
"""

from datetime import datetime

# Check the dates being used
start_date = datetime.strptime("2025-04-24", "%Y-%m-%d")
end_date = datetime.strptime("2025-07-22", "%Y-%m-%d")
today = datetime.now()

print("=== DATE ISSUE CHECK ===")
print(f"Today's date: {today.strftime('%Y-%m-%d')}")
print(f"Backtest start date: {start_date.strftime('%Y-%m-%d')}")
print(f"Backtest end date: {end_date.strftime('%Y-%m-%d')}")
print()

if start_date > today:
    print("❌ ERROR: Start date is in the future!")
    print(f"   Start date is {(start_date - today).days} days in the future")
    
if end_date > today:
    print("❌ ERROR: End date is in the future!")
    print(f"   End date is {(end_date - today).days} days in the future")
    
print("\n=== RECOMMENDATION ===")
print("Use historical dates for backtesting, for example:")
print(f"  Start: 2024-01-01")
print(f"  End: 2024-07-22")
print("\nMarket data providers (Yahoo Finance, FinnHub) cannot provide future data!")