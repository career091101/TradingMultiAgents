#!/usr/bin/env python3
"""
直接バックテスト実行自動化スクリプト
ブラウザを使わずに直接バックテストを実行し、結果を分析する
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('direct_backtest_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# プロジェクトパスの設定
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'TradingMultiAgents'))

# 必要なモジュールのインポート
try:
    from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper
except ImportError as e:
    logger.error(f"Failed to import Backtest2Wrapper: {e}")
    sys.exit(1)

class DirectBacktestAutomation:
    """直接バックテスト自動実行クラス"""
    
    def __init__(self):
        self.wrapper = Backtest2Wrapper()
        self.logs = []
        self.progress_updates = []
        self.results = {}
        
    def log_callback(self, message: str):
        """ログメッセージのコールバック"""
        self.logs.append({
            'timestamp': datetime.now().isoformat(),
            'message': message
        })
        logger.info(f"Backtest Log: {message}")
        
    def progress_callback(self, progress: float, status: str, ticker: str = None):
        """進捗更新のコールバック"""
        update = {
            'timestamp': datetime.now().isoformat(),
            'progress': progress,
            'status': status,
            'ticker': ticker
        }
        self.progress_updates.append(update)
        logger.info(f"Progress: {progress:.1f}% - {status}" + (f" ({ticker})" if ticker else ""))
    
    def create_default_config(self) -> Dict[str, Any]:
        """デフォルトのバックテスト設定を作成"""
        return {
            # 基本設定
            'tickers': ['AAPL', 'MSFT'],
            'start_date': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
            'end_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'initial_capital': 100000.0,
            
            # リスク管理設定
            'position_limits': {
                'aggressive': 0.8,
                'neutral': 0.5,
                'conservative': 0.3
            },
            
            # LLM設定（モックモードで実行）
            'use_mock': True,
            'llm_config': {
                'provider': 'openai',
                'model': 'gpt-4o-mini',
                'temperature': 0.7,
                'max_tokens': 2000
            },
            
            # エージェント設定
            'agents': {
                'trader': {'enabled': True, 'role': 'trader'},
                'risk_manager': {'enabled': True, 'role': 'risk_manager'},
                'fundamental_analyst': {'enabled': True, 'role': 'analyst'},
                'market_analyst': {'enabled': True, 'role': 'analyst'},
                'sentiment_analyst': {'enabled': True, 'role': 'analyst'},
                'technical_analyst': {'enabled': True, 'role': 'analyst'}
            },
            
            # その他の設定
            'enable_reflection': True,
            'enable_short_selling': False,
            'max_iterations': 10,
            'cache_enabled': True
        }
    
    async def run_backtest(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """バックテストを実行"""
        if config is None:
            config = self.create_default_config()
        
        logger.info("バックテスト実行を開始します")
        logger.info(f"設定: {json.dumps(config, indent=2, ensure_ascii=False)}")
        
        try:
            # バックテスト実行
            self.results = await self.wrapper.run_backtest_async(
                config=config,
                progress_callback=self.progress_callback,
                log_callback=self.log_callback
            )
            
            logger.info("バックテストが完了しました")
            return self.results
            
        except Exception as e:
            logger.error(f"バックテスト実行中にエラーが発生しました: {e}")
            raise
    
    def analyze_results(self) -> Dict[str, Any]:
        """実行結果を分析"""
        analysis = {
            'execution_summary': {},
            'problems': [],
            'warnings': [],
            'performance_metrics': {}
        }
        
        # ログ分析
        error_count = 0
        warning_count = 0
        
        for log in self.logs:
            message_lower = log['message'].lower()
            
            if any(word in message_lower for word in ['error', 'failed', 'exception']):
                error_count += 1
                analysis['problems'].append({
                    'type': 'error',
                    'timestamp': log['timestamp'],
                    'message': log['message']
                })
            elif any(word in message_lower for word in ['warning', 'warn']):
                warning_count += 1
                analysis['warnings'].append({
                    'type': 'warning',
                    'timestamp': log['timestamp'],
                    'message': log['message']
                })
        
        analysis['execution_summary'] = {
            'total_logs': len(self.logs),
            'errors': error_count,
            'warnings': warning_count,
            'progress_updates': len(self.progress_updates)
        }
        
        # 結果のパフォーマンス分析
        if self.results:
            for ticker, result in self.results.items():
                if isinstance(result, dict) and 'metrics' in result:
                    metrics = result['metrics']
                    analysis['performance_metrics'][ticker] = {
                        'total_return': metrics.get('total_return', 0),
                        'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                        'max_drawdown': metrics.get('max_drawdown', 0),
                        'win_rate': metrics.get('win_rate', 0),
                        'total_trades': metrics.get('total_trades', 0)
                    }
        
        # 問題の判定
        analysis['has_critical_issues'] = error_count > 0
        analysis['needs_attention'] = warning_count > 5 or any(
            metrics.get('total_return', 0) < -0.2 
            for metrics in analysis['performance_metrics'].values()
        )
        
        return analysis
    
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """分析結果のレポートを生成"""
        report = []
        report.append("=" * 80)
        report.append("バックテスト自動実行レポート")
        report.append("=" * 80)
        report.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 実行サマリー
        report.append("## 実行サマリー")
        summary = analysis['execution_summary']
        report.append(f"- 総ログ数: {summary['total_logs']}")
        report.append(f"- エラー数: {summary['errors']}")
        report.append(f"- 警告数: {summary['warnings']}")
        report.append(f"- 進捗更新数: {summary['progress_updates']}")
        report.append("")
        
        # パフォーマンスメトリクス
        if analysis['performance_metrics']:
            report.append("## パフォーマンスメトリクス")
            for ticker, metrics in analysis['performance_metrics'].items():
                report.append(f"\n### {ticker}")
                report.append(f"- 総リターン: {metrics['total_return']:.2%}")
                report.append(f"- シャープレシオ: {metrics['sharpe_ratio']:.2f}")
                report.append(f"- 最大ドローダウン: {metrics['max_drawdown']:.2%}")
                report.append(f"- 勝率: {metrics['win_rate']:.2%}")
                report.append(f"- 総取引数: {metrics['total_trades']}")
            report.append("")
        
        # 問題点
        if analysis['problems']:
            report.append("## 検出された問題")
            for i, problem in enumerate(analysis['problems'][:10], 1):  # 最初の10個のみ
                report.append(f"{i}. [{problem['timestamp']}] {problem['message']}")
            if len(analysis['problems']) > 10:
                report.append(f"... 他 {len(analysis['problems']) - 10} 件のエラー")
            report.append("")
        
        # 警告
        if analysis['warnings']:
            report.append("## 警告")
            for i, warning in enumerate(analysis['warnings'][:5], 1):  # 最初の5個のみ
                report.append(f"{i}. [{warning['timestamp']}] {warning['message']}")
            if len(analysis['warnings']) > 5:
                report.append(f"... 他 {len(analysis['warnings']) - 5} 件の警告")
            report.append("")
        
        # 判定結果
        report.append("## 判定結果")
        if analysis['has_critical_issues']:
            report.append("❌ **重大な問題が検出されました**")
            report.append("- エラーログを確認し、原因を特定してください")
        elif analysis['needs_attention']:
            report.append("⚠️ **注意が必要です**")
            report.append("- 警告が多い、またはパフォーマンスが低い可能性があります")
        else:
            report.append("✅ **正常に完了しました**")
            report.append("- 問題は検出されませんでした")
        
        # 推奨アクション
        report.append("\n## 推奨アクション")
        if analysis['has_critical_issues']:
            report.append("1. エラーログの詳細を確認")
            report.append("2. APIキーと設定の確認")
            report.append("3. データソースの接続状態を確認")
        elif analysis['needs_attention']:
            report.append("1. 警告内容の確認")
            report.append("2. パフォーマンス低下の原因調査")
            report.append("3. パラメータの調整を検討")
        else:
            report.append("1. 結果の詳細分析を継続")
            report.append("2. より長期間でのバックテストを検討")
            report.append("3. 実際のLLMモードでの検証")
        
        report.append("\n" + "=" * 80)
        
        return '\n'.join(report)
    
    def save_results(self, analysis: Dict[str, Any], report: str):
        """結果を保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # レポートを保存
        report_file = f"backtest_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"レポートを保存しました: {report_file}")
        
        # 詳細な結果をJSON形式で保存
        results_file = f"backtest_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'analysis': analysis,
                'results': self.results,
                'logs': self.logs[-100:],  # 最後の100件のログ
                'progress': self.progress_updates[-50:]  # 最後の50件の進捗
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"詳細結果を保存しました: {results_file}")

async def main():
    """メイン実行関数"""
    automation = DirectBacktestAutomation()
    
    try:
        # バックテスト実行
        results = await automation.run_backtest()
        
        # 結果分析
        analysis = automation.analyze_results()
        
        # レポート生成
        report = automation.generate_report(analysis)
        
        # 結果保存
        automation.save_results(analysis, report)
        
        # レポートを表示
        print("\n" + report)
        
    except Exception as e:
        logger.error(f"実行中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # イベントループを実行
    asyncio.run(main())