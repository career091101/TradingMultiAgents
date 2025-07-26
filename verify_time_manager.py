#!/usr/bin/env python3
"""
Verify TimeManager behavior
"""

from datetime import datetime
from backtest2.utils.time_manager import TimeManager

# Create TimeManager with test dates
start = datetime(2024, 1, 1)
end = datetime(2024, 1, 10)
tm = TimeManager(start, end)

print(f"Start date: {start}")
print(f"End date: {end}")
print(f"Trading days generated: {len(tm.trading_days)}")
print(f"First trading day: {tm.trading_days[0] if tm.trading_days else 'None'}")
print(f"Current date at init: {tm.current_date}")
print(f"Current index: {tm.current_index}")
print(f"has_next(): {tm.has_next()}")

# Simulate the engine loop
print("\n=== Simulating Engine Loop ===")
iteration = 0
while tm.has_next():
    iteration += 1
    print(f"\nIteration {iteration}:")
    print(f"  Current date: {tm.current_date}")
    print(f"  Processing this date...")
    
    # This is what engine does
    tm.next()
    
    if iteration > 5:  # Safety limit
        break

print(f"\nTotal iterations: {iteration}")
print("ISSUE: First trading day is never processed!")