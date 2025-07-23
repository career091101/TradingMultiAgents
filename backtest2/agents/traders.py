"""Trader agent implementation"""

import time
import random
from typing import Dict, Any

from .base import BaseAgent
from ..core.types import AgentOutput, PortfolioState


class Trader(BaseAgent):
    """Makes trading decisions based on investment plans"""
    
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Generate trading decision"""
        start_time = time.time()
        
        investment_plan = input_data.get('investment_plan', {})
        portfolio: PortfolioState = input_data.get('portfolio')
        context = input_data.get('context', {})
        
        # Extract recommendation
        recommendation = investment_plan.get('recommendation', 'HOLD')
        suggested_size = investment_plan.get('position_size', 0.0)
        
        # Check portfolio constraints
        symbol = context.get('market_state', {}).get('symbol', 'UNKNOWN')
        existing_position = symbol in portfolio.positions if portfolio else False
        
        # Determine action
        if recommendation == 'BUY':
            if portfolio.cash < 1000:  # Minimum cash requirement
                action = 'HOLD'
                reason = "Insufficient cash"
                position_size = 0
            elif portfolio.position_count >= 10 and not existing_position:
                action = 'HOLD'
                reason = "Maximum positions reached"
                position_size = 0
            else:
                action = 'BUY'
                reason = "Investment thesis positive"
                # Calculate actual position size
                available_cash = portfolio.cash * 0.9  # Keep 10% cash reserve
                position_size = min(suggested_size * available_cash, available_cash * 0.3)
                
        elif recommendation == 'SELL' and existing_position:
            action = 'SELL'
            reason = "Investment thesis negative"
            position_size = portfolio.positions[symbol].quantity if portfolio else 0
            
        else:
            action = 'HOLD'
            reason = "No clear signal or position constraints"
            position_size = 0
            
        # Generate trading decision
        decision = {
            'action': action,
            'position_size': position_size,
            'confidence': investment_plan.get('bull_score', 0.5),
            'reason': reason,
            'risk_assessment': {
                'portfolio_exposure': portfolio.exposure if portfolio else 0,
                'position_count': portfolio.position_count if portfolio else 0,
                'cash_available': portfolio.cash if portfolio else 0
            },
            'execution_params': {
                'order_type': 'MARKET',
                'time_in_force': 'DAY',
                'slippage_tolerance': 0.01
            }
        }
        
        confidence = 0.7 if action != 'HOLD' else 0.5
        
        return self._create_output(
            content=decision,
            confidence=confidence,
            processing_time=time.time() - start_time,
            rationale=f"{action} decision: {reason}"
        )