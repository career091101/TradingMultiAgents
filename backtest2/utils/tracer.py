"""Distributed tracing implementation for observability"""

import asyncio
import time
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from uuid import uuid4
from enum import Enum


logger = logging.getLogger(__name__)


class SpanStatus(Enum):
    """Span status"""
    OK = "ok"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class Span:
    """Represents a single span in a trace"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    status: SpanStatus = SpanStatus.OK
    tags: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Get duration in milliseconds"""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None
        
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span"""
        event = {
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        }
        self.events.append(event)
        
    def set_tag(self, key: str, value: Any) -> None:
        """Set a tag on the span"""
        self.tags[key] = value
        
    def set_status(self, status: SpanStatus, message: Optional[str] = None) -> None:
        """Set span status"""
        self.status = status
        if message:
            self.set_tag("status.message", message)
            
    def finish(self) -> None:
        """Finish the span"""
        if not self.end_time:
            self.end_time = time.time()
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "tags": self.tags,
            "events": self.events
        }


class Tracer:
    """Distributed tracing implementation"""
    
    def __init__(self, service_name: str = "backtest"):
        self.service_name = service_name
        self.active_spans: Dict[str, Span] = {}
        self.completed_spans: List[Span] = []
        self.current_trace_id: Optional[str] = None
        self.logger = logging.getLogger(__name__)
        
        # Context for async operations
        self._context_var = {}
        
    def start_trace(self, operation_name: str, tags: Optional[Dict[str, Any]] = None) -> Span:
        """Start a new trace"""
        trace_id = str(uuid4())
        span_id = str(uuid4())
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=None,
            operation_name=operation_name,
            start_time=time.time(),
            tags=tags or {}
        )
        
        span.set_tag("service.name", self.service_name)
        self.active_spans[span_id] = span
        self.current_trace_id = trace_id
        self._context_var["current_span"] = span
        
        return span
        
    def start_span(
        self,
        operation_name: str,
        parent_span: Optional[Span] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Start a new span"""
        if not parent_span:
            parent_span = self._context_var.get("current_span")
            
        if not parent_span:
            # No parent, start a new trace
            return self.start_trace(operation_name, tags)
            
        span_id = str(uuid4())
        
        span = Span(
            span_id=span_id,
            trace_id=parent_span.trace_id,
            parent_span_id=parent_span.span_id,
            operation_name=operation_name,
            start_time=time.time(),
            tags=tags or {}
        )
        
        span.set_tag("service.name", self.service_name)
        self.active_spans[span_id] = span
        
        return span
        
    def finish_span(self, span: Span) -> None:
        """Finish a span"""
        span.finish()
        
        if span.span_id in self.active_spans:
            del self.active_spans[span.span_id]
            self.completed_spans.append(span)
            
            # Log span completion
            self.logger.debug(
                f"Span completed: {span.operation_name} "
                f"({span.duration_ms:.2f}ms) "
                f"status={span.status.value}"
            )
            
    @asynccontextmanager
    async def trace(self, operation_name: str, tags: Optional[Dict[str, Any]] = None):
        """Async context manager for tracing"""
        span = self.start_span(operation_name, tags=tags)
        old_span = self._context_var.get("current_span")
        self._context_var["current_span"] = span
        
        try:
            yield span
            span.set_status(SpanStatus.OK)
        except asyncio.CancelledError:
            span.set_status(SpanStatus.CANCELLED, "Operation cancelled")
            raise
        except Exception as e:
            span.set_status(SpanStatus.ERROR, str(e))
            span.set_tag("error.type", type(e).__name__)
            span.set_tag("error.message", str(e))
            raise
        finally:
            self.finish_span(span)
            self._context_var["current_span"] = old_span
            
    def trace_sync(self, operation_name: str, tags: Optional[Dict[str, Any]] = None):
        """Synchronous decorator for tracing"""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                span = self.start_span(operation_name, tags=tags)
                old_span = self._context_var.get("current_span")
                self._context_var["current_span"] = span
                
                try:
                    result = func(*args, **kwargs)
                    span.set_status(SpanStatus.OK)
                    return result
                except Exception as e:
                    span.set_status(SpanStatus.ERROR, str(e))
                    span.set_tag("error.type", type(e).__name__)
                    span.set_tag("error.message", str(e))
                    raise
                finally:
                    self.finish_span(span)
                    self._context_var["current_span"] = old_span
                    
            return wrapper
        return decorator
        
    def get_current_span(self) -> Optional[Span]:
        """Get the current active span"""
        return self._context_var.get("current_span")
        
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add event to current span"""
        span = self.get_current_span()
        if span:
            span.add_event(name, attributes)
            
    def set_tag(self, key: str, value: Any) -> None:
        """Set tag on current span"""
        span = self.get_current_span()
        if span:
            span.set_tag(key, value)
            
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary of a trace"""
        spans = [s for s in self.completed_spans if s.trace_id == trace_id]
        
        if not spans:
            return {}
            
        # Find root span
        root_span = next((s for s in spans if s.parent_span_id is None), spans[0])
        
        # Calculate total duration
        start_time = min(s.start_time for s in spans)
        end_time = max(s.end_time or s.start_time for s in spans)
        total_duration = (end_time - start_time) * 1000
        
        # Count by status
        status_counts = {}
        for span in spans:
            status_counts[span.status.value] = status_counts.get(span.status.value, 0) + 1
            
        return {
            "trace_id": trace_id,
            "root_operation": root_span.operation_name,
            "total_spans": len(spans),
            "total_duration_ms": total_duration,
            "status_counts": status_counts,
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat()
        }
        
    def export_traces(self) -> List[Dict[str, Any]]:
        """Export all completed traces"""
        traces = {}
        
        # Group spans by trace ID
        for span in self.completed_spans:
            if span.trace_id not in traces:
                traces[span.trace_id] = []
            traces[span.trace_id].append(span.to_dict())
            
        # Build trace structures
        result = []
        for trace_id, spans in traces.items():
            trace_data = {
                "trace_id": trace_id,
                "spans": spans,
                "summary": self.get_trace_summary(trace_id)
            }
            result.append(trace_data)
            
        return result
        
    def export_jaeger(self) -> Dict[str, Any]:
        """Export traces in Jaeger format"""
        traces = []
        
        # Group spans by trace ID
        trace_spans = {}
        for span in self.completed_spans:
            if span.trace_id not in trace_spans:
                trace_spans[span.trace_id] = []
            trace_spans[span.trace_id].append(span)
            
        # Convert to Jaeger format
        for trace_id, spans in trace_spans.items():
            jaeger_spans = []
            
            for span in spans:
                jaeger_span = {
                    "traceID": trace_id,
                    "spanID": span.span_id,
                    "operationName": span.operation_name,
                    "references": [],
                    "startTime": int(span.start_time * 1_000_000),  # microseconds
                    "duration": int((span.duration_ms or 0) * 1000),  # microseconds
                    "tags": [
                        {"key": k, "type": "string", "value": str(v)}
                        for k, v in span.tags.items()
                    ],
                    "logs": [
                        {
                            "timestamp": int(e["timestamp"] * 1_000_000),
                            "fields": [
                                {"key": k, "value": str(v)}
                                for k, v in e["attributes"].items()
                            ]
                        }
                        for e in span.events
                    ],
                    "process": {
                        "serviceName": self.service_name,
                        "tags": []
                    }
                }
                
                if span.parent_span_id:
                    jaeger_span["references"].append({
                        "refType": "CHILD_OF",
                        "traceID": trace_id,
                        "spanID": span.parent_span_id
                    })
                    
                jaeger_spans.append(jaeger_span)
                
            traces.append({
                "traceID": trace_id,
                "spans": jaeger_spans
            })
            
        return {"data": traces}
        
    def clear_completed_spans(self) -> None:
        """Clear completed spans to free memory"""
        self.completed_spans.clear()


# Global tracer instance
global_tracer = Tracer()


def get_tracer() -> Tracer:
    """Get the global tracer instance"""
    return global_tracer