#!/usr/bin/env python3
"""
高度なバックテスト検証スクリプト
TradingAgents2のバックテストを自動実行し、結果を検証。
問題発生時には根本原因を分析し、診断レポートを生成する。
"""

import asyncio
import sys
import os
import json
import re
import glob
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def run_backtest() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    バックテストを直接実行する
    
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (成功フラグ, 結果ディレクトリ, エラーメッセージ)
    """
    try:
        from backtest2.core.config import BacktestConfig, LLMConfig, TimeRange
        from backtest2.core.engine import BacktestEngine
        
        print("バックテストを実行中...")
        
        # バックテスト設定
        config = BacktestConfig(
            name="verification_test",
            symbols=["AAPL"],
            initial_capital=10000,
            time_range=TimeRange(
                start=datetime(2023, 1, 1),
                end=datetime(2023, 1, 31)
            ),
            llm_config=LLMConfig(
                deep_think_model="mock",  # モックモードで実行
                quick_think_model="mock",
                timeout=60,
                temperature=0.0
            ),
            debug=True
        )
        
        # エンジンの作成と実行
        engine = BacktestEngine(config)
        
        # タイムアウト付きで実行（5分）
        result = await asyncio.wait_for(engine.run(), timeout=300.0)
        
        if result:
            # 結果ディレクトリのパスを構築
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_dir = Path("results") / f"backtest2_{timestamp}"
            
            # 結果を保存
            result_dir.mkdir(parents=True, exist_ok=True)
            memories_file = result_dir / "AAPL" / "memories.json"
            memories_file.parent.mkdir(parents=True, exist_ok=True)
            
            # メモリデータを保存
            memories_data = {
                "total_return": result.metrics.total_return,
                "total_trades": result.metrics.total_trades,
                "win_rate": result.metrics.win_rate,
                "sharpe_ratio": result.metrics.sharpe_ratio,
                "max_drawdown": result.metrics.max_drawdown,
                "transactions": [
                    {
                        "date": str(t.timestamp),
                        "symbol": t.symbol,
                        "action": str(t.action),
                        "quantity": t.quantity,
                        "price": t.price,
                        "total_cost": t.total_cost
                    } for t in result.transactions
                ],
                "final_portfolio_value": result.metrics.final_value,
                "initial_capital": result.config.initial_capital
            }
            
            with open(memories_file, 'w', encoding='utf-8') as f:
                json.dump(memories_data, f, ensure_ascii=False, indent=2)
            
            return True, str(result_dir), None
            
    except asyncio.TimeoutError:
        error_msg = "Timeout: バックテストの実行が5分を超えました"
        logger.error(error_msg)
        return False, None, error_msg
        
    except ImportError as e:
        error_msg = f"ImportError: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, None, error_msg
        
    except Exception as e:
        import traceback
        error_msg = f"実行エラー: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        logger.error(error_msg)
        return False, None, error_msg


def find_latest_backtest_dir() -> Optional[Path]:
    """
    最新のバックテスト結果ディレクトリを検索する
    
    Returns:
        Optional[Path]: 見つかった場合はPathオブジェクト、見つからない場合はNone
    """
    results_dir = Path("results")
    if not results_dir.exists():
        return None
    
    # backtest2_で始まるディレクトリを検索
    backtest_dirs = list(results_dir.glob("backtest2_*"))
    if not backtest_dirs:
        return None
    
    # 最新のディレクトリを返す（タイムスタンプ順でソート）
    return max(backtest_dirs, key=lambda p: p.stat().st_mtime)


def verify_results(result_dir: Path) -> bool:
    """
    バックテスト結果を検証する
    
    Args:
        result_dir: 検証対象のディレクトリ
    
    Returns:
        bool: 検証成功の場合True
    """
    memories_file = result_dir / "AAPL" / "memories.json"
    
    # ファイルの存在確認
    if not memories_file.exists():
        print(f"エラー: memories.jsonが見つかりません: {memories_file}")
        return False
    
    # ファイルが空でないことを確認
    try:
        with open(memories_file, 'r') as f:
            data = json.load(f)
            if not data:
                print("エラー: memories.jsonが空です")
                return False
    except json.JSONDecodeError:
        print("エラー: memories.jsonが不正なJSON形式です")
        return False
    except Exception as e:
        print(f"エラー: memories.jsonの読み込みに失敗: {e}")
        return False
    
    return True


def save_error_details(error_msg: str) -> None:
    """
    エラー詳細をファイルに保存する
    
    Args:
        error_msg: エラーメッセージ
    """
    with open("error_details.log", "w", encoding="utf-8") as f:
        f.write("=== エラー詳細 ===\n")
        f.write(error_msg)
        f.write("\n\n")
        
        # 最新のログファイルを探す
        log_dir = Path("logs")
        if log_dir.exists():
            error_logs = list(log_dir.glob("backtest_error_*.log"))
            if error_logs:
                latest_error_log = max(error_logs, key=lambda p: p.stat().st_mtime)
                f.write(f"=== {latest_error_log.name} ===\n")
                try:
                    with open(latest_error_log, "r", encoding="utf-8") as err_f:
                        f.write(err_f.read())
                except Exception as e:
                    f.write(f"エラーログの読み込みに失敗: {e}\n")


def analyze_failure(error_msg: str) -> Dict[str, any]:
    """
    エラーを分析して根本原因を特定する
    
    Args:
        error_msg: エラーメッセージ
    
    Returns:
        Dict: 分析結果（error_type, location, root_cause, recommendation）
    """
    # デフォルトの分析結果
    result = {
        "error_type": "不明なエラー",
        "location": {"file": "不明", "line": "不明", "function": "不明"},
        "root_cause": "エラーの詳細を特定できませんでした",
        "recommendation": "ログファイルを手動で確認してください"
    }
    
    # エラータイプの分類
    error_patterns = {
        r"Timeout|TimeoutError|timed out": ("タイムアウトエラー", 
            "処理が指定時間内に完了しませんでした",
            "・処理対象のデータ量を減らしてください\n・タイムアウト時間を延長してください"),
        r"ImportError|ModuleNotFoundError|No module named": ("モジュール未検出エラー",
            "必要なPythonモジュールがインストールされていません",
            "・pip install -e . を実行してください\n・仮想環境が正しく有効化されているか確認してください"),
        r"ConnectionError|NetworkError|URLError|HTTPError": ("接続エラー",
            "外部サービスへの接続に失敗しました",
            "・インターネット接続を確認してください\n・APIのエンドポイントが正しいか確認してください"),
        r"FileNotFoundError|No such file or directory": ("ファイル未検出エラー",
            "必要なファイルが見つかりません",
            "・ファイルパスが正しいか確認してください\n・必要なデータファイルが存在するか確認してください"),
        r"KeyError": ("キーエラー",
            "辞書やデータフレームに存在しないキーへのアクセスが発生しました",
            "・データ構造を確認してください\n・APIレスポンスの形式が変更されていないか確認してください"),
        r"ConfigError|Configuration|API_KEY|api_key": ("設定エラー",
            "設定ファイルまたは環境変数に問題があります",
            "・.envファイルが存在し、必要な設定が記載されているか確認してください\n・APIキーが正しく設定されているか確認してください"),
    }
    
    for pattern, (error_type, cause, recommendation) in error_patterns.items():
        if re.search(pattern, error_msg, re.IGNORECASE):
            result["error_type"] = error_type
            result["root_cause"] = cause
            result["recommendation"] = recommendation
            break
    
    # スタックトレースから発生箇所を特定
    traceback_pattern = r'File "([^"]+)", line (\d+), in ([^\n]+)'
    matches = list(re.finditer(traceback_pattern, error_msg))
    if matches:
        # 最後のマッチ（最も深いスタックフレーム）を使用
        last_match = matches[-1]
        result["location"] = {
            "file": last_match.group(1),
            "line": last_match.group(2),
            "function": last_match.group(3).strip()
        }
    
    return result


def generate_failure_report(analysis: Dict[str, any], error_msg: str) -> None:
    """
    診断レポートをマークダウン形式で生成する
    
    Args:
        analysis: analyze_failure()の結果
        error_msg: エラーメッセージ
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_content = f"""# バックテスト失敗診断レポート

## 発生日時
{timestamp}

## エラー概要
{analysis['error_type']}

## 発生箇所
- ファイル: `{analysis['location']['file']}`
- 行番号: {analysis['location']['line']}
- 関数名: `{analysis['location']['function']}`

## 根本原因の推定
{analysis['root_cause']}

## 推奨される対処法
{analysis['recommendation']}

## 詳細ログ
```
{error_msg}
```
"""
    
    # レポートファイルに保存
    with open("failure_report.md", "w", encoding="utf-8") as f:
        f.write(report_content)


def cleanup_results(result_dir: Path) -> None:
    """
    検証用に作成された結果ディレクトリをクリーンアップする
    
    Args:
        result_dir: 削除対象のディレクトリ
    """
    try:
        shutil.rmtree(result_dir)
        print(f"クリーンアップ完了: {result_dir}")
    except Exception as e:
        print(f"クリーンアップ中にエラーが発生しました: {e}")


async def main():
    """メイン処理"""
    print("=== TradingAgents2 バックテスト検証開始 ===")
    
    # バックテストの実行
    success, result_dir, error_msg = await run_backtest()
    
    # 成功判定
    if success and result_dir:
        result_path = Path(result_dir)
        if verify_results(result_path):
            # 【A】問題なしの場合
            print("\n✅ バックテストは正常に完了しました。")
            cleanup_results(result_path)
            sys.exit(0)
    
    # 【B】問題ありの場合
    print("\n❌ バックテストに失敗しました。")
    
    # エラー情報の収集
    if error_msg:
        save_error_details(error_msg)
        
        # 根本原因の分析
        analysis = analyze_failure(error_msg)
        
        # 診断レポートの生成
        generate_failure_report(analysis, error_msg)
    
    print("詳細は `failure_report.md` を確認してください。")
    sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())