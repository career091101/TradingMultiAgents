#!/usr/bin/env python3
"""
Phase 3 並列テスト実行スクリプト
カテゴリ別、ブラウザ別の並列実行を最適化
"""

import argparse
import asyncio
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import multiprocessing


def parse_arguments():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(
        description="Phase 3 並列E2Eテスト実行"
    )
    parser.add_argument(
        "--categories", 
        nargs='+',
        default=['error_handling', 'performance', 'security'],
        help="実行するテストカテゴリ"
    )
    parser.add_argument(
        "--browsers", 
        nargs='+',
        default=['chromium'],
        help="使用するブラウザ"
    )
    parser.add_argument(
        "--parallel-workers", 
        type=int,
        default=min(4, multiprocessing.cpu_count()),
        help="並列ワーカー数"
    )
    parser.add_argument(
        "--output-dir", 
        default="tests/reports/phase3_parallel",
        help="結果出力ディレクトリ"
    )
    parser.add_argument(
        "--timeout", 
        type=int,
        default=600,
        help="各テストのタイムアウト（秒）"
    )
    parser.add_argument(
        "--retry-failed", 
        type=int,
        default=1,
        help="失敗したテストの再試行回数"
    )
    parser.add_argument(
        "--fast-fail", 
        action='store_true',
        help="最初の失敗で全体を停止"
    )
    return parser.parse_args()


