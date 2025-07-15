#!/usr/bin/env python3
"""
自動分析フローテスト（対話なし）
"""
import sys
import subprocess
import os

# 環境変数設定
os.environ["FINNHUB_API_KEY"] = "test_key"
os.environ["OPENAI_API_KEY"] = "test_key"

# quickモードで自動実行するためのスクリプト
script = """
import asyncio
from analysis_flow_test import AnalysisFlowE2ETest

async def auto_test():
    test = AnalysisFlowE2ETest()
    # 深度1のみで自動実行
    results = await test.run_depth_test(depth=1, ticker="SPY")
    return results

asyncio.run(auto_test())
"""

# Pythonコマンドで実行
result = subprocess.run(
    [sys.executable, "-c", script],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("エラー:", result.stderr)