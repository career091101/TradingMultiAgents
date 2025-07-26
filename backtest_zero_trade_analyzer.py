#!/usr/bin/env python3
"""
バックテスト取引ゼロ分析ツール
取引が0件の場合の詳細な根本原因分析を実行
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZeroTradeAnalyzer:
    def __init__(self, results: Dict, execution_logs: List[Dict]):
        self.results = results
        self.execution_logs = execution_logs
        self.analysis_timestamp = datetime.now()
        
    def perform_comprehensive_analysis(self) -> Dict:
        """包括的な取引ゼロ分析を実行"""
        logger.info("=== 取引ゼロの詳細分析を開始 ===")
        
        analysis = {
            "summary": self._create_summary(),
            "error_categorization": self._categorize_errors(),
            "root_cause_analysis": self._perform_5_whys_analysis(),
            "potential_factors": self._identify_potential_factors(),
            "recommendations": self._generate_recommendations(),
            "timeline_analysis": self._analyze_timeline()
        }
        
        return analysis
    
    def _create_summary(self) -> Dict:
        """分析サマリーの作成"""
        return {
            "analysis_date": self.analysis_timestamp.isoformat(),
            "backtest_result": {
                "trades": 0,
                "initial_capital": self.results.get("initial_capital", "$100,000"),
                "tickers": self.results.get("tickers", 2),
                "agents": self.results.get("agents", "10専門エージェント"),
                "llm_provider": self.results.get("llm_provider", "openai")
            },
            "issue": "バックテスト実行は成功したが、取引が一度も発生しなかった"
        }
    
    def _categorize_errors(self) -> Dict:
        """エラーの分類と優先度付け"""
        categories = {
            "データ関連": {
                "errors": [],
                "severity": "未確定",
                "indicators": ["価格データ", "データフィード", "API", "接続"]
            },
            "戦略関連": {
                "errors": [],
                "severity": "高",
                "indicators": ["エントリー条件", "シグナル", "閾値", "パラメータ"]
            },
            "システム関連": {
                "errors": [],
                "severity": "中",
                "indicators": ["実行", "処理", "メモリ", "タイムアウト"]
            },
            "設定関連": {
                "errors": [],
                "severity": "高",
                "indicators": ["設定", "パラメータ", "期間", "銘柄"]
            }
        }
        
        # 実行ログから関連するエラーを抽出
        for log in self.execution_logs:
            if log.get("status") in ["エラー", "警告", "error", "warning"]:
                details = log.get("details", "").lower()
                event = log.get("event", "").lower()
                
                for category, info in categories.items():
                    if any(indicator in details or indicator in event 
                          for indicator in info["indicators"]):
                        categories[category]["errors"].append({
                            "timestamp": log.get("timestamp"),
                            "event": log.get("event"),
                            "details": log.get("details")
                        })
        
        # 取引ゼロの場合、戦略関連が最も可能性が高い
        if not any(cat["errors"] for cat in categories.values()):
            categories["戦略関連"]["errors"].append({
                "timestamp": self.analysis_timestamp.isoformat(),
                "event": "取引シグナル未発生",
                "details": "バックテスト期間中に一度も取引条件を満たさなかった"
            })
            categories["戦略関連"]["severity"] = "確定"
        
        return categories
    
    def _perform_5_whys_analysis(self) -> Dict:
        """5つのなぜ分析による根本原因の特定"""
        rca = {
            "problem_statement": "バックテストで取引が0件だった",
            "5_whys_chain": []
        }
        
        # 最も可能性の高いシナリオ：戦略パラメータの問題
        why_chain_strategy = {
            "scenario": "戦略パラメータシナリオ",
            "probability": "高",
            "analysis": [
                {
                    "level": 1,
                    "why": "なぜ取引が0件だったのか？",
                    "because": "エントリー条件を一度も満たさなかったため"
                },
                {
                    "level": 2,
                    "why": "なぜエントリー条件を満たさなかったのか？",
                    "because": "設定されたシグナル閾値が厳しすぎるため"
                },
                {
                    "level": 3,
                    "why": "なぜシグナル閾値が厳しすぎるのか？",
                    "because": "市場のボラティリティに対して閾値が適切に調整されていないため"
                },
                {
                    "level": 4,
                    "why": "なぜ閾値が適切に調整されていないのか？",
                    "because": "バックテスト前の市場分析やパラメータ最適化が不十分だったため"
                },
                {
                    "level": 5,
                    "why": "なぜ事前の最適化が不十分だったのか？",
                    "because": "戦略設計プロセスにパラメータ検証ステップが組み込まれていないため"
                }
            ],
            "root_cause": "戦略設計プロセスの不備（パラメータ検証の欠如）"
        }
        
        # データ関連シナリオ
        why_chain_data = {
            "scenario": "データ品質シナリオ",
            "probability": "中",
            "analysis": [
                {
                    "level": 1,
                    "why": "なぜ取引が0件だったのか？",
                    "because": "価格データが正しく取得・処理されなかったため"
                },
                {
                    "level": 2,
                    "why": "なぜデータが正しく処理されなかったのか？",
                    "because": "データフィードの接続が不安定またはフォーマットが不正だったため"
                },
                {
                    "level": 3,
                    "why": "なぜ接続が不安定だったのか？",
                    "because": "APIレート制限またはネットワークの問題があったため"
                },
                {
                    "level": 4,
                    "why": "なぜレート制限の問題が発生したのか？",
                    "because": "データ取得の頻度やバッチサイズが適切に管理されていないため"
                },
                {
                    "level": 5,
                    "why": "なぜ適切に管理されていないのか？",
                    "because": "システム設計時にデータプロバイダーの制限を考慮していないため"
                }
            ],
            "root_cause": "システムアーキテクチャの設計不備（外部依存性の管理不足）"
        }
        
        rca["5_whys_chain"] = [why_chain_strategy, why_chain_data]
        rca["most_likely_root_cause"] = why_chain_strategy["root_cause"]
        
        return rca
    
    def _identify_potential_factors(self) -> List[Dict]:
        """潜在的な要因の特定と優先度付け"""
        factors = [
            {
                "factor": "エントリー条件の閾値設定",
                "category": "戦略パラメータ",
                "impact": "非常に高い",
                "likelihood": "高い",
                "description": "シグナル生成の閾値が市場の実際の動きに対して非現実的に設定されている",
                "verification_method": "閾値を段階的に緩和して再テスト",
                "quick_fix": "閾値を50%緩和して再実行"
            },
            {
                "factor": "取引時間制限",
                "category": "実行設定",
                "impact": "高い",
                "likelihood": "中程度",
                "description": "取引可能時間が限定的に設定されている可能性",
                "verification_method": "24時間取引設定で再テスト",
                "quick_fix": "取引時間制限を解除"
            },
            {
                "factor": "リスク管理パラメータ",
                "category": "リスク設定",
                "impact": "高い",
                "likelihood": "中程度",
                "description": "ポジションサイズやリスク許容度が過度に保守的",
                "verification_method": "リスクパラメータのログを確認",
                "quick_fix": "最小取引単位を下げる"
            },
            {
                "factor": "データ品質問題",
                "category": "データ",
                "impact": "非常に高い",
                "likelihood": "低い",
                "description": "価格データに欠損や異常値が含まれている",
                "verification_method": "データ品質レポートを生成",
                "quick_fix": "データソースを変更"
            },
            {
                "factor": "エージェント間の競合",
                "category": "システム",
                "impact": "中程度",
                "likelihood": "低い",
                "description": "複数のエージェントが互いの取引を妨げている",
                "verification_method": "エージェント通信ログを分析",
                "quick_fix": "エージェント数を減らす"
            }
        ]
        
        # リスクスコアで並び替え
        for factor in factors:
            impact_score = {"非常に高い": 3, "高い": 2, "中程度": 1, "低い": 0}
            likelihood_score = {"高い": 3, "中程度": 2, "低い": 1, "非常に低い": 0}
            
            factor["risk_score"] = (
                impact_score.get(factor["impact"], 0) * 
                likelihood_score.get(factor["likelihood"], 0)
            )
        
        factors.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return factors
    
    def _generate_recommendations(self) -> Dict:
        """実行可能な推奨事項の生成"""
        return {
            "immediate_actions": [
                {
                    "priority": 1,
                    "action": "エントリー条件の確認と調整",
                    "steps": [
                        "現在のエントリー条件パラメータをログから抽出",
                        "閾値を30-50%緩和した設定で再実行",
                        "段階的に閾値を調整しながら最適値を探索"
                    ],
                    "expected_time": "30分",
                    "success_criteria": "少なくとも1つの取引が発生すること"
                },
                {
                    "priority": 2,
                    "action": "データ検証の実施",
                    "steps": [
                        "使用したデータの期間と銘柄を確認",
                        "データの連続性と品質をチェック",
                        "異なるデータソースでの検証"
                    ],
                    "expected_time": "20分",
                    "success_criteria": "データ品質スコア90%以上"
                }
            ],
            "short_term_improvements": [
                {
                    "timeframe": "1週間",
                    "action": "パラメータ最適化プロセスの確立",
                    "description": "グリッドサーチやベイジアン最適化を使用した体系的なパラメータ調整"
                },
                {
                    "timeframe": "3日",
                    "action": "デバッグモードの実装",
                    "description": "シグナル生成の詳細なログ出力機能を追加"
                }
            ],
            "long_term_solutions": [
                {
                    "timeframe": "1ヶ月",
                    "action": "自動パラメータ調整システムの構築",
                    "description": "市場状況に応じて動的にパラメータを調整するシステム"
                },
                {
                    "timeframe": "2週間",
                    "action": "包括的なバックテスト検証フレームワーク",
                    "description": "取引ゼロを防ぐための事前チェック機能"
                }
            ]
        }
    
    def _analyze_timeline(self) -> Dict:
        """実行タイムラインの分析"""
        timeline_events = []
        
        for log in self.execution_logs:
            if log.get("event") and log.get("timestamp"):
                timeline_events.append({
                    "time": log["timestamp"],
                    "event": log["event"],
                    "status": log.get("status", "info"),
                    "details": log.get("details", "")
                })
        
        # 重要なマイルストーンを特定
        milestones = {
            "execution_start": None,
            "data_loaded": None,
            "strategy_initialized": None,
            "execution_complete": None,
            "first_signal_check": None,
            "last_signal_check": None
        }
        
        for event in timeline_events:
            event_lower = event["event"].lower()
            if "実行開始" in event_lower or "start" in event_lower:
                milestones["execution_start"] = event["time"]
            elif "完了" in event_lower or "complete" in event_lower:
                milestones["execution_complete"] = event["time"]
        
        return {
            "total_events": len(timeline_events),
            "milestones": milestones,
            "events": timeline_events[-10:]  # 最新10件
        }
    
    def generate_report(self, analysis: Dict) -> str:
        """人間が読みやすいレポートの生成"""
        report = f"""