class TestRunner:
    """並列テスト実行管理クラス"""
    
    def __init__(self, args):
        self.args = args
        self.output_dir = Path(args.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_configs = self._generate_test_configs()
        self.results = {}
        self.start_time = time.time()
    
    def _generate_test_configs(self) -> List[Dict[str, Any]]:
        """テスト設定の組み合わせを生成"""
        configs = []
        
        for category in self.args.categories:
            for browser in self.args.browsers:
                config = {
                    'category': category,
                    'browser': browser,
                    'test_file': f"test_{category}_adapted.py",
                    'output_file': f"{category}_{browser}_results.json",
                    'log_file': f"{category}_{browser}.log",
                    'screenshot_dir': f"screenshots_{category}_{browser}"
                }
                configs.append(config)
        
        return configs
    
    def _run_single_test(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """単一テスト設定を実行"""
        test_id = f"{config['category']}_{config['browser']}"
        print(f"🚀 テスト開始: {test_id}")
        
        start_time = time.time()
        
        # 出力ディレクトリを準備
        test_output_dir = self.output_dir / test_id
        test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # pytestコマンドを構築
        cmd = [
            "python", "-m", "pytest",
            f"tests/e2e/{config['test_file']}",
            f"--browser={config['browser']}",
            "--screenshot=on",
            f"--html={test_output_dir / 'report.html'}",
            "--self-contained-html",
            f"--json-report={test_output_dir / config['output_file']}",
            "--json-report-summary",
            "-v"
        ]
        
        # CI環境の設定
        env = os.environ.copy()
        env.update({
            'CI': 'true',
            'PYTEST_CURRENT_TEST': test_id,
            'SCREENSHOT_DIR': str(test_output_dir / config['screenshot_dir'])
        })
        
        result = {
            'config': config,
            'test_id': test_id,
            'start_time': start_time,
            'status': 'unknown',
            'return_code': -1,
            'stdout': '',
            'stderr': '',
            'duration': 0,
            'output_dir': str(test_output_dir)
        }
        
        try:
            # テストを実行
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.args.timeout,
                env=env,
                cwd=Path.cwd()
            )
            
            result.update({
                'return_code': process.returncode,
                'stdout': process.stdout,
                'stderr': process.stderr,
                'status': 'passed' if process.returncode == 0 else 'failed'
            })
            
            # 結果ファイルから詳細情報を抽出
            self._extract_test_details(result, test_output_dir)
            
        except subprocess.TimeoutExpired:
            result.update({
                'status': 'timeout',
                'stderr': f"Test timed out after {self.args.timeout} seconds"
            })
            print(f"⏰ タイムアウト: {test_id}")
            
        except Exception as e:
            result.update({
                'status': 'error',
                'stderr': str(e)
            })
            print(f"❌ エラー: {test_id} - {e}")
        
        finally:
            result['duration'] = time.time() - start_time
            
        # 結果をログ出力
        status_emoji = {
            'passed': '✅',
            'failed': '❌', 
            'timeout': '⏰',
            'error': '💥'
        }.get(result['status'], '❓')
        
        print(f"{status_emoji} テスト完了: {test_id} ({result['duration']:.1f}s)")
        
        return result
    
    def _extract_test_details(self, result: Dict, output_dir: Path):
        """テスト結果から詳細情報を抽出"""
        json_file = output_dir / result['config']['output_file']
        
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                summary = data.get('summary', {})
                result['test_details'] = {
                    'total': summary.get('total', 0),
                    'passed': summary.get('passed', 0),
                    'failed': summary.get('failed', 0),
                    'skipped': summary.get('skipped', 0),
                    'error': summary.get('error', 0)
                }
                
                # パフォーマンスデータを抽出
                if 'performance' in result['config']['category']:
                    result['performance'] = self._extract_performance_data(data)
                
                # セキュリティデータを抽出
                if 'security' in result['config']['category']:
                    result['security'] = self._extract_security_data(data)
                    
            except Exception as e:
                print(f"Warning: {json_file}の詳細抽出に失敗: {e}")
    
    def _extract_performance_data(self, data: Dict) -> Dict[str, Any]:
        """パフォーマンスデータを抽出"""
        performance = {}
        
        tests = data.get('tests', [])
        page_loads = []
        navigations = []
        
        for test in tests:
            output = test.get('stdout', '') + test.get('stderr', '')
            
            # ページロード時間
            import re
            page_load_match = re.search(r'Page load time: ([\d.]+)', output)
            if page_load_match:
                page_loads.append(float(page_load_match.group(1)))
            
            # ナビゲーション時間
            nav_match = re.search(r'Navigation time: ([\d.]+)', output)
            if nav_match:
                navigations.append(float(nav_match.group(1)))
        
        if page_loads:
            performance['avg_page_load'] = sum(page_loads) / len(page_loads)
            performance['max_page_load'] = max(page_loads)
        
        if navigations:
            performance['avg_navigation'] = sum(navigations) / len(navigations)
        
        return performance
    
    def _extract_security_data(self, data: Dict) -> Dict[str, Any]:
        """セキュリティデータを抽出"""
        security = {
            'vulnerabilities': 0,
            'warnings': 0,
            'security_tests': 0
        }
        
        tests = data.get('tests', [])
        for test in tests:
            if 'security' in test.get('name', '').lower():
                security['security_tests'] += 1
                
                output = test.get('stdout', '') + test.get('stderr', '')
                if 'vulnerability' in output.lower():
                    security['vulnerabilities'] += 1
                if 'warning' in output.lower():
                    security['warnings'] += 1
        
        return security
    
    def _retry_failed_tests(self, failed_results: List[Dict]) -> List[Dict]:
        """失敗したテストを再試行"""
        if not failed_results or self.args.retry_failed <= 0:
            return failed_results
        
        print(f"🔄 {len(failed_results)}個の失敗テストを再試行中...")
        
        retry_results = []
        with ThreadPoolExecutor(max_workers=min(2, self.args.parallel_workers)) as executor:
            future_to_config = {
                executor.submit(self._run_single_test, result['config']): result 
                for result in failed_results
            }
            
            for future in as_completed(future_to_config):
                retry_result = future.result()
                retry_results.append(retry_result)
        
        return retry_results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """全テストを並列実行"""
        print(f"🚀 Phase 3 並列テスト開始")
        print(f"   📊 設定数: {len(self.test_configs)}")
        print(f"   👥 並列ワーカー: {self.args.parallel_workers}")
        print(f"   ⏱️  タイムアウト: {self.args.timeout}秒")
        
        all_results = []
        failed_results = []
        
        # 並列実行
        with ThreadPoolExecutor(max_workers=self.args.parallel_workers) as executor:
            future_to_config = {
                executor.submit(self._run_single_test, config): config 
                for config in self.test_configs
            }
            
            for future in as_completed(future_to_config):
                result = future.result()
                all_results.append(result)
                
                if result['status'] not in ['passed']:
                    failed_results.append(result)
                    
                    if self.args.fast_fail:
                        print(f"💥 Fast-fail有効: {result['test_id']}で停止")
                        # 残りのfutureをキャンセル
                        for remaining_future in future_to_config:
                            if not remaining_future.done():
                                remaining_future.cancel()
                        break
        
        # 失敗したテストの再試行
        if failed_results and not self.args.fast_fail:
            retry_results = self._retry_failed_tests(failed_results)
            
            # 元の結果を再試行結果で置き換え
            for retry_result in retry_results:
                for i, original_result in enumerate(all_results):
                    if original_result['test_id'] == retry_result['test_id']:
                        all_results[i] = retry_result
                        break
        
        # サマリーを生成
        summary = self._generate_summary(all_results)
        
        # 結果を保存
        self._save_results(all_results, summary)
        
        return {
            'results': all_results,
            'summary': summary
        }
    
    def _generate_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """実行サマリーを生成"""
        total_tests = len(results)
        passed_tests = len([r for r in results if r['status'] == 'passed'])
        failed_tests = len([r for r in results if r['status'] == 'failed'])
        timeout_tests = len([r for r in results if r['status'] == 'timeout'])
        error_tests = len([r for r in results if r['status'] == 'error'])
        
        total_duration = time.time() - self.start_time
        avg_duration = sum(r['duration'] for r in results) / total_tests if total_tests > 0 else 0
        
        summary = {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'timeout': timeout_tests,
            'error': error_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'avg_test_duration': avg_duration,
            'parallel_workers': self.args.parallel_workers,
            'categories': list(set(r['config']['category'] for r in results)),
            'browsers': list(set(r['config']['browser'] for r in results))
        }
        
        # カテゴリ別統計
        category_stats = {}
        for category in summary['categories']:
            cat_results = [r for r in results if r['config']['category'] == category]
            category_stats[category] = {
                'total': len(cat_results),
                'passed': len([r for r in cat_results if r['status'] == 'passed']),
                'failed': len([r for r in cat_results if r['status'] != 'passed'])
            }
        summary['category_stats'] = category_stats
        
        # パフォーマンス統計
        perf_results = [r for r in results if r['config']['category'] == 'performance' and 'performance' in r]
        if perf_results:
            all_page_loads = [p['avg_page_load'] for r in perf_results for p in [r['performance']] if 'avg_page_load' in p]
            if all_page_loads:
                summary['performance'] = {
                    'avg_page_load': sum(all_page_loads) / len(all_page_loads),
                    'max_page_load': max(all_page_loads)
                }
        
        return summary
    
    def _save_results(self, results: List[Dict], summary: Dict):
        """結果を保存"""
        # 詳細結果
        results_file = self.output_dir / "detailed_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': summary,
                'results': results,
                'timestamp': time.time(),
                'args': vars(self.args)
            }, f, indent=2, ensure_ascii=False)
        
        # サマリー
        summary_file = self.output_dir / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"💾 結果を保存: {results_file}")
        print(f"📊 サマリー: {summary_file}")


