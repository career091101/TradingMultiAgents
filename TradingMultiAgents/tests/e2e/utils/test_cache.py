"""
E2Eテスト用のキャッシュ機構
テストの高速化とリソース節約を実現
"""

import json
import pickle
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union, Callable
from functools import wraps
from datetime import datetime, timedelta
import threading
from contextlib import contextmanager


class TestCache:
    """テスト用キャッシュクラス"""
    
    def __init__(self, cache_dir: str = "tests/e2e/.cache", ttl: int = 3600):
        """
        Args:
            cache_dir: キャッシュディレクトリ
            ttl: キャッシュの有効期限（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self.memory_cache: Dict[str, Any] = {}
        self.lock = threading.Lock()
        
        # キャッシュ統計
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "saves": 0
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """キャッシュから値を取得"""
        with self.lock:
            # メモリキャッシュをチェック
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if self._is_valid(entry):
                    self.stats["hits"] += 1
                    return entry["value"]
                else:
                    del self.memory_cache[key]
                    self.stats["evictions"] += 1
            
            # ディスクキャッシュをチェック
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                    
                    if self._is_valid(entry):
                        # メモリキャッシュに追加
                        self.memory_cache[key] = entry
                        self.stats["hits"] += 1
                        return entry["value"]
                    else:
                        # 期限切れのファイルを削除
                        cache_file.unlink()
                        self.stats["evictions"] += 1
                except Exception as e:
                    print(f"キャッシュ読み込みエラー: {e}")
            
            self.stats["misses"] += 1
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """キャッシュに値を保存"""
        with self.lock:
            entry = {
                "value": value,
                "timestamp": time.time(),
                "ttl": ttl or self.ttl
            }
            
            # メモリキャッシュに保存
            self.memory_cache[key] = entry
            
            # ディスクキャッシュに保存
            cache_file = self._get_cache_file(key)
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(entry, f)
                self.stats["saves"] += 1
            except Exception as e:
                print(f"キャッシュ保存エラー: {e}")
    
    def delete(self, key: str):
        """キャッシュから削除"""
        with self.lock:
            # メモリキャッシュから削除
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # ディスクキャッシュから削除
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                cache_file.unlink()
    
    def clear(self):
        """全キャッシュをクリア"""
        with self.lock:
            self.memory_cache.clear()
            
            # すべてのキャッシュファイルを削除
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
    
    def cleanup(self):
        """期限切れのキャッシュをクリーンアップ"""
        with self.lock:
            # メモリキャッシュのクリーンアップ
            expired_keys = []
            for key, entry in self.memory_cache.items():
                if not self._is_valid(entry):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.memory_cache[key]
                self.stats["evictions"] += 1
            
            # ディスクキャッシュのクリーンアップ
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                    
                    if not self._is_valid(entry):
                        cache_file.unlink()
                        self.stats["evictions"] += 1
                except:
                    # 読み込めないファイルは削除
                    cache_file.unlink()
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate": f"{hit_rate:.1f}%",
            "memory_cache_size": len(self.memory_cache),
            "disk_cache_size": len(list(self.cache_dir.glob("*.cache")))
        }
    
    def _get_cache_file(self, key: str) -> Path:
        """キャッシュファイルのパスを取得"""
        # キーをハッシュ化してファイル名に使用
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _is_valid(self, entry: Dict[str, Any]) -> bool:
        """キャッシュエントリが有効かチェック"""
        elapsed = time.time() - entry["timestamp"]
        return elapsed < entry["ttl"]
    
    # デコレーター
    def cached(self, ttl: Optional[int] = None):
        """関数の結果をキャッシュするデコレーター"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # キャッシュキーを生成
                cache_key = self._generate_cache_key(func, args, kwargs)
                
                # キャッシュから取得を試みる
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 関数を実行
                result = func(*args, **kwargs)
                
                # 結果をキャッシュ
                self.set(cache_key, result, ttl)
                
                return result
            
            wrapper.clear_cache = lambda: self.delete(
                self._generate_cache_key(func, (), {})
            )
            
            return wrapper
        return decorator
    
    def _generate_cache_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """関数呼び出しのキャッシュキーを生成"""
        key_parts = [
            func.__module__,
            func.__name__,
            str(args),
            str(sorted(kwargs.items()))
        ]
        return ":".join(key_parts)


