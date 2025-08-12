#!/usr/bin/env python3
"""
社会科目入試問題分析システム メインプログラム
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

# モジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent))

try:
    from modules.social_analyzer_fixed import FixedSocialAnalyzer as SocialAnalyzer
except ImportError:
    try:
        from modules.social_analyzer_improved import ImprovedSocialAnalyzer as SocialAnalyzer
    except ImportError:
        from modules.social_analyzer import SocialAnalyzer
from modules.social_excel_formatter import SocialExcelFormatter
from modules.ocr_handler import OCRHandler

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/social_analyzer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SocialExamAnalyzerGUI:
    """社会科目入試問題分析GUIアプリケーション"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("社会科目入試問題分析システム")
        self.root.geometry("900x700")
        
        # アナライザーとフォーマッターの初期化
        self.analyzer = SocialAnalyzer()
        self.formatter = SocialExcelFormatter()
        self.ocr_handler = OCRHandler()
        
        self.selected_file = None
        self.analysis_result = None
        
        self.setup_gui()
    
    def setup_gui(self):
        """GUI要素のセットアップ"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タイトル
        title_label = ttk.Label(main_frame, text="社会科目入試問題分析システム", 
                               font=('', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # ファイル選択セクション
        file_frame = ttk.LabelFrame(main_frame, text="ファイル選択", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.file_label = ttk.Label(file_frame, text="ファイルを選択してください")
        self.file_label.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Button(file_frame, text="PDFファイルを選択", 
                  command=self.select_file).grid(row=0, column=1, padx=10)
        
        # 学校情報入力セクション
        info_frame = ttk.LabelFrame(main_frame, text="学校情報", padding="10")
        info_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(info_frame, text="学校名:").grid(row=0, column=0, sticky=tk.W)
        self.school_entry = ttk.Entry(info_frame, width=30)
        self.school_entry.grid(row=0, column=1, padx=10)
        
        ttk.Label(info_frame, text="年度:").grid(row=0, column=2, sticky=tk.W)
        self.year_entry = ttk.Entry(info_frame, width=10)
        self.year_entry.grid(row=0, column=3, padx=10)
        self.year_entry.insert(0, "2025")
        
        # 分析オプションセクション
        option_frame = ttk.LabelFrame(main_frame, text="分析オプション", padding="10")
        option_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.analyze_geography = tk.BooleanVar(value=True)
        self.analyze_history = tk.BooleanVar(value=True)
        self.analyze_civics = tk.BooleanVar(value=True)
        self.analyze_current = tk.BooleanVar(value=True)
        self.analyze_resources = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(option_frame, text="地理分析", 
                       variable=self.analyze_geography).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(option_frame, text="歴史分析", 
                       variable=self.analyze_history).grid(row=0, column=1, sticky=tk.W)
        ttk.Checkbutton(option_frame, text="公民分析", 
                       variable=self.analyze_civics).grid(row=0, column=2, sticky=tk.W)
        ttk.Checkbutton(option_frame, text="時事問題", 
                       variable=self.analyze_current).grid(row=1, column=0, sticky=tk.W)
        ttk.Checkbutton(option_frame, text="資料分析", 
                       variable=self.analyze_resources).grid(row=1, column=1, sticky=tk.W)
        
        # 実行ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.analyze_button = ttk.Button(button_frame, text="分析開始", 
                                        command=self.start_analysis,
                                        state=tk.DISABLED)
        self.analyze_button.grid(row=0, column=0, padx=5)
        
        self.save_button = ttk.Button(button_frame, text="Excel保存", 
                                     command=self.save_excel,
                                     state=tk.DISABLED)
        self.save_button.grid(row=0, column=1, padx=5)
        
        # プログレスバー
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 結果表示エリア
        result_frame = ttk.LabelFrame(main_frame, text="分析結果", padding="10")
        result_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # スクロールバー付きテキストエリア
        self.result_text = tk.Text(result_frame, height=15, width=80, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # グリッドの重み設定
        main_frame.rowconfigure(6, weight=1)
        main_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)
    
    def select_file(self):
        """ファイル選択ダイアログ"""
        file_path = filedialog.askopenfilename(
            title="PDFファイルを選択",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            self.selected_file = file_path
            self.file_label.config(text=f"選択: {Path(file_path).name}")
            self.analyze_button.config(state=tk.NORMAL)
            
            # ファイル名から学校名を推測
            filename = Path(file_path).stem
            if not self.school_entry.get():
                # 学校名を抽出（例: "開成中学校_2025" -> "開成中学校"）
                school_name = filename.split('_')[0] if '_' in filename else filename
                self.school_entry.insert(0, school_name)
    
    def start_analysis(self):
        """分析処理を開始"""
        if not self.selected_file:
            messagebox.showwarning("警告", "ファイルを選択してください")
            return
        
        if not self.school_entry.get():
            messagebox.showwarning("警告", "学校名を入力してください")
            return
        
        # プログレスバー開始
        self.progress.start()
        self.analyze_button.config(state=tk.DISABLED)
        
        # 別スレッドで分析実行
        thread = threading.Thread(target=self.run_analysis)
        thread.daemon = True
        thread.start()
    
    def run_analysis(self):
        """分析処理の実行"""
        try:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "分析を開始しています...\n")
            
            # PDFからテキスト抽出
            self.result_text.insert(tk.END, "PDFからテキストを抽出中...\n")
            text = self.ocr_handler.process_pdf(self.selected_file)
            
            if not text:
                raise Exception("テキストの抽出に失敗しました")
            
            self.result_text.insert(tk.END, f"テキスト抽出完了（{len(text)}文字）\n\n")
            
            # 分析実行
            self.result_text.insert(tk.END, "問題を分析中...\n")
            self.analysis_result = self.analyzer.analyze_document(text)
            
            # 結果表示
            self.display_results()
            
            # ボタンを有効化
            self.root.after(0, self.enable_save_button)
            
        except Exception as e:
            logger.error(f"分析エラー: {e}")
            self.root.after(0, lambda: messagebox.showerror("エラー", f"分析中にエラーが発生しました:\n{str(e)}"))
        
        finally:
            self.root.after(0, self.stop_progress)
    
    def display_results(self):
        """分析結果を表示"""
        if not self.analysis_result:
            return
        
        stats = self.analysis_result['statistics']
        
        # 結果をクリア
        self.result_text.delete(1.0, tk.END)
        
        # サマリー表示
        self.result_text.insert(tk.END, "=" * 60 + "\n")
        self.result_text.insert(tk.END, "分析結果サマリー\n")
        self.result_text.insert(tk.END, "=" * 60 + "\n\n")
        
        self.result_text.insert(tk.END, f"総問題数: {self.analysis_result['total_questions']}問\n\n")
        
        # 分野別分布
        self.result_text.insert(tk.END, "【分野別出題状況】\n")
        if 'field_distribution' in stats:
            for field, data in stats['field_distribution'].items():
                self.result_text.insert(tk.END, 
                    f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)\n")
        
        self.result_text.insert(tk.END, "\n")
        
        # 資料活用状況
        self.result_text.insert(tk.END, "【資料活用状況】\n")
        if 'resource_usage' in stats:
            for resource, data in sorted(stats['resource_usage'].items(), 
                                        key=lambda x: x[1]['count'], 
                                        reverse=True)[:5]:
                self.result_text.insert(tk.END, 
                    f"  {resource:10s}: {data['count']:3d}回 ({data['percentage']:5.1f}%)\n")
        
        self.result_text.insert(tk.END, "\n")
        
        # 出題形式
        self.result_text.insert(tk.END, "【出題形式分布】\n")
        if 'format_distribution' in stats:
            for format_type, data in sorted(stats['format_distribution'].items(),
                                           key=lambda x: x[1]['count'],
                                           reverse=True)[:5]:
                self.result_text.insert(tk.END, 
                    f"  {format_type:10s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)\n")
        
        self.result_text.insert(tk.END, "\n")
        
        # 時事問題
        self.result_text.insert(tk.END, "【時事問題】\n")
        if 'current_affairs' in stats:
            self.result_text.insert(tk.END, 
                f"  時事問題: {stats['current_affairs']['count']}問 "
                f"({stats['current_affairs']['percentage']:.1f}%)\n")
        
        self.result_text.insert(tk.END, "\n")
        
        # テーマ一覧（大問ごとに区切って表示）
        self.result_text.insert(tk.END, "【出題テーマ一覧】\n")
        questions = self.analysis_result.get('questions', [])
        
        if questions:
            # 大問ごとにグループ化
            grouped_themes = {}
            for q in questions:
                # 問題番号から大問番号を推定
                if '問' in q.number:
                    q_num = q.number.replace('問', '').strip()
                    if '-' in q_num or '.' in q_num:
                        # "1-1", "1.1" のような形式
                        major_num = q_num.split('-')[0].split('.')[0]
                    else:
                        # 単純な番号の場合、10問ごとに大問として区切る
                        try:
                            num_val = int(q_num)
                            major_num = str((num_val - 1) // 10 + 1)
                        except:
                            major_num = '1'
                else:
                    major_num = '1'
                
                if major_num not in grouped_themes:
                    grouped_themes[major_num] = []
                
                if q.topic:
                    grouped_themes[major_num].append((q.number, q.topic, q.field.value))
            
            # 大問ごとに表示
            for major_num in sorted(grouped_themes.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                if len(grouped_themes) > 1:
                    self.result_text.insert(tk.END, f"\n▼ 大問 {major_num}\n")
                    self.result_text.insert(tk.END, "-" * 40 + "\n")
                
                themes = grouped_themes[major_num]
                if themes:
                    for num, theme, field in themes:
                        # 分野も併記してより分かりやすく
                        self.result_text.insert(tk.END, f"  {num}: {theme} [{field}]\n")
                else:
                    self.result_text.insert(tk.END, "  （テーマ情報なし）\n")
        else:
            self.result_text.insert(tk.END, "  （問題が検出されませんでした）\n")
        
        self.result_text.insert(tk.END, "\n")
        self.result_text.insert(tk.END, "=" * 60 + "\n")
        self.result_text.insert(tk.END, "分析完了！「Excel保存」ボタンで詳細レポートを保存できます。\n")
    
    def save_excel(self):
        """Excel形式で保存"""
        if not self.analysis_result:
            messagebox.showwarning("警告", "先に分析を実行してください")
            return
        
        # 保存先を選択
        school_name = self.school_entry.get()
        year = self.year_entry.get()
        default_filename = f"{school_name}_{year}_社会分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        file_path = filedialog.asksaveasfilename(
            title="保存先を選択",
            defaultextension=".xlsx",
            initialfile=default_filename,
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # Excelレポート作成
                wb = self.formatter.create_excel_report(
                    self.analysis_result,
                    school_name,
                    year
                )
                
                # 保存
                self.formatter.save_excel(wb, file_path)
                
                messagebox.showinfo("完了", f"分析結果を保存しました:\n{file_path}")
                
            except Exception as e:
                logger.error(f"Excel保存エラー: {e}")
                messagebox.showerror("エラー", f"保存中にエラーが発生しました:\n{str(e)}")
    
    def enable_save_button(self):
        """保存ボタンを有効化"""
        self.save_button.config(state=tk.NORMAL)
        self.analyze_button.config(state=tk.NORMAL)
    
    def stop_progress(self):
        """プログレスバーを停止"""
        self.progress.stop()


def main():
    """メイン関数"""
    # ログディレクトリ作成
    log_dir = Path("logs")
    if not log_dir.exists():
        log_dir.mkdir()
    
    # GUI起動
    root = tk.Tk()
    app = SocialExamAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()