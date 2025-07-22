"""LLM client for actual agent integration"""

import os
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..core.config import LLMConfig
from ..utils.retry_handler import LLMRetryHandler
from ..utils.cache_manager import LLMCacheManager


class BacktestJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for backtest objects"""
    
    def default(self, obj):
        # Handle datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle Decimal
        if isinstance(obj, Decimal):
            return float(obj)
            
        # Handle objects with to_dict method
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
            
        # Handle dataclasses
        if hasattr(obj, '__dataclass_fields__'):
            return {field: getattr(obj, field) for field in obj.__dataclass_fields__}
            
        # Let the base class handle it
        return super().default(obj)


class OpenAILLMClient:
    """OpenAI LLM client for agent integration"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize retry handler
        self.retry_handler = LLMRetryHandler()
        
        # Initialize cache manager
        self.cache_manager = LLMCacheManager()
        self._cache_started = False
        
        # Initialize OpenAI clients for deep and fast thinking
        self.deep_llm = ChatOpenAI(
            model=config.deep_think_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout
        )
        
        self.fast_llm = ChatOpenAI(
            model=config.quick_think_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout
        )
        
    async def generate(
        self,
        prompt: str,
        context: Dict[str, Any],
        use_deep_thinking: bool = False,
        system_message: Optional[str] = None,
        agent_name: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """Generate response from LLM with retry logic and caching"""
        
        # Ensure cache is started
        if use_cache and not self._cache_started:
            await self.cache_manager.start()
            self._cache_started = True
        
        # Try to get from cache if enabled
        if use_cache and agent_name:
            cached_result = await self.cache_manager.get_llm_result(
                agent_name,
                prompt,
                context,
                use_deep_thinking
            )
            if cached_result is not None:
                self.logger.debug(f"Cache hit for {agent_name}")
                return cached_result
        
        async def _generate():
            llm = self.deep_llm if use_deep_thinking else self.fast_llm
            
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
                
            # Add context as part of the prompt
            context_str = json.dumps(context, ensure_ascii=False, indent=2, cls=BacktestJSONEncoder)
            full_prompt = f"{prompt}\n\nContext:\n{context_str}"
            messages.append(HumanMessage(content=full_prompt))
            
            response = await llm.ainvoke(messages)
            return response.content
        
        try:
            # Execute with retry handler
            result = await self.retry_handler.execute_with_retry(_generate)
            
            # Cache the result if enabled
            if use_cache and agent_name:
                await self.cache_manager.cache_llm_result(
                    agent_name,
                    prompt,
                    context,
                    result,
                    use_deep_thinking
                )
                
            return result
        except Exception as e:
            self.logger.error(f"LLM generation failed after retries: {e}")
            # Log circuit breaker state
            cb_state = self.retry_handler.get_circuit_state()
            self.logger.error(f"Circuit breaker state: {cb_state}")
            raise
            
    async def generate_structured(
        self,
        prompt: str,
        context: Dict[str, Any],
        output_schema: Dict[str, Any],
        use_deep_thinking: bool = False,
        system_message: Optional[str] = None,
        agent_name: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Generate structured response from LLM with retry logic"""
        
        # Add output schema to prompt
        schema_str = json.dumps(output_schema, ensure_ascii=False, indent=2)
        structured_prompt = f"{prompt}\n\nPlease respond in the following JSON format:\n{schema_str}"
        
        try:
            response = await self.generate(
                structured_prompt,
                context,
                use_deep_thinking,
                system_message,
                agent_name,
                use_cache
            )
            
            # Parse JSON response
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                self.logger.error(f"No JSON found in response: {response}")
                # Return default structure based on schema
                return self._create_default_response(output_schema)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.error(f"Response was: {response}")
            # Return default structure based on schema
            return self._create_default_response(output_schema)
        except Exception as e:
            self.logger.error(f"Failed to generate structured response: {e}")
            # Return default structure based on schema
            return self._create_default_response(output_schema)
            
    def _create_default_response(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create a default response based on the expected schema"""
        default = {}
        
        # Simple schema interpretation - can be enhanced
        for key, value in schema.items():
            if isinstance(value, dict):
                if value.get("type") == "string":
                    default[key] = ""
                elif value.get("type") == "number":
                    default[key] = 0.0
                elif value.get("type") == "boolean":
                    default[key] = False
                elif value.get("type") == "array":
                    default[key] = []
                elif value.get("type") == "object":
                    default[key] = {}
            else:
                # If value is not a dict, use it as default
                default[key] = value
                
        return default
        
    def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry handler statistics"""
        return self.retry_handler.get_circuit_state()
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache_manager.get_stats()
        
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self._cache_started:
            await self.cache_manager.stop()
            self._cache_started = False


class AgentPrompts:
    """Japanese prompts from the main TradingAgents implementation"""
    
    MARKET_ANALYST_SYSTEM = """あなたは金融市場を分析するトレーディングアシスタントです。あなたの役割は、与えられた市場状況やトレーディング戦略に対して、以下のリストから**最も関連性の高い指標**を選択することです。目標は、重複を避けて補完的な洞察を提供する**最大8つの指標**を選択することです。

技術指標の分析：
- 価格トレンド（上昇/下降/横ばい）
- 移動平均線の状態（SMA、EMA）
- MACD、RSI、ボリンジャーバンドなどの指標
- 出来高分析
- サポート/レジスタンスレベル

分析結果をJSON形式で返してください。"""

    NEWS_ANALYST_SYSTEM = """あなたはニュースと市場センチメントを分析するアナリストです。

分析内容：
- ニュースの重要度評価
- センチメント分析（ポジティブ/ネガティブ/ニュートラル）
- 市場への影響予測
- 関連トピックの抽出

分析結果をJSON形式で返してください。"""

    SOCIAL_MEDIA_ANALYST_SYSTEM = """あなたはソーシャルメディアの動向を分析するアナリストです。

分析内容：
- Reddit、Twitter等のセンチメント
- トレンドスコア
- コミュニティの関心度
- 異常な活動の検出

分析結果をJSON形式で返してください。"""

    FUNDAMENTALS_ANALYST_SYSTEM = """あなたは企業のファンダメンタルズを分析するアナリストです。

分析内容：
- 財務指標（PER、PBR、ROE等）
- 収益成長性
- 負債比率
- バリュエーション評価

分析結果をJSON形式で返してください。"""

    BULL_RESEARCHER_SYSTEM = """あなたは強気派の投資リサーチャーです。深い分析に基づいて、投資機会を見出します。

あなたの役割：
- 成長要因の特定
- 上昇シナリオの構築
- 目標株価の設定
- 投資機会の説明

他のアナリストのレポートを参考に、説得力のある強気論を展開してください。"""

    BEAR_RESEARCHER_SYSTEM = """あなたは慎重派の投資リサーチャーです。リスク要因を詳細に分析します。

あなたの役割：
- リスク要因の特定
- 下落シナリオの構築
- 下値目処の設定
- 警戒すべき点の説明

他のアナリストのレポートを参考に、リスクを重視した分析を行ってください。"""

    RESEARCH_MANAGER_SYSTEM = """あなたは投資調査部門のマネージャーです。Bull研究者とBear研究者の意見を調整し、最終的な投資判断を下します。

あなたの役割：
- 両者の議論を公平に評価
- 投資判断（買い/保有/売り）の決定
- 確信度の設定
- 投資戦略の策定

バランスの取れた判断を行ってください。"""

    TRADER_SYSTEM = """あなたは経験豊富なトレーダーです。投資判断に基づいて具体的な取引計画を立案します。

あなたの役割：
- エントリー戦略の決定
- ポジションサイズの提案
- ストップロス/利益確定レベルの設定
- 取引タイミングの判断

リスク管理を重視した実践的な取引計画を立ててください。"""

    AGGRESSIVE_DEBATOR_SYSTEM = """あなたは積極的なリスクテイクを推奨するリスクアドバイザーです。

あなたの役割：
- 高リターンの機会を強調
- 積極的なポジションサイズを提案
- リスクを取る理由を説明

ただし、無謀ではなく、計算されたリスクテイクを推奨してください。"""

    CONSERVATIVE_DEBATOR_SYSTEM = """あなたは慎重なリスク管理を推奨するリスクアドバイザーです。

あなたの役割：
- 潜在的なリスクを強調
- 保守的なポジションサイズを提案
- 資本保全の重要性を説明

過度に悲観的にならず、バランスの取れた助言を行ってください。"""

    NEUTRAL_DEBATOR_SYSTEM = """あなたは中立的な立場のリスクアドバイザーです。

あなたの役割：
- リスクとリターンのバランスを評価
- 中庸なポジションサイズを提案
- 両面からの視点を提供

客観的で実践的な助言を行ってください。"""

    RISK_MANAGER_SYSTEM = """あなたはリスク管理の最高責任者です。すべての意見を総合し、最終的なリスク調整を行います。

あなたの役割：
- 最終的な取引承認/却下
- リスクパラメータの設定
- ポジションサイズの最終決定
- リスク管理ルールの適用

組織全体のリスクを考慮した決定を行ってください。"""