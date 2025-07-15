"""
Python 3.13互換性のためのパスユーティリティ
"""

from pathlib import Path
import sys

def is_relative_to(path1: Path, path2: Path) -> bool:
    """
    path1がpath2の相対パスかどうかを判定（Python 3.9+互換）
    """
    if sys.version_info >= (3, 9):
        # Python 3.9以上ではis_relative_toメソッドが利用可能
        return path1.is_relative_to(path2)
    else:
        # Python 3.8以下では手動で判定
        try:
            path1.relative_to(path2)
            return True
        except ValueError:
            return False

def safe_relative_to(path1: Path, path2: Path, fallback=None) -> str:
    """
    安全に相対パスを取得。取得できない場合はfallbackまたは絶対パスを返す
    """
    try:
        if is_relative_to(path1, path2):
            return str(path1.relative_to(path2))
        else:
            return fallback if fallback is not None else str(path1)
    except Exception:
        return fallback if fallback is not None else str(path1)