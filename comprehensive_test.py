#!/usr/bin/env python
"""包括的なJSONパーシング修正テスト"""

import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json
from collections import Counter

# APIキー設定
bashrc_path = Path.home() / ".bashrc"
if bashrc_path.exists():
    with open(bashrc_path, 'r') as f:
        for line in f:
            if 'export OPENAI_API_KEY=' in line:
                key = line.strip().split('=', 1)[1].strip('"')
                os.environ['OPENAI_API_KEY'] = key
                break

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_test.log'),
        logging.StreamHandler()
    ]
)

from backtest2.core.config import BacktestConfig, AgentConfig, LLMConfig, RiskConfig, TimeRange, RiskProfile
from backtest2.core.engine import BacktestEngine
from backtest2.agents.llm_client import OpenAILLMClient

async def test_json_parsing():
    """JSONパーシング機能の個別テスト"""
    print("\n🧪 JSONパーシング機能テスト")
    print("=" * 50)
    
    config = LLMConfig(
        deep_think_model="gpt-3.5-turbo",
        quick_think_model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=300
    )
    
    client = OpenAILLMClient(config)
    
    # テストケース
    test_cases = [
        {
            "name": "Risk Manager Test",
            "agent": "Risk Manager",
            "prompt": "Strong buy signal detected",
            "schema": {
                "action": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
                "confidence": {"type": "number"},
                "rationale": {"type": "string"}
            }
        },
        {
            "name": "Complex Schema Test",
            "agent": "Research Manager",
            "prompt": "Analyze bull vs bear thesis",
            "schema": {
                "investment_decision": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
                "investment_plan": {"type": "object", "properties": {
                    "action": {"type": "string"},
                    "target_allocation": {"type": "number"}
                }},
                "confidence_level": {"type": "number"}
            }
        }
    ]
    
    results = []
    for test in test_cases:
        print(f"\n📝 {test['name']}")
        try:
            result = await client.generate_structured(
                prompt=test['prompt'],
                context={"test": True},
                output_schema=test['schema'],
                agent_name=test['agent'],
                use_cache=False
            )
            print(f"✅ 成功: {result}")
            results.append(("success", result))
        except Exception as e:
            print(f"❌ エラー: {e}")
            results.append(("error", str(e)))
    
    await client.cleanup()
    return results

