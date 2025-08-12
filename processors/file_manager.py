"""
ファイル管理モジュール
すべてのファイルI/O操作を中央管理
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Union
import json
import pickle
import logging
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """セキュリティ関連のエラー"""
    pass


class FileManager:
    """
    ファイルI/O操作を中央管理するクラス
    キャッシング、バージョニング、エラーハンドリングを提供
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, 
                 allowed_dirs: Optional[List[Path]] = None):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリ（デフォルトは .cache）
            allowed_dirs: アクセスを許可するディレクトリのリスト
        """
        self.cache_dir = cache_dir or Path.home() / '.cache' / 'entrance_exam_analyzer'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # セキュリティ: 許可されたディレクトリのリスト
        self.allowed_dirs = allowed_dirs or [Path.cwd()]
        self.allowed_dirs = [Path(d).resolve() for d in self.allowed_dirs]
        
        # ファイルキャッシュ
        self._file_cache: Dict[str, any] = {}
        self._cache_metadata: Dict[str, dict] = {}
        
        # 設定
        self.max_cache_size_mb = 100
        self.cache_ttl_seconds = 3600  # 1時間
        self.max_single_file_mb = 50  # 単一ファイルの最大サイズ
    
    def _validate_path(self, file_path: Path) -> Path:
        """
        パスの安全性を検証（パストラバーサル攻撃対策）
        
        Args:
            file_path: 検証するパス
            
        Returns:
            解決済みの安全なパス
            
        Raises:
            SecurityError: 不正なパスアクセスの場合
        """
        # パスを正規化（相対パスを絶対パスに変換し、../ などを解決）
        resolved_path = file_path.resolve()
        
        # 許可されたディレクトリ内かチェック
        is_allowed = False
        for allowed_dir in self.allowed_dirs:
            try:
                # relative_to が成功すれば、allowed_dir のサブディレクトリ
                resolved_path.relative_to(allowed_dir)
                is_allowed = True
                break
            except ValueError:
                continue
        
        if not is_allowed:
            logger.error(f"Security violation: Attempted access to {resolved_path}")
            raise SecurityError(
                f"Access denied: Path '{file_path}' is outside allowed directories"
            )
        
        # シンボリックリンクのチェック（オプション）
        if resolved_path.is_symlink():
            link_target = resolved_path.readlink()
            logger.warning(f"Symbolic link detected: {resolved_path} -> {link_target}")
            # シンボリックリンクの宛先も検証
            return self._validate_path(link_target)
        
        return resolved_path
    
    def read_text_file(self, file_path: Union[str, Path], 
                      encoding: str = 'utf-8',
                      use_cache: bool = True) -> str:
        """
        テキストファイルを読み込み
        
        Args:
            file_path: ファイルパス
            encoding: エンコーディング
            use_cache: キャッシュを使用するか
            
        Returns:
            ファイル内容
            
        Raises:
            FileNotFoundError: ファイルが存在しない場合
            IOError: 読み込みエラー
        """
        file_path = Path(file_path)
        
        # セキュリティチェック
        file_path = self._validate_path(file_path)
        
        # キャッシュチェック
        if use_cache:
            cached = self._get_from_cache(file_path)
            if cached is not None:
                logger.debug(f"Using cached content for {file_path}")
                return cached
        
        # ファイル読み込み
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            logger.info(f"Read {len(content)} characters from {file_path}")
            
            # キャッシュに保存
            if use_cache:
                self._save_to_cache(file_path, content)
            
            return content
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise IOError(f"Failed to read {file_path}: {e}")
    
    def write_text_file(self, file_path: Union[str, Path],
                       content: str,
                       encoding: str = 'utf-8',
                       backup: bool = True) -> None:
        """
        テキストファイルを書き込み
        
        Args:
            file_path: ファイルパス
            content: 書き込む内容
            encoding: エンコーディング
            backup: バックアップを作成するか
        """
        file_path = Path(file_path)
        
        # セキュリティチェック
        file_path = self._validate_path(file_path)
        
        # バックアップ作成
        if backup and file_path.exists():
            self._create_backup(file_path)
        
        # ディレクトリ作成
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ファイル書き込み
        try:
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            logger.info(f"Wrote {len(content)} characters to {file_path}")
            
            # キャッシュを無効化
            self._invalidate_cache(file_path)
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            raise IOError(f"Failed to write {file_path}: {e}")
    
    def read_json(self, file_path: Union[str, Path], 
                 use_cache: bool = True) -> dict:
        """
        JSONファイルを読み込み
        
        Args:
            file_path: ファイルパス
            use_cache: キャッシュを使用するか
            
        Returns:
            JSONデータ
        """
        content = self.read_text_file(file_path, use_cache=use_cache)
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
    
    def write_json(self, file_path: Union[str, Path],
                  data: dict,
                  indent: int = 2,
                  backup: bool = True) -> None:
        """
        JSONファイルを書き込み
        
        Args:
            file_path: ファイルパス
            data: 書き込むデータ
            indent: インデント
            backup: バックアップを作成するか
        """
        content = json.dumps(data, ensure_ascii=False, indent=indent)
        self.write_text_file(file_path, content, backup=backup)
    
    def find_files(self, pattern: str,
                  search_dirs: Optional[List[Path]] = None,
                  recursive: bool = True) -> List[Path]:
        """
        パターンに一致するファイルを検索
        
        Args:
            pattern: ファイルパターン（glob形式）
            search_dirs: 検索ディレクトリのリスト
            recursive: 再帰的に検索するか
            
        Returns:
            一致するファイルパスのリスト
        """
        if search_dirs is None:
            search_dirs = [Path.cwd()]
        
        found_files = []
        
        for search_dir in search_dirs:
            search_dir = Path(search_dir)
            
            if not search_dir.exists():
                logger.warning(f"Search directory does not exist: {search_dir}")
                continue
            
            if recursive:
                matches = search_dir.rglob(pattern)
            else:
                matches = search_dir.glob(pattern)
            
            found_files.extend(matches)
        
        # 重複を除去してソート
        found_files = sorted(set(found_files))
        
        logger.debug(f"Found {len(found_files)} files matching '{pattern}'")
        
        return found_files
    
    def get_file_info(self, file_path: Union[str, Path]) -> dict:
        """
        ファイル情報を取得
        
        Args:
            file_path: ファイルパス
            
        Returns:
            ファイル情報の辞書
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {'exists': False, 'path': str(file_path)}
        
        stat = file_path.stat()
        
        return {
            'exists': True,
            'path': str(file_path),
            'name': file_path.name,
            'size': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'is_file': file_path.is_file(),
            'is_dir': file_path.is_dir(),
            'extension': file_path.suffix
        }
    
    def _get_from_cache(self, file_path: Path) -> Optional[any]:
        """キャッシュから取得"""
        cache_key = self._get_cache_key(file_path)
        
        if cache_key not in self._file_cache:
            return None
        
        # TTLチェック
        metadata = self._cache_metadata.get(cache_key, {})
        if 'timestamp' in metadata:
            age = (datetime.now() - metadata['timestamp']).total_seconds()
            if age > self.cache_ttl_seconds:
                logger.debug(f"Cache expired for {file_path}")
                del self._file_cache[cache_key]
                del self._cache_metadata[cache_key]
                return None
        
        return self._file_cache[cache_key]
    
    def _save_to_cache(self, file_path: Path, content: any) -> None:
        """キャッシュに保存"""
        cache_key = self._get_cache_key(file_path)
        
        # キャッシュサイズチェック
        if self._get_cache_size_mb() > self.max_cache_size_mb:
            self._cleanup_cache()
        
        self._file_cache[cache_key] = content
        self._cache_metadata[cache_key] = {
            'timestamp': datetime.now(),
            'file_path': str(file_path),
            'size': len(str(content))
        }
    
    def _invalidate_cache(self, file_path: Path) -> None:
        """キャッシュを無効化"""
        cache_key = self._get_cache_key(file_path)
        
        if cache_key in self._file_cache:
            del self._file_cache[cache_key]
        if cache_key in self._cache_metadata:
            del self._cache_metadata[cache_key]
    
    def _get_cache_key(self, file_path: Path) -> str:
        """キャッシュキーを生成"""
        return hashlib.md5(str(file_path.absolute()).encode()).hexdigest()
    
    def _get_cache_size_mb(self) -> float:
        """キャッシュサイズを取得（MB）"""
        total_size = sum(
            metadata.get('size', 0) 
            for metadata in self._cache_metadata.values()
        )
        return total_size / (1024 * 1024)
    
    def _cleanup_cache(self) -> None:
        """古いキャッシュエントリを削除"""
        # 最も古いエントリから削除
        sorted_entries = sorted(
            self._cache_metadata.items(),
            key=lambda x: x[1].get('timestamp', datetime.min)
        )
        
        # 半分を削除
        to_remove = len(sorted_entries) // 2
        for cache_key, _ in sorted_entries[:to_remove]:
            if cache_key in self._file_cache:
                del self._file_cache[cache_key]
            if cache_key in self._cache_metadata:
                del self._cache_metadata[cache_key]
        
        logger.debug(f"Cleaned up {to_remove} cache entries")
    
    def _create_backup(self, file_path: Path) -> None:
        """バックアップを作成"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = file_path.with_suffix(f'.{timestamp}.bak')
        
        try:
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    def clear_cache(self) -> None:
        """すべてのキャッシュをクリア"""
        self._file_cache.clear()
        self._cache_metadata.clear()
        logger.info("File cache cleared")
    
    def get_cache_stats(self) -> dict:
        """キャッシュ統計を取得"""
        return {
            'entries': len(self._file_cache),
            'size_mb': self._get_cache_size_mb(),
            'oldest': min(
                (m.get('timestamp', datetime.now()) for m in self._cache_metadata.values()),
                default=None
            ),
            'newest': max(
                (m.get('timestamp', datetime.now()) for m in self._cache_metadata.values()),
                default=None
            )
        }