class PageStateCache:
    """ページ状態のキャッシュ"""
    
    def __init__(self, cache: TestCache):
        self.cache = cache
    
    def save_page_state(self, page, state_name: str):
        """ページの状態を保存"""
        state = {
            "url": page.url,
            "cookies": page.context.cookies(),
            "local_storage": self._get_local_storage(page),
            "session_storage": self._get_session_storage(page)
        }
        
        self.cache.set(f"page_state:{state_name}", state, ttl=3600)
    
    def restore_page_state(self, page, state_name: str) -> bool:
        """ページの状態を復元"""
        state = self.cache.get(f"page_state:{state_name}")
        if not state:
            return False
        
        try:
            # URLに移動
            if page.url != state["url"]:
                page.goto(state["url"])
            
            # Cookieを復元
            page.context.add_cookies(state["cookies"])
            
            # LocalStorageを復元
            self._set_local_storage(page, state["local_storage"])
            
            # SessionStorageを復元
            self._set_session_storage(page, state["session_storage"])
            
            return True
            
        except Exception as e:
            print(f"ページ状態の復元エラー: {e}")
            return False
    
    def _get_local_storage(self, page) -> Dict[str, str]:
        """LocalStorageの内容を取得"""
        return page.evaluate("""
            () => {
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            }
        """)
    
    def _set_local_storage(self, page, items: Dict[str, str]):
        """LocalStorageに値を設定"""
        page.evaluate("""
            (items) => {
                localStorage.clear();
                Object.entries(items).forEach(([key, value]) => {
                    localStorage.setItem(key, value);
                });
            }
        """, items)
    
    def _get_session_storage(self, page) -> Dict[str, str]:
        """SessionStorageの内容を取得"""
        return page.evaluate("""
            () => {
                const items = {};
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    items[key] = sessionStorage.getItem(key);
                }
                return items;
            }
        """)
    
    def _set_session_storage(self, page, items: Dict[str, str]):
        """SessionStorageに値を設定"""
        page.evaluate("""
            (items) => {
                sessionStorage.clear();
                Object.entries(items).forEach(([key, value]) => {
                    sessionStorage.setItem(key, value);
                });
            }
        """, items)


class TestDataCache:
    """テストデータのキャッシュ"""
    
    def __init__(self, cache: TestCache):
        self.cache = cache
    
    @contextmanager
    def cached_api_response(self, url: str, ttl: int = 3600):
        """APIレスポンスをキャッシュ"""
        cache_key = f"api_response:{url}"
        
        # キャッシュから取得
        cached_response = self.cache.get(cache_key)
        if cached_response:
            yield cached_response
            return
        
        # 実際のAPIコールを記録
        responses = []
        
        def intercept_response(response):
            if response.url == url:
                response_data = {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body": response.body()
                }
                responses.append(response_data)
        
        yield intercept_response
        
        # レスポンスをキャッシュ
        if responses:
            self.cache.set(cache_key, responses[0], ttl)
    
    def get_cached_test_data(self, data_key: str, generator: Callable) -> Any:
        """テストデータを取得（キャッシュまたは生成）"""
        cache_key = f"test_data:{data_key}"
        
        # キャッシュから取得
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # データを生成
        data = generator()
        
        # キャッシュに保存
        self.cache.set(cache_key, data, ttl=86400)  # 24時間
        
        return data


# グローバルキャッシュインスタンス
_global_cache = None


def get_test_cache() -> TestCache:
    """グローバルキャッシュインスタンスを取得"""
    global _global_cache
    if _global_cache is None:
        _global_cache = TestCache()
    return _global_cache


# 使用例
"""
# 基本的な使用
cache = get_test_cache()
cache.set("key", "value", ttl=3600)
value = cache.get("key")

# デコレーターとして使用
@cache.cached(ttl=3600)
def expensive_operation(param):
    # 時間のかかる処理
    return result

# ページ状態のキャッシュ
page_cache = PageStateCache(cache)
page_cache.save_page_state(page, "logged_in_state")
page_cache.restore_page_state(page, "logged_in_state")

# テストデータのキャッシュ
data_cache = TestDataCache(cache)
test_data = data_cache.get_cached_test_data(
    "user_data",
    lambda: generate_test_users()
)
"""