async def test_backtest_decisions():
    """バックテストでの決定生成テスト"""
    print("\n🎯 バックテスト決定生成テスト")
    print("=" * 50)
    
    config = BacktestConfig(
        symbols=["AAPL"],
        time_range=TimeRange(
            start=datetime(2025, 7, 23),
            end=datetime(2025, 7, 24)  # 1日のみ
        ),
        initial_capital=100000.0,
        debug=False,
        agent_config=AgentConfig(
            llm_config=LLMConfig(
                deep_think_model="gpt-3.5-turbo",
                quick_think_model="gpt-3.5-turbo",
                temperature=0.8,
                max_tokens=400
            ),
            use_japanese_prompts=True,
            max_debate_rounds=1,
            max_risk_discuss_rounds=1,
            enable_memory=False
        ),
        risk_config=RiskConfig(
            max_positions=5,
            position_limits={
                'AAPL': 0.5,
                RiskProfile.AGGRESSIVE: 0.8,
                RiskProfile.NEUTRAL: 0.5,
                RiskProfile.CONSERVATIVE: 0.3
            }
        )
    )
    
    engine = BacktestEngine(config)
    
    # 決定をキャプチャ
    decisions = []
    errors = []
    
    original_info = logging.getLogger('backtest2.agents.orchestrator').info
    original_error = logging.getLogger('backtest2.agents.llm_client').error
    
    def capture_info(msg):
        if "Final decision for" in msg:
            decisions.append(msg)
        original_info(msg)
    
    def capture_error(msg):
        if "Failed to parse" in msg:
            errors.append(msg)
        original_error(msg)
    
    logging.getLogger('backtest2.agents.orchestrator').info = capture_info
    logging.getLogger('backtest2.agents.llm_client').error = capture_error
    
    try:
        result = await engine.run()
        perf = result.agent_performance
        
        return {
            "total_decisions": perf.get('total_decisions', 0),
            "breakdown": perf.get('decision_breakdown', {}),
            "trades": perf.get('total_trades', 0),
            "decisions_captured": decisions,
            "parse_errors": len(errors)
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        await engine._cleanup()

async def analyze_debug_logs():
    """デバッグログの分析"""
    print("\n📊 デバッグログ分析")
    print("=" * 50)
    
    debug_dir = Path("logs/llm_debug")
    if not debug_dir.exists():
        return {"error": "No debug logs found"}
    
    stats = {
        "total_files": 0,
        "successful_json": 0,
        "failed_json": 0,
        "decisions": Counter(),
        "agents": Counter()
    }
    
    for file in sorted(debug_dir.glob("*.json"))[-20:]:  # 最新20ファイル
        stats["total_files"] += 1
        
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                
            agent = data.get('agent', 'unknown')
            stats["agents"][agent] += 1
            
            response = data.get('response', '')
            
            # JSON解析成功をチェック
            try:
                if response.strip().startswith('{'):
                    parsed = json.loads(response)
                    stats["successful_json"] += 1
                    
                    # 決定をカウント
                    for field in ['action', 'recommendation', 'investment_decision']:
                        if field in parsed and parsed[field] in ['BUY', 'SELL', 'HOLD']:
                            stats["decisions"][parsed[field]] += 1
                            break
            except:
                stats["failed_json"] += 1
                
        except Exception as e:
            print(f"Error reading {file.name}: {e}")
    
    return stats

async def main():
    """包括的テストの実行"""
    print("🎯 包括的なJSONパーシング修正テスト")
    print("=" * 70)
    print()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # 1. JSONパーシング機能テスト
    print("\n[1/3] JSONパーシング機能テスト...")
    json_results = await test_json_parsing()
    success_count = sum(1 for r in json_results if r[0] == "success")
    results["tests"]["json_parsing"] = {
        "total": len(json_results),
        "success": success_count,
        "rate": f"{(success_count/len(json_results)*100):.1f}%"
    }
    
    # 2. バックテスト決定生成テスト
    print("\n[2/3] バックテスト決定生成テスト...")
    backtest_results = await test_backtest_decisions()
    results["tests"]["backtest"] = backtest_results
    
    # 3. デバッグログ分析
    print("\n[3/3] デバッグログ分析...")
    debug_stats = await analyze_debug_logs()
    results["tests"]["debug_analysis"] = debug_stats
    
    # 結果サマリー
    print("\n" + "="*70)
    print("📊 テスト結果サマリー")
    print("="*70)
    
    # JSONパーシング結果
    print(f"\n✅ JSONパーシング成功率: {results['tests']['json_parsing']['rate']}")
    
    # バックテスト結果
    if 'error' not in backtest_results:
        total = backtest_results['total_decisions']
        breakdown = backtest_results['breakdown']
        print(f"\n📈 バックテスト決定分布:")
        for action in ['BUY', 'SELL', 'HOLD']:
            count = breakdown.get(action, 0)
            if total > 0:
                pct = count / total * 100
                print(f"  {action}: {count} ({pct:.1f}%)")
            else:
                print(f"  {action}: {count}")
        
        print(f"\n💰 実行された取引: {backtest_results['trades']}")
        print(f"🔧 パースエラー: {backtest_results['parse_errors']}")
    
    # デバッグログ統計
    if 'error' not in debug_stats:
        print(f"\n📄 デバッグログ統計:")
        print(f"  総ファイル数: {debug_stats['total_files']}")
        print(f"  JSON成功: {debug_stats['successful_json']}")
        print(f"  JSON失敗: {debug_stats['failed_json']}")
        
        if debug_stats['total_files'] > 0:
            success_rate = debug_stats['successful_json'] / debug_stats['total_files'] * 100
            print(f"  成功率: {success_rate:.1f}%")
        
        print(f"\n  決定分布:")
        for action, count in debug_stats['decisions'].items():
            print(f"    {action}: {count}")
    
    # 最終評価
    print("\n" + "="*70)
    print("🏁 最終評価")
    print("="*70)
    
    if 'error' not in backtest_results:
        all_hold = breakdown.get('HOLD', 0) == total and total > 0
        has_variety = len([a for a in ['BUY', 'SELL', 'HOLD'] if breakdown.get(a, 0) > 0]) > 1
        
        if all_hold:
            print("❌ 問題: すべての決定がHOLDです")
        elif has_variety:
            print("✅ 成功: システムは多様な決定（BUY/SELL/HOLD）を生成しています！")
        else:
            print("⚠️  警告: 決定の多様性が限定的です")
    
    # 結果を保存
    with open('comprehensive_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 詳細な結果を保存しました: comprehensive_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())