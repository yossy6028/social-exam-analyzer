#!/usr/bin/env python3
"""
社会科目入試問題分析システム - リファクタリング版
段階的に main.py から移行
"""

import sys
import logging
from pathlib import Path

# tkinter
try:
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Warning: tkinter not available")

# プロジェクトルート追加
sys.path.insert(0, str(Path(__file__).parent))

# 設定
from config.unified_settings import settings

# サービス
from services.analysis_service import AnalysisService, AnalysisRequest

# GUI（利用可能な場合）
if TKINTER_AVAILABLE:
    from gui.analysis_window import AnalysisWindow
    

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.logs_dir / 'app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Application:
    """メインアプリケーション"""
    
    def __init__(self):
        """初期化"""
        self.service = AnalysisService()
        logger.info("Application initialized")
    
    def run_gui(self):
        """GUI版を起動"""
        if not TKINTER_AVAILABLE:
            print("Error: tkinter is not available")
            return 1
        
        try:
            root = tk.Tk()
            window = AnalysisWindow(root, self.service)
            window.run()
            return 0
        except Exception as e:
            logger.error(f"GUI startup failed: {e}")
            messagebox.showerror("起動エラー", f"アプリケーションの起動に失敗しました:\n{e}")
            return 1
    
    def run_cli(self, pdf_path: str, school_name: str = "不明", year: str = "不明"):
        """CLI版を実行"""
        try:
            print("=" * 60)
            print("社会科目入試問題分析システム (CLI)")
            print("=" * 60)
            print()
            
            # 分析リクエスト作成
            request = AnalysisRequest(
                pdf_path=pdf_path,
                school_name=school_name,
                year=year,
                options=settings.analysis,
                progress_callback=lambda msg: print(f"  {msg}")
            )
            
            # 分析実行
            print("分析を開始します...")
            result = self.service.analyze(request)
            
            # 結果表示
            self._display_cli_results(result)
            
            return 0
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            print(f"エラー: {e}")
            return 1
    
    def _display_cli_results(self, result):
        """CLI結果表示"""
        print()
        print("=" * 60)
        print("分析結果")
        print("=" * 60)
        print()
        
        print(f"学校名: {result.school_name}")
        print(f"年度: {result.year}")
        print(f"総問題数: {result.total_questions}")
        print(f"分析ソース: {result.source}")
        print()
        
        if result.statistics:
            # 分野別分布
            if field_dist := result.statistics.get('field_distribution'):
                print("◆ 分野別分布:")
                for field, count in field_dist.items():
                    percentage = (count / result.total_questions * 100) if result.total_questions > 0 else 0
                    print(f"  {field}: {count}問 ({percentage:.1f}%)")
                print()
            
            # 出題形式分布
            if format_dist := result.statistics.get('format_distribution'):
                print("◆ 出題形式分布:")
                for fmt, count in format_dist.items():
                    percentage = (count / result.total_questions * 100) if result.total_questions > 0 else 0
                    print(f"  {fmt}: {count}問 ({percentage:.1f}%)")
                print()
        
        # 問題サンプル（最初の5問）
        if result.questions:
            print("◆ 問題サンプル（最初の5問）:")
            for q in result.questions[:5]:
                number = getattr(q, 'number', 'N/A')
                field = getattr(q, 'field', 'N/A')
                if hasattr(field, 'value'):
                    field = field.value
                theme = getattr(q, 'theme', None) or getattr(q, 'topic', None) or '未設定'
                
                print(f"  {number}: {theme} [{field}]")
        
        print()
        print("=" * 60)
        print("分析完了")
        print("=" * 60)


def main():
    """メインエントリーポイント"""
    import argparse
    
    parser = argparse.ArgumentParser(description='社会科目入試問題分析システム')
    parser.add_argument('--pdf', type=str, help='分析するPDFファイルのパス')
    parser.add_argument('--school', type=str, default='不明', help='学校名')
    parser.add_argument('--year', type=str, default='不明', help='年度')
    parser.add_argument('--gui', action='store_true', help='GUI版を起動')
    
    args = parser.parse_args()
    
    app = Application()
    
    if args.gui or not args.pdf:
        # GUI版
        return app.run_gui()
    else:
        # CLI版
        return app.run_cli(args.pdf, args.school, args.year)


if __name__ == "__main__":
    sys.exit(main())