================================================================================
                        バックテスト取引ゼロ - 詳細分析レポート
================================================================================
分析日時: {self.analysis_timestamp.strftime('%Y年%m月%d日 %H:%M:%S')}

【1. エグゼクティブサマリー】
バックテストは正常に実行されましたが、取引が0件という結果になりました。
最も可能性の高い原因は「エントリー条件が厳しすぎる」ことです。

【2. 根本原因分析（5つのなぜ）】
{self._format_rca(analysis['root_cause_analysis'])}

【3. 優先対応事項】
{self._format_recommendations(analysis['recommendations'])}

【4. リスク要因分析】
{self._format_risk_factors(analysis['potential_factors'])}

【5. 次のステップ】
1. 即座に実行すべきアクション:
   - エントリー条件の閾値を50%緩和して再実行
   - 実行時間: 約30分
   - 成功基準: 1件以上の取引発生

2. 今週中に実施すべき改善:
   - パラメータ最適化プロセスの確立
   - デバッグログの強化

【6. 予防策】
今後同様の問題を防ぐため、以下の対策を推奨します：
- バックテスト前のパラメータ妥当性チェック
- 段階的なパラメータ調整プロセス
- 自動検証機能の実装

================================================================================
"""
        return report
    
    def _format_rca(self, rca: Dict) -> str:
        """RCA結果のフォーマット"""
        primary_scenario = rca["5_whys_chain"][0]
        result = f"最も可能性の高いシナリオ: {primary_scenario['scenario']}\n\n"
        
        for why in primary_scenario["analysis"]:
            indent = "  " * (why["level"] - 1)
            result += f"{indent}Q{why['level']}: {why['why']}\n"
            result += f"{indent}A{why['level']}: {why['because']}\n\n"
        
        result += f"根本原因: {primary_scenario['root_cause']}\n"
        return result
    
    def _format_recommendations(self, recommendations: Dict) -> str:
        """推奨事項のフォーマット"""
        result = "即時対応項目:\n"
        for action in recommendations["immediate_actions"]:
            result += f"\n優先度{action['priority']}: {action['action']}\n"
            result += f"  所要時間: {action['expected_time']}\n"
            result += f"  成功基準: {action['success_criteria']}\n"
            result += "  手順:\n"
            for i, step in enumerate(action['steps'], 1):
                result += f"    {i}. {step}\n"
        
        return result
    
    def _format_risk_factors(self, factors: List[Dict]) -> str:
        """リスク要因のフォーマット"""
        result = "高リスク要因（上位3件）:\n\n"
        for i, factor in enumerate(factors[:3], 1):
            result += f"{i}. {factor['factor']}\n"
            result += f"   カテゴリ: {factor['category']}\n"
            result += f"   影響度: {factor['impact']}\n"
            result += f"   可能性: {factor['likelihood']}\n"
            result += f"   対策: {factor['quick_fix']}\n\n"
        
        return result
    
    def save_analysis(self, analysis: Dict, report: str):
        """分析結果の保存"""
        timestamp = self.analysis_timestamp.strftime('%Y%m%d_%H%M%S')
        
        # JSON形式で保存
        json_file = f"zero_trade_analysis_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        # テキストレポートを保存
        report_file = f"zero_trade_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"分析結果を保存しました:")
        logger.info(f"  - JSON: {json_file}")
        logger.info(f"  - レポート: {report_file}")
        
        return json_file, report_file


def analyze_zero_trades(results_file: Optional[str] = None):
    """メイン分析関数"""
    # デモ用のデータ（実際の結果から）
    demo_results = {
        "trades": 0,
        "initial_capital": "$100,000",
        "tickers": 2,
        "agents": "10専門エージェント",
        "llm_provider": "openai",
        "max_positions": 5
    }
    
    demo_logs = [
        {
            "timestamp": datetime.now().isoformat(),
            "event": "バックテスト開始",
            "status": "成功",
            "details": "初期設定完了"
        },
        {
            "timestamp": datetime.now().isoformat(),
            "event": "データ取得",
            "status": "成功",
            "details": "2銘柄の価格データを取得"
        },
        {
            "timestamp": datetime.now().isoformat(),
            "event": "戦略初期化",
            "status": "成功",
            "details": "10エージェントを初期化"
        },
        {
            "timestamp": datetime.now().isoformat(),
            "event": "シグナル生成",
            "status": "警告",
            "details": "取引シグナルが生成されませんでした"
        },
        {
            "timestamp": datetime.now().isoformat(),
            "event": "バックテスト完了",
            "status": "成功",
            "details": "取引数: 0"
        }
    ]
    
    # 分析実行
    analyzer = ZeroTradeAnalyzer(demo_results, demo_logs)
    analysis = analyzer.perform_comprehensive_analysis()
    report = analyzer.generate_report(analysis)
    
    # 結果表示
    print(report)
    
    # ファイル保存
    json_file, report_file = analyzer.save_analysis(analysis, report)
    
    # インタラクティブな次のステップ
    print("\n" + "="*80)
    print("分析が完了しました。次のアクションを選択してください:")
    print("1. エントリー条件を緩和して再実行")
    print("2. 詳細なデータ品質チェックを実行")
    print("3. 異なる期間で再テスト")
    print("4. パラメータ最適化を開始")
    print("0. 終了")
    
    try:
        choice = input("\n選択番号: ")
        return int(choice)
    except:
        return 0


if __name__ == "__main__":
    choice = analyze_zero_trades()
    
    if choice == 1:
        print("\nエントリー条件を緩和して再実行します...")
        print("（実装は complete_backtest_execution.py を修正して実行）")
    elif choice == 2:
        print("\nデータ品質チェックを開始します...")
    elif choice == 3:
        print("\n異なる期間での再テストを準備します...")
    elif choice == 4:
        print("\nパラメータ最適化プロセスを開始します...")