"""
BacktestEngine と PositionManager の統合テスト
エンジンがポジションマネージャーを通じて取引を実行する流れをテスト
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from backtest2.core.config import (
    BacktestConfig, TimeRange, LLMConfig, RiskConfig, 
    RiskProfile, AgentConfig, DataConfig
)
from backtest2.core.engine import BacktestEngine
from backtest2.core.types import (
    MarketData, TradingDecision, TradeAction, TradingSignal,
    Position, PositionStatus
)


class TestEnginePositionIntegration:
    """エンジンとポジションマネージャーの統合テスト"""
    
    @pytest.fixture
    def basic_config(self):
        """基本的なバックテスト設定"""
        return BacktestConfig(
            name="Integration Test",
            symbols=["AAPL", "GOOGL"],
            time_range=TimeRange(
                start=datetime.now() - timedelta(days=30),
                end=datetime.now()
            ),
            initial_capital=100000.0,
            random_seed=42,
            max_positions=5,
            position_limits={
                RiskProfile.AGGRESSIVE: 0.3,
                RiskProfile.NEUTRAL: 0.2,
                RiskProfile.CONSERVATIVE: 0.1
            },
            llm_config=LLMConfig(
                deep_think_model="gpt-4",
                quick_think_model="gpt-4",
                temperature=0.7,
                max_tokens=1000
            ),
            risk_config=RiskConfig(
                position_limits={
                    RiskProfile.AGGRESSIVE: 0.3,
                    RiskProfile.NEUTRAL: 0.2,
                    RiskProfile.CONSERVATIVE: 0.1
                },
                max_positions=5,
                stop_loss=0.1,
                take_profit=0.2
            ),
            slippage=0.001,
            commission=0.001,
            result_dir=Path("test_results")
        )
    
    @pytest.mark.asyncio
    async def test_engine_executes_trades_through_position_manager(self, basic_config):
        """エンジンがポジションマネージャーを通じて取引を実行"""
        engine = BacktestEngine(basic_config)
        
        # モックデータマネージャー
        mock_market_data = MarketData(
            symbol="AAPL",
            date=datetime.now(),
            open=150.0,
            high=152.0,
            low=149.0,
            close=151.0,
            volume=1000000,
            technicals={}
        )
        
        with patch.object(engine.data_manager, 'get_data', return_value=mock_market_data):
            # モック決定
            import uuid
            mock_decision = TradingDecision(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                symbol="AAPL",
                action=TradeAction.BUY,
                confidence=0.8,
                quantity=100,
                rationale="Test buy signal"
            )
            
            with patch.object(engine.agent_orchestrator, 'make_decision', return_value=mock_decision):
                # 取引実行前の状態
                initial_cash = engine.position_manager.cash
                initial_positions = len(engine.position_manager.positions)
                
                # シンボル処理を実行
                await engine._process_symbol("AAPL", datetime.now())
                
                # 取引が実行されたことを確認
                assert engine.position_manager.cash < initial_cash  # 現金が減少
                assert "AAPL" in engine.position_manager.positions  # ポジションが作成
                assert len(engine.transactions) == 1  # トランザクション記録
    
    @pytest.mark.asyncio
    async def test_portfolio_state_updates_after_trades(self, basic_config):
        """取引後のポートフォリオ状態更新"""
        engine = BacktestEngine(basic_config)
        
        # 初期状態を記録
        initial_state = engine.position_manager.get_portfolio_state()
        assert initial_state.total_value == basic_config.initial_capital
        assert initial_state.position_count == 0
        
        # 買い取引を実行
        transaction = await self._execute_test_trade(
            engine, "AAPL", TradeAction.BUY, 100, 150.0
        )
        
        # ポートフォリオ状態を確認
        new_state = engine.position_manager.get_portfolio_state()
        assert new_state.position_count == 1
        assert new_state.exposure > 0  # エクスポージャーが増加
        assert new_state.cash < initial_state.cash  # 現金が減少
        
        # ポジション価値を更新
        engine.position_manager.update_position_value("AAPL", 155.0)
        
        # 未実現利益を確認
        updated_state = engine.position_manager.get_portfolio_state()
        assert updated_state.unrealized_pnl > 0  # 利益が発生
    
    @pytest.mark.asyncio
    async def test_transaction_history_recording(self, basic_config):
        """トランザクション履歴の記録"""
        engine = BacktestEngine(basic_config)
        
        # 複数の取引を実行
        await self._execute_test_trade(engine, "AAPL", TradeAction.BUY, 100, 150.0)
        await self._execute_test_trade(engine, "GOOGL", TradeAction.BUY, 10, 2500.0)  # Reduced quantity
        await self._execute_test_trade(engine, "AAPL", TradeAction.SELL, 50, 155.0)
        
        # トランザクション履歴を確認
        all_transactions = engine.transactions.get_all()
        assert len(all_transactions) == 3
        
        # 各トランザクションの詳細を確認
        assert all_transactions[0].symbol == "AAPL"
        assert all_transactions[0].action == TradeAction.BUY
        assert all_transactions[1].symbol == "GOOGL"
        assert all_transactions[2].action == TradeAction.SELL
        
        # ポジションマネージャーのトランザクション履歴も確認
        pm_transactions = engine.position_manager.transaction_history.get_all()
        assert len(pm_transactions) == 3
    
    @pytest.mark.asyncio
    async def test_position_closure_flow(self, basic_config):
        """ポジションクローズのフロー"""
        engine = BacktestEngine(basic_config)
        
        # ポジションを開く
        await self._execute_test_trade(engine, "AAPL", TradeAction.BUY, 100, 150.0)
        
        # ポジションが開いていることを確認
        assert "AAPL" in engine.position_manager.positions
        position = engine.position_manager.positions["AAPL"]
        assert position.status == PositionStatus.OPEN
        
        # 全量売却してポジションをクローズ
        await self._execute_test_trade(engine, "AAPL", TradeAction.SELL, 100, 155.0)
        
        # ポジションがクローズされたことを確認
        assert "AAPL" not in engine.position_manager.positions
        
        # クローズされたポジションが履歴に記録
        closed_positions = engine.position_manager.closed_positions.get_all()
        assert len(closed_positions) == 1
        assert closed_positions[0].symbol == "AAPL"
        assert closed_positions[0].status == PositionStatus.CLOSED
        assert closed_positions[0].realized_pnl > 0  # 利益確定
    
    @pytest.mark.asyncio
    async def test_stop_loss_trigger(self, basic_config):
        """ストップロスのトリガー"""
        engine = BacktestEngine(basic_config)
        
        # ポジションを開く
        await self._execute_test_trade(engine, "AAPL", TradeAction.BUY, 100, 150.0)
        position = engine.position_manager.positions["AAPL"]
        position.stop_loss = True  # ストップロスを有効化
        
        # 価格が下落
        engine.position_manager.update_position_value("AAPL", 130.0)  # 13%下落
        
        # 終了条件をチェック
        closed = engine.position_manager.check_exit_conditions(datetime.now())
        
        # ストップロスがトリガーされたことを確認
        assert len(closed) == 1
        assert closed[0].exit_reason == "Stop loss triggered"
    
    @pytest.mark.asyncio
    async def test_take_profit_trigger(self, basic_config):
        """利益確定のトリガー"""
        engine = BacktestEngine(basic_config)
        
        # ポジションを開く
        await self._execute_test_trade(engine, "AAPL", TradeAction.BUY, 100, 150.0)
        position = engine.position_manager.positions["AAPL"]
        position.take_profit = True  # 利益確定を有効化
        
        # 価格が上昇
        engine.position_manager.update_position_value("AAPL", 185.0)  # 23%上昇
        
        # 終了条件をチェック
        closed = engine.position_manager.check_exit_conditions(datetime.now())
        
        # 利益確定がトリガーされたことを確認
        assert len(closed) == 1
        assert closed[0].exit_reason == "Take profit triggered"
    
    @pytest.mark.asyncio
    async def test_concurrent_position_updates(self, basic_config):
        """並行ポジション更新のテスト"""
        engine = BacktestEngine(basic_config)
        
        # 複数のポジションを開く
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]
        prices = [150.0, 2500.0, 300.0, 3000.0]
        
        # 並行して取引を実行
        tasks = []
        for symbol, price in zip(symbols, prices):
            task = self._execute_test_trade(engine, symbol, TradeAction.BUY, 10, price)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # 全ポジションが正しく記録されていることを確認
        assert len(engine.position_manager.positions) == 4
        for symbol in symbols:
            assert symbol in engine.position_manager.positions
    
    @pytest.mark.asyncio
    async def test_risk_adjusted_position_sizing(self, basic_config):
        """リスク調整されたポジションサイジング"""
        engine = BacktestEngine(basic_config)
        
        # 高信頼度シグナル
        high_confidence_signal = TradingSignal(
            symbol="AAPL",
            action=TradeAction.BUY,
            confidence=0.9,
            risk_assessment={"risk_stance": "AGGRESSIVE"}
        )
        
        # 低信頼度シグナル
        low_confidence_signal = TradingSignal(
            symbol="GOOGL",
            action=TradeAction.BUY,
            confidence=0.3,
            risk_assessment={"risk_stance": "CONSERVATIVE"}
        )
        
        # ポジションサイズを計算
        high_size = engine.position_manager.calculate_position_size(
            high_confidence_signal, 0.9, 150.0
        )
        low_size = engine.position_manager.calculate_position_size(
            low_confidence_signal, 0.3, 2500.0
        )
        
        # 高信頼度の方が大きなポジションサイズ
        assert high_size > low_size
        assert high_size <= basic_config.initial_capital * 0.3  # 最大30%
        assert low_size <= basic_config.initial_capital * 0.1  # 最大10%
    
    async def _execute_test_trade(
        self,
        engine: BacktestEngine,
        symbol: str,
        action: TradeAction,
        quantity: float,
        price: float
    ):
        """テスト用の取引実行ヘルパー"""
        from backtest2.core.types import Transaction
        
        transaction = Transaction(
            timestamp=datetime.now(),
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            commission=price * quantity * engine.config.commission,
            slippage=price * quantity * engine.config.slippage,
            total_cost=price * quantity * (1 + engine.config.commission + engine.config.slippage)
        )
        
        success = await engine.position_manager.execute_transaction(transaction)
        if success:
            engine.transactions.append(transaction)
        
        return transaction


class TestEngineDataIntegration:
    """エンジンとデータマネージャーの統合テスト"""
    
    @pytest.mark.asyncio
    async def test_market_data_fetch_and_process(self):
        """市場データの取得と処理"""
        config = BacktestConfig(
            name="Data Integration Test",
            symbols=["AAPL"],
            time_range=TimeRange(
                start=datetime.now() - timedelta(days=7),
                end=datetime.now()
            ),
            initial_capital=100000.0,
            data_config=DataConfig(
                primary_source="YahooFinance",
                fallback_sources=["FinnHub"],
                cache_enabled=True
            )
        )
        
        engine = BacktestEngine(config)
        
        # データマネージャーの初期化
        await engine.data_manager.initialize()
        
        # データ取得をモック
        with patch.object(engine.data_manager, 'get_data') as mock_get_data:
            mock_get_data.return_value = MarketData(
                symbol="AAPL",
                date=datetime.now(),
                open=150.0,
                high=152.0,
                low=149.0,
                close=151.0,
                volume=1000000
            )
            
            # データ取得
            data = await engine.data_manager.get_data("AAPL", datetime.now())
            
            assert data is not None
            assert data.symbol == "AAPL"
            assert data.close == 151.0
    
    @pytest.mark.asyncio
    async def test_data_unavailable_handling(self):
        """データ利用不可時の処理"""
        config = BacktestConfig(
            name="Data Error Test",
            symbols=["INVALID"],
            time_range=TimeRange(
                start=datetime.now() - timedelta(days=1),
                end=datetime.now()
            ),
            initial_capital=100000.0
        )
        
        engine = BacktestEngine(config)
        
        with patch.object(engine.data_manager, 'get_data', return_value=None):
            # データがない場合の処理
            await engine._process_symbol("INVALID", datetime.now())
            
            # エラーが発生せず、ポジションも作成されない
            assert "INVALID" not in engine.position_manager.positions
            assert len(engine.transactions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])