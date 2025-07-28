"""
Error monitoring and analysis module for tracking parsing and system errors
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import json
from pathlib import Path
import logging

from ..core.types import TradingDecision
from ..core.exceptions import TradingError


class ErrorMonitor:
    """Monitor and analyze errors in the trading system"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path("logs/error_monitoring")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Error tracking
        self.error_counts = defaultdict(lambda: defaultdict(int))
        self.error_details = defaultdict(list)
        self.parsing_fallbacks = defaultdict(int)
        self.decision_impacts = {
            'total_decisions': 0,
            'successful_parses': 0,
            'fallback_parses': 0,
            'failed_parses': 0,
            'decisions_affected': 0
        }
        
        # Performance tracking
        self.agent_performance = defaultdict(lambda: {
            'total_calls': 0,
            'parse_errors': 0,
            'error_rate': 0.0
        })
        
        self.logger = logging.getLogger(__name__)
    
    def track_llm_parsing(self, agent_name: str, success: bool, 
                         used_fallback: bool = False, error_detail: Optional[str] = None):
        """Track LLM response parsing attempts"""
        self.agent_performance[agent_name]['total_calls'] += 1
        
        if not success:
            self.agent_performance[agent_name]['parse_errors'] += 1
            self.error_counts['llm_parsing'][agent_name] += 1
            
            if error_detail:
                self.error_details['llm_parsing'].append({
                    'timestamp': datetime.now().isoformat(),
                    'agent': agent_name,
                    'error': error_detail,
                    'fallback_used': used_fallback
                })
        
        if used_fallback:
            self.parsing_fallbacks[agent_name] += 1
            self.decision_impacts['fallback_parses'] += 1
        
        # Update error rate
        agent_stats = self.agent_performance[agent_name]
        agent_stats['error_rate'] = agent_stats['parse_errors'] / agent_stats['total_calls']
    
    def track_trading_error(self, error: TradingError, agent_name: Optional[str] = None):
        """Track trading system errors"""
        error_type = error.__class__.__name__
        self.error_counts['trading_errors'][error_type] += 1
        
        self.error_details['trading_errors'].append({
            'timestamp': datetime.now().isoformat(),
            'agent': agent_name,
            'error_type': error_type,
            'severity': error.severity.value,
            'message': error.message,
            'details': error.details
        })
    
    def track_decision_impact(self, original_decision: Optional[TradingDecision], 
                            final_decision: TradingDecision, was_modified: bool):
        """Track how errors impact trading decisions"""
        self.decision_impacts['total_decisions'] += 1
        
        if was_modified:
            self.decision_impacts['decisions_affected'] += 1
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive error monitoring report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_llm_parsing_errors': sum(self.error_counts['llm_parsing'].values()),
                'total_trading_errors': sum(self.error_counts['trading_errors'].values()),
                'total_fallback_uses': sum(self.parsing_fallbacks.values()),
                'decision_impact_rate': (
                    self.decision_impacts['decisions_affected'] / 
                    max(self.decision_impacts['total_decisions'], 1)
                )
            },
            'agent_analysis': self._analyze_agent_performance(),
            'error_patterns': self._analyze_error_patterns(),
            'recommendations': self._generate_recommendations(),
            'detailed_metrics': {
                'error_counts': dict(self.error_counts),
                'parsing_fallbacks': dict(self.parsing_fallbacks),
                'decision_impacts': self.decision_impacts,
                'agent_performance': dict(self.agent_performance)
            }
        }
        
        # Save report
        report_file = self.log_dir / f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _analyze_agent_performance(self) -> List[Dict[str, Any]]:
        """Analyze performance by agent"""
        analysis = []
        
        for agent, stats in self.agent_performance.items():
            if stats['total_calls'] > 0:
                analysis.append({
                    'agent': agent,
                    'error_rate': stats['error_rate'],
                    'fallback_rate': self.parsing_fallbacks.get(agent, 0) / stats['total_calls'],
                    'total_calls': stats['total_calls'],
                    'health_status': self._get_health_status(stats['error_rate'])
                })
        
        # Sort by error rate descending
        return sorted(analysis, key=lambda x: x['error_rate'], reverse=True)
    
    def _analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in errors"""
        patterns = {
            'most_common_llm_errors': [],
            'error_time_distribution': {},
            'error_correlations': []
        }
        
        # Find most common LLM parsing errors
        if 'llm_parsing' in self.error_details:
            error_messages = [e['error'] for e in self.error_details['llm_parsing']]
            # Group similar errors
            error_groups = defaultdict(int)
            for msg in error_messages:
                if 'JSON' in msg:
                    error_groups['JSON_parsing'] += 1
                elif 'KeyError' in msg:
                    error_groups['missing_fields'] += 1
                elif 'TypeError' in msg:
                    error_groups['type_errors'] += 1
                else:
                    error_groups['other'] += 1
            
            patterns['most_common_llm_errors'] = [
                {'type': k, 'count': v} 
                for k, v in sorted(error_groups.items(), key=lambda x: x[1], reverse=True)
            ]
        
        return patterns
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on error analysis"""
        recommendations = []
        
        # Check agent-specific issues
        for agent, stats in self.agent_performance.items():
            if stats['error_rate'] > 0.3:
                recommendations.append(
                    f"High error rate ({stats['error_rate']:.1%}) for {agent}. "
                    f"Consider reviewing and improving prompts."
                )
            
            fallback_rate = self.parsing_fallbacks.get(agent, 0) / max(stats['total_calls'], 1)
            if fallback_rate > 0.5:
                recommendations.append(
                    f"High fallback rate ({fallback_rate:.1%}) for {agent}. "
                    f"LLM may need clearer JSON format instructions."
                )
        
        # Check overall system health
        total_decisions = self.decision_impacts['total_decisions']
        if total_decisions > 0:
            impact_rate = self.decision_impacts['decisions_affected'] / total_decisions
            if impact_rate > 0.2:
                recommendations.append(
                    f"High decision impact rate ({impact_rate:.1%}). "
                    f"Errors are significantly affecting trading decisions."
                )
        
        return recommendations
    
    def _get_health_status(self, error_rate: float) -> str:
        """Determine health status based on error rate"""
        if error_rate < 0.05:
            return "healthy"
        elif error_rate < 0.15:
            return "warning"
        else:
            return "critical"
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics for monitoring dashboard"""
        return {
            'current_error_rates': {
                agent: stats['error_rate'] 
                for agent, stats in self.agent_performance.items()
            },
            'recent_errors': self.error_details['llm_parsing'][-10:] if 'llm_parsing' in self.error_details else [],
            'system_health': self._calculate_system_health()
        }
    
    def _calculate_system_health(self) -> str:
        """Calculate overall system health"""
        if not self.agent_performance:
            return "unknown"
        
        avg_error_rate = sum(
            stats['error_rate'] for stats in self.agent_performance.values()
        ) / len(self.agent_performance)
        
        return self._get_health_status(avg_error_rate)