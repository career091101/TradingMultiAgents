#!/usr/bin/env python3
"""
Backtest2の修正が正しく適用されたか確認するスクリプト
"""

import sys
from pathlib import Path

def verify_fix():
    """修正の確認"""
    print("=== Backtest2 修正確認 ===\n")
    
    # 1. インポートの確認
    print("1. plotly.express インポートの確認...")
    backtest2_path = Path(__file__).parent / "TradingMultiAgents/webui/components/backtest2.py"
    
    try:
        with open(backtest2_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "import plotly.express as px" in content:
            print("✅ plotly.express インポートが正しく追加されています")
        else:
            print("❌ plotly.express インポートが見つかりません")
            return False
            
    except FileNotFoundError:
        print(f"❌ ファイルが見つかりません: {backtest2_path}")
        return False
    
    # 2. plotlyモジュールの利用可能性確認
    print("\n2. plotlyモジュールの確認...")
    try:
        import plotly.express as px
        print("✅ plotly.expressが正常にインポートできます")
        print(f"   バージョン: {plotly.__version__}")
    except ImportError:
        print("❌ plotly.expressがインストールされていません")
        print("   実行: pip install plotly")
        return False
    
    # 3. px.pie使用箇所の確認
    print("\n3. px.pie使用箇所の確認...")
    pie_usage = content.count("px.pie")
    print(f"✅ px.pieの使用箇所: {pie_usage}箇所")
    
    # 4. 推奨事項
    print("\n=== 次のステップ ===")
    print("1. WebUIを再起動してください:")
    print("   cd TradingMultiAgents && python run_webui.py")
    print("\n2. ブラウザでバックテストページにアクセス:")
    print("   http://localhost:8501")
    print("\n3. バックテストを実行:")
    print("   - ティッカー: AAPL, MSFT")
    print("   - 期間: 過去3ヶ月")
    print("   - 「マルチエージェントバックテストを開始」をクリック")
    print("\n4. 結果表示でエラーが発生しないことを確認")
    
    return True

if __name__ == "__main__":
    import plotly
    
    if verify_fix():
        print("\n✅ 修正が正しく適用されています！")
        sys.exit(0)
    else:
        print("\n❌ 修正に問題があります")
        sys.exit(1)