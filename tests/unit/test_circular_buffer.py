"""
CircularBuffer クラスのユニットテスト
メモリリーク防止の核心機能をテスト
"""

import pytest
from concurrent.futures import ThreadPoolExecutor
import threading
from backtest2.utils.memory_manager import CircularBuffer


class TestCircularBuffer:
    """CircularBufferの包括的なテスト"""
    
    def test_append_within_capacity(self):
        """容量内でのアイテム追加"""
        buffer = CircularBuffer(max_size=5)
        
        # 容量内で追加
        for i in range(3):
            buffer.append(f"item_{i}")
        
        assert len(buffer) == 3
        assert buffer.get_all() == ["item_0", "item_1", "item_2"]
    
    def test_append_exceeds_capacity(self):
        """容量超過時の動作（古いアイテムが削除される）"""
        buffer = CircularBuffer(max_size=3)
        
        # 容量を超えて追加
        for i in range(5):
            buffer.append(f"item_{i}")
        
        # 最新の3つのみ保持
        assert len(buffer) == 3
        assert buffer.get_all() == ["item_2", "item_3", "item_4"]
    
    def test_get_all_returns_list(self):
        """get_all()が通常のリストを返すことを確認"""
        buffer = CircularBuffer(max_size=5)
        buffer.append("test")
        
        result = buffer.get_all()
        assert isinstance(result, list)
        assert result == ["test"]
        
        # リストは独立していることを確認
        result.append("extra")
        assert len(buffer.get_all()) == 1  # 元のバッファは変更されない
    
    def test_get_last_n_items(self):
        """最後のn個のアイテムを取得"""
        buffer = CircularBuffer(max_size=10)
        
        for i in range(10):
            buffer.append(i)
        
        # 最後の3個
        assert buffer.get_last(3) == [7, 8, 9]
        
        # バッファサイズより多く要求
        assert buffer.get_last(15) == list(range(10))
        
        # 0個要求
        assert buffer.get_last(0) == []
    
    def test_len_method(self):
        """__len__メソッドの動作確認"""
        buffer = CircularBuffer(max_size=5)
        
        assert len(buffer) == 0
        
        buffer.append("item1")
        assert len(buffer) == 1
        
        for i in range(10):
            buffer.append(f"item_{i}")
        assert len(buffer) == 5  # 最大サイズで制限
    
    def test_clear_buffer(self):
        """バッファのクリア機能"""
        buffer = CircularBuffer(max_size=5)
        
        for i in range(5):
            buffer.append(i)
        
        assert len(buffer) == 5
        
        buffer.clear()
        assert len(buffer) == 0
        assert buffer.get_all() == []
    
    def test_iteration_not_supported(self):
        """直接イテレーションがサポートされていないことを確認"""
        buffer = CircularBuffer(max_size=5)
        buffer.append("test")
        
        # CircularBufferは直接イテレーションをサポートしない
        with pytest.raises(TypeError):
            for item in buffer:
                pass
    
    def test_thread_safety(self):
        """スレッドセーフ性のテスト"""
        buffer = CircularBuffer(max_size=1000)
        errors = []
        
        def append_items(start, count):
            try:
                for i in range(count):
                    buffer.append(f"thread_{start}_{i}")
            except Exception as e:
                errors.append(e)
        
        # 複数スレッドから同時に追加
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(10):
                future = executor.submit(append_items, i * 100, 100)
                futures.append(future)
            
            # 全スレッドの完了を待つ
            for future in futures:
                future.result()
        
        # エラーがないことを確認
        assert len(errors) == 0
        
        # バッファサイズが最大値を超えていないことを確認
        assert len(buffer) <= 1000
    
    def test_different_data_types(self):
        """異なるデータ型の格納"""
        buffer = CircularBuffer(max_size=10)
        
        # 様々な型のデータを追加
        buffer.append(42)  # int
        buffer.append(3.14)  # float
        buffer.append("string")  # str
        buffer.append([1, 2, 3])  # list
        buffer.append({"key": "value"})  # dict
        buffer.append(None)  # None
        
        items = buffer.get_all()
        assert len(items) == 6
        assert items[0] == 42
        assert items[1] == 3.14
        assert items[2] == "string"
        assert items[3] == [1, 2, 3]
        assert items[4] == {"key": "value"}
        assert items[5] is None
    
    def test_memory_efficiency(self):
        """メモリ効率性のテスト（大量データ）"""
        buffer = CircularBuffer(max_size=10000)
        
        # 100万個のアイテムを追加（10000個のみ保持される）
        for i in range(1000000):
            buffer.append(f"item_{i}")
        
        # 最大サイズのみ保持されている
        assert len(buffer) == 10000
        
        # 最新の10000個が保持されている
        all_items = buffer.get_all()
        assert all_items[0] == "item_990000"
        assert all_items[-1] == "item_999999"


class TestCircularBufferEdgeCases:
    """CircularBufferのエッジケーステスト"""
    
    def test_zero_capacity(self):
        """容量0の場合の動作"""
        with pytest.raises(ValueError):
            CircularBuffer(max_size=0)
    
    def test_negative_capacity(self):
        """負の容量の場合"""
        with pytest.raises(ValueError):
            CircularBuffer(max_size=-1)
    
    def test_single_capacity(self):
        """容量1の場合の動作"""
        buffer = CircularBuffer(max_size=1)
        
        buffer.append("first")
        assert buffer.get_all() == ["first"]
        
        buffer.append("second")
        assert buffer.get_all() == ["second"]  # firstは削除される
    
    def test_get_last_with_empty_buffer(self):
        """空のバッファでget_last"""
        buffer = CircularBuffer(max_size=5)
        assert buffer.get_last(3) == []
    
    def test_massive_capacity(self):
        """非常に大きな容量"""
        buffer = CircularBuffer(max_size=1000000)
        
        # 少数のアイテムを追加
        for i in range(10):
            buffer.append(i)
        
        assert len(buffer) == 10
        assert buffer.get_all() == list(range(10))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])