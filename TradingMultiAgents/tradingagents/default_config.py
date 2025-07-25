import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": os.getenv("TRADINGAGENTS_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data")),
    "data_cache_dir": os.getenv(
        "TRADINGAGENTS_CACHE_DIR",
        os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
            "dataflows/data_cache",
        )
    ),
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "o4-mini-2025-04-16",
    "quick_think_llm": "gpt-4o-mini",
    "backend_url": "https://api.openai.com/v1",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Tool settings
    "online_tools": True,
}
