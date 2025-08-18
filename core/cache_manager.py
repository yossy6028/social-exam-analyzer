"""
キャッシングシステム
処理結果をキャッシュして重複処理を削減
"""

import json
import hashlib
import logging
import pickle
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from functools import wraps
import threading
from collections import OrderedDict

from core.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """キャッシュエントリ"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """有効期限切れかチェック"""
        if ttl_seconds <= 0:
            return False
        return time.time() - self.created_at > ttl_seconds
    
    def touch(self):
        """アクセス時刻を更新"""
        self.accessed_at = time.time()
        self.access_count += 1


class CacheManager:
    """キャッシュマネージャー"""
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_size_mb: int = 100,
        ttl_seconds: int = 3600,
        max_entries: int = 1000
    ):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリ
            max_size_mb: 最大キャッシュサイズ（MB）
            ttl_seconds: キャッシュ有効期限（秒）
            max_entries: 最大エントリ数
        """
        self.config = get_config()
        self.cache_dir = cache_dir or self.config.paths.cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        
        # メモリキャッシュ（LRU）
        self.memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.cache_lock = threading.RLock()
        
        # 統計情報
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_size_bytes': 0
        }
        
        # キャッシュディレクトリを作成
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 永続化キャッシュを読み込み
        self._load_persistent_cache()
    
    def get(self, key: str) -> Optional[Any]:
        """
        キャッシュから取得
        
        Args:
            key: キャッシュキー
            
        Returns:
            キャッシュされた値（存在しない場合はNone）
        """
        with self.cache_lock:
            # メモリキャッシュをチェック
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                
                # 有効期限チェック
                if entry.is_expired(self.ttl_seconds):
                    self._evict(key)
                    self.stats['misses'] += 1
                    return None
                
                # LRU更新
                self.memory_cache.move_to_end(key)
                entry.touch()
                
                self.stats['hits'] += 1
                logger.debug(f"Cache hit: {key[:20]}...")
                return entry.value
            
            # ディスクキャッシュをチェック
            disk_value = self._get_from_disk(key)
            if disk_value is not None:
                # メモリキャッシュに追加
                self._add_to_memory(key, disk_value)
                self.stats['hits'] += 1
                return disk_value
            
            self.stats['misses'] += 1
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        キャッシュに保存
        
        Args:
            key: キャッシュキー
            value: 保存する値
            metadata: メタデータ
            
        Returns:
            保存成功かどうか
        """
        try:
            # サイズを計算
            size_bytes = self._calculate_size(value)
            
            # サイズ制限チェック
            if size_bytes > self.max_size_bytes:
                logger.warning(f"Value too large to cache: {size_bytes} bytes")
                return False
            
            with self.cache_lock:
                # 容量を確保
                self._ensure_capacity(size_bytes)
                
                # エントリを作成
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=time.time(),
                    accessed_at=time.time(),
                    size_bytes=size_bytes,
                    metadata=metadata or {}
                )
                
                # メモリキャッシュに追加
                self.memory_cache[key] = entry
                self.stats['total_size_bytes'] += size_bytes
                
                # ディスクに永続化（非同期）
                threading.Thread(
                    target=self._save_to_disk,
                    args=(key, value),
                    daemon=True
                ).start()
                
                logger.debug(f"Cached: {key[:20]}... ({size_bytes} bytes)")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cache {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        キャッシュから削除
        
        Args:
            key: キャッシュキー
            
        Returns:
            削除成功かどうか
        """
        with self.cache_lock:
            if key in self.memory_cache:
                self._evict(key)
                self._delete_from_disk(key)
                return True
            return False
    
    def clear(self):
        """全キャッシュをクリア"""
        with self.cache_lock:
            self.memory_cache.clear()
            self.stats['total_size_bytes'] = 0
            self.stats['evictions'] = 0
            
            # ディスクキャッシュもクリア
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"Failed to delete {cache_file}: {e}")
        
        logger.info("Cache cleared")
    
    def _ensure_capacity(self, required_bytes: int):
        """
        必要な容量を確保
        
        Args:
            required_bytes: 必要なバイト数
        """
        # エントリ数制限
        while len(self.memory_cache) >= self.max_entries:
            self._evict_lru()
        
        # サイズ制限
        while (self.stats['total_size_bytes'] + required_bytes > self.max_size_bytes
               and self.memory_cache):
            self._evict_lru()
    
    def _evict_lru(self):
        """LRUエントリを削除"""
        if not self.memory_cache:
            return
        
        # 最も古いエントリを削除
        key, entry = self.memory_cache.popitem(last=False)
        self.stats['total_size_bytes'] -= entry.size_bytes
        self.stats['evictions'] += 1
        logger.debug(f"Evicted LRU: {key[:20]}...")
    
    def _evict(self, key: str):
        """特定のエントリを削除"""
        if key in self.memory_cache:
            entry = self.memory_cache.pop(key)
            self.stats['total_size_bytes'] -= entry.size_bytes
            self.stats['evictions'] += 1
    
    def _add_to_memory(self, key: str, value: Any):
        """メモリキャッシュに追加"""
        size_bytes = self._calculate_size(value)
        self._ensure_capacity(size_bytes)
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            accessed_at=time.time(),
            size_bytes=size_bytes
        )
        
        self.memory_cache[key] = entry
        self.stats['total_size_bytes'] += size_bytes
    
    def _calculate_size(self, value: Any) -> int:
        """オブジェクトのサイズを計算"""
        try:
            return len(pickle.dumps(value))
        except Exception:
            # pickle化できない場合は概算
            return len(str(value).encode())
    
    def _get_cache_file_path(self, key: str) -> Path:
        """キャッシュファイルパスを取得"""
        # キーをハッシュ化してファイル名にする
        file_name = hashlib.md5(key.encode()).hexdigest() + ".cache"
        return self.cache_dir / file_name
    
    def _save_to_disk(self, key: str, value: Any):
        """ディスクに保存"""
        try:
            cache_file = self._get_cache_file_path(key)
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'key': key,
                    'value': value,
                    'timestamp': time.time()
                }, f)
        except Exception as e:
            logger.error(f"Failed to save to disk: {e}")
    
    def _get_from_disk(self, key: str) -> Optional[Any]:
        """ディスクから取得"""
        try:
            cache_file = self._get_cache_file_path(key)
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            
            # 有効期限チェック
            if time.time() - data['timestamp'] > self.ttl_seconds:
                cache_file.unlink()
                return None
            
            return data['value']
            
        except Exception as e:
            logger.error(f"Failed to load from disk: {e}")
            return None
    
    def _delete_from_disk(self, key: str):
        """ディスクから削除"""
        try:
            cache_file = self._get_cache_file_path(key)
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            logger.error(f"Failed to delete from disk: {e}")
    
    def _load_persistent_cache(self):
        """永続化キャッシュを読み込み"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    
                    # 有効期限チェック
                    if time.time() - data['timestamp'] <= self.ttl_seconds:
                        self._add_to_memory(data['key'], data['value'])
                    else:
                        cache_file.unlink()
                        
                except Exception as e:
                    logger.error(f"Failed to load {cache_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load persistent cache: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        with self.cache_lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100
                       if total_requests > 0 else 0)
            
            return {
                **self.stats,
                'hit_rate': hit_rate,
                'entry_count': len(self.memory_cache),
                'size_mb': self.stats['total_size_bytes'] / 1024 / 1024,
                'max_size_mb': self.max_size_bytes / 1024 / 1024
            }


def cached(
    cache_manager: Optional[CacheManager] = None,
    key_func: Optional[Callable] = None,
    ttl_seconds: Optional[int] = None
):
    """
    キャッシュデコレータ
    
    Args:
        cache_manager: キャッシュマネージャー
        key_func: キャッシュキー生成関数
        ttl_seconds: キャッシュ有効期限
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # キャッシュマネージャーを取得
            cm = cache_manager
            if cm is None:
                # グローバルキャッシュマネージャーを使用
                cm = get_global_cache_manager()
            
            # キャッシュが無効な場合は直接実行
            config = get_config()
            if not config.processing.cache_enabled:
                return func(*args, **kwargs)
            
            # キャッシュキーを生成
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # デフォルトのキー生成
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = "|".join(key_parts)
            
            # キャッシュから取得
            cached_value = cm.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 関数を実行
            result = func(*args, **kwargs)
            
            # キャッシュに保存
            cm.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator


