"""Agent orchestrator for coordinating multi-agent decision making"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from ..core.config import AgentConfig
from ..core.types import (
    MarketData, TradingDecision, PortfolioState, TradeAction,
    AgentOutput, DecisionContext, TradingSignal
)
from ..memory import MemoryStore, AgentMemory
from .base import BaseAgent
from .agent_adapter import (
    MarketAnalystAdapter,
    NewsAnalystAdapter,
    SocialMediaAnalystAdapter,
    FundamentalsAnalystAdapter,
    BullResearcherAdapter,
    BearResearcherAdapter,
    ResearchManagerAdapter,
    TraderAdapter,
    AggressiveDebatorAdapter,
    ConservativeDebatorAdapter,
    NeutralDebatorAdapter,
    RiskManagerAdapter
)


class DecisionFlow:
    """Manages the decision flow between agents"""
    
    def __init__(self):
        self.phase_results = {}
        self.logger = logging.getLogger(__name__)
        
    def store_phase_result(self, phase: str, result: Any):
        """Store result from a phase"""
        self.phase_results[phase] = result
        
    def get_phase_result(self, phase: str) -> Any:
        """Get result from a phase"""
        return self.phase_results.get(phase)
        
    def clear(self):
        """Clear all phase results"""
        self.phase_results.clear()


class AgentOrchestrator:
    """Orchestrates agent coordination for trading decisions"""
    
    def __init__(self, config: 'BacktestConfig', memory_store: MemoryStore):
        self.config = config
        self.memory_store = memory_store
        self.logger = logging.getLogger(__name__)
        self.decision_flow = DecisionFlow()
        self.agents: Dict[str, BaseAgent] = {}
        
    async def initialize(self):
        """Initialize all agents"""
        
        # Check if we should use real LLM or mock agents
        use_mock = self.config.llm_config.deep_think_model == "mock"
        
        if use_mock:
            # Use mock agents for testing
            from .analysts import MarketAnalyst, NewsAnalyst, SocialMediaAnalyst, FundamentalsAnalyst
            from .researchers import BullResearcher, BearResearcher, ResearchManager
            from .traders import Trader
            from .risk import AggressiveDebator, ConservativeDebator, NeutralDebator, RiskManager
            
            self.agents['market_analyst'] = MarketAnalyst(
                "Market Analyst",
                self.config.llm_config,
                self.memory_store.get_agent_memory("market_analyst")
            )
            
            self.agents['news_analyst'] = NewsAnalyst(
                "News Analyst",
                self.config.llm_config,
                self.memory_store.get_agent_memory("news_analyst")
            )
            
            self.agents['social_analyst'] = SocialMediaAnalyst(
                "Social Media Analyst",
                self.config.llm_config,
                self.memory_store.get_agent_memory("social_analyst")
            )
            
            self.agents['fundamentals_analyst'] = FundamentalsAnalyst(
                "Fundamentals Analyst",
                self.config.llm_config,
                self.memory_store.get_agent_memory("fundamentals_analyst")
            )
            
            self.agents['bull_researcher'] = BullResearcher(
                "Bull Researcher",
                self.config.llm_config,
                self.memory_store.get_agent_memory("bull_researcher"),
                use_deep_thinking=True
            )
            
            self.agents['bear_researcher'] = BearResearcher(
                "Bear Researcher",
                self.config.llm_config,
                self.memory_store.get_agent_memory("bear_researcher"),
                use_deep_thinking=True
            )
            
            self.agents['research_manager'] = ResearchManager(
                "Research Manager",
                self.config.llm_config,
                self.memory_store.get_agent_memory("research_manager"),
                use_deep_thinking=True
            )
            
            self.agents['trader'] = Trader(
                "Trader",
                self.config.llm_config,
                self.memory_store.get_agent_memory("trader")
            )
            
            self.agents['aggressive_debator'] = AggressiveDebator(
                "Aggressive Risk Debator",
                self.config.llm_config,
                self.memory_store.get_agent_memory("aggressive_debator")
            )
            
            self.agents['conservative_debator'] = ConservativeDebator(
                "Conservative Risk Debator",
                self.config.llm_config,
                self.memory_store.get_agent_memory("conservative_debator")
            )
            
            self.agents['neutral_debator'] = NeutralDebator(
                "Neutral Risk Debator",
                self.config.llm_config,
                self.memory_store.get_agent_memory("neutral_debator")
            )
            
            self.agents['risk_manager'] = RiskManager(
                "Risk Manager",
                self.config.llm_config,
                self.memory_store.get_agent_memory("risk_manager"),
                use_deep_thinking=True
            )
        else:
            # Use real LLM agents
            # Initialize analysts (quick thinking)
            self.agents['market_analyst'] = MarketAnalystAdapter(
                "Market Analyst",
                self.config.llm_config,
                self.memory_store.get_agent_memory("market_analyst")
            )
            
            self.agents['news_analyst'] = NewsAnalystAdapter(
                "News Analyst",
                self.config.llm_config,
                self.memory_store.get_agent_memory("news_analyst")
            )
            
            self.agents['social_analyst'] = SocialMediaAnalystAdapter(
                "Social Media Analyst",
                self.config.llm_config,
                self.memory_store.get_agent_memory("social_analyst")
            )
            
            self.agents['fundamentals_analyst'] = FundamentalsAnalystAdapter(
                "Fundamentals Analyst",
                self.config.llm_config,
                self.memory_store.get_agent_memory("fundamentals_analyst")
            )
            
            # Initialize researchers (deep thinking)
            self.agents['bull_researcher'] = BullResearcherAdapter(
                "Bull Researcher",
                self.config.llm_config,
                self.memory_store.get_agent_memory("bull_researcher")
            )
            
            self.agents['bear_researcher'] = BearResearcherAdapter(
                "Bear Researcher",
                self.config.llm_config,
                self.memory_store.get_agent_memory("bear_researcher")
            )
            
            self.agents['research_manager'] = ResearchManagerAdapter(
                "Research Manager",
                self.config.llm_config,
                self.memory_store.get_agent_memory("research_manager")
            )
            
            # Initialize trader
            self.agents['trader'] = TraderAdapter(
                "Trader",
                self.config.llm_config,
                self.memory_store.get_agent_memory("trader")
            )
            
            # Initialize risk debators
            self.agents['aggressive_debator'] = AggressiveDebatorAdapter(
                "Aggressive Risk Debator",
                self.config.llm_config,
                self.memory_store.get_agent_memory("aggressive_debator")
            )
            
            self.agents['conservative_debator'] = ConservativeDebatorAdapter(
                "Conservative Risk Debator",
                self.config.llm_config,
                self.memory_store.get_agent_memory("conservative_debator")
            )
            
            self.agents['neutral_debator'] = NeutralDebatorAdapter(
                "Neutral Risk Debator",
                self.config.llm_config,
                self.memory_store.get_agent_memory("neutral_debator")
            )
            
            self.agents['risk_manager'] = RiskManagerAdapter(
                "Risk Manager",
                self.config.llm_config,
                self.memory_store.get_agent_memory("risk_manager")
            )
        
        self.logger.info(f"Initialized {len(self.agents)} agents")
        
    async def make_decision(
        self,
        date: datetime,
        symbol: str,
        market_data: MarketData,
        portfolio: PortfolioState
    ) -> TradingDecision:
        """Make trading decision through agent coordination"""
        
        decision_id = str(uuid.uuid4())
        self.logger.info(f"Starting decision process {decision_id} for {symbol} on {date}")
        
        # Clear previous decision flow
        self.decision_flow.clear()
        
        # Create decision context
        context = DecisionContext(
            timestamp=date,
            market_state={'symbol': symbol, 'data': market_data},
            portfolio_state=portfolio,
            recent_performance=await self._get_recent_performance(symbol),
            risk_metrics=self._calculate_risk_metrics(portfolio)
        )
        self.logger.debug(f"Created context: {type(context)}, portfolio_state: {type(context.portfolio_state)}")
        
        try:
            # Phase 1: Data Collection
            analyst_reports = await self._data_collection_phase(market_data, context)
            
            # Phase 2: Investment Analysis
            investment_thesis = await self._investment_analysis_phase(analyst_reports, context)
            
            # Phase 3: Investment Decision
            investment_plan = await self._investment_decision_phase(investment_thesis, context)
            
            # Phase 4: Trading Decision
            initial_trade = await self._trading_decision_phase(investment_plan, portfolio, context)
            
            # Phase 5: Risk Assessment
            risk_assessment = await self._risk_assessment_phase(initial_trade, portfolio, context)
            
            # Phase 6: Final Decision
            final_decision = await self._final_decision_phase(risk_assessment, context)
            
            # Set metadata
            final_decision.id = decision_id
            final_decision.symbol = symbol
            final_decision.timestamp = date
            
            # Store decision flow for learning
            await self._store_decision_flow(final_decision, context)
            
            return final_decision
            
        except Exception as e:
            self.logger.error(f"Decision process failed: {str(e)}", exc_info=True)
            # Return HOLD decision on error
            return TradingDecision(
                id=decision_id,
                timestamp=date,
                action=TradeAction.HOLD,
                symbol=symbol,
                quantity=0,
                confidence=0,
                rationale=f"Decision process failed: {str(e)}"
            )
            
    async def _data_collection_phase(
        self, 
        market_data: MarketData,
        context: DecisionContext
    ) -> Dict[str, AgentOutput]:
        """Phase 1: Collect data from all analysts"""
        self.logger.info("Phase 1: Data Collection")
        
        # Run analysts in parallel
        analyst_tasks = []
        for analyst_name in ['market_analyst', 'news_analyst', 'social_analyst', 'fundamentals_analyst']:
            agent = self.agents[analyst_name]
            task = agent.process({
                'market_data': market_data,
                'context': context.to_dict() if hasattr(context, 'to_dict') else context
            })
            analyst_tasks.append((analyst_name, task))
            
        # Collect results
        reports = {}
        for name, task in analyst_tasks:
            try:
                report = await task
                reports[name] = report
                self.logger.debug(f"{name} completed analysis")
            except Exception as e:
                self.logger.error(f"{name} failed: {str(e)}")
                reports[name] = AgentOutput(
                    agent_name=name,
                    timestamp=context.timestamp,
                    output_type='error',
                    content={'error': str(e)},
                    confidence=0,
                    processing_time=0
                )
                
        self.decision_flow.store_phase_result('analyst_reports', reports)
        return reports
        
    async def _investment_analysis_phase(
        self,
        analyst_reports: Dict[str, AgentOutput],
        context: DecisionContext
    ) -> Dict[str, Any]:
        """Phase 2: Investment analysis by researchers"""
        self.logger.info("Phase 2: Investment Analysis")
        
        # Prepare researcher input
        researcher_input = {
            'analyst_reports': analyst_reports,
            'context': context.to_dict() if hasattr(context, 'to_dict') else context
        }
        
        # Run bull and bear researchers in parallel
        bull_task = self.agents['bull_researcher'].process(researcher_input)
        bear_task = self.agents['bear_researcher'].process(researcher_input)
        
        bull_thesis = await bull_task
        bear_thesis = await bear_task
        
        thesis = {
            'bull': bull_thesis,
            'bear': bear_thesis
        }
        
        self.decision_flow.store_phase_result('investment_thesis', thesis)
        return thesis
        
    async def _investment_decision_phase(
        self,
        investment_thesis: Dict[str, Any],
        context: DecisionContext
    ) -> Dict[str, Any]:
        """Phase 3: Investment decision by research manager"""
        self.logger.info("Phase 3: Investment Decision")
        
        # Research manager evaluates bull vs bear thesis
        research_manager = self.agents['research_manager']
        
        # Conduct debate rounds
        current_thesis = investment_thesis
        # Use default value if agent_config is not set
        max_debate_rounds = self.config.agent_config.max_debate_rounds if self.config.agent_config else 1
        for round_num in range(max_debate_rounds):
            self.logger.info(f"Debate round {round_num + 1}")
            
            debate_result = await research_manager.process({
                'thesis': current_thesis,
                'round': round_num + 1,
                'context': context.to_dict() if hasattr(context, 'to_dict') else context
            })
            
            # Update thesis based on debate
            if debate_result.content.get('continue_debate', False):
                # Get refined arguments
                refined_bull = await self.agents['bull_researcher'].process({
                    'counter_arguments': debate_result.content.get('bear_points', []),
                    'original_thesis': current_thesis['bull'],
                    'context': context.to_dict() if hasattr(context, 'to_dict') else context
                })
                
                refined_bear = await self.agents['bear_researcher'].process({
                    'counter_arguments': debate_result.content.get('bull_points', []),
                    'original_thesis': current_thesis['bear'],
                    'context': context.to_dict() if hasattr(context, 'to_dict') else context
                })
                
                current_thesis = {
                    'bull': refined_bull,
                    'bear': refined_bear
                }
            else:
                break
                
        # Final investment plan
        investment_plan = debate_result.content.get('investment_plan', {})
        self.decision_flow.store_phase_result('investment_plan', investment_plan)
        return investment_plan
        
    async def _trading_decision_phase(
        self,
        investment_plan: Dict[str, Any],
        portfolio: PortfolioState,
        context: DecisionContext
    ) -> TradingSignal:
        """Phase 4: Trading decision by trader"""
        self.logger.info("Phase 4: Trading Decision")
        
        trader = self.agents['trader']
        trade_decision = await trader.process({
            'investment_plan': investment_plan,
            'portfolio': portfolio,
            'context': context.to_dict() if hasattr(context, 'to_dict') else context
        })
        
        # Convert to trading signal
        action_str = trade_decision.content.get('action', 'HOLD')
        signal = TradingSignal(
            action=TradeAction.from_string(action_str),
            symbol=context.market_state['symbol'],
            confidence=trade_decision.confidence,
            size_recommendation=trade_decision.content.get('position_size'),
            rationale=trade_decision.rationale,
            risk_assessment=trade_decision.content.get('risk_assessment')
        )
        
        self.decision_flow.store_phase_result('initial_trade', signal)
        return signal
        
    async def _risk_assessment_phase(
        self,
        initial_trade: TradingSignal,
        portfolio: PortfolioState,
        context: DecisionContext
    ) -> Dict[str, Any]:
        """Phase 5: Risk assessment by risk debators"""
        self.logger.info("Phase 5: Risk Assessment")
        
        # Run risk debators in parallel
        risk_input = {
            'trade_signal': initial_trade,
            'portfolio': portfolio,
            'context': context.to_dict() if hasattr(context, 'to_dict') else context
        }
        
        risk_tasks = []
        for debator_name in ['aggressive_debator', 'conservative_debator', 'neutral_debator']:
            agent = self.agents[debator_name]
            task = agent.process(risk_input)
            risk_tasks.append((debator_name, task))
            
        # Collect risk perspectives
        risk_perspectives = {}
        for name, task in risk_tasks:
            perspective = await task
            risk_perspectives[name] = perspective
            
        # Risk discussion rounds
        # Use default value if agent_config is not set
        max_risk_discuss_rounds = self.config.agent_config.max_risk_discuss_rounds if self.config.agent_config else 1
        for round_num in range(max_risk_discuss_rounds):
            self.logger.info(f"Risk discussion round {round_num + 1}")
            
            # Each debator responds to others' perspectives
            for debator_name in risk_perspectives:
                agent = self.agents[debator_name]
                refined_perspective = await agent.process({
                    'all_perspectives': risk_perspectives,
                    'own_perspective': risk_perspectives[debator_name],
                    'round': round_num + 1,
                    'context': context.to_dict() if hasattr(context, 'to_dict') else context
                })
                risk_perspectives[debator_name] = refined_perspective
                
        risk_assessment = {
            'perspectives': risk_perspectives,
            'initial_trade': initial_trade
        }
        
        self.decision_flow.store_phase_result('risk_assessment', risk_assessment)
        return risk_assessment
        
    async def _final_decision_phase(
        self,
        risk_assessment: Dict[str, Any],
        context: DecisionContext
    ) -> TradingDecision:
        """Phase 6: Final decision by risk manager"""
        self.logger.info("Phase 6: Final Decision")
        
        risk_manager = self.agents['risk_manager']
        final_output = await risk_manager.process({
            'risk_assessment': risk_assessment,
            'context': context.to_dict() if hasattr(context, 'to_dict') else context,
            'decision_flow': self.decision_flow.phase_results
        })
        
        # Create final trading decision
        decision = TradingDecision(
            id='',  # Will be set by caller
            timestamp=context.timestamp,
            action=TradeAction.from_string(final_output.content.get('action', 'HOLD')),
            symbol='',  # Will be set by caller
            quantity=final_output.content.get('quantity', 0),
            confidence=final_output.confidence,
            rationale=final_output.rationale,
            agent_outputs=self.decision_flow.phase_results,
            risk_assessment=final_output.content.get('risk_assessment', {}),
            position_size_pct=final_output.content.get('position_size_pct', 0),
            stop_loss=final_output.content.get('stop_loss'),
            take_profit=final_output.content.get('take_profit')
        )
        
        return decision
        
    async def _get_recent_performance(self, symbol: str) -> Dict[str, float]:
        """Get recent performance metrics for the symbol"""
        if not self.memory_store:
            return {}
            
        return await self.memory_store.get_recent_performance(symbol)
        
    def _calculate_risk_metrics(self, portfolio: PortfolioState) -> Dict[str, float]:
        """Calculate current risk metrics"""
        if not portfolio:
            return {
                'exposure': 0.0,
                'position_count': 0,
                'cash_ratio': 1.0,
                'unrealized_pnl_pct': 0.0
            }
        
        # Safe division to avoid zero division errors
        total_value = portfolio.total_value if portfolio.total_value > 0 else 1.0
        
        return {
            'exposure': portfolio.exposure,
            'position_count': portfolio.position_count,
            'cash_ratio': portfolio.cash / total_value,
            'unrealized_pnl_pct': portfolio.unrealized_pnl / total_value
        }
        
    async def _store_decision_flow(self, decision: TradingDecision, context: DecisionContext):
        """Store the decision flow for learning"""
        if self.memory_store:
            # Check if the method exists, use store_decision as fallback
            if hasattr(self.memory_store, 'store_decision_flow'):
                await self.memory_store.store_decision_flow(
                    decision, 
                    context, 
                    self.decision_flow.phase_results
                )
            elif hasattr(self.memory_store, 'store_decision'):
                # Use the available method with context
                try:
                    await self.memory_store.store_decision(decision, context)
                except AttributeError as e:
                    # Log the error but don't fail the entire decision process
                    self.logger.debug(f"Memory store error (non-critical): {e}")
            else:
                self.logger.debug("Memory store does not support decision storage")
    
    async def cleanup(self) -> None:
        """Cleanup all resources"""
        self.logger.info("Cleaning up orchestrator resources")
        
        # Cleanup all agents
        for agent_name, agent in self.agents.items():
            if hasattr(agent, 'cleanup'):
                try:
                    await agent.cleanup()
                    self.logger.debug(f"Cleaned up agent: {agent_name}")
                except Exception as e:
                    self.logger.error(f"Error cleaning up {agent_name}: {e}")
            
            # Cleanup LLM clients if they exist
            if hasattr(agent, 'llm_client') and hasattr(agent.llm_client, 'cleanup'):
                try:
                    await agent.llm_client.cleanup()
                    self.logger.debug(f"Cleaned up LLM client for: {agent_name}")
                except Exception as e:
                    self.logger.error(f"Error cleaning up LLM client for {agent_name}: {e}")
        
        self.logger.info("Orchestrator cleanup completed")