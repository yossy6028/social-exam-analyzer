"""
ファイル選択モジュール - インタラクティブなファイル選択機能
"""
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from collections import defaultdict

from config.settings import Settings
from models import FileSelectionResult
from exceptions import InvalidFileError, PathTraversalError
from utils.file_utils import (
    is_valid_text_file,
    resolve_path_safely,
    find_files_recursive,
    get_recent_files
)
from utils.display_utils import (
    print_colored,
    print_header,
    print_section,
    print_error,
    print_warning,
    print_info,
    truncate_path,
    Colors
)
from utils.text_utils import clean_path_string


class FileSelector:
    """ファイル選択クラス"""
    
    def __init__(self, search_dirs: Optional[List[Path]] = None):
        """
        初期化
        
        Args:
            search_dirs: 検索対象ディレクトリのリスト
        """
        self.search_dirs = search_dirs or Settings.get_search_directories()
        self.allowed_dirs = Settings.get_allowed_directories()
        self.cached_files = None
        self.last_search_time = None
    
    def select_file(self, cli_arg: Optional[str] = None) -> FileSelectionResult:
        """
        ファイルを選択（複数の方法をサポート）
        
        Args:
            cli_arg: コマンドライン引数で指定されたファイルパス
        
        Returns:
            FileSelectionResult: 選択結果
        """
        # コマンドライン引数が指定されている場合
        if cli_arg:
            result = self._select_from_cli_arg(cli_arg)
            if result.selected_file:
                return result
        
        # インタラクティブ選択
        print_header("ファイル選択（テキスト/PDF）", 60)
        
        # 選択方法を提示
        print_section("選択方法")
        print("1. ファイル一覧から選択")
        print("2. ファイルをドラッグ＆ドロップ")
        print("3. GUI ファイル選択ダイアログ")
        print("4. パスを手動入力")
        print("0. キャンセル")
        
        while True:
            try:
                choice = input("\n選択方法を入力 (0-4): ").strip()
                
                if choice == '0':
                    return FileSelectionResult(
                        selected_file=None,
                        selection_method='cancelled',
                        cancelled=True
                    )
                elif choice == '1':
                    return self._select_from_list()
                elif choice == '2':
                    return self._select_from_drag_drop()
                elif choice == '3':
                    return self._select_from_gui()
                elif choice == '4':
                    return self._select_from_manual_input()
                else:
                    print_warning("無効な選択です。もう一度入力してください。")
            
            except KeyboardInterrupt:
                return FileSelectionResult(
                    selected_file=None,
                    selection_method='cancelled',
                    cancelled=True
                )
    
    def _select_from_cli_arg(self, cli_arg: str) -> FileSelectionResult:
        """コマンドライン引数からファイルを選択"""
        try:
            path = self._validate_and_resolve_path(cli_arg)
            if path:
                print_info(f"コマンドライン引数からファイルを選択: {path}")
                return FileSelectionResult(
                    selected_file=path,
                    selection_method='cli_arg'
                )
        except (InvalidFileError, PathTraversalError) as e:
            print_error(str(e))
        
        return FileSelectionResult(
            selected_file=None,
            selection_method='cli_arg',
            cancelled=False
        )
    
    def _select_from_list(self) -> FileSelectionResult:
        """ファイル一覧から選択"""
        print_section("ファイル検索中...")
        
        # ファイルを検索
        all_files = self._find_all_text_files()
        
        if not all_files:
            print_warning("テキストファイルまたはPDFファイルが見つかりませんでした。")
            return FileSelectionResult(
                selected_file=None,
                selection_method='list',
                cancelled=False
            )
        
        # 学校別にグループ化
        grouped_files = self._group_files_by_school(all_files)
        
        # 表示用のファイルリストを作成
        display_files = self._prepare_display_list(grouped_files)
        
        # ファイル一覧を表示
        print_section(f"利用可能なファイル（{len(display_files)}件）")
        
        for i, (file_path, display_name) in enumerate(display_files, 1):
            # 学校名で色分け（太字で見やすく）
            if '武蔵' in display_name:
                color = Colors.BRIGHT_CYAN
            elif '開成' in display_name:
                color = Colors.BRIGHT_GREEN
            elif '桜蔭' in display_name or '桜陰' in display_name:
                color = Colors.BRIGHT_YELLOW
            elif '渋谷' in display_name or '渋渋' in display_name:
                color = Colors.BRIGHT_BLUE
            elif '麻布' in display_name:
                color = Colors.BRIGHT_RED
            elif '聖光' in display_name:
                color = Colors.BRIGHT_MAGENTA
            elif '早' in display_name and '実' in display_name:
                color = Colors.BRIGHT_WHITE
            else:
                color = Colors.WHITE
            
            print_colored(f"{i:3d}. {display_name}", color, bold=True)
        
        # 選択
        while True:
            try:
                choice = input(f"\nファイル番号を入力 (1-{len(display_files)}, 0でキャンセル): ").strip()
                
                if choice == '0':
                    return FileSelectionResult(
                        selected_file=None,
                        selection_method='list',
                        cancelled=True
                    )
                
                index = int(choice) - 1
                if 0 <= index < len(display_files):
                    selected_path = display_files[index][0]
                    return FileSelectionResult(
                        selected_file=selected_path,
                        selection_method='list'
                    )
                else:
                    print_warning("無効な番号です。")
            
            except ValueError:
                print_warning("数値を入力してください。")
            except KeyboardInterrupt:
                return FileSelectionResult(
                    selected_file=None,
                    selection_method='list',
                    cancelled=True
                )
    
    def _select_from_drag_drop(self) -> FileSelectionResult:
        """ドラッグ＆ドロップで選択"""
        print_section("ドラッグ＆ドロップ")
        print("テキストファイルまたはPDFファイルをこのウィンドウにドラッグして、Enterキーを押してください。")
        print("（キャンセルする場合は何も入力せずにEnter）")
        
        try:
            path_input = input("\nファイルパス: ").strip()
            
            if not path_input:
                return FileSelectionResult(
                    selected_file=None,
                    selection_method='drag_drop',
                    cancelled=True
                )
            
            path = self._validate_and_resolve_path(path_input)
            if path:
                return FileSelectionResult(
                    selected_file=path,
                    selection_method='drag_drop'
                )
            else:
                return FileSelectionResult(
                    selected_file=None,
                    selection_method='drag_drop',
                    cancelled=False
                )
        
        except KeyboardInterrupt:
            return FileSelectionResult(
                selected_file=None,
                selection_method='drag_drop',
                cancelled=True
            )
    
    def _select_from_gui(self) -> FileSelectionResult:
        """GUIダイアログで選択"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            print_section("GUIファイル選択")
            print("ファイル選択ダイアログが開きます...")
            
            root = tk.Tk()
            root.withdraw()  # メインウィンドウを非表示
            
            # 初期ディレクトリを設定
            initial_dir = str(self.search_dirs[0]) if self.search_dirs else str(Path.home())
            
            file_path = filedialog.askopenfilename(
                title="ファイルを選択",
                initialdir=initial_dir,
                filetypes=[
                    ("テキストファイル", "*.txt"),
                    ("PDFファイル", "*.pdf"),
                    ("すべてのファイル", "*.*"),
                    ("すべてのファイル", "*.*")
                ]
            )
            
            root.destroy()
            
            if file_path:
                path = Path(file_path)
                if is_valid_text_file(path):
                    return FileSelectionResult(
                        selected_file=path,
                        selection_method='gui'
                    )
                else:
                    print_error("選択されたファイルは有効なテキストファイルまたはPDFファイルではありません。")
            
            return FileSelectionResult(
                selected_file=None,
                selection_method='gui',
                cancelled=not bool(file_path)
            )
        
        except ImportError:
            print_error("tkinterがインストールされていません。他の方法を選択してください。")
            return FileSelectionResult(
                selected_file=None,
                selection_method='gui',
                cancelled=False
            )
    
    def _select_from_manual_input(self) -> FileSelectionResult:
        """手動でパスを入力"""
        print_section("手動入力")
        print("テキストファイルまたはPDFファイルのパスを入力してください。")
        print("（相対パスまたは絶対パス）")
        
        try:
            path_input = input("\nファイルパス: ").strip()
            
            if not path_input:
                return FileSelectionResult(
                    selected_file=None,
                    selection_method='manual',
                    cancelled=True
                )
            
            path = self._validate_and_resolve_path(path_input)
            if path:
                return FileSelectionResult(
                    selected_file=path,
                    selection_method='manual'
                )
            else:
                return FileSelectionResult(
                    selected_file=None,
                    selection_method='manual',
                    cancelled=False
                )
        
        except KeyboardInterrupt:
            return FileSelectionResult(
                selected_file=None,
                selection_method='manual',
                cancelled=True
            )
    
    def _find_all_text_files(self) -> List[Path]:
        """すべてのテキストファイルとPDFファイルを検索"""
        all_files = []
        
        for search_dir in self.search_dirs:
            if not search_dir.exists():
                continue
            
            # 再帰的に検索
            # テキストファイルとPDFファイルを検索
            txt_files = find_files_recursive(search_dir, "*.txt", max_depth=5)
            pdf_files = find_files_recursive(search_dir, "*.pdf", max_depth=5)
            files = txt_files + pdf_files
            
            # 有効なファイルのみフィルタ
            valid_files = [f for f in files if is_valid_text_file(f)]
            all_files.extend(valid_files)
        
        # 重複を除去
        unique_files = list(set(all_files))
        
        # 更新時刻でソート（新しい順）
        unique_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        return unique_files
    
    def _group_files_by_school(self, files: List[Path]) -> Dict[str, List[Path]]:
        """ファイルを学校別にグループ化"""
        grouped = defaultdict(list)
        
        for file_path in files:
            # ファイル名やディレクトリ名から学校を推測
            school = self._guess_school_from_path(file_path)
            grouped[school].append(file_path)
        
        return dict(grouped)
    
    def _guess_school_from_path(self, file_path: Path) -> str:
        """パスから学校名を推測"""
        path_str = str(file_path).lower()
        
        school_keywords = {
            '武蔵': ['武蔵', 'musashi'],
            '開成': ['開成', 'kaisei'],
            '桜蔭': ['桜蔭', '桜陰', 'ouin'],
            '麻布': ['麻布', 'azabu'],
            '渋谷': ['渋谷', '渋渋', 'shibuya'],
            '女子学院': ['女子学院', 'jg'],
            '雙葉': ['雙葉', '双葉', 'futaba'],
            '聖光学院': ['聖光', 'seiko'],
            '早稲田実業': ['早実', '早稲田実', 'waseda'],
        }
        
        for school, keywords in school_keywords.items():
            for keyword in keywords:
                if keyword in path_str:
                    return school
        
        return 'その他'
    
    def _prepare_display_list(self, grouped_files: Dict[str, List[Path]]) -> List[Tuple[Path, str]]:
        """表示用のファイルリストを準備"""
        display_list = []
        
        # 各学校から最大N件ずつ取得
        for school in sorted(grouped_files.keys()):
            files = grouped_files[school][:Settings.MAX_FILES_PER_SCHOOL]
            
            for file_path in files:
                # 表示名を作成
                display_name = f"[{school}] {truncate_path(file_path, Settings.MIN_PATH_DISPLAY_LENGTH)}"
                display_list.append((file_path, display_name))
        
        # 全体の件数制限
        if len(display_list) > Settings.MAX_FILES_TO_DISPLAY:
            display_list = display_list[:Settings.MAX_FILES_TO_DISPLAY]
        
        return display_list
    
    def _validate_and_resolve_path(self, path_string: str) -> Optional[Path]:
        """パス文字列を検証して解決"""
        # パス文字列をクリーンアップ
        cleaned_path = clean_path_string(path_string)
        
        # パスを安全に解決
        path = resolve_path_safely(cleaned_path, self.allowed_dirs)
        
        if not path:
            raise PathTraversalError(cleaned_path)
        
        if not is_valid_text_file(path):
            raise InvalidFileError(str(path), "有効なテキストファイルまたはPDFファイルではありません")
        
        return path