"""
バックテスト2の全テストを実行するマスタースクリプト
カバレッジレポートも生成
"""

import subprocess
import sys
import os
from pathlib import Path
import json
from datetime import datetime


class TestRunner:
    """テスト実行管理クラス"""
    
    def __init__(self):
        self.results = {
            "execution_time": datetime.now().isoformat(),
            "test_suites": {},
            "coverage": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
    
    def run_test_suite(self, name: str, path: str, markers: str = None):
        """個別のテストスイートを実行"""
        print(f"\n{'='*60}")
        print(f"Running {name}")
        print('='*60)
        
        cmd = ["pytest", path, "-v", "--tb=short", f"--json-report-file={name}_report.json"]
        if markers:
            cmd.extend(["-m", markers])
        
        # カバレッジ計測を追加
        cmd.extend([
            f"--cov=backtest2",
            f"--cov-report=html:htmlcov/{name}",
            f"--cov-report=json:{name}_coverage.json"
        ])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 結果を解析
        success = result.returncode == 0
        self.results["test_suites"][name] = {
            "success": success,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        # JSON レポートから統計を抽出
        try:
            with open(f"{name}_report.json", 'r') as f:
                report = json.load(f)
                summary = report.get("summary", {})
                self.results["test_suites"][name]["stats"] = {
                    "total": summary.get("total", 0),
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "skipped": summary.get("skipped", 0)
                }
                
                # 全体の統計を更新
                self.results["summary"]["total_tests"] += summary.get("total", 0)
                self.results["summary"]["passed"] += summary.get("passed", 0)
                self.results["summary"]["failed"] += summary.get("failed", 0)
                self.results["summary"]["skipped"] += summary.get("skipped", 0)
        except:
            pass
        
        # カバレッジ情報を抽出
        try:
            with open(f"{name}_coverage.json", 'r') as f:
                coverage = json.load(f)
                self.results["coverage"][name] = coverage.get("totals", {}).get("percent_covered", 0)
        except:
            pass
        
        return success
    
    def run_all_tests(self):
        """全テストスイートを実行"""
        print("Starting Backtest2 Comprehensive Test Suite")
        print(f"Time: {datetime.now()}")
        
        # テストスイート定義
        test_suites = [
            # Phase 1: 基礎機能
            ("unit_circular_buffer", "tests/unit/test_circular_buffer.py"),
            ("unit_memory_store", "tests/unit/test_memory_store.py"),
            ("unit_position_manager", "tests/unit/test_position_manager.py"),
            
            # Phase 2: リスク管理
            ("unit_risk_analyzer", "tests/unit/test_risk_analyzer.py"),
            ("unit_transaction_manager", "tests/unit/test_transaction_manager.py"),
            ("unit_retry_handler", "tests/unit/test_retry_handler.py"),
            
            # Phase 3: パフォーマンス
            ("unit_cache_manager", "tests/unit/test_cache_manager.py"),
            ("unit_metrics_calculator", "tests/unit/test_metrics_calculator.py"),
            
            # Phase 4: 統合テスト
            ("integration_engine_position", "tests/integration/test_engine_position_integration.py"),
            ("integration_error_recovery", "tests/integration/test_error_recovery.py"),
            ("integration_performance", "tests/integration/test_performance.py"),
            
            # Phase 5: E2Eテスト
            ("e2e_complete_flow", "tests/e2e/test_complete_backtest_flow.py"),
            ("e2e_agent_coordination", "tests/e2e/test_agent_coordination.py"),
            ("e2e_webui", "tests/e2e/test_webui_integration.py", "not requires_ui"),
        ]
        
        all_success = True
        
        for suite_info in test_suites:
            name = suite_info[0]
            path = suite_info[1]
            markers = suite_info[2] if len(suite_info) > 2 else None
            
            # ファイルが存在する場合のみ実行
            if Path(path).exists():
                success = self.run_test_suite(name, path, markers)
                all_success = all_success and success
            else:
                print(f"⚠️  Test file not found: {path}")
                self.results["test_suites"][name] = {
                    "success": False,
                    "skipped": True,
                    "reason": "File not found"
                }
        
        return all_success
    
    def generate_report(self):
        """テストレポートを生成"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        # サマリー表示
        summary = self.results["summary"]
        total = summary["total_tests"]
        passed = summary["passed"]
        failed = summary["failed"]
        skipped = summary["skipped"]
        
        if total > 0:
            success_rate = (passed / total) * 100
        else:
            success_rate = 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Skipped: {skipped} ⚠️")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # 各スイートの結果
        print("\nTest Suite Results:")
        print("-" * 60)
        for name, result in self.results["test_suites"].items():
            if result.get("skipped"):
                status = "⚠️  SKIPPED"
            elif result["success"]:
                status = "✅ PASSED"
            else:
                status = "❌ FAILED"
            
            stats = result.get("stats", {})
            if stats:
                print(f"{name:30} {status:10} ({stats.get('passed', 0)}/{stats.get('total', 0)} tests)")
            else:
                print(f"{name:30} {status:10}")
        
        # カバレッジサマリー
        if self.results["coverage"]:
            print("\nCode Coverage:")
            print("-" * 60)
            total_coverage = []
            for name, coverage in self.results["coverage"].items():
                print(f"{name:30} {coverage:.1f}%")
                total_coverage.append(coverage)
            
            if total_coverage:
                avg_coverage = sum(total_coverage) / len(total_coverage)
                print(f"{'Average Coverage':30} {avg_coverage:.1f}%")
        
        # JSON レポートを保存
        with open("test_results_summary.json", 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Detailed reports saved to:")
        print(f"   - test_results_summary.json")
        print(f"   - htmlcov/*/index.html (coverage reports)")
        
        return success_rate >= 80  # 80%以上で成功とする
    
    def cleanup(self):
        """一時ファイルのクリーンアップ"""
        import glob
        
        # 個別のレポートファイルを削除
        for pattern in ["*_report.json", "*_coverage.json"]:
            for file in glob.glob(pattern):
                try:
                    os.remove(file)
                except:
                    pass


def main():
    """メイン実行関数"""
    runner = TestRunner()
    
    try:
        # 環境変数設定
        os.environ["PYTHONPATH"] = str(Path.cwd())
        
        # pytest プラグインのインストール確認
        required_plugins = ["pytest-cov", "pytest-asyncio", "pytest-json-report"]
        for plugin in required_plugins:
            try:
                __import__(plugin.replace("-", "_"))
            except ImportError:
                print(f"Installing required plugin: {plugin}")
                subprocess.run([sys.executable, "-m", "pip", "install", plugin])
        
        # テスト実行
        all_success = runner.run_all_tests()
        
        # レポート生成
        report_success = runner.generate_report()
        
        # クリーンアップ
        runner.cleanup()
        
        # 終了コード
        if all_success and report_success:
            print("\n🎉 All tests passed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed. Please check the reports.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()