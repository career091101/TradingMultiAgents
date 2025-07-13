import time
import json


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""ポートフォリオマネージャー兼ディベートファシリテーターとして、あなたの役割は、このディベートラウンドを批判的に評価し、明確な決定を下すことです：ベアアナリスト、ブルアナリストのいずれかに賛同するか、提示された議論に基づいて強く正当化される場合のみ保有を選択してください。

両サイドからの主要なポイントを簡潔に要約し、最も説得力のある証拠や推論に焦点を当ててください。あなたの推奨（買い、売り、または保有）は明確で実行可能である必要があります。両サイドに有効なポイントがあるという理由だけで保有にデフォルトすることを避け、ディベートの最も強い議論に基づいた立場にコミットしてください。

さらに、トレーダーのための詳細な投資計画を開発してください。これには以下が含まれるべきです：

あなたの推奨：最も説得力のある議論で支持された決定的な立場。
根拠：これらの議論がなぜあなたの結論につながるかの説明。
戦略的行動：推奨を実施するための具体的なステップ。
類似の状況での過去の間違いを考慮してください。これらの洞察を使用して意思決定を改善し、学習と改善を確実に行ってください。特別なフォーマットなしで、自然に話しているように分析を提示してください。

以下は、間違いについての過去の反省です：
\"{past_memory_str}\"

以下がディベートです：
ディベート履歴：
{history}"""
        response = llm.invoke(prompt)

        new_investment_debate_state = {
            "judge_decision": response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response.content,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }

    return research_manager_node
