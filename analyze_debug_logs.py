#!/usr/bin/env python
"""デバッグログの詳細分析"""

import json
from pathlib import Path
from collections import Counter
from datetime import datetime

def analyze_logs():
    debug_dir = Path("logs/llm_debug")
    
    stats = {
        "total_files": 0,
        "successful_json": 0,
        "failed_json": 0,
        "decisions": Counter(),
        "agents": Counter(),
        "errors": [],
        "json_examples": {
            "success": [],
            "failure": []
        }
    }
    
    # 最新の30ファイルを分析
    files = sorted(debug_dir.glob("*.json"))[-30:]
    
    for file in files:
        stats["total_files"] += 1
        
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            
            agent = data.get('agent', 'unknown')
            stats["agents"][agent] += 1
            
            response = data.get('response', '')
            
            # JSON解析を試みる
            try:
                if response.strip().startswith('{'):
                    parsed = json.loads(response)
                    stats["successful_json"] += 1
                    
                    # 成功例を保存
                    if len(stats["json_examples"]["success"]) < 3:
                        stats["json_examples"]["success"].append({
                            "agent": agent,
                            "response": parsed
                        })
                    
                    # 決定をカウント
                    for field in ['action', 'recommendation', 'investment_decision', 'final_decision']:
                        if field in parsed and parsed[field] in ['BUY', 'SELL', 'HOLD']:
                            stats["decisions"][parsed[field]] += 1
                            break
                else:
                    stats["failed_json"] += 1
            except json.JSONDecodeError as e:
                stats["failed_json"] += 1
                if len(stats["json_examples"]["failure"]) < 3:
                    stats["json_examples"]["failure"].append({
                        "agent": agent,
                        "error": str(e),
                        "response_preview": response[:200]
                    })
                
        except Exception as e:
            stats["errors"].append(f"{file.name}: {e}")
    
    return stats

def main():
    print("📊 デバッグログ詳細分析")
    print("=" * 70)
    
    stats = analyze_logs()
    
    # 基本統計
    print(f"\n📈 基本統計:")
    print(f"  総ファイル数: {stats['total_files']}")
    print(f"  JSON成功: {stats['successful_json']}")
    print(f"  JSON失敗: {stats['failed_json']}")
    
    if stats['total_files'] > 0:
        success_rate = stats['successful_json'] / stats['total_files'] * 100
        print(f"  成功率: {success_rate:.1f}%")
    
    # エージェント別統計
    print(f"\n👥 エージェント別:")
    for agent, count in stats['agents'].most_common():
        print(f"  {agent}: {count}")
    
    # 決定分布
    print(f"\n🎯 決定分布:")
    total_decisions = sum(stats['decisions'].values())
    for action, count in stats['decisions'].items():
        if total_decisions > 0:
            pct = count / total_decisions * 100
            print(f"  {action}: {count} ({pct:.1f}%)")
        else:
            print(f"  {action}: {count}")
    
    # 成功例
    print(f"\n✅ JSON成功例:")
    for i, example in enumerate(stats['json_examples']['success'], 1):
        print(f"\n  例{i} - {example['agent']}:")
        resp = example['response']
        if 'action' in resp:
            print(f"    action: {resp.get('action')}")
        if 'recommendation' in resp:
            print(f"    recommendation: {resp.get('recommendation')}")
        if 'confidence' in resp:
            print(f"    confidence: {resp.get('confidence')}")
    
    # 失敗例
    if stats['json_examples']['failure']:
        print(f"\n❌ JSON失敗例:")
        for i, example in enumerate(stats['json_examples']['failure'], 1):
            print(f"\n  例{i} - {example['agent']}:")
            print(f"    エラー: {example['error']}")
            print(f"    応答プレビュー: {example['response_preview']}...")
    
    # 最終評価
    print(f"\n🏁 最終評価:")
    if success_rate >= 70:
        print("✅ JSONパーシングは良好に機能しています")
    elif success_rate >= 50:
        print("⚠️ JSONパーシングは部分的に機能しています")
    else:
        print("❌ JSONパーシングに問題があります")
    
    if stats['decisions']['BUY'] > 0 and stats['decisions']['SELL'] > 0:
        print("✅ BUY/SELL決定が生成されています")
    else:
        print("❌ BUY/SELL決定が生成されていません")
    
    # 結果を保存
    with open('debug_log_analysis.json', 'w') as f:
        # Counterをdictに変換
        save_stats = stats.copy()
        save_stats['decisions'] = dict(stats['decisions'])
        save_stats['agents'] = dict(stats['agents'])
        json.dump(save_stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 詳細な分析結果を保存しました: debug_log_analysis.json")

if __name__ == "__main__":
    main()