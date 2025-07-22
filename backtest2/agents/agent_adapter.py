"""Adapter to integrate TradingAgents agents with backtest2"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BaseAgent
from .llm_client import OpenAILLMClient
from .prompts import OfficialPrompts
from ..core.types import AgentOutput, MarketData, TradingSignal, TradeAction
from ..memory.agent_memory import AgentMemory


class TradingAgentAdapter(BaseAgent):
    """Base adapter for integrating TradingAgents agents"""
    
    def __init__(
        self,
        name: str,
        llm_config,
        memory: AgentMemory,
        use_deep_thinking: bool = False,
        system_prompt: str = ""
    ):
        super().__init__(name, llm_config, memory, use_deep_thinking)
        self.system_prompt = system_prompt
        self.llm_client = OpenAILLMClient(llm_config)
        
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Process input using LLM"""
        start_time = datetime.now()
        
        try:
            # Prepare context
            context = self._prepare_context(input_data)
            
            # Generate prompt
            prompt = self._generate_prompt(input_data)
            
            # Get response from LLM
            response = await self.llm_client.generate_structured(
                prompt=prompt,
                context=context,
                output_schema=self._get_output_schema(),
                use_deep_thinking=self.use_deep_thinking,
                system_message=self.system_prompt,
                agent_name=self.name
            )
            
            # Process response
            content = self._process_response(response)
            confidence = self._calculate_confidence(response)
            rationale = response.get('rationale', '')
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return self._create_output(
                content=content,
                confidence=confidence,
                processing_time=processing_time,
                rationale=rationale
            )
            
        except Exception as e:
            self.logger.error(f"Agent {self.name} processing failed: {e}")
            return self._create_error_output(str(e))
            
    def _prepare_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for LLM"""
        # Convert DecisionContext to dict if present
        context = {}
        for key, value in input_data.items():
            if hasattr(value, 'to_dict'):
                context[key] = value.to_dict()
            elif hasattr(value, '__dict__'):
                # Handle dataclasses or objects with __dict__
                context[key] = {k: v for k, v in value.__dict__.items() if not k.startswith('_')}
            else:
                context[key] = value
        return context
        
    def _generate_prompt(self, input_data: Dict[str, Any]) -> str:
        # Normalize context to dict if it's an object
        context = input_data.get('context', {})
        if hasattr(context, 'to_dict'):
            context = context.to_dict()
            input_data['context'] = context
        
        """Generate prompt for LLM"""
        return "Analyze the provided data and generate insights."
        
    def _get_output_schema(self) -> Dict[str, Any]:
        """Get expected output schema"""
        return {
            "analysis": "string",
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "rationale": {"type": "string"}
        }
        
    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process LLM response"""
        return response
        
    def _calculate_confidence(self, response: Dict[str, Any]) -> float:
        """Calculate confidence from response"""
        return response.get('confidence', 0.5)
        
    def _create_error_output(self, error_msg: str) -> AgentOutput:
        """Create error output"""
        return self._create_output(
            content={'error': error_msg},
            confidence=0.0,
            processing_time=0.0,
            rationale=f"Error: {error_msg}"
        )


