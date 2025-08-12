"""
ファイル操作関連のユーティリティ関数
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List


def is_valid_text_file(file_path: Path) -> bool:
    """
    有効なテキストファイルまたはPDFファイルかチェック
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        有効なテキストファイルまたはPDFファイルの場合True
    """
    if not file_path.exists():
        return False
    
    if not file_path.is_file():
        return False
    
    # .txtまたは.pdfファイルを受け入れる
    if file_path.suffix.lower() not in ['.txt', '.pdf']:
        return False
    
    # ファイルサイズチェック（0バイトファイルを除外）
    if file_path.stat().st_size == 0:
        return False
    
    return True


def get_file_size_formatted(file_path: Path) -> str:
    """
    ファイルサイズを人間が読みやすい形式で取得
    
    Args:
        file_path: ファイルパス
    
    Returns:
        フォーマットされたファイルサイズ文字列
    """
    if not file_path.exists():
        return "0 B"
    
    size = file_path.stat().st_size
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    
    return f"{size:.1f} TB"


def create_backup(file_path: Path, backup_dir: Optional[Path] = None) -> Optional[Path]:
    """
    ファイルのバックアップを作成
    
    Args:
        file_path: バックアップ対象のファイル
        backup_dir: バックアップ先ディレクトリ（省略時はdata/backups）
    
    Returns:
        バックアップファイルのパス、失敗時はNone
    """
    if not file_path.exists():
        return None
    
    if backup_dir is None:
        backup_dir = Path("data/backups")
    
    # バックアップディレクトリを作成
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # タイムスタンプ付きのバックアップファイル名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name
    
    try:
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception:
        return None


def ensure_directory_exists(directory: Path) -> bool:
    """
    ディレクトリが存在することを保証（なければ作成）
    
    Args:
        directory: 確認/作成対象のディレクトリ
    
    Returns:
        成功した場合True
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def clean_path_string(path_string: str) -> str:
    """
    パス文字列をクリーンアップ
    
    Args:
        path_string: クリーンアップ対象のパス文字列
    
    Returns:
        クリーンアップされたパス文字列
    """
    # 前後の空白を削除
    cleaned = path_string.strip()
    
    # 前後の引用符を削除
    if (cleaned.startswith('"') and cleaned.endswith('"')) or \
       (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1]
    
    # バックスラッシュエスケープされたスペースと括弧を処理
    cleaned = cleaned.replace('\\ ', ' ')
    cleaned = cleaned.replace('\\(', '(')
    cleaned = cleaned.replace('\\)', ')')
    
    return cleaned


def resolve_path_safely(path_string: str, allowed_dirs: Optional[List[Path]] = None) -> Optional[Path]:
    """
    パス文字列を安全に解決（パストラバーサル対策付き）
    
    Args:
        path_string: 解決対象のパス文字列
        allowed_dirs: アクセス許可ディレクトリのリスト
    
    Returns:
        解決されたPath、許可されていない場合はNone
    """
    try:
        # パスを解決
        path = Path(path_string).expanduser().resolve()
        
        # 許可ディレクトリが指定されていない場合はホームディレクトリ以下のみ許可
        if allowed_dirs is None:
            allowed_dirs = [Path.home(), Path.cwd()]
            if os.name == 'posix':
                allowed_dirs.append(Path("/tmp"))
        
        # 許可されたディレクトリ内かチェック
        for allowed_dir in allowed_dirs:
            try:
                path.relative_to(allowed_dir.resolve())
                return path
            except ValueError:
                continue
        
        return None
    except Exception:
        return None


def find_files_recursive(
    directory: Path,
    pattern: str = "*.[tp][xd][tf]",  # *.txt と *.pdf にマッチ
    max_depth: Optional[int] = None
) -> List[Path]:
    """
    ディレクトリ内のファイルを再帰的に検索
    
    Args:
        directory: 検索対象ディレクトリ
        pattern: ファイル名パターン（glob形式）
        max_depth: 最大検索深度
    
    Returns:
        見つかったファイルのリスト
    """
    if not directory.exists() or not directory.is_dir():
        return []
    
    files = []
    
    # .txtと.pdfの両方を検索
    patterns = ["*.txt", "*.pdf"] if pattern == "*.[tp][xd][tf]" else [pattern]
    
    for pat in patterns:
        if max_depth is None:
            # 深度制限なし
            files.extend(list(directory.rglob(pat)))
        else:
            # 深度制限あり
            current_depth = 0
            dirs_to_search = [directory]
            
            while dirs_to_search and current_depth <= max_depth:
                next_dirs = []
                for d in dirs_to_search:
                    # 現在のディレクトリのファイルを追加
                    files.extend(d.glob(pat))
                    
                    if current_depth < max_depth:
                        # サブディレクトリを次の検索対象に追加
                        next_dirs.extend([x for x in d.iterdir() if x.is_dir()])
                
                dirs_to_search = next_dirs
                current_depth += 1
    
    return sorted(files)


def get_recent_files(directory: Path, pattern: str = "*.[tp][xd][tf]", limit: int = 10) -> List[Path]:
    """
    最近更新されたファイルを取得
    
    Args:
        directory: 検索対象ディレクトリ
        pattern: ファイル名パターン
        limit: 取得する最大ファイル数
    
    Returns:
        最近更新されたファイルのリスト（新しい順）
    """
    files = find_files_recursive(directory, pattern)
    
    # 更新時刻でソート（新しい順）
    files_with_time = [(f, f.stat().st_mtime) for f in files]
    files_with_time.sort(key=lambda x: x[1], reverse=True)
    
    return [f[0] for f in files_with_time[:limit]]