"""
E2Eテスト用の設定管理
環境変数とテスト設定を一元管理
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import json
import yaml


@dataclass
class TestConfig:
    """E2Eテストの設定を管理するクラス"""
    
    # 基本設定
    base_url: str = "http://localhost:8501"
    headless: bool = True
    browser: str = "chromium"  # chromium, firefox, webkit
    timeout: int = 30000  # ミリ秒
    
    # スクリーンショット設定
    screenshot_on_failure: bool = True
    screenshot_dir: str = "tests/e2e/screenshots"
    video_on_failure: bool = False
    video_dir: str = "tests/e2e/videos"
    
    # リトライ設定
    retry_count: int = 3
    retry_delay: float = 2.0
    
    # 並列実行設定
    parallel_workers: int = 4
    parallel_scope: str = "function"  # function, class, module, session
    
    # テストデータ
    test_data_dir: str = "tests/e2e/data"
    
    # APIキー（環境変数から読み込み）
    finnhub_api_key: str = field(default_factory=lambda: os.getenv("FINNHUB_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    
    # WebUI設定
    webui_startup_timeout: int = 60  # 秒
    webui_port: int = 8501
    
    # テスト実行モード
    test_mode: str = "normal"  # normal, smoke, regression, performance
    
    # レポート設定
    generate_html_report: bool = True
    report_dir: str = "reports/e2e"
    
    @classmethod
    def from_env(cls) -> "TestConfig":
        """環境変数から設定を読み込む"""
        config = cls()
        
        # 環境変数のマッピング
        env_mapping = {
            "E2E_BASE_URL": "base_url",
            "E2E_HEADLESS": "headless",
            "E2E_BROWSER": "browser",
            "E2E_TIMEOUT": "timeout",
            "E2E_RETRY_COUNT": "retry_count",
            "E2E_PARALLEL_WORKERS": "parallel_workers",
            "E2E_TEST_MODE": "test_mode",
        }
        
        for env_key, attr_name in env_mapping.items():
            if env_value := os.getenv(env_key):
                # 型変換
                attr_type = type(getattr(config, attr_name))
                if attr_type == bool:
                    value = env_value.lower() in ("true", "1", "yes")
                elif attr_type == int:
                    value = int(env_value)
                elif attr_type == float:
                    value = float(env_value)
                else:
                    value = env_value
                
                setattr(config, attr_name, value)
        
        return config
    
    @classmethod
    def from_file(cls, config_file: str) -> "TestConfig":
        """設定ファイルから読み込む"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_file}")
        
        # ファイル形式に応じて読み込み
        if config_path.suffix == ".json":
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        elif config_path.suffix in (".yml", ".yaml"):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        else:
            raise ValueError(f"サポートされていないファイル形式: {config_path.suffix}")
        
        return cls(**config_data)
    
    def validate(self) -> bool:
        """設定の妥当性を検証"""
        errors = []
        
        # 必須のAPIキーチェック
        if not self.finnhub_api_key:
            errors.append("FINNHUB_API_KEY が設定されていません")
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY が設定されていません")
        
        # URLの形式チェック
        if not self.base_url.startswith(("http://", "https://")):
            errors.append(f"無効なURL形式: {self.base_url}")
        
        # ブラウザの妥当性チェック
        valid_browsers = ["chromium", "firefox", "webkit"]
        if self.browser not in valid_browsers:
            errors.append(f"無効なブラウザ: {self.browser} (有効: {', '.join(valid_browsers)})")
        
        if errors:
            print("❌ 設定エラー:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def get_browser_context_args(self) -> Dict[str, Any]:
        """Playwright のブラウザコンテキスト用の引数を取得"""
        args = {
            "viewport": {"width": 1920, "height": 1080},
            "ignore_https_errors": True,
        }
        
        if self.video_on_failure:
            args["record_video_dir"] = self.video_dir
            args["record_video_size"] = {"width": 1920, "height": 1080}
        
        return args
    
    def get_test_data_path(self, filename: str) -> Path:
        """テストデータファイルのパスを取得"""
        return Path(self.test_data_dir) / filename
    
    def save_to_file(self, output_file: str):
        """設定をファイルに保存"""
        output_path = Path(output_file)
        config_dict = {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }
        
        if output_path.suffix == ".json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
        elif output_path.suffix in (".yml", ".yaml"):
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)


# シングルトンインスタンス
_config_instance: Optional[TestConfig] = None


def get_test_config() -> TestConfig:
    """テスト設定のシングルトンインスタンスを取得"""
    global _config_instance
    
    if _config_instance is None:
        # 優先順位: 環境変数 > 設定ファイル > デフォルト
        config_file = os.getenv("E2E_CONFIG_FILE")
        
        if config_file and Path(config_file).exists():
            _config_instance = TestConfig.from_file(config_file)
        else:
            _config_instance = TestConfig.from_env()
        
        # 設定の検証
        if not _config_instance.validate():
            raise ValueError("テスト設定の検証に失敗しました")
    
    return _config_instance


# 環境別の設定プリセット
class TestEnvironments:
    """環境別の設定プリセット"""
    
    @staticmethod
    def local() -> TestConfig:
        """ローカル開発環境用の設定"""
        return TestConfig(
            headless=False,
            timeout=60000,
            retry_count=2,
            parallel_workers=2,
        )
    
    @staticmethod
    def ci() -> TestConfig:
        """CI環境用の設定"""
        return TestConfig(
            headless=True,
            timeout=30000,
            retry_count=3,
            parallel_workers=4,
            screenshot_on_failure=True,
            video_on_failure=True,
        )
    
    @staticmethod
    def performance() -> TestConfig:
        """パフォーマンステスト用の設定"""
        return TestConfig(
            headless=True,
            timeout=120000,
            retry_count=1,
            test_mode="performance",
        )


# 使用例
"""
from tests.e2e.config.test_config import get_test_config, TestEnvironments

# デフォルト設定を使用
config = get_test_config()

# CI環境用の設定を使用
ci_config = TestEnvironments.ci()

# 設定をファイルに保存
config.save_to_file("tests/e2e/config/test_config.json")

# カスタム設定を作成
custom_config = TestConfig(
    base_url="https://staging.example.com",
    browser="firefox",
    headless=True,
)
"""