class MarketAnalystAdapter(TradingAgentAdapter):
    """Market Analyst adapter"""
    

    def _validate_response(self, response: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix LLM response to match schema"""
        # Fix action field if it's in wrong format
        if 'action' in response:
            action = response['action']
            if isinstance(action, str):
                # Handle "string (BUY/SELL/HOLD)" format
                if "BUY" in action and "SELL" in action and "HOLD" in action:
                    response['action'] = 'HOLD'  # Default to HOLD if unclear
                elif action.upper() in ['BUY', 'SELL', 'HOLD']:
                    response['action'] = action.upper()
                else:
                    response['action'] = 'HOLD'
        
        # Fix final_decision field similarly
        if 'final_decision' in response:
            decision = response['final_decision']
            if isinstance(decision, str):
                if "BUY" in decision and "SELL" in decision and "HOLD" in decision:
                    response['final_decision'] = 'HOLD'
                elif decision.upper() in ['BUY', 'SELL', 'HOLD']:
                    response['final_decision'] = decision.upper()
                else:
                    response['final_decision'] = 'HOLD'
        
        return response


    def __init__(self, name: str, llm_config, memory: AgentMemory):
        super().__init__(
            name=name,
            llm_config=llm_config,
            memory=memory,
            use_deep_thinking=False,
            system_prompt=OfficialPrompts.MARKET_ANALYST_SYSTEM
        )
        
    def _generate_prompt(self, input_data: Dict[str, Any]) -> str:
        # Normalize context to dict if it's an object
        context = input_data.get('context', {})
        if hasattr(context, 'to_dict'):
            context = context.to_dict()
            input_data['context'] = context
        
        market_data: MarketData = input_data.get('market_data')
        # Context is already normalized to dict above
        current_date = context.get('timestamp', datetime.now())
        
        return f"""
参考として、現在の日付は {current_date.strftime('%Y-%m-%d')} です。調査対象の企業は {market_data.symbol} です。

価格データ:
- 始値: ${market_data.open:.2f}
- 高値: ${market_data.high:.2f}
- 安値: ${market_data.low:.2f}
- 終値: ${market_data.close:.2f}
- 出来高: {market_data.volume:,}

上記の指標リストから最も関連性の高い指標を選択し、詳細な分析レポートを作成してください。
観察するトレンドの非常に詳細で細かい分析レポートを作成してください。
レポートの最後に、重要なポイントを整理したMarkdownテーブルを追加してください。
"""
        
    def _get_output_schema(self) -> Dict[str, Any]:
        return {
            "selected_indicators": {"type": "array", "items": {"type": "string"}},
            "price_trend": {"type": "string", "enum": ["bullish", "bearish", "neutral"]},
            "volume_analysis": {"type": "string"},
            "technical_analysis": {"type": "string"},
            "recommendation": {"type": "string", "enum": ["BUY", "HOLD", "SELL"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "rationale": {"type": "string"},
            "summary_table": {"type": "string", "description": "Markdown formatted table"}
        }
        
    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'price_trend': response.get('price_trend', 'neutral'),
            'volume_analysis': response.get('volume_analysis', ''),
            'technical_indicators': response.get('technical_signals', {}),
            'signal': response.get('recommendation', 'HOLD')
        }


class NewsAnalystAdapter(TradingAgentAdapter):
    """News Analyst adapter"""
    
    def __init__(self, name: str, llm_config, memory: AgentMemory):
        super().__init__(
            name=name,
            llm_config=llm_config,
            memory=memory,
            use_deep_thinking=False,
            system_prompt=OfficialPrompts.NEWS_ANALYST_SYSTEM
        )
        
    def _generate_prompt(self, input_data: Dict[str, Any]) -> str:
        # Normalize context to dict if it's an object
        context = input_data.get('context', {})
        if hasattr(context, 'to_dict'):
            context = context.to_dict()
            input_data['context'] = context
        
        market_data: MarketData = input_data.get('market_data')
        news_items = market_data.news if market_data.news else []
        
        news_text = "\n".join([
            f"- {item.get('title', '')}: {item.get('summary', '')}"
            for item in news_items[:5]  # Limit to 5 items
        ])
        
        return f"""
{market_data.symbol}に関するニュースを分析してください。

最新ニュース:
{news_text if news_text else "現在ニュースはありません"}

センチメント分析と市場への影響を評価してください。
"""
        
    def _get_output_schema(self) -> Dict[str, Any]:
        return {
            "overall_sentiment": {"type": "number", "minimum": -1, "maximum": 1},
            "key_topics": {"type": "array", "items": {"type": "string"}},
            "market_impact": {"type": "string", "enum": ["positive", "negative", "neutral"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "rationale": {"type": "string"}
        }
        
    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'overall_sentiment': response.get('overall_sentiment', 0.0),
            'key_topics': response.get('key_topics', []),
            'sentiment_trend': response.get('market_impact', 'neutral')
        }


class SocialMediaAnalystAdapter(TradingAgentAdapter):
    """Social Media Analyst adapter"""
    
    def __init__(self, name: str, llm_config, memory: AgentMemory):
        super().__init__(
            name=name,
            llm_config=llm_config,
            memory=memory,
            use_deep_thinking=False,
            system_prompt=OfficialPrompts.SOCIAL_MEDIA_ANALYST_SYSTEM
        )
        
    def _generate_prompt(self, input_data: Dict[str, Any]) -> str:
        # Normalize context to dict if it's an object
        context = input_data.get('context', {})
        if hasattr(context, 'to_dict'):
            context = context.to_dict()
            input_data['context'] = context
        
        market_data: MarketData = input_data.get('market_data')
        
        return f"""
{market_data.symbol}のソーシャルメディア動向を分析してください。

価格変動: {((market_data.close - market_data.open) / market_data.open * 100):.2f}%

ソーシャルメディアでの注目度や感情を評価してください。
"""
        
    def _get_output_schema(self) -> Dict[str, Any]:
        return {
            "sentiment_score": {"type": "number", "minimum": -1, "maximum": 1},
            "trending_level": {"type": "string", "enum": ["high", "medium", "low"]},
            "community_sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "rationale": {"type": "string"}
        }


class FundamentalsAnalystAdapter(TradingAgentAdapter):
    """Fundamentals Analyst adapter"""
    
    def __init__(self, name: str, llm_config, memory: AgentMemory):
        super().__init__(
            name=name,
            llm_config=llm_config,
            memory=memory,
            use_deep_thinking=False,
            system_prompt=OfficialPrompts.FUNDAMENTALS_ANALYST_SYSTEM
        )
        
    def _generate_prompt(self, input_data: Dict[str, Any]) -> str:
        # Normalize context to dict if it's an object
        context = input_data.get('context', {})
        if hasattr(context, 'to_dict'):
            context = context.to_dict()
            input_data['context'] = context
        
        market_data: MarketData = input_data.get('market_data')
        
        return f"""
{market_data.symbol}のファンダメンタル分析を行ってください。

現在価格: ${market_data.close:.2f}

財務指標とバリュエーションを評価してください。
"""
        
    def _get_output_schema(self) -> Dict[str, Any]:
        return {
            "valuation": {"type": "string", "enum": ["undervalued", "fair", "overvalued"]},
            "financial_health": {"type": "string", "enum": ["strong", "moderate", "weak"]},
            "growth_prospects": {"type": "string", "enum": ["high", "medium", "low"]},
            "key_metrics": {
                "pe_ratio": "number",
                "profit_margin": "number",
                "debt_to_equity": "number"
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "rationale": {"type": "string"}
        }


class BullResearcherAdapter(TradingAgentAdapter):
    """Bull Researcher adapter"""
    
    def __init__(self, name: str, llm_config, memory: AgentMemory):
        super().__init__(
            name=name,
            llm_config=llm_config,
            memory=memory,
            use_deep_thinking=True,  # Deep thinking
            system_prompt=""  # Will be set dynamically
        )
        
    def _generate_prompt(self, input_data: Dict[str, Any]) -> str:
        # Normalize context to dict if it's an object
        context = input_data.get('context', {})
        if hasattr(context, 'to_dict'):
            context = context.to_dict()
            input_data['context'] = context
        
        analyst_reports = input_data.get('analyst_reports', {})
        
        # Extract report contents
        market_report = analyst_reports.get('market_analyst', {}).content if 'market_analyst' in analyst_reports else {}
        news_report = analyst_reports.get('news_analyst', {}).content if 'news_analyst' in analyst_reports else {}
        sentiment_report = analyst_reports.get('social_analyst', {}).content if 'social_analyst' in analyst_reports else {}
        fundamentals_report = analyst_reports.get('fundamentals_analyst', {}).content if 'fundamentals_analyst' in analyst_reports else {}
        
        # Get debate history and past memories
        thesis = input_data.get('thesis', {})
        history = input_data.get('history', '')
        current_response = thesis.get('bear', {}).content if hasattr(thesis.get('bear'), 'content') else ''
        
        # Get past memories from context
        past_memory_str = self._get_past_memories_str(context)
        
        # Use official prompt
        return OfficialPrompts.get_bull_researcher_prompt(
            market_research_report=json.dumps(market_report, ensure_ascii=False),
            sentiment_report=json.dumps(sentiment_report, ensure_ascii=False),
            news_report=json.dumps(news_report, ensure_ascii=False),
            fundamentals_report=json.dumps(fundamentals_report, ensure_ascii=False),
            history=history,
            current_response=str(current_response),
            past_memory_str=past_memory_str
        )
        
    def _get_past_memories_str(self, context: Dict[str, Any]) -> str:
        """Get past memories string from context"""
        # In full implementation, this would retrieve actual memories
        # For now, return a placeholder
        return "No past memories found."


class BearResearcherAdapter(TradingAgentAdapter):
    """Bear Researcher adapter"""
    
    def __init__(self, name: str, llm_config, memory: AgentMemory):
        super().__init__(
            name=name,
            llm_config=llm_config,
            memory=memory,
            use_deep_thinking=True,  # Deep thinking
            system_prompt=""  # Will be set dynamically
        )
        
    def _generate_prompt(self, input_data: Dict[str, Any]) -> str:
        # Normalize context to dict if it's an object
        context = input_data.get('context', {})
        if hasattr(context, 'to_dict'):
            context = context.to_dict()
            input_data['context'] = context
        
        analyst_reports = input_data.get('analyst_reports', {})
        
        # Extract report contents
        market_report = analyst_reports.get('market_analyst', {}).content if 'market_analyst' in analyst_reports else {}
        news_report = analyst_reports.get('news_analyst', {}).content if 'news_analyst' in analyst_reports else {}
        sentiment_report = analyst_reports.get('social_analyst', {}).content if 'social_analyst' in analyst_reports else {}
        fundamentals_report = analyst_reports.get('fundamentals_analyst', {}).content if 'fundamentals_analyst' in analyst_reports else {}
        
        # Get debate history and past memories
        thesis = input_data.get('thesis', {})
        history = input_data.get('history', '')
        current_response = thesis.get('bull', {}).content if hasattr(thesis.get('bull'), 'content') else ''
        
        # Get past memories from context
        past_memory_str = self._get_past_memories_str(context)
        
        # Use official prompt
        return OfficialPrompts.get_bear_researcher_prompt(
            market_research_report=json.dumps(market_report, ensure_ascii=False),
            sentiment_report=json.dumps(sentiment_report, ensure_ascii=False),
            news_report=json.dumps(news_report, ensure_ascii=False),
            fundamentals_report=json.dumps(fundamentals_report, ensure_ascii=False),
            history=history,
            current_response=str(current_response),
            past_memory_str=past_memory_str
        )
        
    def _get_past_memories_str(self, context: Dict[str, Any]) -> str:
        """Get past memories string from context"""
        # In full implementation, this would retrieve actual memories
        # For now, return a placeholder
        return "No past memories found."


class ResearchManagerAdapter(TradingAgentAdapter):
    """Research Manager adapter"""
    
    def __init__(self, name: str, llm_config, memory: AgentMemory):
        super().__init__(
            name=name,
            llm_config=llm_config,
            memory=memory,
            use_deep_thinking=True,  # Deep thinking
            system_prompt=""  # Will be set dynamically
        )
        
    def _generate_prompt(self, input_data: Dict[str, Any]) -> str:
        # Normalize context to dict if it's an object
        context = input_data.get('context', {})
        if hasattr(context, 'to_dict'):
            context = context.to_dict()
            input_data['context'] = context
        
        thesis = input_data.get('thesis', {})
        
        bull_content = thesis.get('bull', {}).content if hasattr(thesis.get('bull'), 'content') else {}
        bear_content = thesis.get('bear', {}).content if hasattr(thesis.get('bear'), 'content') else {}
        
        # Format reports
        bull_report = f"Bull Analyst: {json.dumps(bull_content, ensure_ascii=False)}"
        bear_report = f"Bear Analyst: {json.dumps(bear_content, ensure_ascii=False)}"
        
        # Get debate history
        history = input_data.get('history', f"{bull_report}\n\n{bear_report}")
        
        # Get past memories
        past_memory_str = self._get_past_memories_str(context)
        
        # Use official prompt
        return OfficialPrompts.get_research_manager_prompt(
            bull_report=bull_report,
            bear_report=bear_report,
            history=history,
            past_memory_str=past_memory_str
        )
    
    def _get_past_memories_str(self, context: Dict[str, Any]) -> str:
        """Get past memories string from context"""
        return "No past memories found."
        
    def _get_output_schema(self) -> Dict[str, Any]:
        return {
            "investment_decision": {"type": "string", "enum": ["BUY", "HOLD", "SELL"]},
            "confidence_level": {"type": "number"},
            "investment_plan": {
                "action": "string",
                "target_allocation": {"type": "number"},
                "time_horizon": "string"
            },
            "key_factors": ["string"],
            "rationale": {"type": "string"}
        }


class TraderAdapter(TradingAgentAdapter):
    """Trader adapter"""
    
    def __init__(self, name: str, llm_config, memory: AgentMemory):
        super().__init__(
            name=name,
            llm_config=llm_config,
            memory=memory,
            use_deep_thinking=False,
            system_prompt=""  # Will be set dynamically
        )
        
    def _generate_prompt(self, input_data: Dict[str, Any]) -> str:
        # Normalize context to dict if it's an object
        context = input_data.get('context', {})
        if hasattr(context, 'to_dict'):
            context = context.to_dict()
            input_data['context'] = context
        
        investment_plan = input_data.get('investment_plan', {})
        portfolio = input_data.get('portfolio')
        
        # Get company name from context
        company_name = context.get('market_state', {}).get('symbol', 'UNKNOWN')
        
        # Get past memories
        past_memory_str = self._get_past_memories_str(context)
        
        # Use official prompt
        return OfficialPrompts.get_trader_prompt(
            company_name=company_name,
            investment_plan=json.dumps(investment_plan, ensure_ascii=False),
            past_memory_str=past_memory_str
        )
    
    def _get_past_memories_str(self, context: Dict[str, Any]) -> str:
        """Get past memories string from context"""
        return "No past memories found."
        
    def _get_output_schema(self) -> Dict[str, Any]:
        return {
            "action": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
            "position_size": {"type": "number", "minimum": 0, "maximum": 1},
            "stop_loss": {"type": "number"},
            "take_profit": {"type": "number"},
            "entry_strategy": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "rationale": {"type": "string"},
            "final_decision": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]}
        }


class RiskDebatorAdapter(TradingAgentAdapter):
    """Base Risk Debator adapter"""
    
    def _generate_prompt(self, input_data: Dict[str, Any]) -> str:
        # Normalize context to dict if it's an object
        context = input_data.get('context', {})
        if hasattr(context, 'to_dict'):
            context = context.to_dict()
            input_data['context'] = context
        
        trade_signal = input_data.get('trade_signal')
        portfolio = input_data.get('portfolio')
        
        return f"""
以下の取引提案を評価してください。

取引提案:
- アクション: {trade_signal.action.value if hasattr(trade_signal, 'action') else 'N/A'}
- 確信度: {trade_signal.confidence if hasattr(trade_signal, 'confidence') else 0}
- 理由: {trade_signal.rationale if hasattr(trade_signal, 'rationale') else ''}

ポートフォリオ状況:
- 現金比率: {((portfolio.cash if portfolio else 0) / portfolio.total_value * 100 if portfolio and portfolio.total_value > 0 else 100):.1f}%
- 含み損益: ${(portfolio.unrealized_pnl if portfolio else 0):,.2f}

あなたの立場からリスク評価を行ってください。
"""


class AggressiveDebatorAdapter(RiskDebatorAdapter):
    """Aggressive Risk Debator adapter"""
    
    def __init__(self, name: str, llm_config, memory: AgentMemory):
        super().__init__(
            name=name,
            llm_config=llm_config,
            memory=memory,
            use_deep_thinking=False,
            system_prompt=OfficialPrompts.RISKY_DEBATOR_SYSTEM
        )


class ConservativeDebatorAdapter(RiskDebatorAdapter):
    """Conservative Risk Debator adapter"""
    
    def __init__(self, name: str, llm_config, memory: AgentMemory):
        super().__init__(
            name=name,
            llm_config=llm_config,
            memory=memory,
            use_deep_thinking=False,
            system_prompt=OfficialPrompts.SAFE_DEBATOR_SYSTEM
        )


class NeutralDebatorAdapter(RiskDebatorAdapter):
    """Neutral Risk Debator adapter"""
    
    def __init__(self, name: str, llm_config, memory: AgentMemory):
        super().__init__(
            name=name,
            llm_config=llm_config,
            memory=memory,
            use_deep_thinking=False,
            system_prompt=OfficialPrompts.NEUTRAL_DEBATOR_SYSTEM
        )


class RiskManagerAdapter(TradingAgentAdapter):
    """Risk Manager adapter"""
    
    def __init__(self, name: str, llm_config, memory: AgentMemory):
        super().__init__(
            name=name,
            llm_config=llm_config,
            memory=memory,
            use_deep_thinking=True,  # Deep thinking
            system_prompt=""  # Will be set dynamically
        )
        
    def _generate_prompt(self, input_data: Dict[str, Any]) -> str:
        # Normalize context to dict if it's an object
        context = input_data.get('context', {})
        if hasattr(context, 'to_dict'):
            context = context.to_dict()
            input_data['context'] = context
        
        risk_assessment = input_data.get('risk_assessment', {})
        perspectives = risk_assessment.get('perspectives', {})
        
        # Build debate history
        history_parts = []
        for name, perspective in perspectives.items():
            if hasattr(perspective, 'content'):
                content = perspective.content
                # Format based on the agent type
                if 'aggressive' in name:
                    history_parts.append(f"Risky Analyst: {json.dumps(content, ensure_ascii=False)}")
                elif 'conservative' in name:
                    history_parts.append(f"Safe Analyst: {json.dumps(content, ensure_ascii=False)}")
                elif 'neutral' in name:
                    history_parts.append(f"Neutral Analyst: {json.dumps(content, ensure_ascii=False)}")
        
        history = "\n\n".join(history_parts)
        
        # Get trader plan from initial trade
        initial_trade = risk_assessment.get('initial_trade', {})
        trader_plan = initial_trade.rationale if hasattr(initial_trade, 'rationale') else 'No specific plan provided'
        
        # Get past memories
        past_memory_str = self._get_past_memories_str(context)
        
        # Use official prompt
        return OfficialPrompts.get_risk_manager_prompt(
            history=history,
            trader_plan=trader_plan,
            past_memory_str=past_memory_str
        )
    
    def _get_past_memories_str(self, context: Dict[str, Any]) -> str:
        """Get past memories string from context"""
        return "No past memories found."
        
    def _get_output_schema(self) -> Dict[str, Any]:
        return {
            "action": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
            "quantity": {"type": "number"},
            "position_size_pct": {"type": "number", "minimum": 0, "maximum": 1},
            "stop_loss": {"type": "number"},
            "take_profit": {"type": "number"},
            "risk_assessment": {
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "risk_score": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "rationale": {"type": "string"}
        }