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
            # まず出現順で大問番号の正規化マップを作成（1..Nに再割当）
            raw_groups = []
            for q in questions:
                raw_major = self._extract_major_number(q.number)
                raw_groups.append(raw_major)
            normalized_map = {}
            order = []
            for m in raw_groups:
                if m not in normalized_map:
                    order.append(m)
                    normalized_map[m] = str(len(order))
            # 異常に大きい番号（例: 14,22 など）は並び順に応じて再割当される

            grouped_themes = {}
            for q in questions:
                major_num_raw = self._extract_major_number(q.number)
                major_num = normalized_map.get(major_num_raw, major_num_raw)
                if major_num not in grouped_themes:
                    grouped_themes[major_num] = []

                # テーマがない場合は使用語句や分野から推定（できるだけ具体化）
                topic = q.topic
                if not topic:
                    base_text = getattr(q, 'original_text', None) or q.text
                    topic = self._infer_fallback_theme(base_text, q.field.value)

                grouped_themes[major_num].append((q.number, topic if topic else '（テーマ不明）', q.field.value))
            
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
                        self.result_text.insert(tk.END, f"  {display_num}: {theme} [{field}]\n")
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

    def _extract_major_number(self, number_str: str) -> str:
        """設問番号文字列から大問番号を堅牢に抽出"""
        try:
            import re
            # パターン1: 大問X-問Y / 大問X
            m = re.search(r'大問(\d+)', number_str)
            if m:
                major_num = int(m.group(1))
                # 異常値チェック（中学入試で大問10以上は稀）
                if major_num > 10:
                    # 問22が誤って大問22になった場合の補正
                    logger.warning(f"異常な大問番号を検出: {major_num} → 補正")
                    return str((major_num - 1) // 10 + 1)
                return str(major_num)
            # パターン2: X-問Y / X.Y
            m2 = re.match(r'\s*(\d+)[\-\.]', number_str)
            if m2:
                return m2.group(1)
            # パターン3: 問Yのみ → グルーピング規則（10問ごと）
            if '問' in number_str:
                y = number_str.split('問')[-1]
                y = y.split('-')[0].split('.')[0].strip()
                num_val = int(y)
                return str((num_val - 1) // 10 + 1)
        except:
            pass
        return '1'

    def _infer_fallback_theme(self, text: str, field_label: str) -> str:
        """テーマ未検出時の簡易推定（使用語句/分野から補う）"""
        try:
            import re
            t = (text or '').strip()
            
            # まず重要キーワードを抽出してみる
            # 歴史的事件・人物
            historical_events = re.findall(r'([一-龥]{2,8}(?:の乱|の変|戦争|条約|改革|革命))', t)
            if historical_events:
                return historical_events[0]
            
            persons = re.findall(r'([一-龥]{2,4}[\s　]?[一-龥]{2,4})', t)
            for person in persons:
                if any(name in person for name in ['源頼朝', '平清盛', '織田信長', '豊臣秀吉', '徳川家康']):
                    return f'{person}の業績'
            
            # 地理的要素
            locations = re.findall(r'([一-龥]{2,6}(?:県|府|都|道|市|平野|盆地|山地))', t)
            if locations:
                return f'{locations[0]}の特徴'
            
            # 公民的要素
            civics = re.findall(r'([一-龥]{2,8}(?:憲法|法律|選挙|制度|条約))', t)
            if civics:
                return f'{civics[0]}の内容'
            
            # 固有名詞を探す（3文字以上の漢字の連続）
            proper_nouns = re.findall(r'[一-龥]{3,8}', t)
            exclude_words = {'答えなさい', '選びなさい', '説明しなさい', '述べなさい', 'について', 
                           'あてはまる', '正しい', 'まちがって', '次のうち', '下線部'}
            proper_nouns = [n for n in proper_nouns if n not in exclude_words]
            
            if proper_nouns:
                # 最も重要そうな単語を選択
                keyword = proper_nouns[0]
                if field_label == '歴史':
                    return f'{keyword}の歴史的意義'
                elif field_label == '地理':
                    return f'{keyword}の地理的特徴'
                elif field_label == '公民':
                    return f'{keyword}の制度'
                else:
                    return f'{keyword}について'
            
            # 分野別の簡易推定
            if field_label == '地理':
                if '人口ピラミッド' in t:
                    return '人口ピラミッドの分析'
                if '地図' in t or '地図中' in t:
                    return '地図の読み取り'
                if '雨温図' in t:
                    return '雨温図の読み取り'
                if 'グラフ' in t:
                    return 'グラフの分析'
                if '表' in t:
                    return '統計表の分析'
                return '地理問題'
            
            if field_label == '歴史':
                period = re.search(r'(縄文|弥生|古墳|飛鳥|奈良|平安|鎌倉|室町|戦国|江戸|明治|大正|昭和|平成|令和)時代', t)
                if period:
                    return f"{period.group(0)}の特徴"
                return '歴史問題'
            
            if field_label == '公民':
                for kw in ['日本国憲法', '三権分立', '国会', '内閣', '裁判所', '選挙']:
                    if kw in t:
                        return f"{kw}の仕組み"
                return '公民問題'
            
            # その他
            return f"{field_label}問題"
            
        except Exception:
            return f"{field_label}問題"


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
