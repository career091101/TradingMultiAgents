import functools
import time
import json


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        context = {
            "role": "user",
            "content": f"アナリストチームによる包括的な分析に基づき、{company_name}に特化した投資計画を提示します。この計画は、現在の技術的市場トレンド、マクロ経済指標、ソーシャルメディアセンチメントからの洞察を組み込んでいます。この計画を基礎として、次のトレーディング決定を評価してください。\n\n提案された投資計画: {investment_plan}\n\nこれらの洞察を活用して、情報に基づいた戦略的決定を行ってください。",
        }

        messages = [
            {
                "role": "system",
                "content": f"""あなたは市場データを分析して投資決定を行うトレーディングエージェントです。分析に基づいて、買い、売り、または保有の具体的な推奨を提供してください。明確な決定で終了し、常に推奨を確認するために「FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**」で回答を締めくくってください。過去の決定からの教訓を活用して間違いから学ぶことを忘れないでください。以下は、あなたが過去に取引した類似の状況からの反省と学んだ教訓です: {past_memory_str}""",
            },
            context,
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
