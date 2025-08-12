"""
CLIインターフェース - コマンドライン操作の最適化
"""
import argparse
import sys
from pathlib import Path
from typing import Optional, List
import json

from .application import EntranceExamAnalyzer
from config.settings import Settings
from utils.display_utils import (
    print_header,
    print_section,
    print_success,
    print_error,
    print_warning,
    print_info,
    clear_screen,
    Colors
)
from plugins.loader import get_plugin_loader
from modules.excel_manager import ExcelManager
from modules.text_file_manager import TextFileManager


class CLI:
    """コマンドラインインターフェース"""
    
    def __init__(self):
        self.app = EntranceExamAnalyzer()
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """ArgumentParserを作成"""
        parser = argparse.ArgumentParser(
            description='入試問題テキスト分析システム',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用例:
  %(prog)s                          # 対話モードで起動
  %(prog)s file.txt                 # ファイルを直接分析
  %(prog)s --batch *.txt            # 複数ファイルをバッチ分析
  %(prog)s --list-plugins           # 利用可能なプラグインを表示
  %(prog)s --validate-db            # データベースを検証
  %(prog)s --export-summary         # サマリーレポートを出力
            """
        )
        
        # 位置引数
        parser.add_argument(
            'file',
            nargs='?',
            help='分析対象のテキストファイル'
        )
        
        # オプション引数
        parser.add_argument(
            '--batch',
            action='store_true',
            help='バッチ分析モード'
        )
        
        parser.add_argument(
            '--output',
            '-o',
            type=str,
            default=Settings.DEFAULT_DB_FILENAME,
            help='出力先Excelファイル（デフォルト: %(default)s）'
        )
        
        parser.add_argument(
            '--text-output',
            '-t',
            action='store_true',
            help='テキストファイルとして保存（過去問フォルダに年度別・学校別で保存）'
        )
        
        parser.add_argument(
            '--text-output-dir',
            type=str,
            help='テキストファイルの保存先ディレクトリを指定'
        )
        
        parser.add_argument(
            '--no-backup',
            action='store_true',
            help='バックアップを作成しない'
        )
        
        parser.add_argument(
            '--school',
            '-s',
            type=str,
            help='学校名を指定（自動検出をスキップ）'
        )
        
        parser.add_argument(
            '--year',
            '-y',
            type=str,
            help='年度を指定（自動検出をスキップ）'
        )
        
        parser.add_argument(
            '--plugin',
            '-p',
            type=str,
            help='使用するプラグインを指定'
        )
        
        # 管理コマンド
        parser.add_argument(
            '--list-plugins',
            action='store_true',
            help='利用可能なプラグインを一覧表示'
        )
        
        parser.add_argument(
            '--list-schools',
            action='store_true',
            help='サポートされている学校を一覧表示'
        )
        
        parser.add_argument(
            '--validate-db',
            action='store_true',
            help='データベースの整合性を検証'
        )
        
        parser.add_argument(
            '--export-summary',
            action='store_true',
            help='サマリーレポートをエクスポート'
        )
        
        parser.add_argument(
            '--clear',
            action='store_true',
            help='画面をクリア'
        )
        
        # デバッグオプション
        parser.add_argument(
            '--debug',
            action='store_true',
            help='デバッグモードで実行'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際の保存を行わずに分析のみ実行'
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s 2.0.0 (Refactored)'
        )
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        CLIを実行
        
        Args:
            args: コマンドライン引数（テスト用）
        
        Returns:
            終了コード
        """
        try:
            # 引数を解析
            parsed_args = self.parser.parse_args(args)
            
            # 管理コマンドの処理
            if parsed_args.list_plugins:
                return self._list_plugins()
            
            if parsed_args.list_schools:
                return self._list_schools()
            
            if parsed_args.validate_db:
                return self._validate_database()
            
            if parsed_args.export_summary:
                return self._export_summary()
            
            if parsed_args.clear:
                clear_screen()
                return 0
            
            # 設定を適用
            self._apply_settings(parsed_args)
            
            # メイン処理
            if parsed_args.batch:
                return self._run_batch(parsed_args)
            else:
                return self._run_single(parsed_args)
        
        except KeyboardInterrupt:
            print_warning("\n中断されました。")
            return 130
        
        except Exception as e:
            print_error(f"エラー: {e}")
            if parsed_args.debug:
                import traceback
                traceback.print_exc()
            return 1
    
    def _apply_settings(self, args):
        """設定を適用"""
        # バックアップ設定
        if args.no_backup:
            self.app.excel_manager.config.create_backup = False
        
        # 出力ファイル設定
        if args.output:
            self.app.excel_manager.config.db_filename = args.output
            self.app.excel_manager.db_path = Path(args.output)
        
        # テキスト出力設定（デフォルトでTrue）
        self.app.config['text_output'] = True  # 常にテキスト出力
        self.app.config['excel_output'] = False  # Excel出力はデフォルトでオフ
        
        # テキスト出力ディレクトリ設定
        if args.text_output_dir:
            self.app.config['text_output_dir'] = args.text_output_dir
        
        # ドライラン設定
        if args.dry_run:
            self.app.config['dry_run'] = True
            self.app.config['skip_confirmation'] = True  # dry-runモードでは確認をスキップ
    
    def _run_single(self, args) -> int:
        """単一ファイルを処理"""
        if args.file:
            # ファイルが指定されている場合
            file_path = Path(args.file)
            if not file_path.exists():
                print_error(f"ファイルが見つかりません: {file_path}")
                return 1
            
            success = self.app.run(str(file_path))
            return 0 if success else 1
        else:
            # 対話モード
            return self._run_interactive()
    
    def _run_interactive(self) -> int:
        """対話モードで実行"""
        while True:
            print_header("入試問題テキスト分析システム", 60)
            print("\n1. テキストファイルを分析")
            print("2. プラグイン管理")
            print("3. データベース管理")
            print("4. ヘルプ")
            print("0. 終了")
            
            choice = input("\n選択してください (0-4): ").strip()
            
            if choice == '0':
                print_info("終了します。")
                return 0
            elif choice == '1':
                success = self.app.run()
                if not self._continue_prompt():
                    return 0 if success else 1
            elif choice == '2':
                self._manage_plugins()
            elif choice == '3':
                self._manage_database()
            elif choice == '4':
                self._show_help()
            else:
                print_warning("無効な選択です。")
    
    def _run_batch(self, args) -> int:
        """バッチ処理を実行"""
        # ファイルパターンからファイルリストを作成
        file_patterns = args.file.split(',') if args.file else ['*.txt']
        file_paths = []
        
        for pattern in file_patterns:
            paths = list(Path.cwd().glob(pattern))
            file_paths.extend(paths)
        
        if not file_paths:
            print_warning("処理対象のファイルが見つかりません。")
            return 1
        
        # バッチ分析を実行
        summary = self.app.batch_analyze(file_paths)
        
        # サマリーを表示
        print_section("バッチ分析結果")
        print(f"処理ファイル数: {summary['total']}")
        print(f"成功: {summary['success']}")
        print(f"失敗: {summary['failed']}")
        
        return 0 if summary['failed'] == 0 else 1
    
    def _list_plugins(self) -> int:
        """プラグインを一覧表示"""
        print_header("利用可能なプラグイン", 60)
        
        loader = get_plugin_loader()
        plugins = loader.list_plugins()
        
        for plugin in sorted(plugins, key=lambda p: p.priority, reverse=True):
            print(f"\n[{plugin.name}] v{plugin.version}")
            print(f"  説明: {plugin.description}")
            print(f"  対応学校: {', '.join(plugin.school_names)}")
            print(f"  優先度: {plugin.priority}")
            print(f"  作成者: {plugin.author}")
        
        return 0
    
    def _list_schools(self) -> int:
        """サポートされている学校を一覧表示"""
        print_header("サポートされている学校", 60)
        
        loader = get_plugin_loader()
        schools = loader.get_supported_schools()
        
        for i, school in enumerate(schools, 1):
            print(f"{i:2d}. {school}")
        
        print(f"\n合計: {len(schools)}校")
        return 0
    
    def _validate_database(self) -> int:
        """データベースを検証"""
        print_header("データベース検証", 60)
        
        manager = ExcelManager()
        result = manager.validate_database()
        
        if result['is_valid']:
            print_success("データベースは正常です。")
        else:
            print_error("データベースに問題があります。")
        
        if result['errors']:
            print_section("エラー")
            for error in result['errors']:
                print(f"  ❌ {error}")
        
        if result['warnings']:
            print_section("警告")
            for warning in result['warnings']:
                print(f"  ⚠️  {warning}")
        
        if result['info']:
            print_section("情報")
            for key, value in result['info'].items():
                print(f"  {key}: {value}")
        
        return 0 if result['is_valid'] else 1
    
    def _export_summary(self) -> int:
        """サマリーレポートをエクスポート"""
        print_header("サマリーレポート出力", 60)
        
        manager = ExcelManager()
        output_path = Path("summary_report.xlsx")
        
        if manager.export_summary_report(output_path):
            print_success(f"サマリーレポートを出力しました: {output_path}")
            return 0
        else:
            print_error("サマリーレポートの出力に失敗しました。")
            return 1
    
    def _manage_plugins(self):
        """プラグイン管理メニュー"""
        while True:
            print_section("プラグイン管理")
            print("1. プラグイン一覧")
            print("2. プラグイン再読み込み")
            print("3. カスタムプラグイン追加")
            print("0. 戻る")
            
            choice = input("\n選択してください (0-3): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._list_plugins()
            elif choice == '2':
                loader = get_plugin_loader()
                loader.reload_plugins()
                print_success("プラグインを再読み込みしました。")
            elif choice == '3':
                print_info("カスタムプラグインは plugins/custom_plugins/ ディレクトリに配置してください。")
    
    def _manage_database(self):
        """データベース管理メニュー"""
        while True:
            print_section("データベース管理")
            print("1. データベース検証")
            print("2. サマリーレポート出力")
            print("3. バックアップ作成")
            print("0. 戻る")
            
            choice = input("\n選択してください (0-3): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._validate_database()
            elif choice == '2':
                self._export_summary()
            elif choice == '3':
                manager = ExcelManager()
                if manager.db_path.exists():
                    backup_path = manager._create_backup()
                    if backup_path:
                        print_success(f"バックアップを作成: {backup_path}")
                    else:
                        print_error("バックアップの作成に失敗しました。")
                else:
                    print_warning("データベースファイルが存在しません。")
    
    def _show_help(self):
        """ヘルプを表示"""
        print_header("ヘルプ", 60)
        self.parser.print_help()
        input("\nEnterキーを押して続行...")
    
    def _continue_prompt(self) -> bool:
        """続行プロンプト"""
        response = input("\n続けますか？ (y/n): ").strip().lower()
        return response == 'y'


def main():
    """エントリーポイント"""
    cli = CLI()
    sys.exit(cli.run())