# グローバルキャッシュマネージャー
_global_cache_manager: Optional[CacheManager] = None


def get_global_cache_manager() -> CacheManager:
    """グローバルキャッシュマネージャーを取得"""
    global _global_cache_manager
    if _global_cache_manager is None:
        config = get_config()
        _global_cache_manager = CacheManager(
            cache_dir=config.paths.cache_dir,
            ttl_seconds=config.processing.cache_ttl_seconds
        )
    return _global_cache_manager


def reset_global_cache_manager():
    """グローバルキャッシュマネージャーをリセット"""
    global _global_cache_manager
    if _global_cache_manager:
        _global_cache_manager.clear()
    _global_cache_manager = None


# 使用例
@cached()
def expensive_operation(x: int, y: int) -> int:
    """高コストな処理の例"""
    import time
    time.sleep(1)  # 重い処理をシミュレート
    return x * y


if __name__ == "__main__":
    # テスト
    cache = CacheManager(max_size_mb=10, ttl_seconds=60)
    
    # 値を設定
    cache.set("key1", {"data": "value1"})
    cache.set("key2", [1, 2, 3, 4, 5])
    
    # 値を取得
    print(cache.get("key1"))  # {'data': 'value1'}
    print(cache.get("key2"))  # [1, 2, 3, 4, 5]
    print(cache.get("key3"))  # None
    
    # 統計を表示
    stats = cache.get_statistics()
    print(f"Hit rate: {stats['hit_rate']:.1f}%")
    print(f"Cache size: {stats['size_mb']:.2f} MB")
    
    # デコレータの使用例
    result1 = expensive_operation(5, 10)  # 1秒かかる
    result2 = expensive_operation(5, 10)  # キャッシュから即座に返す
    
    print(f"Results: {result1}, {result2}")