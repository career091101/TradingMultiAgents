# バックテスト最適化オプション

## 実装可能な最適化オプション

### 1. 簡易分析モード
エージェント数を減らして高速化

```python
class BacktestSimulator:
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 debug: bool = False,
                 fast_mode: bool = False):  # 新規追加
        
        if fast_mode:
            # 最小限のエージェントのみ使用
            base_config.update({
                "use_minimal_agents": True,
                "skip_risk_analysis": True,
                "max_debate_rounds": 0,  # 議論をスキップ
                "max_risk_discuss_rounds": 0
            })
```

### 2. 判断結果キャッシング
同じ条件の判断結果を保存して再利用

```python
import pickle
import hashlib

class DecisionCache:
    def __init__(self, cache_dir="./backtest/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_key(self, ticker: str, date: str, config: dict) -> str:
        """キャッシュキーを生成"""
        cache_data = f"{ticker}_{date}_{str(sorted(config.items()))}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def get(self, ticker: str, date: str, config: dict) -> Optional[str]:
        """キャッシュから判断結果を取得"""
        key = self.get_cache_key(ticker, date, config)
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def set(self, ticker: str, date: str, config: dict, decision: str):
        """判断結果をキャッシュに保存"""
        key = self.get_cache_key(ticker, date, config)
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        
        with open(cache_file, 'wb') as f:
            pickle.dump(decision, f)
```

### 3. サンプリングモード
全取引日ではなく、一定間隔でサンプリング

```python
def run_backtest(self, ticker: str, start_date: str, end_date: str,
                initial_capital: float = 10000.0, slippage: float = 0.0,
                sampling_interval: int = 1) -> BacktestResult:  # 新規追加
    
    # データ取得後
    if sampling_interval > 1:
        # N日ごとにサンプリング
        hist_data = hist_data.iloc[::sampling_interval]
        logger.info(f"Sampling every {sampling_interval} days")
```

### 4. バッチ処理モード
複数の判断を一度に処理

```python
def _get_batch_decisions(self, ticker: str, dates: List[str]) -> Dict[str, str]:
    """複数日の判断をバッチで取得"""
    # LLMへのリクエストを統合
    batch_prompt = f"Analyze {ticker} for the following dates and provide trading decisions:\n"
    for date in dates:
        batch_prompt += f"- {date}\n"
    
    # 一度のAPI呼び出しで複数の判断を取得
    response = self.agent.batch_propagate(ticker, dates)
    return response
```

### 5. 並列処理
複数の銘柄や日付を並列で処理

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

def run_parallel_backtest(self, tickers: List[str], start_date: str, 
                         end_date: str, max_workers: int = 4):
    """複数銘柄を並列でバックテスト"""
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for ticker in tickers:
            future = executor.submit(
                self.run_backtest, ticker, start_date, end_date
            )
            futures.append((ticker, future))
        
        results = {}
        for ticker, future in futures:
            results[ticker] = future.result()
    
    return results
```

### 6. 軽量LLMモード
高速な推論用の軽量モデルを使用

```python
FAST_BACKTEST_CONFIG = {
    "deep_think_llm": "gpt-4o-mini",  # より高速なモデル
    "quick_think_llm": "gpt-3.5-turbo",  # 最速モデル
    "temperature": 0,  # 決定論的な出力
    "max_tokens": 100  # 短い応答
}
```

## 実装優先順位

1. **キャッシング** - 最も効果的、同じ分析の繰り返しを避ける
2. **簡易分析モード** - エージェント数削減で大幅な高速化
3. **サンプリングモード** - 長期間のバックテストに有効
4. **並列処理** - 複数銘柄の同時処理
5. **バッチ処理** - API呼び出し回数の削減
6. **軽量LLMモード** - コストと速度のバランス

## 使用例

```python
# 高速バックテストの例
simulator = BacktestSimulator(
    config={
        "max_debate_rounds": 0,
        "use_minimal_agents": True,
        "quick_think_llm": "gpt-3.5-turbo"
    },
    fast_mode=True
)

# キャッシュ付きバックテスト
simulator.enable_cache()
result = simulator.run_backtest("AAPL", "2023-01-01", "2023-12-31")

# サンプリングバックテスト（5日ごと）
result = simulator.run_backtest(
    "AAPL", "2023-01-01", "2023-12-31",
    sampling_interval=5
)
```