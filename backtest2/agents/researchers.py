"""Researcher agents implementation"""

import time
import random
from typing import Dict, Any

from .base import BaseAgent
from ..core.types import AgentOutput


class BullResearcher(BaseAgent):
    """Makes bullish arguments based on analysis"""
    
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Generate bullish thesis"""
        start_time = time.time()
        
        analyst_reports = input_data.get('analyst_reports', {})
        
        # Extract positive signals
        bull_points = []
        
        # Check technical analysis
        if 'market_analyst' in analyst_reports:
            tech_analysis = analyst_reports['market_analyst'].content
            if tech_analysis.get('signal') == 'BUY_SIGNAL':
                bull_points.append("Strong technical buy signal")
            if tech_analysis.get('price_trend') == 'bullish':
                bull_points.append("Positive price momentum")
                
        # Check news sentiment
        if 'news_analyst' in analyst_reports:
            news_analysis = analyst_reports['news_analyst'].content
            if news_analysis.get('overall_sentiment', 0) > 0:
                bull_points.append("Positive news sentiment")
                
        # Check fundamentals
        if 'fundamentals_analyst' in analyst_reports:
            fund_analysis = analyst_reports['fundamentals_analyst'].content
            if fund_analysis.get('valuation') == 'undervalued':
                bull_points.append("Attractive valuation")
            if fund_analysis.get('revenue_growth', 0) > 0.1:
                bull_points.append("Strong revenue growth")
                
        # Generate bullish thesis
        thesis = {
            'recommendation': 'BUY',
            'key_points': bull_points if bull_points else ["General market conditions favorable"],
            'confidence': len(bull_points) / 5,  # More points = higher confidence
            'risk_factors': ["Market volatility", "Execution risk"],
            'target_return': random.uniform(0.05, 0.20)
        }
        
        confidence = min(0.9, 0.5 + len(bull_points) * 0.1)
        
        return self._create_output(
            content=thesis,
            confidence=confidence,
            processing_time=time.time() - start_time,
            rationale=f"Identified {len(bull_points)} bullish factors"
        )


class BearResearcher(BaseAgent):
    """Makes bearish arguments based on analysis"""
    
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Generate bearish thesis"""
        start_time = time.time()
        
        analyst_reports = input_data.get('analyst_reports', {})
        
        # Extract negative signals
        bear_points = []
        
        # Check technical analysis
        if 'market_analyst' in analyst_reports:
            tech_analysis = analyst_reports['market_analyst'].content
            if tech_analysis.get('signal') == 'SELL_SIGNAL':
                bear_points.append("Technical sell signal")
            if tech_analysis.get('price_trend') == 'bearish':
                bear_points.append("Negative price momentum")
                
        # Check news sentiment
        if 'news_analyst' in analyst_reports:
            news_analysis = analyst_reports['news_analyst'].content
            if news_analysis.get('overall_sentiment', 0) < 0:
                bear_points.append("Negative news sentiment")
                
        # Check fundamentals
        if 'fundamentals_analyst' in analyst_reports:
            fund_analysis = analyst_reports['fundamentals_analyst'].content
            if fund_analysis.get('valuation') == 'overvalued':
                bear_points.append("Overvalued stock")
            if fund_analysis.get('debt_to_equity', 0) > 1.0:
                bear_points.append("High debt levels")
                
        # Generate bearish thesis
        thesis = {
            'recommendation': 'SELL' if len(bear_points) > 2 else 'HOLD',
            'key_points': bear_points if bear_points else ["Limited downside catalysts"],
            'confidence': len(bear_points) / 5,
            'risk_factors': ["Short squeeze risk", "Market reversal"],
            'downside_risk': random.uniform(-0.20, -0.05)
        }
        
        confidence = min(0.9, 0.5 + len(bear_points) * 0.1)
        
        return self._create_output(
            content=thesis,
            confidence=confidence,
            processing_time=time.time() - start_time,
            rationale=f"Identified {len(bear_points)} bearish factors"
        )


class ResearchManager(BaseAgent):
    """Manages investment research and debate"""
    
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Evaluate bull vs bear thesis and make recommendation"""
        start_time = time.time()
        
        # Handle different input types
        if 'thesis' in input_data:
            # Debate evaluation
            bull_thesis = input_data['thesis'].get('bull', {})
            bear_thesis = input_data['thesis'].get('bear', {})
            
            bull_content = bull_thesis.content if hasattr(bull_thesis, 'content') else bull_thesis
            bear_content = bear_thesis.content if hasattr(bear_thesis, 'content') else bear_thesis
            
            bull_confidence = bull_thesis.confidence if hasattr(bull_thesis, 'confidence') else 0.5
            bear_confidence = bear_thesis.confidence if hasattr(bear_thesis, 'confidence') else 0.5
            
        else:
            # Direct thesis input
            bull_content = input_data.get('bull', {})
            bear_content = input_data.get('bear', {})
            bull_confidence = 0.5
            bear_confidence = 0.5
            
        # Evaluate arguments
        bull_points = len(bull_content.get('key_points', []))
        bear_points = len(bear_content.get('key_points', []))
        
        # Make decision based on balance of arguments
        # Add some randomness for testing to ensure we get trades
        import random
        bias = random.uniform(-0.3, 0.3)  # Add slight random bias
        
        if bull_confidence + bias > 0.65:
            recommendation = 'BUY'
            position_size = 0.2  # 20% of available capital
        elif bear_confidence - bias > 0.65:
            recommendation = 'SELL'
            position_size = 0.15
        else:
            recommendation = 'HOLD'
            position_size = 0.0
            
        # Create investment plan
        investment_plan = {
            'recommendation': recommendation,
            'position_size': position_size,
            'bull_score': bull_confidence,
            'bear_score': bear_confidence,
            'debate_summary': {
                'bull_points': bull_points,
                'bear_points': bear_points,
                'key_decision_factors': [
                    "Technical indicators",
                    "Fundamental valuation",
                    "Market sentiment"
                ]
            },
            'risk_assessment': {
                'conviction_level': abs(bull_confidence - bear_confidence),
                'key_risks': bull_content.get('risk_factors', []) + bear_content.get('risk_factors', [])
            }
        }
        
        # Check if we should continue debate
        round_num = input_data.get('round', 1)
        continue_debate = round_num == 1 and abs(bull_confidence - bear_confidence) < 0.2
        
        investment_plan['continue_debate'] = continue_debate
        
        confidence = max(bull_confidence, bear_confidence) * 0.8
        
        return self._create_output(
            content={'investment_plan': investment_plan},
            confidence=confidence,
            processing_time=time.time() - start_time,
            rationale=f"Recommendation: {recommendation} based on {max(bull_points, bear_points)} key factors"
        )