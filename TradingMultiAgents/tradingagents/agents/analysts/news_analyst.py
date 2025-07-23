from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_news_analyst(llm, toolkit):
    def news_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [toolkit.get_global_news_openai, toolkit.get_google_news]
        else:
            tools = [
                toolkit.get_finnhub_news,
                toolkit.get_reddit_news,
                toolkit.get_google_news,
            ]

        system_message = (
            "あなたは過去1週間の最近のニュースとトレンドを分析するニュース研究者です。トレーディングとマクロ経済学に関連する世界の現在の状況の包括的なレポートを作成してください。包括的にするためにEODHDとfinnhubからのニュースを見てください。単にトレンドが混在していると述べるのではなく、トレーダーが意思決定に役立つ詳細で細かい分析と洞察を提供してください。"
            + """ レポートの最後に、レポートの重要なポイントを整理し、読みやすくするためのMarkdownテーブルを必ず追加してください。"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "あなたは他のアシスタントと協力して作業を行う有用なAIアシスタントです。"
                    "提供されたツールを使用して、質問への回答に向けて進展を図ってください。"
                    "完全に回答できなくても問題ありません。異なるツールを持つ別のアシスタントが"
                    "あなたが残した部分から支援します。進展できる部分を実行してください。"
                    "あなたまたは他のアシスタントが最終取引提案: **買い/保有/売り** または成果物を持っている場合、"
                    "チームが停止すべきことを知らせるため、応答の前に最終取引提案: **買い/保有/売り** を付けてください。"
                    "次のツールにアクセスできます: {tool_names}。\n{system_message}"
                    "参考として、現在の日付は {current_date} です。調査対象の企業は {ticker} です。",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "news_report": report,
        }

    return news_analyst_node
