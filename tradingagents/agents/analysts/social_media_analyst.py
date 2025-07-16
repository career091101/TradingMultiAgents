from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_social_media_analyst(llm, toolkit):
    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [toolkit.get_stock_news_openai]
        else:
            tools = [
                toolkit.get_reddit_stock_info,
            ]

        system_message = (
            "あなたは特定の企業の過去1週間のソーシャルメディア投稿、最近の企業ニュース、公共センチメントを分析するソーシャルメディアおよび企業固有のニュース研究者/アナリストです。企業名が与えられ、あなたの目標は、ソーシャルメディアとその企業について人々が何を言っているかを調べ、人々がその企業について毎日感じているセンチメントデータを分析し、最近の企業ニュースを見た後、この企業の現在の状況についてトレーダーと投資家に詳細な長いレポートを作成することです。ソーシャルメディアからセンチメント、ニュースまで、可能な限りすべてのソースを見てください。単にトレンドが混在していると述べるのではなく、トレーダーが意思決定に役立つ詳細で細かい分析と洞察を提供してください。"
            + """ レポートの最後に、レポートの重要なポイントを整理し、読みやすくするためのMarkdownテーブルを必ず追加してください。""",
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
                    "参考として、現在の日付は {current_date} です。分析対象の企業は {ticker} です。",
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
            "sentiment_report": report,
        }

    return social_media_analyst_node
