"""Metrics collection and observability utilities"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import json


logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """Single metric value"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    
    
@dataclass
class MetricSummary:
    """Summary statistics for a metric"""
    name: str
    count: int
    sum: float
    min: float
    max: float
    avg: float
    p50: float  # median
    p95: float
    p99: float
    
    
class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, metrics_collector: 'MetricsCollector', name: str, tags: Optional[Dict[str, str]] = None):
        self.metrics_collector = metrics_collector
        self.name = name
        self.tags = tags or {}
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics_collector.record_timer(self.name, duration, self.tags)
            

class MetricsCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self, window_size: timedelta = timedelta(minutes=5)):
        self.window_size = window_size
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.logger = logging.getLogger(__name__)
        
        # Aggregated metrics
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        
        # Cleanup task
        self._cleanup_task = None
        
    async def start(self) -> None:
        """Start the metrics cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
    async def stop(self) -> None:
        """Stop the metrics cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            
    async def _cleanup_loop(self) -> None:
        """Periodically clean up old metrics"""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                self._cleanup_old_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in metrics cleanup: {e}")
                
    def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than window size"""
        cutoff_time = datetime.now() - self.window_size
        
        for name, values in self.metrics.items():
            # Remove old values
            while values and values[0].timestamp < cutoff_time:
                values.popleft()
                
    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric"""
        key = self._get_key(name, tags)
        self.counters[key] += value
        
        metric = MetricValue(
            name=name,
            value=self.counters[key],
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        self.metrics[key].append(metric)
        
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric"""
        key = self._get_key(name, tags)
        self.gauges[key] = value
        
        metric = MetricValue(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        self.metrics[key].append(metric)
        
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram value"""
        key = self._get_key(name, tags)
        
        metric = MetricValue(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        self.metrics[key].append(metric)
        
    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timer value (in seconds)"""
        key = self._get_key(name, tags)
        
        metric = MetricValue(
            name=name,
            value=duration * 1000,  # Convert to milliseconds
            metric_type=MetricType.TIMER,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        self.metrics[key].append(metric)
        
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None) -> Timer:
        """Create a timer context manager"""
        return Timer(self, name, tags)
        
    def _get_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Generate a unique key for metric with tags"""
        if not tags:
            return name
            
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name},{tag_str}"
        
    def get_summary(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[MetricSummary]:
        """Get summary statistics for a metric"""
        key = self._get_key(name, tags)
        values = [m.value for m in self.metrics.get(key, [])]
        
        if not values:
            return None
            
        values.sort()
        count = len(values)
        
        return MetricSummary(
            name=name,
            count=count,
            sum=sum(values),
            min=min(values),
            max=max(values),
            avg=sum(values) / count,
            p50=self._percentile(values, 0.50),
            p95=self._percentile(values, 0.95),
            p99=self._percentile(values, 0.99)
        )
        
    def _percentile(self, sorted_values: List[float], p: float) -> float:
        """Calculate percentile from sorted values"""
        if not sorted_values:
            return 0.0
            
        k = (len(sorted_values) - 1) * p
        f = int(k)
        c = k - f
        
        if f + 1 < len(sorted_values):
            return sorted_values[f] * (1 - c) + sorted_values[f + 1] * c
        else:
            return sorted_values[f]
            
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        result = {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "summaries": {}
        }
        
        # Add summaries for histogram and timer metrics
        for key, metrics in self.metrics.items():
            if metrics and metrics[-1].metric_type in [MetricType.HISTOGRAM, MetricType.TIMER]:
                summary = self.get_summary(metrics[-1].name, metrics[-1].tags)
                if summary:
                    result["summaries"][key] = {
                        "count": summary.count,
                        "sum": summary.sum,
                        "min": summary.min,
                        "max": summary.max,
                        "avg": summary.avg,
                        "p50": summary.p50,
                        "p95": summary.p95,
                        "p99": summary.p99
                    }
                    
        return result
        
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Export counters
        for key, value in self.counters.items():
            name, tags = self._parse_key(key)
            line = f"{name}_total"
            if tags:
                tag_str = ",".join(f'{k}="{v}"' for k, v in tags.items())
                line += f"{{{tag_str}}}"
            line += f" {value}"
            lines.append(line)
            
        # Export gauges
        for key, value in self.gauges.items():
            name, tags = self._parse_key(key)
            line = name
            if tags:
                tag_str = ",".join(f'{k}="{v}"' for k, v in tags.items())
                line += f"{{{tag_str}}}"
            line += f" {value}"
            lines.append(line)
            
        # Export histograms/timers as summaries
        for key, metrics in self.metrics.items():
            if metrics and metrics[-1].metric_type in [MetricType.HISTOGRAM, MetricType.TIMER]:
                summary = self.get_summary(metrics[-1].name, metrics[-1].tags)
                if summary:
                    name, tags = self._parse_key(key)
                    base_line = name
                    if tags:
                        tag_str = ",".join(f'{k}="{v}"' for k, v in tags.items())
                        base_line += f"{{{tag_str}}}"
                        
                    lines.extend([
                        f"{base_line}_count {summary.count}",
                        f"{base_line}_sum {summary.sum}",
                        f'{base_line}_bucket{{le="0.5"}} {summary.p50}',
                        f'{base_line}_bucket{{le="0.95"}} {summary.p95}',
                        f'{base_line}_bucket{{le="0.99"}} {summary.p99}',
                        f'{base_line}_bucket{{le="+Inf"}} {summary.count}'
                    ])
                    
        return "\n".join(lines)
        
    def _parse_key(self, key: str) -> tuple[str, Dict[str, str]]:
        """Parse metric key to extract name and tags"""
        parts = key.split(",")
        name = parts[0]
        tags = {}
        
        for part in parts[1:]:
            if "=" in part:
                k, v = part.split("=", 1)
                tags[k] = v
                
        return name, tags


class BacktestMetrics(MetricsCollector):
    """Specialized metrics collector for backtesting"""
    
    def __init__(self):
        super().__init__()
        
    def record_trade_execution(self, symbol: str, action: str, quantity: float, price: float) -> None:
        """Record trade execution metrics"""
        self.increment("trades.executed", tags={"symbol": symbol, "action": action})
        self.record_histogram("trade.quantity", quantity, tags={"symbol": symbol})
        self.record_histogram("trade.price", price, tags={"symbol": symbol})
        
    def record_llm_call(self, agent: str, duration: float, success: bool, cache_hit: bool = False) -> None:
        """Record LLM call metrics"""
        tags = {
            "agent": agent,
            "success": str(success).lower(),
            "cache_hit": str(cache_hit).lower()
        }
        self.increment("llm.calls", tags=tags)
        self.record_timer("llm.duration", duration, tags=tags)
        
    def record_position_update(self, symbol: str, quantity: float, pnl: float) -> None:
        """Record position update metrics"""
        self.gauge(f"position.quantity.{symbol}", quantity)
        self.gauge(f"position.pnl.{symbol}", pnl)
        
    def record_portfolio_state(self, cash: float, total_value: float, position_count: int) -> None:
        """Record portfolio state metrics"""
        self.gauge("portfolio.cash", cash)
        self.gauge("portfolio.total_value", total_value)
        self.gauge("portfolio.position_count", position_count)
        
    def record_risk_metrics(self, symbol: str, gap_risk: float, correlation_risk: float) -> None:
        """Record risk metrics"""
        self.gauge(f"risk.gap.{symbol}", gap_risk)
        self.gauge(f"risk.correlation.{symbol}", correlation_risk)
        
    def record_cache_stats(self, cache_type: str, hits: int, misses: int) -> None:
        """Record cache statistics"""
        self.gauge(f"cache.hit_rate.{cache_type}", hits / (hits + misses) if (hits + misses) > 0 else 0)
        self.increment(f"cache.hits.{cache_type}", hits)
        self.increment(f"cache.misses.{cache_type}", misses)