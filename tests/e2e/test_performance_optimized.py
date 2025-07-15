"""
Week 4のパフォーマンス最適化機能を使用したE2Eテスト例
"""

import pytest
from playwright.sync_api import Page
import time
from utils.performance_monitor import PerformanceMonitor, measure_performance, MemoryOptimizer
from utils.test_cache import get_test_cache, PageStateCache, TestDataCache
from utils.parallel_optimizer import TestNode, SmartTestScheduler
from utils.custom_assertions import CustomAssertions


class TestPerformanceOptimized:
    """パフォーマンス最適化されたテスト"""
    
    def setup_class(cls):
        """クラスレベルのセットアップ"""
        cls.performance_monitor = PerformanceMonitor()
        cls.cache = get_test_cache()
        cls.page_cache = PageStateCache(cls.cache)
        cls.data_cache = TestDataCache(cls.cache)
    
    def teardown_class(cls):
        """クラスレベルのクリーンアップ"""
        # パフォーマンスレポートを生成
        report_path = cls.performance_monitor.generate_performance_report()
        print(f"\n📊 パフォーマンスレポート: {report_path}")
        
        # ボトルネック分析
        bottlenecks = cls.performance_monitor.analyze_bottlenecks()
        if bottlenecks["slow_tests"]:
            print("\n🐌 遅いテスト:")
            for test in bottlenecks["slow_tests"]:
                print(f"  - {test['test']}: {test['duration']:.2f}秒")
        
        # キャッシュ統計
        cache_stats = cls.cache.get_stats()
        print(f"\n💾 キャッシュ統計: {cache_stats}")
    
    def test_cached_navigation(self, page: Page):
        """キャッシュを活用したナビゲーションテスト"""
        test_name = "cached_navigation"
        
        with self.performance_monitor.measure(test_name, page) as metrics:
            # マーカー: テスト開始
            self.performance_monitor.mark(metrics, "test_start")
            
            # ページ状態をキャッシュから復元
            if not self.page_cache.restore_page_state(page, "dashboard_state"):
                # 初回はナビゲーション実行
                page.goto(page.url)
                page.wait_for_load_state("networkidle")
                
                # ダッシュボードへ移動
                dashboard_button = page.locator('[data-testid="stSidebar"] button:has-text("ダッシュボード")')
                dashboard_button.click()
                page.wait_for_load_state("networkidle")
                
                # 状態を保存
                self.page_cache.save_page_state(page, "dashboard_state")
                
                self.performance_monitor.mark(metrics, "navigation_complete")
            else:
                self.performance_monitor.mark(metrics, "restored_from_cache")
            
            # アサーション
            assertions = CustomAssertions(page)
            assertions.assert_element_visible('[data-testid="stMetric"]')
            
            self.performance_monitor.mark(metrics, "test_complete")
    
    @pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "GOOGL"])
    def test_cached_api_data(self, page: Page, ticker: str):
        """APIデータのキャッシュテスト"""
        test_name = f"cached_api_data_{ticker}"
        
        with self.performance_monitor.measure(test_name, page) as metrics:
            # テストデータをキャッシュから取得または生成
            stock_data = self.data_cache.get_cached_test_data(
                f"stock_data_{ticker}",
                lambda: self._generate_stock_data(ticker)
            )
            
            # 設定ページへ移動
            settings_button = page.locator('[data-testid="stSidebar"] button:has-text("分析設定")')
            settings_button.click()
            page.wait_for_load_state("networkidle")
            
            # ティッカーを入力
            ticker_input = page.locator('input[type="text"]').first
            if ticker_input.is_visible():
                ticker_input.fill(ticker)
            
            # キャッシュされたデータの使用をマーク
            if stock_data.get("from_cache"):
                self.performance_monitor.mark(metrics, "used_cached_data")
            else:
                self.performance_monitor.mark(metrics, "generated_new_data")
    
    def test_memory_optimized_batch(self, page: Page):
        """メモリ最適化されたバッチテスト"""
        test_name = "memory_optimized_batch"
        
        with self.performance_monitor.measure(test_name, page) as metrics:
            # 初期メモリ使用量
            initial_memory = MemoryOptimizer.get_memory_usage()
            self.performance_monitor.mark(metrics, f"initial_memory_{initial_memory:.1f}MB")
            
            # メモリ制限内でバッチ処理
            with MemoryOptimizer.memory_limit(max_mb=100):
                for i in range(10):
                    # スクリーンショットを撮影（メモリ消費）
                    page.screenshot()
                    
                    # 定期的にクリーンアップ
                    if i % 3 == 0:
                        MemoryOptimizer.cleanup()
                        current_memory = MemoryOptimizer.get_memory_usage()
                        self.performance_monitor.mark(
                            metrics, 
                            f"cleanup_{i}_memory_{current_memory:.1f}MB"
                        )
            
            # 最終メモリ使用量
            final_memory = MemoryOptimizer.get_memory_usage()
            self.performance_monitor.mark(metrics, f"final_memory_{final_memory:.1f}MB")
            
            # メモリ増加量を確認
            memory_increase = final_memory - initial_memory
            assert memory_increase < 100, f"メモリ使用量が過度に増加: {memory_increase:.1f}MB"
    
    @measure_performance(PerformanceMonitor())
    def test_decorated_performance(self, page: Page):
        """デコレーターでパフォーマンス測定"""
        # 重い処理のシミュレーション
        for _ in range(5):
            page.evaluate("() => { return Array(1000000).fill(0).map((_, i) => i * 2); }")
            time.sleep(0.1)
        
        # アサーション
        assert page.title() == "TradingAgents WebUI"
    
    def test_parallel_execution_simulation(self):
        """並列実行の最適化シミュレーション"""
        # テストスケジューラーを初期化
        scheduler = SmartTestScheduler()
        
        # テストノードを作成
        test_nodes = [
            TestNode(
                name="test_navigation",
                module="test_navigation",
                estimated_duration=3.0,
                resource_requirements={"cpu": 0.2, "memory": 0.1},
                priority=1
            ),
            TestNode(
                name="test_dashboard",
                module="test_dashboard",
                estimated_duration=5.0,
                resource_requirements={"cpu": 0.3, "memory": 0.2},
                priority=2
            ),
            TestNode(
                name="test_settings",
                module="test_settings",
                estimated_duration=4.0,
                resource_requirements={"cpu": 0.2, "memory": 0.15},
                dependencies={"test_navigation"}
            ),
            TestNode(
                name="test_execution",
                module="test_execution",
                estimated_duration=10.0,
                resource_requirements={"cpu": 0.5, "memory": 0.4},
                dependencies={"test_settings"},
                priority=3
            ),
            TestNode(
                name="test_results",
                module="test_results",
                estimated_duration=6.0,
                resource_requirements={"cpu": 0.3, "memory": 0.3},
                dependencies={"test_execution"}
            )
        ]
        
        # グラフに追加
        for node in test_nodes:
            scheduler.dependency_graph.add_test(node)
        
        # 依存関係を設定
        for node in test_nodes:
            for dep in node.dependencies:
                dep_node = next((n for n in test_nodes if n.name == dep), None)
                if dep_node:
                    scheduler.dependency_graph.add_dependency(dep_node.id, node.id)
        
        # 最適なスケジュールを作成
        schedule = scheduler.create_optimal_schedule(max_workers=3)
        
        # 実行時間を推定
        estimated_time = scheduler.estimate_execution_time(schedule)
        
        print(f"\n📅 最適化されたスケジュール:")
        for i, group in enumerate(schedule):
            print(f"  グループ {i+1}: {group}")
        print(f"  推定実行時間: {estimated_time:.2f}秒")
        
        # 並列実行なしの場合の時間
        sequential_time = sum(node.estimated_duration for node in test_nodes)
        speedup = sequential_time / estimated_time
        
        print(f"  逐次実行時間: {sequential_time:.2f}秒")
        print(f"  高速化率: {speedup:.2f}x")
        
        assert speedup > 1.5, "並列化による十分な高速化が得られていません"
    
    def test_smart_wait_optimization(self, page: Page):
        """スマートな待機処理の最適化"""
        test_name = "smart_wait_optimization"
        
        with self.performance_monitor.measure(test_name, page) as metrics:
            # 従来の固定待機
            start_time = time.time()
            page.wait_for_timeout(2000)  # 2秒の固定待機
            fixed_wait_time = time.time() - start_time
            self.performance_monitor.mark(metrics, f"fixed_wait_{fixed_wait_time:.2f}s")
            
            # スマートな待機（要素ベース）
            start_time = time.time()
            page.wait_for_selector('[data-testid="stMetric"]', state="visible", timeout=30000)
            smart_wait_time = time.time() - start_time
            self.performance_monitor.mark(metrics, f"smart_wait_{smart_wait_time:.2f}s")
            
            # 待機時間の改善を確認
            improvement = fixed_wait_time - smart_wait_time
            print(f"\n⏱️ 待機時間の改善: {improvement:.2f}秒")
            
            assert smart_wait_time < fixed_wait_time, "スマート待機が固定待機より遅い"
    
    def _generate_stock_data(self, ticker: str) -> dict:
        """テスト用の株価データを生成"""
        import random
        
        # キャッシュされていない場合のマーク
        data = {
            "ticker": ticker,
            "price": random.uniform(100, 500),
            "volume": random.randint(1000000, 10000000),
            "change": random.uniform(-5, 5),
            "from_cache": False
        }
        
        # 生成に時間がかかるシミュレーション
        time.sleep(0.5)
        
        return data


# パフォーマンス最適化のベストプラクティス
"""
1. キャッシュの活用
   - ページ状態のキャッシュ
   - APIレスポンスのキャッシュ
   - テストデータのキャッシュ

2. 並列実行の最適化
   - 依存関係の分析
   - リソースベースの負荷分散
   - 優先度に基づくスケジューリング

3. メモリ管理
   - 定期的なガベージコレクション
   - メモリ使用量の監視
   - リソースの早期解放

4. 待機処理の最適化
   - 固定待機の排除
   - 要素ベースの待機
   - 条件ベースの待機

5. パフォーマンス測定
   - 実行時間の測定
   - リソース使用量の監視
   - ボトルネックの特定
"""