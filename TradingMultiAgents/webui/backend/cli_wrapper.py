"""
CLI実行ラッパー
CLIの機能をWebUIから呼び出すためのインターフェース
"""

import os
import sys
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import json

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cli.models import AnalystType

# ログ設定を強化
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AnalysisConfig:
    """分析設定"""
    ticker: str
    analysis_date: str
    analysts: List[AnalystType]
    research_depth: int
    llm_provider: str
    backend_url: str
    shallow_thinker: str
    deep_thinker: str
    # 新しいチーム設定
    enable_research_team: bool = True
    enable_bull_researcher: bool = True
    enable_bear_researcher: bool = True
    enable_research_manager: bool = True
    debate_rounds: int = 3
    enable_risk_team: bool = True
    enable_aggressive_analyst: bool = True
    enable_conservative_analyst: bool = True
    enable_neutral_analyst: bool = True
    enable_trader: bool = True
    trading_strategy: str = "Balanced"
    enable_portfolio_manager: bool = True
    risk_tolerance: str = "Medium"

@dataclass
class AnalysisProgress:
    """分析進捗状況"""
    stage: str
    agent: str
    status: str  # "waiting", "running", "completed", "error"
    progress: float  # 0.0 - 1.0
    message: str
    timestamp: datetime

class CLIWrapper:
    """CLI機能をWebUIから実行するためのラッパークラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.cli_module = self.project_root / "cli" / "main.py"
        self.results_dir = self.project_root / "results"
        self.progress_callbacks: List[Callable[[AnalysisProgress], None]] = []
        
    def add_progress_callback(self, callback: Callable[[AnalysisProgress], None]):
        """進捗コールバックを追加"""
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self, progress: AnalysisProgress):
        """進捗を通知"""
        for callback in self.progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def get_available_llm_providers(self) -> Dict[str, List[str]]:
        """利用可能なLLMプロバイダーとモデルを取得"""
        return {
            "openai": ["gpt-4o-mini", "gpt-4o", "o1-mini", "o4-mini", "o3-2025-04-16"],
            "anthropic": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-5-sonnet-20241022"],
            "google": ["gemini-1.5-flash", "gemini-1.5-pro"],
            "openrouter": ["meta-llama/llama-3.1-8b-instruct", "anthropic/claude-3.5-sonnet"],
            "ollama": ["llama3.1", "mistral", "codellama"]
        }
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """過去の分析履歴を取得"""
        history = []
        
        if not self.results_dir.exists():
            return history
            
        try:
            for ticker_dir in self.results_dir.iterdir():
                if not ticker_dir.is_dir():
                    continue
                    
                for date_dir in ticker_dir.iterdir():
                    if not date_dir.is_dir():
                        continue
                    
                    reports_dir = date_dir / "reports"
                    if not reports_dir.exists():
                        continue
                    
                    # 最終決定レポートの存在確認
                    final_report = reports_dir / "final_trade_decision.md"
                    status = "completed" if final_report.exists() else "incomplete"
                    
                    # レポートファイル数カウント
                    report_files = list(reports_dir.glob("*.md"))
                    
                    history.append({
                        "ticker": ticker_dir.name,
                        "date": date_dir.name,
                        "status": status,
                        "report_count": len(report_files),
                        "timestamp": date_dir.stat().st_mtime,
                        "path": str(date_dir)
                    })
        except Exception as e:
            logger.error(f"Error getting analysis history: {e}")
        
        # タイムスタンプで降順ソート
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history
    
    def get_analysis_results(self, ticker: str, date: str) -> Dict[str, Any]:
        """特定の分析結果を取得"""
        result_path = self.results_dir / ticker / date
        
        if not result_path.exists():
            return {"error": "Analysis results not found"}
        
        reports_dir = result_path / "reports"
        log_file = result_path / "message_tool.log"
        
        result = {
            "ticker": ticker,
            "date": date,
            "path": str(result_path),
            "reports": {},
            "log": None
        }
        
        # レポートファイルを読み込み
        if reports_dir.exists():
            for report_file in reports_dir.glob("*.md"):
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        result["reports"][report_file.stem] = f.read()
                except Exception as e:
                    logger.error(f"Error reading report {report_file}: {e}")
                    result["reports"][report_file.stem] = f"Error reading file: {e}"
        
        # ログファイルを読み込み
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    result["log"] = f.read()
            except Exception as e:
                logger.error(f"Error reading log file: {e}")
                result["log"] = f"Error reading log: {e}"
        
        return result
    
    async def run_analysis(self, config: AnalysisConfig) -> Dict[str, Any]:
        """分析を実行"""
        try:
            # 環境変数チェック
            required_env_vars = ["FINNHUB_API_KEY", "OPENAI_API_KEY"]
            missing_vars = [var for var in required_env_vars if not os.getenv(var)]
            
            if missing_vars:
                return {
                    "success": False,
                    "error": f"Missing environment variables: {', '.join(missing_vars)}"
                }
            
            # CLIコマンド構築
            cmd = [
                sys.executable, "-m", "cli.main",
                "--ticker", config.ticker,
                "--date", config.analysis_date,
                "--depth", str(config.research_depth),
                "--provider", config.llm_provider,
                "--shallow-model", config.shallow_thinker,
                "--deep-model", config.deep_thinker
            ]
            
            logger.info(f"Executing CLI command: {' '.join(cmd)}")
            
            # アナリスト選択
            for analyst in config.analysts:
                cmd.extend(["--analyst", analyst.value])
            
            # 研究チーム設定
            if not config.enable_research_team:
                cmd.append("--no-research-team")
            else:
                if not config.enable_bull_researcher:
                    cmd.append("--no-bull-researcher")
                if not config.enable_bear_researcher:
                    cmd.append("--no-bear-researcher")
                if not config.enable_research_manager:
                    cmd.append("--no-research-manager")
                cmd.extend(["--debate-rounds", str(config.debate_rounds)])
            
            # リスク管理チーム設定
            if not config.enable_risk_team:
                cmd.append("--no-risk-team")
            else:
                if not config.enable_aggressive_analyst:
                    cmd.append("--no-aggressive-analyst")
                if not config.enable_conservative_analyst:
                    cmd.append("--no-conservative-analyst")
                if not config.enable_neutral_analyst:
                    cmd.append("--no-neutral-analyst")
            
            # トレーディング設定
            if not config.enable_trader:
                cmd.append("--no-trader")
            else:
                cmd.extend(["--trading-strategy", config.trading_strategy])
            
            # ポートフォリオマネージャー設定
            if not config.enable_portfolio_manager:
                cmd.append("--no-portfolio-manager")
            else:
                cmd.extend(["--risk-tolerance", config.risk_tolerance])
            
            # 進捗通知開始
            self._notify_progress(AnalysisProgress(
                stage="initialization",
                agent="system",
                status="running",
                progress=0.0,
                message="分析を開始中...",
                timestamp=datetime.now()
            ))
            
            # ログディレクトリを作成
            log_dir = self.project_root / "logs" / "webui"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # 実行ログファイル
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"analysis_{config.ticker}_{timestamp}.log"
            
            # CLI実行（リアルタイムログ出力）
            logger.info(f"Starting CLI process, logs will be written to: {log_file}")
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"CLI Command: {' '.join(cmd)}\n")
                f.write(f"Environment variables:\n")
                f.write(f"  OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}\n")
                f.write(f"  FINNHUB_API_KEY: {'set' if os.getenv('FINNHUB_API_KEY') else 'not set'}\n")
                f.write(f"Working directory: {self.project_root}\n")
                f.write(f"Analysis started at: {datetime.now()}\n\n")
                
            # 環境変数を明示的に設定
            env = os.environ.copy()
            logger.info(f"Environment check - OPENAI_API_KEY: {'set' if env.get('OPENAI_API_KEY') else 'not set'}")
            logger.info(f"Environment check - FINNHUB_API_KEY: {'set' if env.get('FINNHUB_API_KEY') else 'not set'}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env
            )
            
            # リアルタイムログ監視
            await self._monitor_cli_output(process, config.ticker, config.analysis_date, log_file)
            
            # プロセス完了待機
            await process.wait()
            
            if process.returncode == 0:
                self._notify_progress(AnalysisProgress(
                    stage="completed",
                    agent="system",
                    status="completed",
                    progress=1.0,
                    message="分析が完了しました",
                    timestamp=datetime.now()
                ))
                
                # 分析結果を取得
                results = self.get_analysis_results(config.ticker, config.analysis_date)
                
                # 通知を送信
                if results:
                    self._send_completion_notification(config, results)
                
                return {
                    "success": True,
                    "results": results
                }
            else:
                self._notify_progress(AnalysisProgress(
                    stage="error",
                    agent="system", 
                    status="error",
                    progress=0.0,
                    message=f"分析エラー (return code: {process.returncode})",
                    timestamp=datetime.now()
                ))
                
                return {
                    "success": False,
                    "error": f"CLI execution failed with return code: {process.returncode}"
                }
                
        except Exception as e:
            logger.error(f"Analysis execution error: {e}")
            self._notify_progress(AnalysisProgress(
                stage="error",
                agent="system",
                status="error", 
                progress=0.0,
                message=f"実行エラー: {str(e)}",
                timestamp=datetime.now()
            ))
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _monitor_cli_output(self, process, ticker: str, date: str, log_file: Path):
        """CLIの出力をリアルタイムで監視してログを配信"""
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                while True:
                    # プロセスからの出力を1行ずつ読み取り
                    line = await process.stdout.readline()
                    
                    if not line:
                        break
                        
                    line_text = line.decode('utf-8', errors='ignore').strip()
                    
                    if line_text:
                        # ログファイルに書き込み
                        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {line_text}\n")
                        f.flush()
                        
                        # デバッグログ
                        logger.debug(f"CLI Output: {line_text}")
                        
                        # CLIログの解析と進捗通知
                        self._parse_cli_log_and_notify(line_text)
                        
        except Exception as e:
            logger.error(f"CLI output monitoring error: {e}")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\nERROR: {str(e)}\n")
    
    def _parse_cli_log_and_notify(self, log_line: str):
        """CLIログを解析して進捗通知"""
        try:
            # Rich ライブラリの進捗ログを解析
            if "Market Analyst" in log_line:
                self._notify_progress(AnalysisProgress(
                    stage="analysis",
                    agent="Market Analyst",
                    status="running",
                    progress=0.2,
                    message=log_line,
                    timestamp=datetime.now()
                ))
            elif "Social Analyst" in log_line:
                self._notify_progress(AnalysisProgress(
                    stage="analysis", 
                    agent="Social Analyst",
                    status="running",
                    progress=0.4,
                    message=log_line,
                    timestamp=datetime.now()
                ))
            elif "News Analyst" in log_line:
                self._notify_progress(AnalysisProgress(
                    stage="analysis",
                    agent="News Analyst", 
                    status="running",
                    progress=0.6,
                    message=log_line,
                    timestamp=datetime.now()
                ))
            elif "Fundamentals Analyst" in log_line:
                self._notify_progress(AnalysisProgress(
                    stage="analysis",
                    agent="Fundamentals Analyst",
                    status="running", 
                    progress=0.8,
                    message=log_line,
                    timestamp=datetime.now()
                ))
            elif "Bull Researcher" in log_line or "Bear Researcher" in log_line:
                self._notify_progress(AnalysisProgress(
                    stage="research",
                    agent="Research Team",
                    status="running",
                    progress=0.85,
                    message=log_line,
                    timestamp=datetime.now()
                ))
            elif "Research Manager" in log_line:
                self._notify_progress(AnalysisProgress(
                    stage="research",
                    agent="Research Manager",
                    status="running",
                    progress=0.87,
                    message=log_line,
                    timestamp=datetime.now()
                ))
            elif "Aggressive" in log_line or "Conservative" in log_line or "Neutral" in log_line:
                self._notify_progress(AnalysisProgress(
                    stage="risk_management",
                    agent="Risk Management Team",
                    status="running",
                    progress=0.88,
                    message=log_line,
                    timestamp=datetime.now()
                ))
            elif "Trader" in log_line:
                self._notify_progress(AnalysisProgress(
                    stage="trading",
                    agent="Trader",
                    status="running",
                    progress=0.9,
                    message=log_line,
                    timestamp=datetime.now()
                ))
            elif "Portfolio Manager" in log_line:
                self._notify_progress(AnalysisProgress(
                    stage="portfolio",
                    agent="Portfolio Manager",
                    status="running",
                    progress=0.95,
                    message=log_line,
                    timestamp=datetime.now()
                ))
            elif "Tool Call" in log_line or "API" in log_line:
                # ツール呼び出しログ
                self._notify_progress(AnalysisProgress(
                    stage="tools",
                    agent="System",
                    status="running",
                    progress=0.0,
                    message=log_line,
                    timestamp=datetime.now()
                ))
            elif "ERROR" in log_line or "Error" in log_line:
                # エラーログ
                self._notify_progress(AnalysisProgress(
                    stage="error",
                    agent="System",
                    status="error",
                    progress=0.0,
                    message=log_line,
                    timestamp=datetime.now()
                ))
            else:
                # 一般的なログ
                self._notify_progress(AnalysisProgress(
                    stage="general",
                    agent="CLI",
                    status="running",
                    progress=0.0,
                    message=log_line,
                    timestamp=datetime.now()
                ))
                
        except Exception as e:
            logger.error(f"Log parsing error: {e}")
    
    async def _monitor_analysis_progress(self, ticker: str, date: str):
        """分析進捗を監視（ファイルベース - 旧バージョン）"""
        result_path = self.results_dir / ticker / date / "reports"
        
        # 期待されるレポートファイル
        expected_reports = [
            "market_report.md",
            "sentiment_report.md", 
            "news_report.md",
            "fundamentals_report.md",
            "investment_plan.md",
            "trader_investment_plan.md",
            "final_trade_decision.md"
        ]
        
        completed_reports = set()
        
        for i in range(60):  # 最大60秒間監視
            await asyncio.sleep(1)
            
            if not result_path.exists():
                continue
            
            # 新しく完了したレポートをチェック
            for report in expected_reports:
                report_file = result_path / report
                if report_file.exists() and report not in completed_reports:
                    completed_reports.add(report)
                    
                    progress = len(completed_reports) / len(expected_reports)
                    
                    self._notify_progress(AnalysisProgress(
                        stage="analysis",
                        agent=report.replace("_report.md", "").replace("_", " "),
                        status="completed",
                        progress=progress,
                        message=f"{report} が完了",
                        timestamp=datetime.now()
                    ))
            
            # 全て完了したら終了
            if len(completed_reports) >= len(expected_reports):
                break
    
    def _send_completion_notification(self, config: AnalysisConfig, result: Dict[str, Any]):
        """分析完了通知を送信"""
        try:
            import streamlit as st
            from tradingagents.services.browser_notification import (
                AnalysisNotificationService
            )
            
            # ユーザーIDの取得（セッションベース）
            user_id = st.session_state.get("user_id", "default")
            
            # 通知が有効な場合のみ送信
            if st.session_state.get("notifications_enabled", False):
                service = AnalysisNotificationService()
                
                # 分析結果から情報を抽出
                # 結果の構造に基づいて適切な値を取得
                recommendation = "N/A"
                confidence = 0.0
                
                # 最終的な取引決定を探す
                if isinstance(result, dict):
                    for key, value in result.items():
                        if "final_decision" in key.lower() and isinstance(value, dict):
                            recommendation = value.get("recommendation", recommendation)
                            confidence = value.get("confidence", confidence)
                            break
                
                # 分析時間を計算（仮に10分とする）
                duration_minutes = 10
                
                service.send_analysis_complete(
                    user_id=user_id,
                    ticker=config.ticker,
                    analysis_date=config.analysis_date,
                    recommendation=recommendation,
                    confidence=confidence,
                    duration_minutes=duration_minutes,
                    analysis_id=f"{config.ticker}_{config.analysis_date}"
                )
                
                logger.info(f"Notification sent for {config.ticker}")
                
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")