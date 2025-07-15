"""
E2Eテストの並列実行を最適化
テストの依存関係を分析し、最適な実行順序を決定
"""

import networkx as nx
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict


@dataclass
class TestNode:
    """テストノードのデータクラス"""
    name: str
    module: str
    estimated_duration: float = 5.0
    resource_requirements: Dict[str, float] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    priority: int = 0
    
    @property
    def id(self) -> str:
        return f"{self.module}::{self.name}"


class TestDependencyGraph:
    """テストの依存関係グラフ"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.test_nodes: Dict[str, TestNode] = {}
    
    def add_test(self, test: TestNode):
        """テストを追加"""
        self.test_nodes[test.id] = test
        self.graph.add_node(test.id, test=test)
    
    def add_dependency(self, from_test: str, to_test: str):
        """依存関係を追加"""
        self.graph.add_edge(from_test, to_test)
    
    def get_execution_order(self) -> List[List[str]]:
        """並列実行可能なグループに分けた実行順序を取得"""
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("テストの依存関係に循環があります")
        
        # トポロジカルソートでレベルを計算
        levels = defaultdict(list)
        for node in nx.topological_sort(self.graph):
            # ノードのレベル（依存関係の深さ）を計算
            if self.graph.in_degree(node) == 0:
                level = 0
            else:
                level = max(levels[pred] for pred in self.graph.predecessors(node)) + 1
            
            levels[level].append(node)
        
        # レベルごとにグループ化
        execution_groups = []
        for level in sorted(levels.keys()):
            execution_groups.append(levels[level])
        
        return execution_groups
    
    def optimize_for_resources(self, max_workers: int) -> List[List[str]]:
        """リソース使用量を考慮して最適化"""
        execution_groups = self.get_execution_order()
        optimized_groups = []
        
        for group in execution_groups:
            # グループ内のテストをリソース使用量でソート
            tests = [(test_id, self.test_nodes[test_id]) for test_id in group]
            tests.sort(key=lambda x: (
                -x[1].priority,  # 優先度が高い順
                -x[1].estimated_duration  # 実行時間が長い順
            ))
            
            # リソース制約を考慮してサブグループに分割
            subgroups = self._partition_by_resources(tests, max_workers)
            optimized_groups.extend(subgroups)
        
        return optimized_groups
    
    def _partition_by_resources(self, 
                               tests: List[Tuple[str, TestNode]], 
                               max_workers: int) -> List[List[str]]:
        """リソース制約に基づいてテストを分割"""
        subgroups = []
        current_group = []
        current_resources = defaultdict(float)
        
        for test_id, test_node in tests:
            # リソース要件をチェック
            can_add = True
            for resource, requirement in test_node.resource_requirements.items():
                if current_resources[resource] + requirement > 1.0:
                    can_add = False
                    break
            
            if can_add and len(current_group) < max_workers:
                current_group.append(test_id)
                for resource, requirement in test_node.resource_requirements.items():
                    current_resources[resource] += requirement
            else:
                if current_group:
                    subgroups.append(current_group)
                current_group = [test_id]
                current_resources = defaultdict(float)
                for resource, requirement in test_node.resource_requirements.items():
                    current_resources[resource] = requirement
        
        if current_group:
            subgroups.append(current_group)
        
        return subgroups


class ParallelTestExecutor:
    """並列テスト実行エンジン"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.results: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.resource_locks: Dict[str, threading.Semaphore] = {}
    
    def execute_tests(self, 
                     test_groups: List[List[str]], 
                     test_runner: callable) -> Dict[str, Any]:
        """テストグループを並列実行"""
        total_start_time = time.time()
        
        for group_index, test_group in enumerate(test_groups):
            print(f"\n🚀 グループ {group_index + 1}/{len(test_groups)} を実行中...")
            print(f"   テスト数: {len(test_group)}")
            
            group_start_time = time.time()
            
            # グループ内のテストを並列実行
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._run_test, test_id, test_runner): test_id
                    for test_id in test_group
                }
                
                for future in as_completed(futures):
                    test_id = futures[future]
                    try:
                        result = future.result()
                        with self.lock:
                            self.results[test_id] = result
                    except Exception as e:
                        with self.lock:
                            self.results[test_id] = {
                                "status": "error",
                                "error": str(e),
                                "duration": 0
                            }
            
            group_duration = time.time() - group_start_time
            print(f"   ✅ グループ完了: {group_duration:.2f}秒")
        
        total_duration = time.time() - total_start_time
        
        return {
            "results": self.results,
            "total_duration": total_duration,
            "groups_executed": len(test_groups),
            "tests_executed": len(self.results)
        }
    
    def _run_test(self, test_id: str, test_runner: callable) -> Dict[str, Any]:
        """個別のテストを実行"""
        start_time = time.time()
        
        try:
            # テストを実行
            test_runner(test_id)
            
            return {
                "status": "passed",
                "duration": time.time() - start_time
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - start_time
            }


