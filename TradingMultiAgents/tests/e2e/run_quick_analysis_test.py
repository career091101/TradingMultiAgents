#!/usr/bin/env python3
"""
クイック分析フローテスト（深度1）
対話なしで自動実行
"""
import asyncio
import os

# 環境変数設定（デモ用）
os.environ["FINNHUB_API_KEY"] = os.environ.get("FINNHUB_API_KEY", "test_finnhub_key")
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "test_openai_key")

from analysis_flow_test import AnalysisFlowE2ETest

async def run_quick_test():
    """深度1のクイックテストを自動実行"""
    print("=== TradingAgents WebUI クイック分析テスト ===")
    print("テスト内容: 深度1での完全分析フロー")
    print("予想時間: 約15分")
    print("-" * 60)
    
    # テストインスタンス作成
    test = AnalysisFlowE2ETest()
    
    # 深度1のみでテスト実行
    results = await test.run_all_tests(depths=[1])
    
    # 結果サマリー表示
    summary = results.get("summary", {})
    if summary.get("successful", 0) > 0:
        print("\n✅ テスト成功!")
        
        # 深度1の詳細結果
        depth1_result = results["depth_results"].get(1, {})
        if depth1_result.get("duration"):
            print(f"実行時間: {depth1_result['duration']//60:.0f}分")
            
        if depth1_result.get("verification", {}).get("results_found"):
            print("結果検証: 成功")
            reports = depth1_result["verification"].get("reports_available", [])
            print(f"利用可能なレポート: {len(reports)}個")
    else:
        print("\n❌ テスト失敗")
        
    return results

if __name__ == "__main__":
    # WebUI起動確認
    import requests
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        print("✅ WebUI起動確認済み")
    except:
        print("❌ WebUIが起動していません")
        print("先に 'python run_webui.py' でWebUIを起動してください")
        exit(1)
    
    # テスト実行
    asyncio.run(run_quick_test())