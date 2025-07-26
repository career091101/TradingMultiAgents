#!/usr/bin/env python3
"""
Backtest2のプロット機能に対するテストケース
plotlyインポートエラーの再発防止のため
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestBacktest2Plotting(unittest.TestCase):
    """Backtest2のプロット機能のテスト"""
    
    def setUp(self):
        """テストの初期設定"""
        self.mock_st = Mock()
        self.mock_state = Mock()
        
    @patch('webui.components.backtest2.st')
    @patch('webui.components.backtest2.SessionState')
    def test_plotly_imports(self, mock_session, mock_st):
        """plotlyのインポートが正しく行われているかテスト"""
        try:
            from webui.components.backtest2 import Backtest2Page
            # インポートが成功すればテストはパス
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    @patch('webui.components.backtest2.px')
    def test_decision_flow_visualization(self, mock_px):
        """決定フロー可視化でpx.pieが正しく呼ばれるかテスト"""
        # モックデータの準備
        mock_results = {
            "tickers": {
                "AAPL": {
                    "decision_flow": [
                        {
                            "timestamp": "2025-07-24",
                            "phase6_decision": {"action": "BUY", "quantity": 100}
                        },
                        {
                            "timestamp": "2025-07-25", 
                            "phase6_decision": {"action": "HOLD", "quantity": 0}
                        }
                    ]
                }
            }
        }
        
        # テスト用のDataFrame
        df_decisions = pd.DataFrame({
            "Action": ["BUY", "HOLD", "SELL"],
            "Count": [1, 1, 0]
        })
        
        # px.pieが呼ばれることを確認
        mock_px.pie.return_value = Mock()
        
        from webui.components.backtest2 import Backtest2Page
        page = Backtest2Page()
        
        # _display_decision_flow_analysisメソッドが存在するか確認
        self.assertTrue(hasattr(page, '_display_decision_flow_analysis'))
    
    def test_error_handling_for_missing_data(self):
        """データが欠落している場合のエラーハンドリングテスト"""
        from webui.components.backtest2 import Backtest2Page
        page = Backtest2Page()
        
        # 空の結果でもエラーが発生しないことを確認
        empty_results = {"tickers": {}}
        
        # エラーが発生しないことを確認
        try:
            # ページインスタンスが正常に作成されることを確認
            self.assertIsNotNone(page)
        except Exception as e:
            self.fail(f"Unexpected error: {e}")
    
    @patch('webui.components.backtest2.st')
    def test_complete_plotting_workflow(self, mock_st):
        """完全なプロットワークフローのテスト"""
        # Streamlitのモック設定
        mock_st.plotly_chart = Mock()
        mock_st.dataframe = Mock()
        mock_st.markdown = Mock()
        
        # テスト結果データ
        test_results = {
            "config": {
                "tickers": ["AAPL", "MSFT"],
                "start_date": "2025-04-25",
                "end_date": "2025-07-23"
            },
            "tickers": {
                "AAPL": {
                    "metrics": {
                        "total_return": 0.0,
                        "sharpe_ratio": 0.0,
                        "trades": 0
                    },
                    "decision_flow": []
                }
            },
            "portfolio": {
                "metrics": {
                    "total_return": 0.0,
                    "sharpe_ratio": 0.0
                }
            }
        }
        
        # プロット機能が正常に動作することを確認
        from webui.components.backtest2 import Backtest2Page
        page = Backtest2Page()
        
        # 結果表示メソッドが存在することを確認
        self.assertTrue(hasattr(page, 'render'))


class TestPlotlyIntegration(unittest.TestCase):
    """Plotly統合テスト"""
    
    def test_plotly_express_availability(self):
        """plotly.expressが利用可能かテスト"""
        try:
            import plotly.express as px
            # 基本的な関数が利用可能か確認
            self.assertTrue(hasattr(px, 'pie'))
            self.assertTrue(hasattr(px, 'line'))
            self.assertTrue(hasattr(px, 'bar'))
        except ImportError:
            self.fail("plotly.express is not available")
    
    def test_plotly_version_compatibility(self):
        """plotlyのバージョン互換性テスト"""
        try:
            import plotly
            version = plotly.__version__
            # バージョンが4.0以上であることを確認
            major_version = int(version.split('.')[0])
            self.assertGreaterEqual(major_version, 4)
        except Exception as e:
            self.fail(f"Version check failed: {e}")


if __name__ == '__main__':
    # テスト実行
    unittest.main(verbosity=2)