class TestLoadBalancer:
    """テストの負荷分散"""
    
    def __init__(self, historical_data_path: Optional[Path] = None):
        self.historical_data = {}
        if historical_data_path and historical_data_path.exists():
            with open(historical_data_path, 'r') as f:
                self.historical_data = json.load(f)
    
    def balance_tests(self, 
                     tests: List[TestNode], 
                     num_workers: int) -> List[List[TestNode]]:
        """テストをワーカー間で均等に分散"""
        # 実行時間の推定値で降順ソート
        sorted_tests = sorted(tests, key=lambda t: self._estimate_duration(t), reverse=True)
        
        # ワーカーごとの負荷を追跡
        worker_loads = [0.0] * num_workers
        worker_tests = [[] for _ in range(num_workers)]
        
        # 貪欲法で割り当て
        for test in sorted_tests:
            # 最も負荷の少ないワーカーを選択
            min_load_index = worker_loads.index(min(worker_loads))
            
            # テストを割り当て
            worker_tests[min_load_index].append(test)
            worker_loads[min_load_index] += self._estimate_duration(test)
        
        return worker_tests
    
    def _estimate_duration(self, test: TestNode) -> float:
        """テストの実行時間を推定"""
        # 履歴データがあれば使用
        if test.id in self.historical_data:
            historical_durations = self.historical_data[test.id].get("durations", [])
            if historical_durations:
                # 最近の実行時間の平均を使用
                return sum(historical_durations[-5:]) / len(historical_durations[-5:])
        
        # デフォルトの推定値を返す
        return test.estimated_duration
    
    def update_historical_data(self, test_id: str, duration: float):
        """履歴データを更新"""
        if test_id not in self.historical_data:
            self.historical_data[test_id] = {"durations": []}
        
        self.historical_data[test_id]["durations"].append(duration)
        
        # 最新の10件のみ保持
        self.historical_data[test_id]["durations"] = \
            self.historical_data[test_id]["durations"][-10:]
    
    def save_historical_data(self, path: Path):
        """履歴データを保存"""
        with open(path, 'w') as f:
            json.dump(self.historical_data, f, indent=2)


class SmartTestScheduler:
    """スマートなテストスケジューラー"""
    
    def __init__(self):
        self.dependency_graph = TestDependencyGraph()
        self.load_balancer = TestLoadBalancer()
        self.executor = ParallelTestExecutor()
    
    def analyze_test_suite(self, test_files: List[Path]) -> Dict[str, Any]:
        """テストスイートを分析"""
        analysis = {
            "total_tests": 0,
            "modules": set(),
            "dependencies_found": 0,
            "resource_intensive_tests": [],
            "long_running_tests": []
        }
        
        for test_file in test_files:
            # テストファイルを解析（簡易版）
            module_name = test_file.stem
            analysis["modules"].add(module_name)
            
            # テストを追加（実際の実装では AST 解析などを使用）
            test_node = TestNode(
                name=f"test_{module_name}",
                module=module_name,
                estimated_duration=5.0,
                resource_requirements={"cpu": 0.25, "memory": 0.2}
            )
            
            self.dependency_graph.add_test(test_node)
            analysis["total_tests"] += 1
        
        return analysis
    
    def create_optimal_schedule(self, max_workers: int = 4) -> List[List[str]]:
        """最適な実行スケジュールを作成"""
        # 依存関係を考慮した実行順序を取得
        execution_groups = self.dependency_graph.optimize_for_resources(max_workers)
        
        # 各グループ内で負荷分散
        optimized_schedule = []
        for group in execution_groups:
            # グループ内のテストノードを取得
            group_tests = [self.dependency_graph.test_nodes[test_id] for test_id in group]
            
            # 負荷分散
            balanced_groups = self.load_balancer.balance_tests(group_tests, max_workers)
            
            # テストIDのリストに変換
            for worker_tests in balanced_groups:
                if worker_tests:
                    optimized_schedule.append([test.id for test in worker_tests])
        
        return optimized_schedule
    
    def estimate_execution_time(self, schedule: List[List[str]]) -> float:
        """実行時間を推定"""
        total_time = 0
        
        for group in schedule:
            # グループ内の最大実行時間を計算
            group_times = []
            for test_id in group:
                test_node = self.dependency_graph.test_nodes.get(test_id)
                if test_node:
                    group_times.append(
                        self.load_balancer._estimate_duration(test_node)
                    )
            
            if group_times:
                total_time += max(group_times)
        
        return total_time


# 使用例
"""
# スケジューラーの初期化
scheduler = SmartTestScheduler()

# テストスイートの分析
test_files = list(Path("tests/e2e").glob("test_*.py"))
analysis = scheduler.analyze_test_suite(test_files)

# 最適なスケジュールを作成
schedule = scheduler.create_optimal_schedule(max_workers=4)

# 実行時間の推定
estimated_time = scheduler.estimate_execution_time(schedule)
print(f"推定実行時間: {estimated_time:.2f}秒")

# テストを実行
def test_runner(test_id):
    # 実際のテスト実行ロジック
    pytest.main([test_id])

executor = ParallelTestExecutor(max_workers=4)
results = executor.execute_tests(schedule, test_runner)
"""