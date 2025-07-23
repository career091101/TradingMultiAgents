"""
MemoryStore クラスのユニットテスト
エージェントのメモリ管理機能をテスト
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import json
import tempfile
from backtest2.memory import MemoryStore
from backtest2.core.types import TradingDecision, TradeAction


class TestMemoryStore:
    """MemoryStoreの基本機能テスト"""
    
    @pytest.mark.asyncio
    async def test_add_memory(self):
        """メモリ追加の基本動作"""
        store = MemoryStore()
        
        memory = {
            "type": "test",
            "data": "test_data",
            "value": 42
        }
        
        await store.add("test_agent", memory)
        
        # メモリが追加されたことを確認
        recent = await store.get_recent("test_agent", limit=1)
        assert len(recent) == 1
        assert recent[0]["type"] == "test"
        assert recent[0]["data"] == "test_data"
        assert "stored_at" in recent[0]
    
    @pytest.mark.asyncio
    async def test_get_recent_memories(self):
        """最近のメモリ取得"""
        store = MemoryStore()
        
        # 複数のメモリを追加
        for i in range(10):
            await store.add("agent1", {"index": i, "type": "test"})
        
        # 最近の5個を取得
        recent = await store.get_recent("agent1", limit=5)
        assert len(recent) == 5
        # 最新のものから取得される
        assert recent[0]["index"] == 5
        assert recent[-1]["index"] == 9
    
    @pytest.mark.asyncio
    async def test_get_recent_with_type_filter(self):
        """タイプフィルタ付きメモリ取得"""
        store = MemoryStore()
        
        # 異なるタイプのメモリを追加
        await store.add("agent1", {"type": "decision", "value": 1})
        await store.add("agent1", {"type": "analysis", "value": 2})
        await store.add("agent1", {"type": "decision", "value": 3})
        await store.add("agent1", {"type": "analysis", "value": 4})
        
        # decisionタイプのみ取得
        decisions = await store.get_recent("agent1", limit=10, memory_type="decision")
        assert len(decisions) == 2
        assert all(m["type"] == "decision" for m in decisions)
    
    def test_get_agent_memory(self):
        """エージェントメモリインスタンス取得"""
        store = MemoryStore()
        
        agent_memory = store.get_agent_memory("test_agent")
        
        assert agent_memory is not None
        assert agent_memory.agent_name == "test_agent"
        assert agent_memory.memory_store == store
    
    @pytest.mark.asyncio
    async def test_get_recent_performance(self):
        """パフォーマンスメトリクス取得"""
        store = MemoryStore()
        
        # パフォーマンスデータを追加
        await store.add("engine", {
            "type": "position_closed",
            "outcome": {
                "position": {"symbol": "AAPL"},
                "pnl": 500.0,
                "return_pct": 0.05
            }
        })
        
        await store.add("engine", {
            "type": "position_closed",
            "outcome": {
                "position": {"symbol": "AAPL"},
                "pnl": -200.0,
                "return_pct": -0.02
            }
        })
        
        # パフォーマンス取得
        perf = await store.get_recent_performance("AAPL")
        
        assert perf["trade_count"] == 2
        assert perf["win_rate"] == 0.5  # 1勝1敗
        assert perf["recent_pnl"] == 300.0  # 500 - 200
        assert perf["avg_return"] == pytest.approx(0.015, rel=1e-9)  # (0.05 - 0.02) / 2
    
    @pytest.mark.asyncio
    async def test_get_recent_performance_no_data(self):
        """データがない場合のパフォーマンス取得"""
        store = MemoryStore()
        
        perf = await store.get_recent_performance("AAPL")
        
        assert perf["trade_count"] == 0
        assert perf["win_rate"] == 0.0
        assert perf["recent_pnl"] == 0.0
        assert perf["avg_return"] == 0.0
    
    @pytest.mark.asyncio
    async def test_store_decision(self):
        """取引決定の保存"""
        store = MemoryStore()
        
        # モックDecisionとContext
        class MockDecision:
            symbol = "AAPL"
            action = TradeAction.BUY
            confidence = 0.8
            rationale = "Strong bullish signals"
        
        class MockContext:
            timestamp = datetime.now()
            portfolio_state = type('obj', (object,), {'total_value': 100000})()
            risk_metrics = {'exposure': 0.5}
            recent_performance = {'win_rate': 0.6}
        
        decision = MockDecision()
        context = MockContext()
        
        await store.store_decision(decision, context)
        
        # 保存されたことを確認
        memories = await store.get_recent("decision_store", limit=1)
        assert len(memories) == 1
        assert memories[0]["type"] == "trading_decision"
        assert memories[0]["symbol"] == "AAPL"
        assert memories[0]["action"] == "BUY"
        assert memories[0]["confidence"] == 0.8
    
    @pytest.mark.asyncio
    async def test_memory_limit_enforcement(self):
        """メモリ数制限の適用"""
        store = MemoryStore(max_memories_per_agent=5)
        
        # 制限を超えてメモリを追加
        for i in range(10):
            await store.add("limited_agent", {"index": i})
        
        # 最新の5個のみ保持
        memories = await store.get_recent("limited_agent", limit=100)
        assert len(memories) == 5
        assert memories[0]["index"] == 5  # 最も古いのはindex=5
        assert memories[-1]["index"] == 9  # 最新はindex=9
    
    @pytest.mark.asyncio
    async def test_search_memories(self):
        """メモリ検索機能"""
        store = MemoryStore()
        
        # 様々なメモリを追加
        await store.add("agent1", {"type": "analysis", "symbol": "AAPL", "score": 0.8})
        await store.add("agent1", {"type": "analysis", "symbol": "GOOGL", "score": 0.7})
        await store.add("agent1", {"type": "decision", "symbol": "AAPL", "score": 0.9})
        
        # 条件に合うメモリを検索
        results = await store.search("agent1", {"type": "analysis", "symbol": "AAPL"})
        assert len(results) == 1
        assert results[0]["score"] == 0.8
    
    @pytest.mark.asyncio
    async def test_clear_agent_memories(self):
        """特定エージェントのメモリクリア"""
        store = MemoryStore()
        
        await store.add("agent1", {"data": "test1"})
        await store.add("agent2", {"data": "test2"})
        
        # agent1のメモリのみクリア
        await store.clear("agent1")
        
        agent1_memories = await store.get_recent("agent1")
        agent2_memories = await store.get_recent("agent2")
        
        assert len(agent1_memories) == 0
        assert len(agent2_memories) == 1
    
    @pytest.mark.asyncio
    async def test_clear_all_memories(self):
        """全メモリクリア"""
        store = MemoryStore()
        
        await store.add("agent1", {"data": "test1"})
        await store.add("agent2", {"data": "test2"})
        
        # 全メモリクリア
        await store.clear()
        
        agent1_memories = await store.get_recent("agent1")
        agent2_memories = await store.get_recent("agent2")
        
        assert len(agent1_memories) == 0
        assert len(agent2_memories) == 0


class TestMemoryStorePersistence:
    """MemoryStoreの永続化機能テスト"""
    
    @pytest.mark.asyncio
    async def test_save_and_load(self):
        """メモリの保存と読み込み"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence_path = Path(tmpdir) / "memories.json"
            
            # メモリを追加して保存
            store1 = MemoryStore(persistence_path=persistence_path)
            await store1.add("agent1", {"type": "test", "value": 42})
            await store1.add("agent2", {"type": "test", "value": 100})
            store1.save()
            
            # 新しいインスタンスで読み込み
            store2 = MemoryStore(persistence_path=persistence_path)
            
            agent1_memories = await store2.get_recent("agent1")
            agent2_memories = await store2.get_recent("agent2")
            
            assert len(agent1_memories) == 1
            assert agent1_memories[0]["value"] == 42
            assert len(agent2_memories) == 1
            assert agent2_memories[0]["value"] == 100
    
    @pytest.mark.asyncio
    async def test_auto_save_on_add(self):
        """追加時の自動保存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence_path = Path(tmpdir) / "memories.json"
            
            store = MemoryStore(persistence_path=persistence_path)
            await store.add("agent1", {"type": "test"})
            
            # ファイルが作成されていることを確認
            assert persistence_path.exists()
            
            # ファイル内容を確認
            with open(persistence_path, 'r') as f:
                data = json.load(f)
                assert "agent1" in data
                assert len(data["agent1"]) == 1


class TestMemoryStoreEdgeCases:
    """MemoryStoreのエッジケーステスト"""
    
    @pytest.mark.asyncio
    async def test_get_recent_from_nonexistent_agent(self):
        """存在しないエージェントからの取得"""
        store = MemoryStore()
        
        memories = await store.get_recent("nonexistent_agent")
        assert memories == []
    
    @pytest.mark.asyncio
    async def test_search_with_no_matches(self):
        """マッチしない検索"""
        store = MemoryStore()
        
        await store.add("agent1", {"type": "test", "value": 1})
        
        results = await store.search("agent1", {"type": "nonexistent"})
        assert results == []
    
    @pytest.mark.asyncio
    async def test_concurrent_additions(self):
        """並行追加のテスト"""
        store = MemoryStore()
        
        async def add_memories(agent_name, count):
            for i in range(count):
                await store.add(agent_name, {"index": i})
        
        # 複数エージェントから並行して追加
        await asyncio.gather(
            add_memories("agent1", 100),
            add_memories("agent2", 100),
            add_memories("agent3", 100)
        )
        
        # 各エージェントのメモリ数を確認
        for agent in ["agent1", "agent2", "agent3"]:
            memories = await store.get_recent(agent, limit=200)
            assert len(memories) == 100
    
    @pytest.mark.asyncio
    async def test_large_memory_objects(self):
        """大きなメモリオブジェクトの処理"""
        store = MemoryStore()
        
        # 大きなオブジェクトを作成
        large_data = {
            "matrix": [[i * j for j in range(100)] for i in range(100)],
            "text": "x" * 10000,
            "nested": {"level": {str(i): i for i in range(1000)}}
        }
        
        await store.add("agent1", large_data)
        
        memories = await store.get_recent("agent1")
        assert len(memories) == 1
        assert len(memories[0]["text"]) == 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])