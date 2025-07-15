"""
Streamlit用のセレクタヘルパー
Streamlitの構造に基づいて安定したセレクタを提供
"""

from typing import Optional


class StreamlitSelectors:
    """Streamlit要素のセレクタを生成するヘルパークラス"""
    
    @staticmethod
    def button(key: str, text: Optional[str] = None) -> str:
        """
        ボタンのセレクタを生成
        
        Args:
            key: StreamlitコンポーネントのKey
            text: ボタンのテキスト（オプション）
        
        Returns:
            セレクタ文字列
        """
        if text:
            return f'button:has-text("{text}")'
        return f'[data-testid="stButton"] button'
    
    @staticmethod
    def button_by_key(key: str) -> str:
        """特定のkeyを持つボタンのセレクタ"""
        # Streamlitは内部的にkeyをdata-testidやaria-labelに設定することがある
        return f'[data-testid*="{key}"] button, button[aria-label*="{key}"], button[key="{key}"]'
    
    @staticmethod
    def text_input(label: str) -> str:
        """
        テキスト入力フィールドのセレクタ
        
        Args:
            label: 入力フィールドのラベル
        
        Returns:
            セレクタ文字列
        """
        return f'[data-testid="stTextInput"] input'
    
    @staticmethod
    def select_box(label: str) -> str:
        """セレクトボックスのセレクタ"""
        return f'[data-testid="stSelectbox"]'
    
    @staticmethod
    def sidebar() -> str:
        """サイドバーのセレクタ"""
        return '[data-testid="stSidebar"]'
    
    @staticmethod
    def metric(label: str) -> str:
        """メトリック要素のセレクタ"""
        return f'[data-testid="stMetric"]'
    
    @staticmethod
    def expander(label: str) -> str:
        """エクスパンダーのセレクタ"""
        return f'[data-testid="stExpander"] summary:has-text("{label}")'
    
    @staticmethod
    def dataframe() -> str:
        """データフレームのセレクタ"""
        return '[data-testid="stDataFrame"]'
    
    @staticmethod
    def markdown_with_text(text: str) -> str:
        """特定のテキストを含むマークダウン要素"""
        return f'[data-testid="stMarkdown"] >> text="{text}"'
    
    @staticmethod
    def progress_bar() -> str:
        """プログレスバーのセレクタ"""
        return '[data-testid="stProgress"]'
    
    @staticmethod
    def alert(severity: str = "info") -> str:
        """
        アラート要素のセレクタ
        
        Args:
            severity: "info", "warning", "error", "success"
        """
        return f'[data-testid="stAlert"][data-baseweb="notification"][kind="{severity}"]'
    
    @staticmethod
    def spinner() -> str:
        """スピナー（ローディング）のセレクタ"""
        return '[data-testid="stSpinner"]'
    
    @staticmethod
    def file_uploader() -> str:
        """ファイルアップローダーのセレクタ"""
        return '[data-testid="stFileUploader"]'
    
    @staticmethod
    def checkbox(label: str) -> str:
        """チェックボックスのセレクタ"""
        return f'[data-testid="stCheckbox"] label:has-text("{label}")'
    
    @staticmethod
    def radio(label: str) -> str:
        """ラジオボタンのセレクタ"""
        return f'[data-testid="stRadio"] label:has-text("{label}")'
    
    @staticmethod
    def slider() -> str:
        """スライダーのセレクタ"""
        return '[data-testid="stSlider"] [role="slider"]'
    
    # ナビゲーション関連のセレクタ
    @staticmethod
    def nav_button(page: str) -> str:
        """ナビゲーションボタンのセレクタ"""
        mapping = {
            "dashboard": "ダッシュボード",
            "settings": "分析設定",
            "execution": "分析実行",
            "results": "結果表示"
        }
        text = mapping.get(page, page)
        return f'{StreamlitSelectors.sidebar()} button:has-text("{text}")'
    
    # 特定のページ要素
    @staticmethod
    def dashboard_stat(stat_type: str) -> str:
        """ダッシュボードの統計要素"""
        return f'[data-testid="stMetric"] >> text="{stat_type}"'
    
    @staticmethod
    def settings_input(input_type: str) -> str:
        """設定ページの入力要素"""
        mapping = {
            "ticker": "ティッカーシンボル",
            "date": "分析日",
            "api_key": "APIキー"
        }
        label = mapping.get(input_type, input_type)
        return f'text="{label}" >> xpath=../.. >> input'
    
    @staticmethod
    def execution_status() -> str:
        """実行ステータス要素"""
        return '[data-testid="stProgress"], [data-testid="stSpinner"]'
    
    @staticmethod
    def execution_button(action: str) -> str:
        """実行ページの特定アクションボタン"""
        mapping = {
            "start": "exec_start_analysis",
            "stop": "exec_stop_analysis", 
            "refresh": "exec_refresh",
            "settings": "exec_change_settings",
            "dashboard": "exec_to_home"
        }
        key = mapping.get(action, action)
        return StreamlitSelectors.button_by_key(key)
    
    @staticmethod
    def results_section(section: str) -> str:
        """結果ページのセクション"""
        return f'[data-testid="stExpander"] summary:has-text("{section}")'


class StreamlitPageObjects:
    """ページオブジェクトパターン用のヘルパー"""
    
    def __init__(self, page):
        self.page = page
        self.selectors = StreamlitSelectors()
    
    async def navigate_to(self, page_name: str):
        """特定のページへナビゲート"""
        await self.page.click(self.selectors.nav_button(page_name))
        await self.page.wait_for_load_state("networkidle")
    
    async def wait_for_element(self, selector: str, state: str = "visible"):
        """要素の待機"""
        await self.page.wait_for_selector(selector, state=state)
    
    async def fill_input(self, label: str, value: str):
        """入力フィールドに値を入力"""
        input_selector = self.selectors.text_input(label)
        await self.page.fill(input_selector, value)
    
    async def click_button(self, text: str):
        """ボタンをクリック"""
        button_selector = self.selectors.button(text=text)
        await self.page.click(button_selector)
    
    async def select_option(self, label: str, value: str):
        """セレクトボックスで選択"""
        select_selector = self.selectors.select_box(label)
        await self.page.click(select_selector)
        await self.page.click(f'[role="option"]:has-text("{value}")')
    
    async def expand_section(self, label: str):
        """エクスパンダーを展開"""
        expander_selector = self.selectors.expander(label)
        await self.page.click(expander_selector)
    
    async def get_metric_value(self, label: str) -> str:
        """メトリックの値を取得"""
        metric_selector = f'{self.selectors.metric(label)} [data-testid="stMetricValue"]'
        return await self.page.text_content(metric_selector)
    
    async def wait_for_analysis_complete(self):
        """分析完了を待機"""
        # スピナーが消えるまで待機
        await self.wait_for_element(self.selectors.spinner(), state="hidden")
        # プログレスバーが100%になるまで待機
        progress_selector = self.selectors.progress_bar()
        await self.page.wait_for_function(
            f'document.querySelector("{progress_selector}")?.getAttribute("aria-valuenow") === "100"'
        )


# 使用例
"""
from tests.e2e.utils.streamlit_selectors import StreamlitSelectors, StreamlitPageObjects

# セレクタの使用
selectors = StreamlitSelectors()
dashboard_button = selectors.nav_button("dashboard")
await page.click(dashboard_button)

# ページオブジェクトの使用
page_obj = StreamlitPageObjects(page)
await page_obj.navigate_to("settings")
await page_obj.fill_input("ティッカーシンボル", "AAPL")
await page_obj.click_button("分析を実行")
"""