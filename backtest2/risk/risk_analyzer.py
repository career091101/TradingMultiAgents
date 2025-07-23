"""Advanced risk analysis with gap and correlation considerations"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from ..config.constants import RISK_ANALYSIS


logger = logging.getLogger(__name__)


@dataclass
class GapRiskMetrics:
    """Metrics for price gap risk"""
    max_gap_percentage: float
    average_gap_percentage: float
    gap_frequency: float  # Percentage of days with gaps
    expected_slippage: float
    
    
@dataclass
class CorrelationRiskMetrics:
    """Metrics for correlation risk"""
    portfolio_correlation: float
    max_pair_correlation: float
    correlation_concentration: float  # How concentrated correlations are
    diversification_ratio: float
    
    
@dataclass
class EnhancedRiskMetrics:
    """Enhanced risk metrics including gap and correlation risks"""
    gap_risk: GapRiskMetrics
    correlation_risk: CorrelationRiskMetrics
    adjusted_var: float  # VaR adjusted for gaps
    adjusted_position_size: float  # Position size adjusted for risks
    risk_score: float  # Overall risk score (0-100)


class RiskAnalyzer:
    """Analyzes advanced risk metrics including gaps and correlations"""
    
    def __init__(
        self,
        lookback_days: Optional[int] = None,
        gap_threshold: Optional[float] = None,
        correlation_window: Optional[int] = None
    ):
        self.lookback_days = lookback_days or RISK_ANALYSIS.lookback_days
        self.gap_threshold = gap_threshold or RISK_ANALYSIS.gap_threshold
        self.correlation_window = correlation_window or RISK_ANALYSIS.correlation_window
        self.logger = logging.getLogger(__name__)
        
        # Cache for historical data
        self.price_history: Dict[str, pd.DataFrame] = {}
        self.correlation_matrix: Optional[pd.DataFrame] = None
        
    def analyze_gap_risk(
        self,
        symbol: str,
        price_data: pd.DataFrame
    ) -> GapRiskMetrics:
        """Analyze price gap risk for a symbol
        
        Args:
            symbol: Stock symbol
            price_data: DataFrame with columns [open, high, low, close]
            
        Returns:
            Gap risk metrics
        """
        if len(price_data) < 2:
            return GapRiskMetrics(0, 0, 0, 0)
            
        # Calculate overnight gaps
        gaps = (price_data['open'].values[1:] - price_data['close'].values[:-1]) / price_data['close'].values[:-1]
        
        # Filter significant gaps
        significant_gaps = gaps[np.abs(gaps) > self.gap_threshold]
        
        # Calculate metrics
        max_gap = np.max(np.abs(gaps)) if len(gaps) > 0 else 0
        avg_gap = np.mean(np.abs(gaps)) if len(gaps) > 0 else 0
        gap_freq = len(significant_gaps) / len(gaps) if len(gaps) > 0 else 0
        
        # Estimate expected slippage based on gap patterns
        expected_slippage = avg_gap * RISK_ANALYSIS.slippage_multiplier
        
        return GapRiskMetrics(
            max_gap_percentage=max_gap,
            average_gap_percentage=avg_gap,
            gap_frequency=gap_freq,
            expected_slippage=expected_slippage
        )
        
    def analyze_correlation_risk(
        self,
        positions: List[str],
        returns_data: Dict[str, pd.Series]
    ) -> CorrelationRiskMetrics:
        """Analyze correlation risk in portfolio
        
        Args:
            positions: List of symbols in portfolio
            returns_data: Dictionary of return series by symbol
            
        Returns:
            Correlation risk metrics
        """
        if len(positions) < 2:
            return CorrelationRiskMetrics(0, 0, 0, 1.0)
            
        # Create returns DataFrame
        returns_df = pd.DataFrame(returns_data)[positions]
        
        # Calculate correlation matrix
        corr_matrix = returns_df.corr()
        self.correlation_matrix = corr_matrix
        
        # Calculate metrics
        # Portfolio correlation (average pairwise correlation)
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        correlations = corr_matrix.where(mask).stack().values
        
        portfolio_corr = np.mean(correlations)
        max_corr = np.max(correlations) if len(correlations) > 0 else 0
        
        # Correlation concentration (using HHI)
        corr_squared = correlations ** 2
        concentration = np.sum(corr_squared) / len(correlations) if len(correlations) > 0 else 0
        
        # Diversification ratio
        # Higher ratio means better diversification
        equal_weights = np.ones(len(positions)) / len(positions)
        portfolio_var = equal_weights @ corr_matrix @ equal_weights
        avg_var = np.mean(np.diag(corr_matrix))
        div_ratio = np.sqrt(avg_var / portfolio_var) if portfolio_var > 0 else 1.0
        
        return CorrelationRiskMetrics(
            portfolio_correlation=portfolio_corr,
            max_pair_correlation=max_corr,
            correlation_concentration=concentration,
            diversification_ratio=div_ratio
        )
        
    def calculate_adjusted_var(
        self,
        returns: pd.Series,
        gap_metrics: GapRiskMetrics,
        confidence_level: Optional[float] = None
    ) -> float:
        """Calculate Value at Risk adjusted for gap risk
        
        Args:
            returns: Historical returns
            gap_metrics: Gap risk metrics
            confidence_level: VaR confidence level
            
        Returns:
            Adjusted VaR
        """
        # Calculate standard VaR
        conf_level = confidence_level or RISK_ANALYSIS.var_confidence_level
        var_percentile = (1 - conf_level) * 100
        standard_var = np.percentile(returns, var_percentile)
        
        # Adjust for gap risk
        # Increase VaR based on gap frequency and magnitude
        gap_adjustment = 1 + (gap_metrics.gap_frequency * gap_metrics.average_gap_percentage)
        adjusted_var = standard_var * gap_adjustment
        
        return adjusted_var
        
    def calculate_adjusted_position_size(
        self,
        base_position_size: float,
        gap_metrics: GapRiskMetrics,
        correlation_metrics: CorrelationRiskMetrics,
        current_positions: int
    ) -> float:
        """Calculate position size adjusted for various risks
        
        Args:
            base_position_size: Base position size from standard calculation
            gap_metrics: Gap risk metrics
            correlation_metrics: Correlation risk metrics
            current_positions: Number of current positions
            
        Returns:
            Adjusted position size
        """
        # Gap risk adjustment
        gap_factor = 1 - (gap_metrics.expected_slippage * RISK_ANALYSIS.gap_risk_multiplier)
        gap_factor = max(RISK_ANALYSIS.min_gap_factor, gap_factor)
        
        # Correlation risk adjustment
        if current_positions > 0:
            # Reduce size if adding correlated position
            corr_factor = 1 - (correlation_metrics.portfolio_correlation * RISK_ANALYSIS.correlation_risk_multiplier)
            corr_factor = max(RISK_ANALYSIS.min_correlation_factor, corr_factor)
        else:
            corr_factor = 1.0
            
        # Diversification benefit
        div_factor = min(RISK_ANALYSIS.max_diversification_bonus, correlation_metrics.diversification_ratio)
        
        # Combined adjustment
        total_adjustment = gap_factor * corr_factor * div_factor
        adjusted_size = base_position_size * total_adjustment
        
        self.logger.info(
            f"Position size adjustment: base={base_position_size:.2f}, "
            f"gap_factor={gap_factor:.2f}, corr_factor={corr_factor:.2f}, "
            f"div_factor={div_factor:.2f}, adjusted={adjusted_size:.2f}"
        )
        
        return adjusted_size
        
    def calculate_risk_score(
        self,
        gap_metrics: GapRiskMetrics,
        correlation_metrics: CorrelationRiskMetrics,
        position_concentration: float
    ) -> float:
        """Calculate overall risk score (0-100, higher is riskier)
        
        Args:
            gap_metrics: Gap risk metrics
            correlation_metrics: Correlation risk metrics
            position_concentration: Position concentration (0-1)
            
        Returns:
            Risk score
        """
        # Gap risk component (0-30)
        gap_score = min(30, (
            gap_metrics.max_gap_percentage * RISK_ANALYSIS.gap_score_weights['max_gap'] +
            gap_metrics.gap_frequency * RISK_ANALYSIS.gap_score_weights['frequency'] +
            gap_metrics.expected_slippage * RISK_ANALYSIS.gap_score_weights['slippage']
        ))
        
        # Correlation risk component (0-30)
        corr_score = min(30, (
            correlation_metrics.portfolio_correlation * RISK_ANALYSIS.correlation_score_weights['portfolio'] +
            correlation_metrics.max_pair_correlation * RISK_ANALYSIS.correlation_score_weights['max_pair'] +
            (1 - correlation_metrics.diversification_ratio) * RISK_ANALYSIS.correlation_score_weights['diversification']
        ))
        
        # Concentration risk component (0-40)
        conc_score = position_concentration * RISK_ANALYSIS.concentration_score_weight
        
        # Total risk score
        total_score = gap_score + corr_score + conc_score
        
        return min(100, total_score)
        
    def get_risk_recommendations(
        self,
        risk_score: float,
        gap_metrics: GapRiskMetrics,
        correlation_metrics: CorrelationRiskMetrics
    ) -> List[str]:
        """Get risk management recommendations
        
        Args:
            risk_score: Overall risk score
            gap_metrics: Gap risk metrics
            correlation_metrics: Correlation risk metrics
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Overall risk level
        if risk_score > RISK_ANALYSIS.high_risk_threshold:
            recommendations.append("HIGH RISK: Consider reducing position sizes")
        elif risk_score > RISK_ANALYSIS.moderate_risk_threshold:
            recommendations.append("MODERATE RISK: Monitor positions closely")
            
        # Gap risk recommendations
        if gap_metrics.max_gap_percentage > RISK_ANALYSIS.large_gap_threshold:
            recommendations.append(
                f"Large gaps detected ({gap_metrics.max_gap_percentage:.1%}). "
                "Use limit orders and avoid market orders"
            )
            
        if gap_metrics.gap_frequency > RISK_ANALYSIS.frequent_gap_threshold:
            recommendations.append(
                f"Frequent gaps ({gap_metrics.gap_frequency:.1%} of days). "
                "Consider wider stop losses"
            )
            
        # Correlation risk recommendations
        if correlation_metrics.portfolio_correlation > RISK_ANALYSIS.high_correlation_threshold:
            recommendations.append(
                "High portfolio correlation. Add uncorrelated assets"
            )
            
        if correlation_metrics.max_pair_correlation > RISK_ANALYSIS.extreme_correlation_threshold:
            recommendations.append(
                "Extremely high correlation between some positions. "
                "Consider closing redundant positions"
            )
            
        if correlation_metrics.diversification_ratio < RISK_ANALYSIS.low_diversification_threshold:
            recommendations.append(
                "Low diversification benefit. Spread risk across more assets"
            )
            
        return recommendations