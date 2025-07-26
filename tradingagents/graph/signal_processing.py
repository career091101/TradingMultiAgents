# TradingAgents/graph/signal_processing.py

from langchain_openai import ChatOpenAI


class SignalProcessor:
    """Processes trading signals to extract actionable decisions."""

    def __init__(self, quick_thinking_llm: ChatOpenAI):
        """Initialize with an LLM for processing."""
        self.quick_thinking_llm = quick_thinking_llm

    def process_signal(self, full_signal: str) -> str:
        """
        Process a full trading signal to extract the core decision.

        Args:
            full_signal: Complete trading signal text

        Returns:
            Extracted decision (BUY, SELL, or HOLD)
        """
        messages = [
            (
                "system",
                "You are an efficient assistant designed to analyze paragraphs or financial reports provided by a group of analysts. Your task is to extract the investment decision: SELL, BUY, or HOLD. Provide only the extracted decision (SELL, BUY, or HOLD) as your output, without adding any additional text or information.",
            ),
            ("human", full_signal),
        ]

        response = self.quick_thinking_llm.invoke(messages).content
        
        # Normalize Japanese trading signals to English
        response = response.strip()
        japanese_to_english = {
            "買い": "BUY",
            "売り": "SELL", 
            "保有": "HOLD",
            "買う": "BUY",
            "売る": "SELL",
            "ホールド": "HOLD",
            "購入": "BUY",
            "売却": "SELL",
            "維持": "HOLD"
        }
        
        # Check if response contains Japanese trading terms
        for jp_term, en_term in japanese_to_english.items():
            if jp_term in response:
                return en_term
                
        # Return the original response if it's already in English
        return response.upper() if response.upper() in ["BUY", "SELL", "HOLD"] else "HOLD"
