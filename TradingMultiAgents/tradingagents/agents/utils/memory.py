import chromadb
from chromadb.config import Settings
from openai import OpenAI
import tiktoken
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FinancialSituationMemory:
    def __init__(self, name, config):
        if config["backend_url"] == "http://localhost:11434/v1":
            self.embedding = "nomic-embed-text"
            self.encoding_name = "cl100k_base"  # デフォルトエンコーディング
        else:
            self.embedding = "text-embedding-3-small"
            self.encoding_name = "cl100k_base"  # OpenAIのエンコーディング
            
        # トークン制限設定
        self.max_tokens = 8000  # 8191から安全マージンを確保
        
        self.client = OpenAI(base_url=config["backend_url"])
        self.chroma_client = chromadb.Client(Settings(allow_reset=True))
        self.situation_collection = self.chroma_client.create_collection(name=name)
        
        # トークナイザー初期化
        try:
            self.encoding = tiktoken.encoding_for_model(self.embedding)
        except:
            # モデルが見つからない場合はデフォルトエンコーディングを使用
            self.encoding = tiktoken.get_encoding(self.encoding_name)
            
        logger.info(f"Initialized FinancialSituationMemory with model: {self.embedding}")

    def count_tokens(self, text: str) -> int:
        """テキストのトークン数をカウント"""
        return len(self.encoding.encode(text))
    
    def truncate_text_to_tokens(self, text: str, max_tokens: int) -> str:
        """テキストを指定トークン数に切り詰め"""
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            return text
        
        # トークンを切り詰めてデコード
        truncated_tokens = tokens[:max_tokens]
        truncated_text = self.encoding.decode(truncated_tokens)
        
        # 切り詰めインジケーターを追加
        return truncated_text + "... [truncated]"
    
    def get_embedding(self, text):
        """Get OpenAI embedding for a text with proper token counting"""
        
        # トークン数をチェック
        token_count = self.count_tokens(text)
        logger.debug(f"Text token count: {token_count}")
        
        if token_count <= self.max_tokens:
            # トークン数が制限内の場合はそのまま処理
            try:
                response = self.client.embeddings.create(
                    model=self.embedding, input=text
                )
                return response.data[0].embedding
            except Exception as e:
                if "maximum context length" in str(e):
                    logger.warning(f"Token limit exceeded despite count ({token_count}). Truncating...")
                    # カウントが間違っていた場合のフォールバック
                    text = self.truncate_text_to_tokens(text, self.max_tokens - 100)
                    response = self.client.embeddings.create(
                        model=self.embedding, input=text
                    )
                    return response.data[0].embedding
                else:
                    raise
        else:
            # トークン数が制限を超える場合
            logger.info(f"Text exceeds token limit ({token_count} > {self.max_tokens}). Truncating...")
            
            # 切り詰め処理
            truncated_text = self.truncate_text_to_tokens(text, self.max_tokens)
            response = self.client.embeddings.create(
                model=self.embedding, input=truncated_text
            )
            return response.data[0].embedding

    def add_situations(self, situations_and_advice):
        """Add financial situations and their corresponding advice. Parameter is a list of tuples (situation, rec)"""

        situations = []
        advice = []
        ids = []
        embeddings = []

        offset = self.situation_collection.count()

        for i, (situation, recommendation) in enumerate(situations_and_advice):
            # トークン数をログ出力
            token_count = self.count_tokens(situation)
            logger.debug(f"Situation {i} tokens: {token_count}")
            
            situations.append(situation)
            advice.append(recommendation)
            ids.append(str(offset + i))
            
            # 埋め込みを生成（エラーハンドリング付き）
            try:
                embedding = self.get_embedding(situation)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to embed situation {i}: {e}")
                # エラーの場合は切り詰めて再試行
                truncated_situation = self.truncate_text_to_tokens(situation, self.max_tokens - 500)
                try:
                    embedding = self.get_embedding(truncated_situation)
                    embeddings.append(embedding)
                    situations[-1] = truncated_situation  # 切り詰めたテキストで置き換え
                except Exception as e2:
                    logger.error(f"Failed to embed even after truncation: {e2}")
                    # この状況をスキップ
                    situations.pop()
                    advice.pop()
                    ids.pop()
                    continue

        if embeddings:
            self.situation_collection.add(
                documents=situations,
                metadatas=[{"recommendation": rec} for rec in advice],
                embeddings=embeddings,
                ids=ids,
            )
            logger.info(f"Added {len(embeddings)} situations to memory")
        else:
            logger.warning("No situations were added due to embedding errors")

    def get_memories(self, current_situation, n_matches=1):
        """Find matching recommendations using OpenAI embeddings"""
        query_embedding = self.get_embedding(current_situation)

        results = self.situation_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_matches,
            include=["metadatas", "documents", "distances"],
        )

        matched_results = []
        for i in range(len(results["documents"][0])):
            matched_results.append(
                {
                    "matched_situation": results["documents"][0][i],
                    "recommendation": results["metadatas"][0][i]["recommendation"],
                    "similarity_score": 1 - results["distances"][0][i],
                }
            )

        return matched_results


if __name__ == "__main__":
    # Example usage
    matcher = FinancialSituationMemory()

    # Example data
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    # Add the example situations and recommendations
    matcher.add_situations(example_data)

    # Example query
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            print(f"\nMatch {i}:")
            print(f"Similarity Score: {rec['similarity_score']:.2f}")
            print(f"Matched Situation: {rec['matched_situation']}")
            print(f"Recommendation: {rec['recommendation']}")

    except Exception as e:
        print(f"Error during recommendation: {str(e)}")
