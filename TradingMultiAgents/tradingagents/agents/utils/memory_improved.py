"""
改善されたメモリモジュール
トークンカウントとチャンキング機能を実装
"""

import chromadb
from chromadb.config import Settings
from openai import OpenAI
import tiktoken
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FinancialSituationMemory:
    """金融状況メモリクラス（改善版）"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        # モデル設定
        if config["backend_url"] == "http://localhost:11434/v1":
            self.embedding_model = "nomic-embed-text"
            self.encoding_name = "cl100k_base"  # デフォルトエンコーディング
        else:
            self.embedding_model = "text-embedding-3-small"
            self.encoding_name = "cl100k_base"  # OpenAIのエンコーディング
        
        # トークン制限設定
        self.max_tokens = 8000  # 8191から安全マージンを確保
        
        # クライアント初期化
        self.client = OpenAI(base_url=config["backend_url"])
        self.chroma_client = chromadb.Client(Settings(allow_reset=True))
        self.situation_collection = self.chroma_client.create_collection(name=name)
        
        # トークナイザー初期化
        try:
            self.encoding = tiktoken.encoding_for_model(self.embedding_model)
        except:
            # モデルが見つからない場合はデフォルトエンコーディングを使用
            self.encoding = tiktoken.get_encoding(self.encoding_name)
            
        logger.info(f"Initialized FinancialSituationMemory with model: {self.embedding_model}")
    
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
    
    def chunk_text(self, text: str, chunk_size: int = 6000, overlap: int = 500) -> List[str]:
        """テキストをチャンクに分割（オーバーラップ付き）"""
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # オーバーラップを考慮して次の開始位置を設定
            start += chunk_size - overlap
            
        return chunks
    
    def get_embedding(self, text: str) -> List[float]:
        """OpenAI埋め込みを取得（改善版）"""
        # トークン数をチェック
        token_count = self.count_tokens(text)
        
        if token_count <= self.max_tokens:
            # トークン数が制限内の場合はそのまま処理
            try:
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                if "maximum context length" in str(e):
                    logger.warning(f"Token limit exceeded despite count ({token_count}). Truncating...")
                    # カウントが間違っていた場合のフォールバック
                    text = self.truncate_text_to_tokens(text, self.max_tokens - 100)
                    response = self.client.embeddings.create(
                        model=self.embedding_model,
                        input=text
                    )
                    return response.data[0].embedding
                else:
                    raise
        else:
            # トークン数が制限を超える場合
            logger.info(f"Text exceeds token limit ({token_count} > {self.max_tokens}). Using truncation.")
            
            # オプション1: 単純な切り詰め（デフォルト）
            truncated_text = self.truncate_text_to_tokens(text, self.max_tokens)
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=truncated_text
            )
            return response.data[0].embedding
    
    def get_embedding_chunked(self, text: str) -> List[float]:
        """チャンク分割して複数の埋め込みを平均化（高度なオプション）"""
        chunks = self.chunk_text(text, chunk_size=6000, overlap=500)
        
        if len(chunks) == 1:
            return self.get_embedding(chunks[0])
        
        logger.info(f"Text split into {len(chunks)} chunks for embedding")
        
        # 各チャンクの埋め込みを取得
        embeddings = []
        for i, chunk in enumerate(chunks):
            try:
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=chunk
                )
                embeddings.append(response.data[0].embedding)
            except Exception as e:
                logger.error(f"Error embedding chunk {i}: {e}")
                continue
        
        if not embeddings:
            raise ValueError("Failed to generate any embeddings")
        
        # 埋め込みベクトルを平均化
        avg_embedding = np.mean(embeddings, axis=0).tolist()
        
        return avg_embedding
    
    def add_situations(self, situations_and_advice: List[Tuple[str, str]]):
        """金融状況と対応するアドバイスを追加"""
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
            
            # 埋め込みを生成
            try:
                embedding = self.get_embedding(situation)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to embed situation {i}: {e}")
                # エラーの場合はスキップ
                continue
        
        if embeddings:
            self.situation_collection.add(
                documents=situations[:len(embeddings)],
                metadatas=[{"recommendation": rec} for rec in advice[:len(embeddings)]],
                embeddings=embeddings,
                ids=ids[:len(embeddings)],
            )
            logger.info(f"Added {len(embeddings)} situations to memory")
        else:
            logger.warning("No situations were added due to embedding errors")
    
    def get_memories(self, current_situation: str, n_matches: int = 1) -> List[Dict[str, Any]]:
        """OpenAI埋め込みを使用して一致する推奨事項を検索"""
        # 現在の状況のトークン数をログ
        token_count = self.count_tokens(current_situation)
        logger.debug(f"Query situation tokens: {token_count}")
        
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
    
    def analyze_text_length(self, text: str) -> Dict[str, Any]:
        """テキストの長さを分析（デバッグ用）"""
        return {
            "character_count": len(text),
            "token_count": self.count_tokens(text),
            "exceeds_limit": self.count_tokens(text) > self.max_tokens,
            "recommended_action": "truncate" if self.count_tokens(text) > self.max_tokens else "process_as_is"
        }


# 既存のコードとの互換性のためのエイリアス
def create_memory_with_backward_compatibility(name: str, config: Dict[str, Any]) -> FinancialSituationMemory:
    """既存のコードとの互換性を保つためのファクトリ関数"""
    return FinancialSituationMemory(name, config)


if __name__ == "__main__":
    # テスト用コード
    import os
    
    config = {
        "backend_url": os.getenv("OPENAI_API_URL", "https://api.openai.com/v1")
    }
    
    # メモリインスタンスを作成
    memory = FinancialSituationMemory("test_memory", config)
    
    # 長いテキストでテスト
    long_text = "This is a test. " * 2000  # 約8000トークン相当
    
    # テキスト分析
    analysis = memory.analyze_text_length(long_text)
    print(f"Text analysis: {analysis}")
    
    # 埋め込み生成テスト
    try:
        embedding = memory.get_embedding(long_text)
        print(f"Embedding generated successfully. Length: {len(embedding)}")
    except Exception as e:
        print(f"Error generating embedding: {e}")