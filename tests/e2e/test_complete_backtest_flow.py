"""
完全なバックテストフローのE2Eテスト
システム全体が正しく動作することを確認
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import json
import pandas as pd
from unittest.mock import patch, Mock

from backtest2.core.config import (
    BacktestConfig, TimeRange, LLMConfig, RiskConfig,
    RiskProfile, AgentConfig, DataConfig
)
from backtest2.core.engine import BacktestEngine
from backtest2.core.types import MarketData, TradeAction


class TestCompleteBacktestFlow:
    """完全なバックテストフローのE2Eテスト"""
    
    @pytest.fixture
    def e2e_config(self):
        """E2Eテスト用の設定"""
        return BacktestConfig(
            name="E2E Complete Test",
            symbols=["AAPL", "GOOGL", "MSFT"],
            time_range=TimeRange(
                start=datetime(2024, 1, 1),
                end=datetime(2024, 1, 31)
            ),
            initial_capital=100000.0,
            random_seed=42,
            max_positions=3,
            position_limits={
                RiskProfile.AGGRESSIVE: 0.4,
                RiskProfile.NEUTRAL: 0.25,
                RiskProfile.CONSERVATIVE: 0.15
            },
            llm_config=LLMConfig(
                deep_think_model="gpt-4",
                quick_think_model="gpt-4",
                temperature=0.7,
                max_tokens=2000,
                timeout=30
            ),
            agent_config=AgentConfig(
                max_debate_rounds=2,
                max_risk_discuss_rounds=1,
                llm_config=LLMConfig(
                    deep_think_model="gpt-4",
                    quick_think_model="gpt-4"
                ),
                use_japanese_prompts=False,
                enable_memory=True
            ),
            data_config=DataConfig(
                primary_source="YahooFinance",
                fallback_sources=["FinnHub"],
                cache_enabled=True,
                force_refresh=False
            ),
            risk_config=RiskConfig(
                position_limits={
                    RiskProfile.AGGRESSIVE: 0.4,
                    RiskProfile.NEUTRAL: 0.25,
                    RiskProfile.CONSERVATIVE: 0.15
                },
                max_positions=3,
                stop_loss=0.1,
                take_profit=0.2,
                confidence_thresholds={
                    'high': 0.8,
                    'medium': 0.5,
                    'low': 0.2
                }
            ),
            slippage=0.001,
            commission=0.001,
            risk_free_rate=0.05,
            benchmark="SPY",
            save_results=True,
            results_path="test_results/e2e",
            enable_monitoring=True
        )
    
    @pytest.mark.asyncio
    async def test_single_stock_one_month_backtest(self, e2e_config):
        """単一銘柄、1ヶ月のバックテスト"""
        # 単一銘柄に変更
        e2e_config.symbols = ["AAPL"]
        
        engine = BacktestEngine(e2e_config)
        
        # モック市場データを生成
        market_data = self._generate_mock_market_data("AAPL", 30)
        
        with patch.object(engine.data_manager, 'get_data') as mock_get_data:
            mock_get_data.side_effect = lambda symbol, date: self._get_mock_data_for_date(
                market_data, symbol, date
            )
            
            # エージェントの決定をモック
            with patch.object(engine.agent_orchestrator, 'make_decision') as mock_decision:
                mock_decision.side_effect = self._generate_mock_decisions
                
                # バックテスト実行
                result = await engine.run()
                
                # 基本的な結果検証
                assert result is not None
                assert result.execution_id == engine.execution_id
                assert result.config == e2e_config
                
                # メトリクス検証
                assert hasattr(result, 'metrics')
                assert result.metrics is not None
                assert result.metrics.total_trades >= 0
                assert -100 <= result.metrics.total_return <= 1000  # 妥当な範囲
                
                # トランザクション検証
                # メトリクスのtotal_tradesは閉じたポジション数、transactionsは全取引
                assert len(result.transactions) >= result.metrics.total_trades
                # 取引があった場合は、少なくとも1つは存在するはず
                if result.metrics.total_trades > 0:
                    assert len(result.transactions) > 0
                
                # ポートフォリオ状態検証
                assert result.final_portfolio.total_value > 0
                assert result.final_portfolio.cash >= 0
    
    @pytest.mark.asyncio
    async def test_multi_stock_portfolio_backtest(self, e2e_config):
        """複数銘柄ポートフォリオのバックテスト"""
        engine = BacktestEngine(e2e_config)
        
        # 各銘柄のモックデータ
        market_data = {
            "AAPL": self._generate_mock_market_data("AAPL", 30),
            "GOOGL": self._generate_mock_market_data("GOOGL", 30, base_price=2500),
            "MSFT": self._generate_mock_market_data("MSFT", 30, base_price=300)
        }
        
        with patch.object(engine.data_manager, 'get_data') as mock_get_data:
            mock_get_data.side_effect = lambda symbol, date: self._get_mock_data_for_date(
                market_data[symbol], symbol, date
            )
            
            with patch.object(engine.agent_orchestrator, 'make_decision') as mock_decision:
                mock_decision.side_effect = self._generate_mock_decisions
                
                # バックテスト実行
                result = await engine.run()
                
                # ポートフォリオの分散を確認
                unique_symbols = set(t.symbol for t in result.transactions)
                assert len(unique_symbols) <= 3  # 最大3銘柄
                
                # ポジション制限の確認
                assert result.final_portfolio.position_count <= e2e_config.max_positions
    
    @pytest.mark.asyncio
    async def test_bull_market_scenario(self, e2e_config):
        """上昇相場シナリオ"""
        e2e_config.symbols = ["AAPL"]
        engine = BacktestEngine(e2e_config)
        
        # 上昇トレンドのデータ（毎日0.5%上昇）
        market_data = self._generate_trending_market_data("AAPL", 30, daily_return=0.005)
        
        with patch.object(engine.data_manager, 'get_data') as mock_get_data:
            mock_get_data.side_effect = lambda symbol, date: self._get_mock_data_for_date(
                market_data, symbol, date
            )
            
            # 常に買いシグナルを出す
            with patch.object(engine.agent_orchestrator, 'make_decision') as mock_decision:
                mock_decision.side_effect = lambda **kwargs: self._generate_bullish_decision(
                    kwargs['symbol']
                )
                
                result = await engine.run()
                
                # 取引が実行されたか確認
                print(f"Total trades: {result.metrics.total_trades}")
                print(f"Transactions: {len(result.transactions)}")
                print(f"Total return: {result.metrics.total_return}")
                
                # 上昇相場では少なくとも取引が実行されるはず
                assert len(result.transactions) > 0, "No transactions were executed"
                # 全体的にはプラスになるか、少なくとも大きな損失は出ないはず
                assert result.metrics.total_return > -0.1  # 10%以上の損失は出ないはず
    
    @pytest.mark.asyncio
    async def test_bear_market_scenario(self, e2e_config):
        """下降相場シナリオ"""
        e2e_config.symbols = ["AAPL"]
        engine = BacktestEngine(e2e_config)
        
        # 下降トレンドのデータ（毎日0.5%下落）
        market_data = self._generate_trending_market_data("AAPL", 30, daily_return=-0.005)
        
        with patch.object(engine.data_manager, 'get_data') as mock_get_data:
            mock_get_data.side_effect = lambda symbol, date: self._get_mock_data_for_date(
                market_data, symbol, date
            )
            
            with patch.object(engine.agent_orchestrator, 'make_decision') as mock_decision:
                mock_decision.side_effect = self._generate_bearish_decisions
                
                result = await engine.run()
                
                # 下降相場では保守的な戦略で損失を回避
                # max_drawdownは負の値なので、-0.1より大きい（損失が少ない）ことを確認
                assert result.metrics.max_drawdown >= -0.1  # 最大10%以内の損失
                # 大きな損失を避けているはず
                assert result.metrics.total_return >= -0.15  # 15%以上の損失は出ない
    
    @pytest.mark.asyncio
    async def test_volatile_market_scenario(self, e2e_config):
        """高ボラティリティシナリオ"""
        e2e_config.symbols = ["AAPL"]
        engine = BacktestEngine(e2e_config)
        
        # 高ボラティリティデータ（日次±5%の変動）
        market_data = self._generate_volatile_market_data("AAPL", 30, volatility=0.05)
        
        with patch.object(engine.data_manager, 'get_data') as mock_get_data:
            mock_get_data.side_effect = lambda symbol, date: self._get_mock_data_for_date(
                market_data, symbol, date
            )
            
            with patch.object(engine.agent_orchestrator, 'make_decision') as mock_decision:
                mock_decision.side_effect = self._generate_cautious_decisions
                
                result = await engine.run()
                
                # 高ボラティリティではリスク管理が機能
                assert result.metrics.volatility > 0.2  # 高いボラティリティ
                # ポジションサイズが制限される
                avg_position_size = sum(t.total_cost for t in result.transactions) / len(result.transactions) if result.transactions else 0
                assert avg_position_size < e2e_config.initial_capital * 0.15  # 保守的なサイズ
    
    @pytest.mark.asyncio
    async def test_memory_persistence_across_runs(self, e2e_config):
        """実行間でのメモリ永続性"""
        e2e_config.symbols = ["AAPL"]
        results_dir = Path("test_results/memory_test")
        e2e_config.result_dir = results_dir
        
        # 1回目の実行
        engine1 = BacktestEngine(e2e_config)
        with self._mock_market_data_and_decisions(engine1):
            result1 = await engine1.run()
        
        # メモリが保存されたことを確認
        memory_file = results_dir / "memories.json"
        assert memory_file.exists()
        
        # 2回目の実行で新しいメモリストアをロード
        engine2 = BacktestEngine(e2e_config)
        
        # メモリが永続化されていることを確認
        # メモリストア全体に何かデータがあるかチェック
        assert len(engine2.memory_store.memories) > 0, "No memories were loaded from file"
    
    @pytest.mark.asyncio
    async def test_benchmark_comparison(self, e2e_config):
        """ベンチマーク比較機能"""
        engine = BacktestEngine(e2e_config)
        
        with self._mock_market_data_and_decisions(engine):
            # ベンチマークデータもモック
            with patch.object(engine, '_load_benchmark_data'):
                result = await engine.run()
                
                # ベンチマーク比較が含まれることを確認
                assert hasattr(result, 'benchmark_comparison')
                if result.benchmark_comparison:
                    assert 'portfolio' in result.benchmark_comparison
                    assert 'benchmark' in result.benchmark_comparison
                    assert 'relative' in result.benchmark_comparison
    
    # ヘルパーメソッド
    def _generate_mock_market_data(self, symbol: str, days: int, base_price: float = 150.0):
        """モック市場データ生成"""
        data = []
        current_price = base_price
        start_date = datetime(2024, 1, 1)
        
        for i in range(days):
            # ランダムな日次変動（±2%）
            import random
            daily_return = random.uniform(-0.02, 0.02)
            current_price *= (1 + daily_return)
            
            data.append(MarketData(
                symbol=symbol,
                date=start_date + timedelta(days=i),
                open=current_price * 0.99,
                high=current_price * 1.01,
                low=current_price * 0.98,
                close=current_price,
                volume=random.randint(1000000, 5000000),
                technicals={
                    'sma_20': current_price,
                    'rsi': random.uniform(30, 70)
                }
            ))
        
        return data
    
    def _generate_trending_market_data(self, symbol: str, days: int, daily_return: float):
        """トレンドのある市場データ生成"""
        data = []
        current_price = 150.0
        start_date = datetime(2024, 1, 1)
        
        for i in range(days):
            current_price *= (1 + daily_return)
            
            data.append(MarketData(
                symbol=symbol,
                date=start_date + timedelta(days=i),
                open=current_price * 0.995,
                high=current_price * 1.005,
                low=current_price * 0.99,
                close=current_price,
                volume=2000000
            ))
        
        return data
    
    def _generate_volatile_market_data(self, symbol: str, days: int, volatility: float):
        """高ボラティリティ市場データ生成"""
        import random
        data = []
        current_price = 150.0
        start_date = datetime(2024, 1, 1)
        
        for i in range(days):
            daily_return = random.uniform(-volatility, volatility)
            current_price *= (1 + daily_return)
            
            data.append(MarketData(
                symbol=symbol,
                date=start_date + timedelta(days=i),
                open=current_price,
                high=current_price * (1 + volatility/2),
                low=current_price * (1 - volatility/2),
                close=current_price * (1 + random.uniform(-volatility/4, volatility/4)),
                volume=random.randint(3000000, 10000000)
            ))
        
        return data
    
    def _get_mock_data_for_date(self, data_list, symbol, date):
        """特定日付のデータを取得"""
        for data in data_list:
            if data.date.date() == date.date():
                return data
        return None
    
    async def _generate_mock_decisions(self, **kwargs):
        """モック決定生成"""
        from backtest2.core.types import TradingDecision
        import random
        
        symbol = kwargs['symbol']
        portfolio = kwargs['portfolio']
        
        # シンプルな決定ロジック
        if symbol in portfolio.positions:
            # ポジションがある場合は50%の確率で売り
            position = portfolio.positions[symbol]
            if random.random() > 0.5:
                action = TradeAction.SELL
                # 実際の保有数量を使用
                quantity = position.quantity
            else:
                action = TradeAction.HOLD
                quantity = 0
        else:
            # ポジションがない場合は30%の確率で買い
            if random.random() > 0.7:
                action = TradeAction.BUY
                quantity = 100  # 買いの場合は金額ベース
            else:
                action = TradeAction.HOLD
                quantity = 0
        
        import uuid
        return TradingDecision(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            symbol=symbol,
            action=action,
            confidence=random.uniform(0.4, 0.9),
            quantity=quantity,
            rationale="Mock decision for testing"
        )
    
    def _generate_bullish_decision(self, symbol):
        """強気の決定生成"""
        from backtest2.core.types import TradingDecision
        import uuid
        return TradingDecision(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            symbol=symbol,
            action=TradeAction.BUY,
            confidence=0.9,
            quantity=100,
            rationale="Bullish market conditions"
        )
    
    async def _generate_bearish_decisions(self, **kwargs):
        """弱気の決定生成"""
        from backtest2.core.types import TradingDecision
        symbol = kwargs['symbol']
        portfolio = kwargs['portfolio']
        
        if symbol in portfolio.positions:
            # ポジションがある場合は売り
            action = TradeAction.SELL
        else:
            # ポジションがない場合は買わない
            action = TradeAction.HOLD
        
        import uuid
        return TradingDecision(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            symbol=symbol,
            action=action,
            confidence=0.8,
            quantity=100,
            rationale="Bearish market conditions"
        )
    
    async def _generate_cautious_decisions(self, **kwargs):
        """慎重な決定生成（高ボラティリティ対応）"""
        from backtest2.core.types import TradingDecision
        symbol = kwargs['symbol']
        
        # 高ボラティリティでは低信頼度で小さなポジション
        import random
        if random.random() > 0.8:  # 20%の確率でのみ取引
            action = TradeAction.BUY if random.random() > 0.5 else TradeAction.SELL
            confidence = 0.3  # 低信頼度
        else:
            action = TradeAction.HOLD
            confidence = 0.5
        
        import uuid
        return TradingDecision(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            symbol=symbol,
            action=action,
            confidence=confidence,
            quantity=50,  # 小さなポジション
            rationale="High volatility - cautious approach"
        )
    
    def _mock_market_data_and_decisions(self, engine):
        """市場データと決定をモックするコンテキストマネージャー"""
        from contextlib import ExitStack
        
        stack = ExitStack()
        
        # 市場データのモック
        market_data = self._generate_mock_market_data("AAPL", 30)
        mock_get_data = stack.enter_context(
            patch.object(engine.data_manager, 'get_data')
        )
        mock_get_data.side_effect = lambda symbol, date: self._get_mock_data_for_date(
            market_data, symbol, date
        )
        
        # 決定のモック
        mock_decision = stack.enter_context(
            patch.object(engine.agent_orchestrator, 'make_decision')
        )
        mock_decision.side_effect = self._generate_mock_decisions
        
        return stack


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])