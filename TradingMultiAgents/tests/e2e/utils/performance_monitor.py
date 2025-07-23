"""
E2Eテストのパフォーマンス監視と最適化
実行時間の測定、ボトルネックの特定、最適化提案を提供
"""

import time
import psutil
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from contextlib import contextmanager
import statistics
from dataclasses import dataclass, field
from functools import wraps
import threading
import gc


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクスのデータクラス"""
    test_name: str
    start_time: float
    end_time: float = 0
    duration: float = 0
    cpu_usage: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    network_io: Dict[str, int] = field(default_factory=dict)
    disk_io: Dict[str, int] = field(default_factory=dict)
    browser_metrics: Dict[str, Any] = field(default_factory=dict)
    custom_markers: Dict[str, float] = field(default_factory=dict)
    
    def calculate_duration(self):
        """実行時間を計算"""
        self.duration = self.end_time - self.start_time
    
    def get_summary(self) -> Dict[str, Any]:
        """メトリクスのサマリーを取得"""
        return {
            "test_name": self.test_name,
            "duration": self.duration,
            "cpu_usage_avg": statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
            "cpu_usage_max": max(self.cpu_usage) if self.cpu_usage else 0,
            "memory_usage_avg": statistics.mean(self.memory_usage) if self.memory_usage else 0,
            "memory_usage_max": max(self.memory_usage) if self.memory_usage else 0,
            "network_io": self.network_io,
            "disk_io": self.disk_io,
            "browser_metrics": self.browser_metrics,
            "custom_markers": self.custom_markers
        }


class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self, report_dir: str = "reports/e2e/performance"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()
        self.process = psutil.Process(os.getpid())
    
    @contextmanager
    def measure(self, test_name: str, page=None):
        """テストのパフォーマンスを測定"""
        metrics = PerformanceMetrics(
            test_name=test_name,
            start_time=time.time()
        )
        
        # 初期リソース情報を記録
        self._record_initial_resources(metrics)
        
        # 監視スレッドを開始
        self.stop_monitoring.clear()
        self.monitoring_thread = threading.Thread(
            target=self._monitor_resources,
            args=(metrics,)
        )
        self.monitoring_thread.start()
        
        try:
            # ブラウザメトリクスの収集を開始
            if page:
                self._setup_browser_monitoring(page, metrics)
            
            yield metrics
            
        finally:
            # 監視を停止
            self.stop_monitoring.set()
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            
            # 最終メトリクスを記録
            metrics.end_time = time.time()
            metrics.calculate_duration()
            
            # ブラウザメトリクスを収集
            if page:
                self._collect_browser_metrics(page, metrics)
            
            # メトリクスを保存
            self.metrics[test_name] = metrics
            self._save_metrics(metrics)
    
    def mark(self, metrics: PerformanceMetrics, marker_name: str):
        """カスタムマーカーを追加"""
        metrics.custom_markers[marker_name] = time.time() - metrics.start_time
    
    def _monitor_resources(self, metrics: PerformanceMetrics):
        """リソース使用状況を監視"""
        while not self.stop_monitoring.is_set():
            try:
                # CPU使用率
                cpu_percent = self.process.cpu_percent(interval=0.1)
                metrics.cpu_usage.append(cpu_percent)
                
                # メモリ使用量
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                metrics.memory_usage.append(memory_mb)
                
                # ネットワークI/O
                net_io = psutil.net_io_counters()
                metrics.network_io = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv
                }
                
                # ディスクI/O
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    metrics.disk_io = {
                        "read_bytes": disk_io.read_bytes,
                        "write_bytes": disk_io.write_bytes
                    }
                
            except Exception as e:
                print(f"リソース監視エラー: {e}")
            
            time.sleep(0.5)
    
    def _record_initial_resources(self, metrics: PerformanceMetrics):
        """初期リソース状態を記録"""
        try:
            # 初期ネットワークI/O
            net_io = psutil.net_io_counters()
            metrics.network_io["initial_bytes_sent"] = net_io.bytes_sent
            metrics.network_io["initial_bytes_recv"] = net_io.bytes_recv
            
            # 初期ディスクI/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics.disk_io["initial_read_bytes"] = disk_io.read_bytes
                metrics.disk_io["initial_write_bytes"] = disk_io.write_bytes
        except:
            pass
    
    def _setup_browser_monitoring(self, page, metrics: PerformanceMetrics):
        """ブラウザのパフォーマンス監視を設定"""
        try:
            # パフォーマンスエントリの収集を有効化
            page.evaluate("""
                window.__performanceEntries = [];
                const observer = new PerformanceObserver((list) => {
                    window.__performanceEntries.push(...list.getEntries());
                });
                observer.observe({ entryTypes: ['navigation', 'resource', 'measure'] });
            """)
        except:
            pass
    
    def _collect_browser_metrics(self, page, metrics: PerformanceMetrics):
        """ブラウザメトリクスを収集"""
        try:
            # パフォーマンスタイミング
            timing = page.evaluate("""
                () => {
                    const nav = performance.getEntriesByType('navigation')[0];
                    return nav ? {
                        domContentLoaded: nav.domContentLoadedEventEnd - nav.domContentLoadedEventStart,
                        loadComplete: nav.loadEventEnd - nav.loadEventStart,
                        domInteractive: nav.domInteractive - nav.fetchStart,
                        responseTime: nav.responseEnd - nav.requestStart
                    } : {};
                }
            """)
            metrics.browser_metrics["timing"] = timing
            
            # リソース読み込み統計
            resources = page.evaluate("""
                () => {
                    const resources = performance.getEntriesByType('resource');
                    const stats = {
                        total: resources.length,
                        byType: {},
                        slowest: []
                    };
                    
                    resources.forEach(r => {
                        const type = r.initiatorType || 'other';
                        stats.byType[type] = (stats.byType[type] || 0) + 1;
                    });
                    
                    stats.slowest = resources
                        .sort((a, b) => b.duration - a.duration)
                        .slice(0, 5)
                        .map(r => ({
                            name: r.name.split('/').pop(),
                            duration: Math.round(r.duration),
                            type: r.initiatorType
                        }));
                    
                    return stats;
                }
            """)
            metrics.browser_metrics["resources"] = resources
            
            # メモリ使用量（Chrome限定）
            memory = page.evaluate("""
                () => {
                    if (performance.memory) {
                        return {
                            usedJSHeapSize: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                            totalJSHeapSize: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                            jsHeapSizeLimit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
                        };
                    }
                    return null;
                }
            """)
            if memory:
                metrics.browser_metrics["memory"] = memory
            
        except Exception as e:
            print(f"ブラウザメトリクス収集エラー: {e}")
    
    def _save_metrics(self, metrics: PerformanceMetrics):
        """メトリクスをファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{metrics.test_name}_{timestamp}.json"
        filepath = self.report_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics.get_summary(), f, ensure_ascii=False, indent=2)
    
    def generate_performance_report(self) -> Path:
        """パフォーマンスレポートを生成"""
        all_metrics = []
        
        # 保存されたメトリクスを読み込み
        for json_file in self.report_dir.glob("*.json"):
            with open(json_file, 'r') as f:
                all_metrics.append(json.load(f))
        
        # HTMLレポートを生成
        html_content = self._generate_html_report(all_metrics)
        
        report_path = self.report_dir / "performance_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path
    
    def _generate_html_report(self, metrics_list: List[Dict]) -> str:
        """HTMLパフォーマンスレポートを生成"""
        # テスト別に集計
        test_summary = {}
        for metrics in metrics_list:
            test_name = metrics["test_name"]
            if test_name not in test_summary:
                test_summary[test_name] = {
                    "runs": [],
                    "durations": [],
                    "cpu_usage": [],
                    "memory_usage": []
                }
            
            test_summary[test_name]["runs"].append(metrics)
            test_summary[test_name]["durations"].append(metrics["duration"])
            test_summary[test_name]["cpu_usage"].append(metrics["cpu_usage_avg"])
            test_summary[test_name]["memory_usage"].append(metrics["memory_usage_avg"])
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>E2E Test Performance Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-title {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .metric-unit {{
            font-size: 0.8em;
            color: #999;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .test-details {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .performance-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .performance-table th,
        .performance-table td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .performance-table th {{
            background: #f8f9fa;
            font-weight: bold;
        }}
        .slow {{ color: #dc3545; }}
        .medium {{ color: #ffc107; }}
        .fast {{ color: #28a745; }}
        canvas {{
            max-height: 400px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 E2E Test Performance Report</h1>
        <p>生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        <p>総テスト実行数: {len(metrics_list)}</p>
    </div>
    
    <div class="summary-grid">
        <div class="metric-card">
            <div class="metric-title">平均実行時間</div>
            <div class="metric-value">
                {statistics.mean([m['duration'] for m in metrics_list]):.2f}
                <span class="metric-unit">秒</span>
            </div>
        </div>
        <div class="metric-card">
            <div class="metric-title">最大実行時間</div>
            <div class="metric-value">
                {max([m['duration'] for m in metrics_list]):.2f}
                <span class="metric-unit">秒</span>
            </div>
        </div>
        <div class="metric-card">
            <div class="metric-title">平均CPU使用率</div>
            <div class="metric-value">
                {statistics.mean([m['cpu_usage_avg'] for m in metrics_list]):.1f}
                <span class="metric-unit">%</span>
            </div>
        </div>
        <div class="metric-card">
            <div class="metric-title">平均メモリ使用量</div>
            <div class="metric-value">
                {statistics.mean([m['memory_usage_avg'] for m in metrics_list]):.0f}
                <span class="metric-unit">MB</span>
            </div>
        </div>
    </div>
    
    <div class="chart-container">
        <h2>実行時間の推移</h2>
        <canvas id="durationChart"></canvas>
    </div>
    
    <div class="chart-container">
        <h2>リソース使用状況</h2>
        <canvas id="resourceChart"></canvas>
    </div>
    
    <div class="test-details">
        <h2>テスト別パフォーマンス</h2>
        <table class="performance-table">
            <thead>
                <tr>
                    <th>テスト名</th>
                    <th>実行回数</th>
                    <th>平均時間</th>
                    <th>最小/最大</th>
                    <th>CPU使用率</th>
                    <th>メモリ使用量</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for test_name, summary in test_summary.items():
            avg_duration = statistics.mean(summary["durations"])
            min_duration = min(summary["durations"])
            max_duration = max(summary["durations"])
            avg_cpu = statistics.mean(summary["cpu_usage"])
            avg_memory = statistics.mean(summary["memory_usage"])
            
            # パフォーマンス評価
            perf_class = "fast" if avg_duration < 5 else "medium" if avg_duration < 10 else "slow"
            
            html += f"""
                <tr>
                    <td>{test_name}</td>
                    <td>{len(summary["runs"])}</td>
                    <td class="{perf_class}">{avg_duration:.2f}秒</td>
                    <td>{min_duration:.2f} / {max_duration:.2f}</td>
                    <td>{avg_cpu:.1f}%</td>
                    <td>{avg_memory:.0f}MB</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
    
    <script>
        // 実行時間チャート
        const durationCtx = document.getElementById('durationChart').getContext('2d');
        new Chart(durationCtx, {
            type: 'line',
            data: {
                labels: """ + json.dumps([m["test_name"] for m in metrics_list[-20:]]) + """,
                datasets: [{
                    label: '実行時間 (秒)',
                    data: """ + json.dumps([m["duration"] for m in metrics_list[-20:]]) + """,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
        
        // リソース使用チャート
        const resourceCtx = document.getElementById('resourceChart').getContext('2d');
        new Chart(resourceCtx, {
            type: 'bar',
            data: {
                labels: """ + json.dumps(list(test_summary.keys())[:10]) + """,
                datasets: [{
                    label: 'CPU使用率 (%)',
                    data: """ + json.dumps([statistics.mean(s["cpu_usage"]) for s in list(test_summary.values())[:10]]) + """,
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    yAxisID: 'y-cpu'
                }, {
                    label: 'メモリ使用量 (MB)',
                    data: """ + json.dumps([statistics.mean(s["memory_usage"]) for s in list(test_summary.values())[:10]]) + """,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    yAxisID: 'y-memory'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    'y-cpu': {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'CPU (%)'
                        }
                    },
                    'y-memory': {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Memory (MB)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""
        
        return html
    
    def analyze_bottlenecks(self) -> Dict[str, Any]:
        """ボトルネックを分析"""
        bottlenecks = {
            "slow_tests": [],
            "high_cpu_tests": [],
            "high_memory_tests": [],
            "recommendations": []
        }
        
        for test_name, metrics in self.metrics.items():
            summary = metrics.get_summary()
            
            # 遅いテスト（10秒以上）
            if summary["duration"] > 10:
                bottlenecks["slow_tests"].append({
                    "test": test_name,
                    "duration": summary["duration"],
                    "markers": summary["custom_markers"]
                })
            
            # 高CPU使用率（80%以上）
            if summary["cpu_usage_max"] > 80:
                bottlenecks["high_cpu_tests"].append({
                    "test": test_name,
                    "cpu_max": summary["cpu_usage_max"],
                    "cpu_avg": summary["cpu_usage_avg"]
                })
            
            # 高メモリ使用（500MB以上）
            if summary["memory_usage_max"] > 500:
                bottlenecks["high_memory_tests"].append({
                    "test": test_name,
                    "memory_max": summary["memory_usage_max"],
                    "memory_avg": summary["memory_usage_avg"]
                })
        
        # 推奨事項を生成
        if bottlenecks["slow_tests"]:
            bottlenecks["recommendations"].append(
                "遅いテストを並列実行または分割することを検討してください"
            )
        
        if bottlenecks["high_cpu_tests"]:
            bottlenecks["recommendations"].append(
                "CPU負荷の高いテストでは、待機処理や非同期処理を最適化してください"
            )
        
        if bottlenecks["high_memory_tests"]:
            bottlenecks["recommendations"].append(
                "メモリ使用量の多いテストでは、不要なデータのクリーンアップを実施してください"
            )
        
        return bottlenecks


# パフォーマンス測定デコレーター
def measure_performance(monitor: PerformanceMonitor):
    """関数のパフォーマンスを測定するデコレーター"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            test_name = f"{func.__module__}.{func.__name__}"
            with monitor.measure(test_name) as metrics:
                result = func(*args, **kwargs)
                return result
        return wrapper
    return decorator


# メモリ最適化ユーティリティ
class MemoryOptimizer:
    """メモリ使用量を最適化するユーティリティ"""
    
    @staticmethod
    def cleanup():
        """ガベージコレクションを強制実行"""
        gc.collect()
    
    @staticmethod
    def get_memory_usage() -> float:
        """現在のメモリ使用量を取得（MB）"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    @staticmethod
    @contextmanager
    def memory_limit(max_mb: float):
        """メモリ使用量を制限"""
        initial_memory = MemoryOptimizer.get_memory_usage()
        
        yield
        
        current_memory = MemoryOptimizer.get_memory_usage()
        memory_increase = current_memory - initial_memory
        
        if memory_increase > max_mb:
            MemoryOptimizer.cleanup()
            raise MemoryError(
                f"メモリ使用量が制限を超えました: "
                f"{memory_increase:.1f}MB > {max_mb}MB"
            )