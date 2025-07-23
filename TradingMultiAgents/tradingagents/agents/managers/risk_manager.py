import time
import json


def create_risk_manager(llm, memory):
    def risk_manager_node(state) -> dict:

        company_name = state["company_of_interest"]

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["news_report"]
        sentiment_report = state["sentiment_report"]
        trader_plan = state["investment_plan"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""リスク管理の裁判官兼ディベートファシリテーターとして、あなたの目標は、3人のリスクアナリスト（リスク、中立、安全/保守）間のディベートを評価し、トレーダーの最適な行動方針を決定することです。あなたの決定は明確な推奨（買い、売り、または保有）をもたらす必要があります。すべての側面が有効に見える場合のフォールバックとしてではなく、具体的な議論によって強く正当化される場合のみ保有を選択してください。明確さと決断力を目指してください。

決定のためのガイドライン：
1. **主要な議論を要約する**: 各アナリストから最も強いポイントを抽出し、コンテキストとの関連性に焦点を当てる。
2. **根拠を提供する**: ディベートからの直接引用と反論で推奨を支持する。
3. **トレーダーの計画を改善する**: トレーダーの元の計画「{trader_plan}」から始め、アナリストの洞察に基づいて調整する。
4. **過去の間違いから学ぶ**: 「{past_memory_str}」からの教訓を使用して、以前の誤った判断に対処し、現在行っている決定を改善し、お金を失う間違った買い/売り/保有の呼び出しをしないようにする。

成果物：
- 明確で実行可能な推奨：買い、売り、または保有。
- ディベートと過去の反省に基づく詳細な根拠。

---

**アナリストディベート履歴:**  
{history}

---

実行可能な洞察と継続的改善に焦点を当ててください。過去の教訓を基に構築し、すべての視点を批判的に評価し、各決定がより良い結果に向けて進歩することを確実にしてください。"""

        response = llm.invoke(prompt)

        new_risk_debate_state = {
            "judge_decision": response.content,
            "history": risk_debate_state["history"],
            "risky_history": risk_debate_state["risky_history"],
            "safe_history": risk_debate_state["safe_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_risky_response": risk_debate_state["current_risky_response"],
            "current_safe_response": risk_debate_state["current_safe_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response.content,
        }

    return risk_manager_node