def main():
    """メイン処理"""
    args = parse_arguments()
    
    # 環境チェック
    if not Path("tests/e2e").exists():
        print("❌ tests/e2eディレクトリが見つかりません")
        sys.exit(1)
    
    # テストランナーを作成して実行
    runner = TestRunner(args)
    result = runner.run_all_tests()
    
    summary = result['summary']
    
    # 結果を出力
    print("\n" + "="*60)
    print("📊 Phase 3 並列テスト実行結果")
    print("="*60)
    print(f"⏱️  総実行時間: {summary['total_duration']:.1f}秒")
    print(f"📊 総テスト数: {summary['total_tests']}")
    print(f"✅ 成功: {summary['passed']}")
    print(f"❌ 失敗: {summary['failed']}")
    print(f"⏰ タイムアウト: {summary['timeout']}")
    print(f"💥 エラー: {summary['error']}")
    print(f"📈 成功率: {summary['success_rate']:.1f}%")
    print(f"👥 並列ワーカー: {summary['parallel_workers']}")
    print(f"⚡ 平均テスト時間: {summary['avg_test_duration']:.1f}秒")
    
    if 'performance' in summary:
        print(f"🚀 平均ページロード: {summary['performance']['avg_page_load']:.2f}秒")
    
    # カテゴリ別結果
    print("\n📂 カテゴリ別結果:")
    for category, stats in summary['category_stats'].items():
        success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"   {category}: {stats['passed']}/{stats['total']} ({success_rate:.0f}%)")
    
    # 終了コード決定
    if summary['failed'] > 0 or summary['error'] > 0:
        print("\n❌ テストに失敗があります")
        sys.exit(1)
    else:
        print("\n✅ 全テストが成功しました")


if __name__ == "__main__":
    main()