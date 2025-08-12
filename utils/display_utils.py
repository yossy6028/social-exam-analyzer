"""
表示・出力関連のユーティリティ関数
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path


# カラーコード定義（より明るい色に変更）
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[31m'      # 通常の赤（より見やすい）
    GREEN = '\033[32m'    # 通常の緑（より見やすい）  
    YELLOW = '\033[33m'   # 通常の黄色（より見やすい）
    BLUE = '\033[34m'     # 通常の青
    CYAN = '\033[36m'     # 通常のシアン（より見やすい）
    WHITE = '\033[37m'    # 通常の白
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'


def print_colored(text: str, color: str = Colors.WHITE, bold: bool = False) -> None:
    """
    色付きテキストを出力
    
    Args:
        text: 出力するテキスト
        color: カラーコード
        bold: 太字にするか
    """
    if bold:
        print(f"{Colors.BOLD}{color}{text}{Colors.RESET}")
    else:
        print(f"{color}{text}{Colors.RESET}")


def print_header(title: str, width: int = 80) -> None:
    """
    ヘッダーを出力
    
    Args:
        title: ヘッダータイトル
        width: ヘッダーの幅
    """
    border = "=" * width
    padding = (width - len(title) - 2) // 2
    header = f"{'=' * padding} {title} {'=' * (width - padding - len(title) - 2)}"
    
    print_colored(border, Colors.CYAN, bold=True)
    print_colored(header, Colors.CYAN, bold=True)
    print_colored(border, Colors.CYAN, bold=True)


def print_section(title: str, content: Optional[str] = None) -> None:
    """
    セクションを出力
    
    Args:
        title: セクションタイトル
        content: セクションの内容
    """
    print_colored(f"\n▶ {title}", Colors.YELLOW, bold=True)
    if content:
        print(content)


def print_progress(current: int, total: int, prefix: str = "Progress", suffix: str = "") -> None:
    """
    プログレスバーを出力
    
    Args:
        current: 現在の進捗
        total: 全体数
        prefix: プレフィックス文字列
        suffix: サフィックス文字列
    """
    if total == 0:
        percent = 100
    else:
        percent = int(100 * current / total)
    
    bar_length = 40
    filled_length = int(bar_length * current // total) if total > 0 else bar_length
    
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    # カーソルを行頭に戻して上書き
    print(f'\r{prefix}: |{bar}| {percent}% {suffix}', end='', flush=True)
    
    # 完了時は改行
    if current >= total:
        print()


def format_table(
    headers: List[str],
    rows: List[List[Any]],
    col_widths: Optional[List[int]] = None
) -> str:
    """
    テーブル形式のテキストを生成
    
    Args:
        headers: ヘッダー行
        rows: データ行のリスト
        col_widths: 各列の幅（省略時は自動計算）
    
    Returns:
        フォーマットされたテーブル文字列
    """
    if not headers:
        return ""
    
    # 列幅を計算
    if col_widths is None:
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(str(header))
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(max_width + 2)
    
    # ヘッダー行
    header_row = "|"
    separator_row = "|"
    for header, width in zip(headers, col_widths):
        header_row += f" {str(header):<{width-2}} |"
        separator_row += "-" * width + "|"
    
    # データ行
    data_rows = []
    for row in rows:
        data_row = "|"
        for i, (cell, width) in enumerate(zip(row, col_widths)):
            if i < len(row):
                data_row += f" {str(cell):<{width-2}} |"
            else:
                data_row += " " * width + "|"
        data_rows.append(data_row)
    
    # 結合
    table = [header_row, separator_row] + data_rows
    return "\n".join(table)


def truncate_path(path: Path, max_length: int = 60) -> str:
    """
    パスを指定長に切り詰めて表示
    
    Args:
        path: 切り詰め対象のパス
        max_length: 最大表示長
    
    Returns:
        切り詰められたパス文字列
    """
    path_str = str(path)
    
    if len(path_str) <= max_length:
        return path_str
    
    # ファイル名は残す
    if path.is_file():
        filename = path.name
        if len(filename) >= max_length - 3:
            return "..." + filename[-(max_length-3):]
        
        # ディレクトリ部分を切り詰め
        dir_part = str(path.parent)
        remaining = max_length - len(filename) - 4  # ".../"の分
        
        if remaining > 0:
            return "..." + dir_part[-remaining:] + "/" + filename
        else:
            return ".../" + filename
    else:
        # ディレクトリの場合
        return "..." + path_str[-(max_length-3):]


def print_error(message: str, exception: Optional[Exception] = None) -> None:
    """
    エラーメッセージを出力
    
    Args:
        message: エラーメッセージ
        exception: 例外オブジェクト（オプション）
    """
    print_colored(f"❌ エラー: {message}", Colors.RED, bold=True)
    if exception:
        print_colored(f"   詳細: {str(exception)}", Colors.RED)


def print_warning(message: str) -> None:
    """
    警告メッセージを出力
    
    Args:
        message: 警告メッセージ
    """
    print_colored(f"⚠️  警告: {message}", Colors.YELLOW)


def print_success(message: str) -> None:
    """
    成功メッセージを出力
    
    Args:
        message: 成功メッセージ
    """
    print_colored(f"✅ {message}", Colors.GREEN, bold=True)


def print_info(message: str) -> None:
    """
    情報メッセージを出力
    
    Args:
        message: 情報メッセージ
    """
    print_colored(f"ℹ️  {message}", Colors.BLUE)


def clear_screen() -> None:
    """画面をクリア"""
    os.system('clear' if os.name == 'posix' else 'cls')


def print_separator(char: str = "-", width: int = 80) -> None:
    """
    区切り線を出力
    
    Args:
        char: 区切り文字
        width: 幅
    """
    print(char * width)