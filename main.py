#!/usr/bin/env python3
"""
社会科目入試問題分析システム メインプログラム
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import threading
from typing import Optional

# tkinterは後で条件付きでインポート
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

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
from modules.social_analyzer import SocialAnalyzer, SocialQuestion
from modules.social_excel_formatter import SocialExcelFormatter
from modules.gemini_theme_analyzer import GeminiThemeAnalyzer
from modules.question_number_normalizer import normalize_question_number, fix_duplicate_numbers
from modules.theme_refinement import ThemeRefiner
from modules.hierarchical_question_manager import HierarchicalQuestionManager

# ThemeKnowledgeBase（GUI用）
try:
    from modules.theme_knowledge_base import ThemeKnowledgeBase
    THEME_KNOWLEDGE_AVAILABLE = True
except ImportError:
    THEME_KNOWLEDGE_AVAILABLE = False

# Gemini Analyzer（オプション）
try:
    from modules.gemini_analyzer import GeminiAnalyzer
    from dotenv import load_dotenv
    load_dotenv()
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Gemini Bridge（詳細分析用）
try:
    from modules.gemini_bridge import GeminiBridge
    GEMINI_BRIDGE_AVAILABLE = True
except ImportError:
    GEMINI_BRIDGE_AVAILABLE = False
    logger.warning("GeminiBridge が利用できません")
    
# ヘルパー関数
def safe_get_field_value(field):
    """Enum型または文字列型のフィールド値を安全に文字列に変換"""
    if isinstance(field, str):
        return field
    elif hasattr(field, 'value'):
        return field.value
    else:
        return str(field)

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
        # ThemeKnowledgeBaseの初期化（利用可能な場合）
        if THEME_KNOWLEDGE_AVAILABLE:
            self.theme_knowledge = ThemeKnowledgeBase()
        else:
            self.theme_knowledge = None
        self.theme_refiner = ThemeRefiner()
        
        # GeminiBridgeの初期化（利用可能な場合）
        if GEMINI_BRIDGE_AVAILABLE:
            self.gemini_bridge = GeminiBridge()
            logger.info("GeminiBridge を初期化しました")
        else:
            self.gemini_bridge = None
        
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
        # デフォルト値は現在の年に設定
        from datetime import datetime
        self.year_entry.insert(0, str(datetime.now().year))
        
        # 分析オプションセクション
        option_frame = ttk.LabelFrame(main_frame, text="分析オプション", padding="10")
        option_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.analyze_geography = tk.BooleanVar(value=True)
        self.analyze_history = tk.BooleanVar(value=True)
        self.analyze_civics = tk.BooleanVar(value=True)
        self.analyze_current = tk.BooleanVar(value=True)
        self.analyze_resources = tk.BooleanVar(value=True)
        self.use_gemini = tk.BooleanVar(value=False)
        
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
        
        # Gemini API オプション（利用可能な場合のみ表示）
        if GEMINI_AVAILABLE:
            gemini_checkbox = ttk.Checkbutton(option_frame, text="Gemini AI分析を使用（高精度）", 
                           variable=self.use_gemini)
            gemini_checkbox.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
            
            # API キーの確認
            import os
            if not os.getenv('GEMINI_API_KEY'):
                gemini_checkbox.config(state=tk.DISABLED)
                ttk.Label(option_frame, text="※ GEMINI_API_KEY が設定されていません", 
                         foreground="red").grid(row=3, column=0, columnspan=3, sticky=tk.W)
        
        # Gemini詳細分析オプション（GeminiBridge利用可能な場合）
        # デフォルトでON
        self.use_gemini_detailed = tk.BooleanVar(value=True)
        if GEMINI_BRIDGE_AVAILABLE and self.gemini_bridge:
            if self.gemini_bridge.check_availability():
                ttk.Checkbutton(option_frame, text="Gemini詳細分析を使用（最高精度・一問一問分析）", 
                               variable=self.use_gemini_detailed).grid(
                    row=4, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
            else:
                ttk.Label(option_frame, text="※ Gemini詳細分析は利用できません", 
                         foreground="gray").grid(row=4, column=0, columnspan=3, sticky=tk.W)
        
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
        
        self.save_text_button = ttk.Button(button_frame, text="テキスト保存", 
                                          command=self.save_text,
                                          state=tk.DISABLED)
        self.save_text_button.grid(row=0, column=2, padx=5)
        
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
            
            # ファイル名から学校名と年度を推測
            filename = Path(file_path).stem
            
            # 年度を抽出
            year = self._extract_year_from_filename(filename)
            if year:
                # ファイルから年度が抽出できた場合は、既存の値をクリアして新しい値を設定
                self.year_entry.delete(0, tk.END)
                self.year_entry.insert(0, str(year))
            
            # 学校名を抽出（年度情報を除去してから）
            # 年度パターンを除去
            import re
            school_name = filename
            # 年度パターンを削除（「度」も含めて削除）
            school_name = re.sub(r'20\d{2}年度?', '', school_name)
            school_name = re.sub(r'令和\d+年度?', '', school_name)
            school_name = re.sub(r'R\d+年?度?', '', school_name)
            school_name = re.sub(r'平成\d+年度?', '', school_name)
            school_name = re.sub(r'H\d+年?度?', '', school_name)
            school_name = re.sub(r'\d{2}年度?', '', school_name)
            # 前後の不要な文字（アンダースコア、ハイフン、スペース）を削除
            school_name = re.sub(r'^[_\-\s]+', '', school_name)
            school_name = re.sub(r'[_\-\s]+$', '', school_name)
            # アンダースコアで分割して最初の部分を取得
            school_name = school_name.split('_')[0] if '_' in school_name else school_name
            # 「問題」で分割して学校名部分のみ取得
            school_name = school_name.split('問題')[0] if '問題' in school_name else school_name
            # 最終的なクリーンアップ
            school_name = school_name.strip()
            if school_name:
                # 既存の値をクリアして新しい値を設定
                self.school_entry.delete(0, tk.END)
                self.school_entry.insert(0, school_name)

    def _extract_year_from_filename(self, filename: str) -> Optional[int]:
        """
        ファイル名から年度を抽出
        
        対応パターン:
        - 2023年、2023
        - 令和5年、令和5、R5
        - 平成31年、平成31、H31
        - 23年（2000年代として解釈）
        """
        import re
        from datetime import datetime
        
        # 現在の年を取得（上限チェック用）
        current_year = datetime.now().year
        
        # 1. 4桁の西暦年（2020年、2020など）
        match = re.search(r'(20\d{2})年?', filename)
        if match:
            year = int(match.group(1))
            if 2000 <= year <= current_year + 1:  # 未来の入試問題も考慮
                return year
        
        # 2. 令和年号（令和5年、令和5、R5など）
        match = re.search(r'令和(\d+)年?', filename)
        if match:
            reiwa_year = int(match.group(1))
            return 2018 + reiwa_year  # 令和元年 = 2019年
        
        match = re.search(r'R(\d+)年?', filename)
        if match:
            reiwa_year = int(match.group(1))
            return 2018 + reiwa_year
        
        # 3. 平成年号（平成31年、平成31、H31など）
        match = re.search(r'平成(\d+)年?', filename)
        if match:
            heisei_year = int(match.group(1))
            return 1988 + heisei_year  # 平成元年 = 1989年
        
        match = re.search(r'H(\d+)年?', filename)
        if match:
            heisei_year = int(match.group(1))
            return 1988 + heisei_year
        
        # 4. 2桁の年（23年など）- 2000年代として解釈
        match = re.search(r'(\d{2})年', filename)
        if match:
            two_digit_year = int(match.group(1))
            # 00-99の範囲で、現在の年の下2桁より大きければ1900年代、そうでなければ2000年代
            current_two_digit = current_year % 100
            if two_digit_year <= current_two_digit + 1:
                return 2000 + two_digit_year
            elif two_digit_year >= 90:  # 90年代は1990年代と解釈
                return 1900 + two_digit_year
            else:
                return 2000 + two_digit_year
        
        # 年度が見つからない場合はNoneを返す
        return None
    
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
    
    def normalize_question_number(self, number: str) -> str:
        """問題番号を正規化"""
        import re
        # "問-" のような不正な番号を修正
        normalized = number
        
        # "問-" を "問" に修正
        normalized = re.sub(r'問[-－ー]+', '問', normalized)
        
        # "問問" を "問" に修正
        normalized = re.sub(r'問問+', '問', normalized)
        
        # "間1" を "問1" に修正（OCRエラー）
        normalized = re.sub(r'間(\d)', r'問\1', normalized)
        
        # 数字なしの "問" を "問1" に修正
        if re.match(r'^[大]?問$', normalized):
            normalized = normalized + "1"
        
        # 大問X-問- を 大問X-問1 に修正
        normalized = re.sub(r'(大問\d+)-問$', r'\1-問1', normalized)
        
        return normalized
    
    def fix_duplicate_numbers(self, questions):
        """重複する問題番号を修正"""
        seen_numbers = {}
        for q in questions:
            if hasattr(q, 'number'):
                original = q.number
                # 正規化
                normalized = self.normalize_question_number(original)
                
                # 重複チェック
                if normalized in seen_numbers:
                    # 重複の場合はサフィックスを追加
                    count = seen_numbers[normalized] + 1
                    seen_numbers[normalized] = count
                    q.number = f"{normalized}-{count}"
                else:
                    seen_numbers[normalized] = 1
                    q.number = normalized
        
        return questions
    
    def run_analysis(self):
        """分析処理の実行"""
        try:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "分析を開始しています...\n")
            
            # Gemini詳細分析を優先的に使用
            if self.use_gemini_detailed.get() and self.gemini_bridge:
                self.run_gemini_detailed_analysis()
                return
            
            # Gemini API を使用するかチェック
            if GEMINI_AVAILABLE and self.use_gemini.get():
                import os
                api_key = os.getenv('GEMINI_API_KEY')
                if api_key:
                    self.result_text.insert(tk.END, "Gemini AI による高精度分析を実行中...\n")
                    self.run_gemini_analysis(api_key)
                    return
                else:
                    self.result_text.insert(tk.END, "警告: GEMINI_API_KEY が設定されていません\n")
                    self.result_text.insert(tk.END, "従来の分析方法に切り替えます...\n\n")
            
            # PDFからテキスト抽出
            self.result_text.insert(tk.END, "PDFからテキストを抽出中...\n")
            text = self.ocr_handler.process_pdf(self.selected_file)
            
            # 階層的な問題番号管理システムで問題を抽出
            hierarchy_manager = HierarchicalQuestionManager()
            hierarchical_questions = hierarchy_manager.extract_hierarchical_questions(text)
            flattened_questions = hierarchy_manager.get_flattened_questions()
            
            # 「問-」などの不正な番号を修正
            if hasattr(hierarchy_manager, 'fix_invalid_numbers'):
                flattened_questions = hierarchy_manager.fix_invalid_numbers(flattened_questions)
            
            self.result_text.insert(tk.END, f"階層構造で{len(flattened_questions)}個の問題を検出\n")
            
            if not text:
                raise Exception("テキストの抽出に失敗しました")
            
            self.result_text.insert(tk.END, f"テキスト抽出完了（{len(text)}文字）\n\n")
            
            # 分析実行
            self.result_text.insert(tk.END, "問題を分析中...\n")
            self.analysis_result = self.analyzer.analyze_document_with_hierarchy(text, flattened_questions) if hasattr(self.analyzer, 'analyze_document_with_hierarchy') else self.analyzer.analyze_document(text)
            
            # デバッグ: 分析結果の確認
            if self.analysis_result:
                logger.info(f"分析結果のキー: {self.analysis_result.keys()}")
                if 'statistics' in self.analysis_result:
                    logger.info(f"統計情報のキー: {self.analysis_result['statistics'].keys()}")
                else:
                    logger.warning("統計情報が生成されていません")
            
            # Gemini APIによるテーマ分析強化（必須）
            if self.analysis_result and 'questions' in self.analysis_result:
                self.result_text.insert(tk.END, "Gemini APIでテーマを分析中...\n")
                try:
                    from modules.gemini_theme_analyzer import GeminiThemeAnalyzer
                    gemini_analyzer = GeminiThemeAnalyzer()
                    
                    if gemini_analyzer.api_enabled:
                        # 全問題をGemini APIで分析
                        questions = self.analysis_result['questions']
                        questions = gemini_analyzer.analyze_all_questions_with_api(questions)
                        self.analysis_result['questions'] = questions
                        self.result_text.insert(tk.END, "Gemini APIによるテーマ分析完了\n")
                    else:
                        self.result_text.insert(tk.END, "警告: Gemini APIが利用できません\n")
                except Exception as e:
                    logger.error(f"Gemini API分析エラー: {e}")
                    self.result_text.insert(tk.END, f"Gemini API分析エラー: {e}\n")
            
            # 分析結果の後処理
            if self.analysis_result and 'questions' in self.analysis_result:
                self.result_text.insert(tk.END, "分析結果を精緻化中...\n")
                
                # 問題番号の正規化
                questions = self.analysis_result['questions']
                questions = self.fix_duplicate_numbers(questions)
                
                # テーマの精緻化
                questions = self.theme_refiner.refine_all_themes(questions)
                
                self.analysis_result['questions'] = questions
                
                # 統計情報の再計算（統計情報が存在しない場合）
                if 'statistics' not in self.analysis_result or not self.analysis_result['statistics']:
                    logger.info("統計情報を再計算中...")
                    self.analysis_result['statistics'] = self.analyzer._calculate_statistics(questions)
                    
                self.result_text.insert(tk.END, "精緻化完了\n\n")
            
            # 結果表示
            self.display_results()
            
            # ボタンを有効化
            self.root.after(0, self.enable_save_button)
            
        except Exception as e:
            logger.error(f"分析エラー: {e}")
            self.root.after(0, lambda: messagebox.showerror("エラー", f"分析中にエラーが発生しました:\n{str(e)}"))
        
        finally:
            self.root.after(0, self.stop_progress)
    
    def run_gemini_detailed_analysis(self):
        """Gemini詳細分析の実行"""
        try:
            self.result_text.insert(tk.END, "\n【Gemini詳細分析モード】\n")
            self.result_text.insert(tk.END, "各問題を一問一問詳細に分析します...\n\n")
            
            # プログレスコールバック
            def progress_callback(message):
                self.root.after(0, lambda: self.result_text.insert(tk.END, f"  {message}\n"))
                self.root.update_idletasks()
            
            # 分析実行
            self.result_text.insert(tk.END, f"PDF: {Path(self.selected_file).name}\n")
            result = self.gemini_bridge.analyze_pdf(self.selected_file, progress_callback)
            
            # デバッグ情報
            logger.info(f"Gemini詳細分析結果: questions={len(result.get('questions', []))}, source={result.get('source')}")
            
            # 結果を保存
            self.analysis_result = result
            
            # サマリー表示
            summary = self.gemini_bridge.get_summary_text(result)
            self.result_text.insert(tk.END, "\n" + summary + "\n")
            
            # 詳細結果表示
            self.display_results()
            
            # ボタンを有効化
            self.root.after(0, self.enable_save_button)
            
        except Exception as e:
            logger.error(f"Gemini詳細分析エラー: {e}")
            self.result_text.insert(tk.END, f"\n❌ エラー: {e}\n")
            self.result_text.insert(tk.END, "従来の分析方法にフォールバックします...\n\n")
            
            # フォールバック：従来の分析を実行
            self.use_gemini_detailed.set(False)
            self.run_analysis()
    
    def run_gemini_analysis(self, api_key):
        """Gemini APIを使用した分析"""
        try:
            # Gemini Analyzer の初期化
            gemini_analyzer = GeminiAnalyzer(api_key)
            
            school = self.school_entry.get()
            year = self.year_entry.get()
            
            # Vision API を優先して使用
            self.result_text.insert(tk.END, f"\n学校: {school}\n")
            self.result_text.insert(tk.END, f"年度: {year}\n\n")
            self.result_text.insert(tk.END, "PDFを画像として解析中...\n")
            
            # Vision API による分析
            result = gemini_analyzer.analyze_pdf_with_vision(
                pdf_path=self.selected_file,
                school=school,
                year=year
            )
            
            # Gemini の結果を既存のフォーマットに変換
            self.analysis_result = self._convert_gemini_result(result)
            
            # 分析結果の後処理
            if self.analysis_result and 'questions' in self.analysis_result:
                self.result_text.insert(tk.END, "分析結果を精緻化中...\n")
                
                # 問題番号の正規化
                questions = self.analysis_result['questions']
                questions = self.fix_duplicate_numbers(questions)
                
                # テーマの精緻化
                questions = self.theme_refiner.refine_all_themes(questions)
                
                self.analysis_result['questions'] = questions
                self.result_text.insert(tk.END, "精緻化完了\n\n")
            
            # 結果表示
            self.result_text.insert(tk.END, "\n分析完了！\n")
            self.result_text.insert(tk.END, "=" * 60 + "\n")
            self.result_text.insert(tk.END, gemini_analyzer.format_analysis_result(result))
            
            # 詳細な結果も表示
            self.display_results()
            
            # ボタンを有効化
            self.root.after(0, self.enable_save_button)
            
        except Exception as e:
            logger.error(f"Gemini分析エラー: {e}")
            # フォールバック
            self.result_text.insert(tk.END, f"\nGemini分析エラー: {e}\n")
            self.result_text.insert(tk.END, "従来の分析方法にフォールバック...\n\n")
            
            # 従来の分析を実行
            text = self.ocr_handler.process_pdf(self.selected_file)
            
            # 階層的な問題番号管理システムで問題を抽出
            hierarchy_manager = HierarchicalQuestionManager()
            hierarchical_questions = hierarchy_manager.extract_hierarchical_questions(text)
            flattened_questions = hierarchy_manager.get_flattened_questions()
            
            # 「問-」などの不正な番号を修正
            if hasattr(hierarchy_manager, 'fix_invalid_numbers'):
                flattened_questions = hierarchy_manager.fix_invalid_numbers(flattened_questions)
            
            self.result_text.insert(tk.END, f"階層構造で{len(flattened_questions)}個の問題を検出\n")
            if text:
                self.analysis_result = self.analyzer.analyze_document_with_hierarchy(text, flattened_questions) if hasattr(self.analyzer, 'analyze_document_with_hierarchy') else self.analyzer.analyze_document(text)
                self.display_results()
                self.root.after(0, self.enable_save_button)
    
    def _convert_gemini_result(self, gemini_result):
        """Gemini の結果を既存のフォーマットに変換"""
        from models import Question
        
        # 質問オブジェクトのリストを作成
        questions = []
        question_id = 1
        
        for section in gemini_result.get('sections', []):
            section_num = section['section_number']
            
            for q in section.get('questions', []):
                # Question オブジェクトを作成
                question = Question(
                    number=f"大問{section_num}-問{q['question_number']}",
                    text=q.get('question_summary', q.get('question_text', '')),
                    field=q.get('field', '総合'),
                    theme=', '.join(q.get('keywords', [])) if q.get('keywords') else ''
                )
                questions.append(question)
                question_id += 1
        
        # 統計情報を生成
        summary = gemini_result.get('summary', {})
        
        statistics = {
            'field_distribution': {
                '地理': {
                    'count': summary.get('geography_count', 0),
                    'percentage': (summary.get('geography_count', 0) / max(summary.get('total_questions', 1), 1)) * 100
                },
                '歴史': {
                    'count': summary.get('history_count', 0),
                    'percentage': (summary.get('history_count', 0) / max(summary.get('total_questions', 1), 1)) * 100
                },
                '公民': {
                    'count': summary.get('civics_count', 0),
                    'percentage': (summary.get('civics_count', 0) / max(summary.get('total_questions', 1), 1)) * 100
                },
                '時事': {
                    'count': summary.get('current_affairs_count', 0),
                    'percentage': (summary.get('current_affairs_count', 0) / max(summary.get('total_questions', 1), 1)) * 100
                }
            },
            'resource_usage': {},
            'format_distribution': {},
            'current_affairs': {
                'count': summary.get('current_affairs_count', 0),
                'percentage': (summary.get('current_affairs_count', 0) / max(summary.get('total_questions', 1), 1)) * 100
            }
        }
        
        return {
            'questions': questions,
            'total_questions': summary.get('total_questions', len(questions)),
            'statistics': statistics,
            'school': gemini_result.get('school', ''),
            'year': gemini_result.get('year', ''),
            'gemini_analysis': True  # フラグを追加
        }
    
    def display_results(self):
        """分析結果を表示"""
        if not self.analysis_result:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "分析結果がありません。\n")
            return
        
        # statisticsが存在しない場合のフォールバック
        if 'statistics' not in self.analysis_result:
            logger.warning("statistics が分析結果に存在しません")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "分析結果の統計情報が不完全です。\n")
            # 基本情報だけでも表示
            if 'total_questions' in self.analysis_result:
                self.result_text.insert(tk.END, f"\n総問題数: {self.analysis_result['total_questions']}問\n")
            if 'questions' in self.analysis_result:
                self.result_text.insert(tk.END, f"\n検出された問題:\n")
                for i, q in enumerate(self.analysis_result['questions'][:10], 1):
                    num = getattr(q, 'number', f'問題{i}')
                    theme = getattr(q, 'theme', '（テーマなし）')
                    self.result_text.insert(tk.END, f"  {num}: {theme}\n")
                if len(self.analysis_result['questions']) > 10:
                    self.result_text.insert(tk.END, f"  ...他{len(self.analysis_result['questions'])-10}問\n")
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
        if 'field_distribution' in stats and stats['field_distribution']:
            for field, data in stats['field_distribution'].items():
                # dataが辞書であることを確認
                if isinstance(data, dict) and 'count' in data and 'percentage' in data:
                    self.result_text.insert(tk.END, 
                        f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)\n")
                else:
                    logger.warning(f"field_distribution のデータ形式が不正: {field}={data}")
        else:
            self.result_text.insert(tk.END, "  （データなし）\n")
        
        self.result_text.insert(tk.END, "\n")
        
        # 資料活用状況
        self.result_text.insert(tk.END, "【資料活用状況】\n")
        if 'resource_usage' in stats and stats['resource_usage']:
            # ソート可能なデータのみ処理
            valid_resources = [(k, v) for k, v in stats['resource_usage'].items() 
                              if isinstance(v, dict) and 'count' in v]
            if valid_resources:
                for resource, data in sorted(valid_resources, 
                                            key=lambda x: x[1].get('count', 0), 
                                            reverse=True)[:5]:
                    self.result_text.insert(tk.END, 
                        f"  {resource:10s}: {data['count']:3d}回 ({data['percentage']:5.1f}%)\n")
            else:
                self.result_text.insert(tk.END, "  （データなし）\n")
        else:
            self.result_text.insert(tk.END, "  （データなし）\n")
        
        self.result_text.insert(tk.END, "\n")
        
        # 出題形式
        self.result_text.insert(tk.END, "【出題形式分布】\n")
        if 'format_distribution' in stats and stats['format_distribution']:
            # ソート可能なデータのみ処理
            valid_formats = [(k, v) for k, v in stats['format_distribution'].items() 
                            if isinstance(v, dict) and 'count' in v]
            if valid_formats:
                for format_type, data in sorted(valid_formats,
                                               key=lambda x: x[1].get('count', 0),
                                               reverse=True)[:5]:
                    self.result_text.insert(tk.END, 
                        f"  {format_type:10s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)\n")
            else:
                self.result_text.insert(tk.END, "  （データなし）\n")
        else:
            self.result_text.insert(tk.END, "  （データなし）\n")
        
        self.result_text.insert(tk.END, "\n")
        
        # 時事問題
        self.result_text.insert(tk.END, "【時事問題】\n")
        if 'current_affairs' in stats and isinstance(stats['current_affairs'], dict):
            self.result_text.insert(tk.END, 
                f"  時事問題: {stats['current_affairs']['count']}問 "
                f"({stats['current_affairs']['percentage']:.1f}%)\n")
        
        self.result_text.insert(tk.END, "\n")
        
        # テーマ一覧（大問ごとに区切って表示）
        self.result_text.insert(tk.END, "【出題テーマ一覧】\n")
        questions = self.analysis_result.get('questions', [])
        
        if questions:
            # 大問ごとにグループ化
            # 階層情報がある場合はそれを優先、なければ問題番号から抽出
            normalized_map = {}
            order = []
            for q in questions:
                # 階層IDがある場合は大問番号として使用
                if hasattr(q, 'hierarchy_id') and q.hierarchy_id:
                    # hierarchy_idの最初の部分が大問番号
                    major_num = q.hierarchy_id.split('-')[0]
                else:
                    # 階層情報がない場合は従来の方法
                    major_num = self._extract_major_number(q.number)
                
                if major_num not in normalized_map:
                    order.append(major_num)
                    normalized_map[major_num] = major_num  # 正規化せずそのまま使用

            grouped_themes = {}
            for q in questions:
                # 階層情報を優先的に使用
                if hasattr(q, 'hierarchy_id') and q.hierarchy_id:
                    major_num = q.hierarchy_id.split('-')[0]
                else:
                    major_num_raw = self._extract_major_number(q.number)
                    major_num = normalized_map.get(major_num_raw, major_num_raw)
                if major_num not in grouped_themes:
                    grouped_themes[major_num] = []

                # テーマがない場合は使用語句や分野から推定（できるだけ具体化）
                # Gemini APIの結果（topic）を優先、なければtheme
                topic = getattr(q, 'topic', None) or getattr(q, 'theme', None)
                if not topic:
                    base_text = getattr(q, 'original_text', None) or q.text
                    topic = self._infer_fallback_theme(base_text, safe_get_field_value(q.field))

                grouped_themes[major_num].append((q.number, topic if topic else '（テーマ不明）', safe_get_field_value(q.field)))
            
            # 大問ごとに表示
            # 数値としてソート
            def _to_int(s):
                try:
                    return int(s)
                except:
                    return 0
            for major_num in sorted(grouped_themes.keys(), key=_to_int):
                if len(grouped_themes) > 1:
                    self.result_text.insert(tk.END, f"\n▼ 大問 {major_num}\n")
                    self.result_text.insert(tk.END, "-" * 40 + "\n")
                
                themes = grouped_themes[major_num]
                if themes:
                    for num, theme, field in themes:
                        # 分野も併記してより分かりやすく
                        display_num = num
                        try:
                            import re
                            m = re.search(r'大問(\d+)[\-－―]?問?\s*(.+)', num)
                            if m:
                                # 正規化した大問番号で置換
                                norm = normalized_map.get(m.group(1), m.group(1))
                                display_num = f"問{m.group(2)}"
                        except Exception:
                            pass
                        # 出題形式を取得
                        q_format = ''
                        try:
                            # 元のオブジェクトから検索
                            for q in self.analysis_result.get('questions', []):
                                if q.number == num:
                                    q_format = getattr(q, 'question_format', None)
                                    if q_format and hasattr(q_format, 'value'):
                                        q_format = q_format.value
                                    elif q_format:
                                        q_format = str(q_format)
                                    else:
                                        q_format = ''
                                    break
                        except Exception:
                            q_format = ''
                        
                        # テーマ、ジャンル、出題形式を併記
                        if q_format:
                            self.result_text.insert(tk.END, f"  {display_num}: テーマ: {theme} | ジャンル: {field} | 出題形式: {q_format}\n")
                        else:
                            self.result_text.insert(tk.END, f"  {display_num}: テーマ: {theme} | ジャンル: {field}\n")
                else:
                    self.result_text.insert(tk.END, "  （テーマ情報なし）\n")
        else:
            self.result_text.insert(tk.END, "  （問題が検出されませんでした）\n")
        
        # 分野別主要語一覧を追加
        self.result_text.insert(tk.END, "\n" + "=" * 60 + "\n")
        self.result_text.insert(tk.END, "【分野別主要語一覧】\n")
        self.result_text.insert(tk.END, "-" * 40 + "\n")
        
        # 分野別にキーワードを集計
        field_keywords = {
            '地理': set(),
            '歴史': set(),
            '公民': set(),
            '時事問題': set(),
            'その他': set()
        }
        
        questions = self.analysis_result.get('questions', [])
        for q in questions:
            field = safe_get_field_value(q.field)
            if field not in field_keywords:
                field = 'その他'
            
            keywords = getattr(q, 'keywords', [])
            if keywords:
                for kw in keywords:
                    if kw and len(kw) > 1:  # 1文字のキーワードは除外
                        field_keywords[field].add(kw)
        
        # 分野別に表示
        for field in ['地理', '歴史', '公民', '時事問題', 'その他']:
            if keywords := field_keywords.get(field):
                self.result_text.insert(tk.END, f"\n【{field}】\n")
                sorted_keywords = sorted(list(keywords))
                # 5個ずつ改行して表示
                for i in range(0, len(sorted_keywords), 5):
                    batch = sorted_keywords[i:i+5]
                    self.result_text.insert(tk.END, f"  {', '.join(batch)}\n")
        
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

    def save_text(self):
        """テキスト形式でテーマ一覧を保存"""
        if not self.analysis_result:
            messagebox.showwarning("警告", "先に分析を実行してください")
            return
        
        # 保存先ディレクトリを固定
        save_dir = Path("/Users/yoshiikatsuhiko/Desktop/過去問_社会")
        
        # ディレクトリが存在しない場合は作成
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"保存先ディレクトリの作成エラー: {e}")
            messagebox.showerror("エラー", f"保存先ディレクトリを作成できませんでした：\n{str(e)}")
            return
        
        # ファイル名を生成
        school_name = self.school_entry.get()
        year = self.year_entry.get()
        filename = f"{school_name}_{year}_テーマ一覧_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = save_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # ヘッダー情報
                f.write("=" * 60 + "\n")
                f.write(f"社会科入試問題分析 - テーマ一覧\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"学校名: {school_name}\n")
                f.write(f"年度: {year}年\n")
                f.write(f"分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
                f.write(f"総問題数: {self.analysis_result['total_questions']}問\n\n")
                
                # 分野別出題状況
                stats = self.analysis_result['statistics']
                f.write("【分野別出題状況】\n")
                if 'field_distribution' in stats:
                    for field, data in stats['field_distribution'].items():
                        f.write(f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)\n")
                f.write("\n")
                
                # テーマ一覧（大問ごと）
                f.write("【出題テーマ一覧】\n")
                questions = self.analysis_result.get('questions', [])
                
                if questions:
                    # 大問ごとにグループ化（display_resultsと同じロジック）
                    # 大問番号を正規化（異常値を修正）
                    raw_groups = []
                    for q in questions:
                        raw_major = self._extract_major_number(q.number)
                        # 異常な大問番号を検出（10以上は異常）
                        if raw_major.isdigit() and int(raw_major) > 10:
                            logger.warning(f"異常な大問番号検出: {raw_major}")
                        raw_groups.append(raw_major)
                    
                    # 順番に1から番号を振り直す
                    normalized_map = {}
                    order = []
                    for m in raw_groups:
                        if m not in normalized_map:
                            order.append(m)
                            # 常に1から順番に番号を振る
                            normalized_map[m] = str(len(order))
                    
                    grouped_themes = {}
                    for q in questions:
                        major_num_raw = self._extract_major_number(q.number)
                        major_num = normalized_map.get(major_num_raw, major_num_raw)
                        if major_num not in grouped_themes:
                            grouped_themes[major_num] = []
                        
                        # テーマがない場合は推定（topicを優先、なければtheme）
                        topic = getattr(q, 'topic', None) or getattr(q, 'theme', None)
                        if not topic:
                            base_text = getattr(q, 'original_text', None) or q.text
                            topic = self._infer_fallback_theme(base_text, safe_get_field_value(q.field))
                        # 重要語は subject_index.md の語のみから抽出
                        base_text = getattr(q, 'original_text', None) or q.text or ''
                        keywords = self.theme_knowledge.extract_important_terms(base_text, safe_get_field_value(q.field), limit=5)
                        
                        # Gemini APIによる更新結果を確認して保存
                        final_topic = topic if topic else '（テーマ不明）'
                        grouped_themes[major_num].append((q.number, final_topic, safe_get_field_value(q.field), keywords[:5]))
                    
                    # 大問ごとに出力
                    def _to_int(s):
                        try:
                            return int(s)
                        except:
                            return 0
                    
                    for major_num in sorted(grouped_themes.keys(), key=_to_int):
                        if len(grouped_themes) > 1:
                            f.write(f"\n▼ 大問 {major_num}\n")
                            f.write("-" * 40 + "\n")
                        
                        themes = grouped_themes[major_num]
                        if themes:
                            for num, theme, field, keywords in themes:
                                # 問題番号を整形
                                display_num = num
                                try:
                                    import re
                                    m = re.search(r'大問(\d+)[\-－‐]?問?\s*(.+)', num)
                                    if m:
                                        norm = normalized_map.get(m.group(1), m.group(1))
                                        display_num = f"問{m.group(2)}"
                                except Exception:
                                    pass
                                # 関連語候補
                                related = []
                                try:
                                    related = self.theme_knowledge.suggest_related_terms(theme, field, limit=3)
                                except Exception:
                                    related = []
                                if keywords and related:
                                    related = [r for r in related if r not in keywords]
                                if keywords and related:
                                    f.write(f"  {display_num}: {theme} [{field}] | 主要語: {'、'.join(keywords)} | 関連語候補: {'、'.join(related)}\n")
                                elif keywords:
                                    f.write(f"  {display_num}: {theme} [{field}] | 主要語: {'、'.join(keywords)}\n")
                                elif related:
                                    f.write(f"  {display_num}: {theme} [{field}] | 関連語候補: {'、'.join(related)}\n")
                                else:
                                    f.write(f"  {display_num}: {theme} [{field}]\n")
                        else:
                            f.write("  （テーマ情報なし）\n")
                else:
                    f.write("  （問題が検出されませんでした）\n")
                
                f.write("\n")
                f.write("=" * 60 + "\n")
                f.write("分析終了\n")
            
            # Gemini検証を実行
            try:
                from modules.gemini_validator import GeminiValidator
                validator = GeminiValidator()
                
                if validator.enabled:
                    logger.info("Gemini検証を実行中...")
                    # ファイルを読み込み
                    with open(file_path, 'r', encoding='utf-8') as f:
                        original_text = f.read()
                    
                    # 検証・修正
                    fixed_text = validator.validate_and_fix(original_text)
                    
                    # 修正があった場合は上書き保存
                    if fixed_text != original_text:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_text)
                        logger.info("Gemini検証により出力を修正しました")
                        messagebox.showinfo("完了", f"テーマ一覧を保存しました（Gemini検証済み）：\n{file_path}")
                    else:
                        messagebox.showinfo("完了", f"テーマ一覧を保存しました：\n{file_path}")
                else:
                    logger.info("Gemini検証はスキップされました（APIキー未設定）")
                    messagebox.showinfo("完了", f"テーマ一覧を保存しました：\n{file_path}")
                    
            except Exception as e:
                logger.warning(f"Gemini検証をスキップ: {e}")
                messagebox.showinfo("完了", f"テーマ一覧を保存しました：\n{file_path}")
            
            logger.info(f"テーマ一覧を保存: {file_path}")
            
        except Exception as e:
            logger.error(f"テキスト保存エラー: {e}")
            messagebox.showerror("エラー", f"保存中にエラーが発生しました：\n{str(e)}")
    
    def enable_save_button(self):
        """保存ボタンを有効化"""
        self.save_button.config(state=tk.NORMAL)
        self.save_text_button.config(state=tk.NORMAL)
        self.analyze_button.config(state=tk.NORMAL)
    
    def stop_progress(self):
        """プログレスバーを停止"""
        self.progress.stop()

    def _extract_major_number(self, number_str: str) -> str:
        """設問番号文字列から大問番号を堅牢に抽出"""
        try:
            import re
            # パターン1: 大問X-問Y / 大問X
            m = re.search(r'大問(\d+)', number_str)
            if m:
                # 大問番号は出現順で別途正規化するため、
                # ここでは数値をそのまま返す（異常値はログのみ）
                major_num = int(m.group(1))
                if major_num > 10:
                    logger.warning(f"異常な大問番号を検出: {major_num}")
                return str(major_num)
            # パターン2: X-問Y / X.Y
            m2 = re.match(r'\s*(\d+)[\-\.]', number_str)
            if m2:
                return m2.group(1)
            # パターン3: 単独の問題番号は大問1として扱う
            # 10問ごとのグループ化は削除（階層管理システムに任せる）
            if '問' in number_str:
                return '1'
        except:
            pass
        return '1'

    def _infer_fallback_theme(self, text: str, field_label: str) -> str:
        """テーマ未検出時の推定（カリキュラムと主題インデックスを参照）"""
        try:
            # 知識ベースが利用可能な場合のみ使用
            if self.theme_knowledge and hasattr(self.theme_knowledge, 'determine_theme'):
                theme = self.theme_knowledge.determine_theme(text, field_label)
                if theme and theme != "分析対象外":
                    return theme
        except Exception as e:
            logger.warning(f"テーマ推定エラー: {e}")
        
        # より具体的なフォールバック処理
        if not text:
            return f"{field_label}総合問題"
        
        # テキストからキーワードを抽出して具体的なテーマを生成
        keywords = []
        if "農業" in text or "栽培" in text:
            keywords.append("農業")
        if "憲法" in text:
            keywords.append("憲法")
        if "選挙" in text:
            keywords.append("選挙")
        if "貿易" in text:
            keywords.append("貿易")
        
        if keywords:
            return ", ".join(keywords[:3])
        else:
            return f"{field_label}総合問題"




if __name__ == "__main__":
    # GUI版のみを起動
    if not TKINTER_AVAILABLE:
        print("エラー: GUI版を実行するにはtkinterが必要です")
        sys.exit(1)
    
    root = tk.Tk()
    app = SocialExamAnalyzerGUI(root)
    root.mainloop()
