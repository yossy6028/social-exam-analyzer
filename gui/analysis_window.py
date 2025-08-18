"""
分析ウィンドウ - GUI版のメインウィンドウ
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
from typing import Optional

from config.unified_settings import settings
from services.analysis_service import AnalysisRequest


class AnalysisWindow:
    """分析ウィンドウ"""
    
    def __init__(self, root: tk.Tk, service):
        """初期化"""
        self.root = root
        self.service = service
        self.selected_file = None
        self.analysis_result = None
        
        self.setup_window()
        self.create_widgets()
    
    def setup_window(self):
        """ウィンドウ設定"""
        self.root.title("社会科目入試問題分析システム")
        self.root.geometry(f"{settings.ui.window_width}x{settings.ui.window_height}")
    
    def create_widgets(self):
        """ウィジェット作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # ファイル選択セクション
        self._create_file_section(main_frame)
        
        # オプションセクション
        self._create_options_section(main_frame)
        
        # 結果表示セクション
        self._create_result_section(main_frame)
        
        # ボタンセクション
        self._create_button_section(main_frame)
    
    def _create_file_section(self, parent):
        """ファイル選択セクション"""
        frame = ttk.LabelFrame(parent, text="ファイル選択", padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # ファイルパス表示
        self.file_var = tk.StringVar(value="PDFファイルを選択してください")
        ttk.Label(frame, textvariable=self.file_var).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # 選択ボタン
        ttk.Button(frame, text="ファイル選択", command=self.select_file).grid(row=0, column=1)
        
        # 学校名・年度
        ttk.Label(frame, text="学校名:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.school_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.school_var, width=30).grid(row=1, column=1, pady=(10, 0))
        
        ttk.Label(frame, text="年度:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.year_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.year_var, width=30).grid(row=2, column=1, pady=(5, 0))
    
    def _create_options_section(self, parent):
        """オプションセクション"""
        frame = ttk.LabelFrame(parent, text="分析オプション", padding="10")
        frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 分野オプション
        self.opt_geography = tk.BooleanVar(value=settings.analysis.analyze_geography)
        self.opt_history = tk.BooleanVar(value=settings.analysis.analyze_history)
        self.opt_civics = tk.BooleanVar(value=settings.analysis.analyze_civics)
        self.opt_current = tk.BooleanVar(value=settings.analysis.analyze_current_affairs)
        self.opt_gemini = tk.BooleanVar(value=settings.analysis.use_gemini_detailed)
        
        ttk.Checkbutton(frame, text="地理", variable=self.opt_geography).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(frame, text="歴史", variable=self.opt_history).grid(row=0, column=1, sticky=tk.W)
        ttk.Checkbutton(frame, text="公民", variable=self.opt_civics).grid(row=0, column=2, sticky=tk.W)
        ttk.Checkbutton(frame, text="時事問題", variable=self.opt_current).grid(row=0, column=3, sticky=tk.W)
        
        # Geminiオプション（API キーがある場合のみ）
        if settings.api.gemini_api_key:
            ttk.Checkbutton(frame, text="Gemini詳細分析", variable=self.opt_gemini).grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
    
    def _create_result_section(self, parent):
        """結果表示セクション"""
        frame = ttk.LabelFrame(parent, text="分析結果", padding="10")
        frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # スクロール可能なテキストエリア
        self.result_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=20)
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
    
    def _create_button_section(self, parent):
        """ボタンセクション"""
        frame = ttk.Frame(parent)
        frame.grid(row=3, column=0, sticky=(tk.E), pady=(10, 0))
        
        ttk.Button(frame, text="分析開始", command=self.start_analysis).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(frame, text="Excel保存", command=self.save_excel).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(frame, text="終了", command=self.root.quit).grid(row=0, column=2)
    
    def select_file(self):
        """ファイル選択"""
        file_path = filedialog.askopenfilename(
            title="PDFファイルを選択",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            self.selected_file = file_path
            self.file_var.set(Path(file_path).name)
            
            # ファイル名から学校名と年度を推測
            filename = Path(file_path).stem
            import re
            
            # 年度抽出
            year_match = re.search(r'(\d{4})', filename)
            if year_match:
                self.year_var.set(year_match.group(1))
            
            # 学校名抽出
            school_match = re.search(r'([^0-9_]+)(?:中学|高校)?', filename)
            if school_match:
                self.school_var.set(school_match.group(1).strip())
    
    def start_analysis(self):
        """分析開始"""
        if not self.selected_file:
            messagebox.showwarning("警告", "PDFファイルを選択してください")
            return
        
        # オプション更新
        settings.analysis.analyze_geography = self.opt_geography.get()
        settings.analysis.analyze_history = self.opt_history.get()
        settings.analysis.analyze_civics = self.opt_civics.get()
        settings.analysis.analyze_current_affairs = self.opt_current.get()
        settings.analysis.use_gemini_detailed = self.opt_gemini.get()
        
        # プログレス表示
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "分析を開始します...\n")
        
        # 別スレッドで分析実行
        thread = threading.Thread(target=self._run_analysis)
        thread.daemon = True
        thread.start()
    
    def _run_analysis(self):
        """分析実行（別スレッド）"""
        try:
            # リクエスト作成
            request = AnalysisRequest(
                pdf_path=self.selected_file,
                school_name=self.school_var.get() or "不明",
                year=self.year_var.get() or "不明",
                options=settings.analysis,
                progress_callback=self._update_progress
            )
            
            # 分析実行
            self.analysis_result = self.service.analyze(request)
            
            # 結果表示
            self.root.after(0, self._display_results)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("エラー", f"分析中にエラーが発生しました:\n{e}"))
    
    def _update_progress(self, message: str):
        """プログレス更新"""
        self.root.after(0, lambda: self.result_text.insert(tk.END, f"{message}\n"))
    
    def _display_results(self):
        """結果表示"""
        self.result_text.delete(1.0, tk.END)
        
        if not self.analysis_result:
            self.result_text.insert(tk.END, "分析結果がありません\n")
            return
        
        # ヘッダー
        self.result_text.insert(tk.END, "=" * 60 + "\n")
        self.result_text.insert(tk.END, f"【分析結果】\n")
        self.result_text.insert(tk.END, f"学校: {self.analysis_result.school_name}\n")
        self.result_text.insert(tk.END, f"年度: {self.analysis_result.year}\n")
        self.result_text.insert(tk.END, f"総問題数: {self.analysis_result.total_questions}問\n")
        self.result_text.insert(tk.END, "=" * 60 + "\n\n")
        
        # 統計情報
        if self.analysis_result.statistics:
            self._display_statistics(self.analysis_result.statistics)
        
        # 問題リスト（最初の20問）
        if self.analysis_result.questions:
            self.result_text.insert(tk.END, "【問題一覧（抜粋）】\n")
            self.result_text.insert(tk.END, "-" * 40 + "\n")
            
            for q in self.analysis_result.questions[:20]:
                self._display_question(q)
            
            if len(self.analysis_result.questions) > 20:
                self.result_text.insert(tk.END, f"\n... 他 {len(self.analysis_result.questions) - 20} 問\n")
        
        self.result_text.insert(tk.END, "\n" + "=" * 60 + "\n")
        self.result_text.insert(tk.END, "分析完了！\n")
    
    def _display_statistics(self, stats: dict):
        """統計情報表示"""
        # 分野別
        if field_dist := stats.get('field_distribution'):
            self.result_text.insert(tk.END, "◆ 分野別分布:\n")
            for field, count in field_dist.items():
                self.result_text.insert(tk.END, f"  {field}: {count}問\n")
            self.result_text.insert(tk.END, "\n")
        
        # 形式別
        if format_dist := stats.get('format_distribution'):
            self.result_text.insert(tk.END, "◆ 出題形式分布:\n")
            for fmt, count in format_dist.items():
                self.result_text.insert(tk.END, f"  {fmt}: {count}問\n")
            self.result_text.insert(tk.END, "\n")
    
    def _display_question(self, question):
        """問題表示"""
        number = getattr(question, 'number', 'N/A')
        field = getattr(question, 'field', 'N/A')
        if hasattr(field, 'value'):
            field = field.value
        theme = getattr(question, 'theme', None) or getattr(question, 'topic', None) or '未設定'
        q_format = getattr(question, 'question_format', 'N/A')
        if hasattr(q_format, 'value'):
            q_format = q_format.value
        
        self.result_text.insert(tk.END, f"{number}: テーマ: {theme} | ジャンル: {field} | 形式: {q_format}\n")
    
    def save_excel(self):
        """Excel保存"""
        if not self.analysis_result:
            messagebox.showwarning("警告", "先に分析を実行してください")
            return
        
        # ファイル保存ダイアログ
        file_path = filedialog.asksaveasfilename(
            title="保存先を選択",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # TODO: Excel保存処理を実装
                from modules.social_excel_formatter import SocialExcelFormatter
                formatter = SocialExcelFormatter()
                formatter.format_and_save(
                    self.analysis_result.questions,
                    file_path,
                    self.analysis_result.school_name,
                    self.analysis_result.year
                )
                messagebox.showinfo("成功", f"Excelファイルを保存しました:\n{file_path}")
            except Exception as e:
                messagebox.showerror("エラー", f"保存中にエラーが発生しました:\n{e}")
    
    def run(self):
        """実行"""
        self.root.mainloop()