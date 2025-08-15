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
from modules.theme_knowledge_base import ThemeKnowledgeBase

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
        self.theme_knowledge = ThemeKnowledgeBase()
        
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
                    
                    grouped_themes = {}
                    for q in questions:
                        major_num_raw = self._extract_major_number(q.number)
                        major_num = normalized_map.get(major_num_raw, major_num_raw)
                        if major_num not in grouped_themes:
                            grouped_themes[major_num] = []
                        
                        # テーマがない場合は推定
                        topic = q.topic
                        if not topic:
                            base_text = getattr(q, 'original_text', None) or q.text
                            topic = self._infer_fallback_theme(base_text, q.field.value)
                        
                        grouped_themes[major_num].append((q.number, topic if topic else '（テーマ不明）', q.field.value))
                    
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
                            for num, theme, field in themes:
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
                                f.write(f"  {display_num}: {theme} [{field}]\n")
                        else:
                            f.write("  （テーマ情報なし）\n")
                else:
                    f.write("  （問題が検出されませんでした）\n")
                
                f.write("\n")
                f.write("=" * 60 + "\n")
                f.write("分析終了\n")
            
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
        """テーマ未検出時の推定（カリキュラムと主題インデックスを参照）"""
        try:
            # 知識ベースを使用してテーマを決定
            theme = self.theme_knowledge.determine_theme(text, field_label)
            return theme
        except Exception as e:
            logger.warning(f"テーマ推定エラー: {e}")
            # フォールバック処理
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
    import argparse
    parser = argparse.ArgumentParser(description='社会科入試問題分析ツール')
    parser.add_argument('pdf_path', nargs='?', help='PDFファイルのパス')
    parser.add_argument('--school', help='学校名')
    parser.add_argument('--year', help='年度')
    parser.add_argument('--debug', action='store_true', help='デバッグモード')
    parser.add_argument('--dry-run', action='store_true', help='分析のみ実行（保存しない）')
    
    args = parser.parse_args()
    
    if args.pdf_path:
        # コマンドライン実行モード
        from pathlib import Path
        import json
        from modules.social_analyzer_fixed import FixedSocialAnalyzer as SocialAnalyzer
        from modules.theme_knowledge_base import ThemeKnowledgeBase
        from modules.social_excel_formatter import SocialExcelFormatter
        from datetime import datetime
        
        try:
            # PDFファイルを読み込み
            pdf_path = Path(args.pdf_path)
            if not pdf_path.exists():
                print(f"エラー: ファイルが見つかりません: {pdf_path}")
                exit(1)
            
            # PDFからテキストを抽出
            from modules.ocr_handler import OCRHandler
            ocr = OCRHandler()
            pdf_text = ocr.process_pdf(str(pdf_path))
            
            if not pdf_text:
                print(f"エラー: PDFからテキストを抽出できませんでした")
                exit(1)
            
            # 分析実行
            analyzer = SocialAnalyzer()
            result = analyzer.analyze_document(pdf_text)
            
            # 結果に成功フラグを追加
            if result:
                result['success'] = bool(result.get('questions'))
            
            if result and result.get('success'):
                # テキストファイル生成
                theme_kb = ThemeKnowledgeBase()
                save_dir = Path("/Users/yoshiikatsuhiko/Desktop/過去問_社会")
                save_dir.mkdir(parents=True, exist_ok=True)
                
                school_name = args.school or pdf_path.stem.split('_')[0]
                year = args.year or "2025"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{school_name}_{year}_テーマ一覧_{timestamp}.txt"
                save_path = save_dir / filename
                
                # テキスト生成
                output_lines = []
                output_lines.append("="*60)
                output_lines.append("社会科入試問題分析 - テーマ一覧")
                output_lines.append("="*60)
                output_lines.append("")
                output_lines.append(f"学校名: {school_name}")
                output_lines.append(f"年度: {year}年")
                output_lines.append(f"分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
                output_lines.append(f"総問題数: {result.get('total_questions', 0)}問")
                output_lines.append("")
                output_lines.append("【分野別出題状況】")
                
                # 分野別集計
                field_counts = {}
                for q in result.get('questions', []):
                    # qはSocialQuestionオブジェクト
                    field_name = q.field.value if hasattr(q, 'field') and hasattr(q.field, 'value') else 'MIXED'
                    field_counts[field_name] = field_counts.get(field_name, 0) + 1
                
                for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / result.get('total_questions', 1)) * 100
                    # fieldは既に日本語なのでそのまま使用
                    output_lines.append(f"  {field:10s}: {count:3d}問 ({percentage:5.1f}%)")
                
                output_lines.append("")
                output_lines.append("【出題テーマ一覧】")
                output_lines.append("")
                
                # 大問ごとのテーマ
                current_major = None
                for q in result.get('questions', []):
                    # qはSocialQuestionオブジェクト
                    # 問題番号から大問番号を推定（例：大問1-問3 -> 1）
                    q_num = q.number if hasattr(q, 'number') else '問?'
                    major_num = 1
                    if '-' in q_num:
                        try:
                            major_num = int(q_num.split('-')[0].replace('大問', ''))
                        except:
                            major_num = 1
                    if current_major != major_num:
                        current_major = major_num
                        output_lines.append(f"▼ 大問 {current_major}")
                        output_lines.append("-"*40)
                    
                    # テーマ決定
                    field_value = q.field.value if hasattr(q, 'field') and hasattr(q.field, 'value') else '総合'
                    # field_valueは既に日本語なのでそのまま使用
                    field_name = field_value
                    
                    question_text = q.text if hasattr(q, 'text') else ''
                    question_num = q.number if hasattr(q, 'number') else '問?'
                    # トピックがあればそれを使用、なければテーマを決定
                    if hasattr(q, 'topic') and q.topic:
                        theme = q.topic
                    else:
                        theme = theme_kb.determine_theme(question_text[:200], field_name)
                    output_lines.append(f"  {question_num}: {theme} [{field_name}]")
                
                output_lines.append("")
                output_lines.append("="*60)
                output_lines.append("分析終了")
                output_lines.append("")
                
                # ファイル保存
                if not args.dry_run:
                    with open(save_path, 'w', encoding='utf-8') as f:
                        output_text = '\n'.join(output_lines)
                        f.write(output_text)
                    print(f"✅ テキストファイル保存完了: {save_path}")
                
                # デバッグ出力
                if args.debug:
                    output_text = '\n'.join(output_lines)
                    print(output_text)
            else:
                print(f"❌ 分析に失敗しました: {result.get('error_message', 'Unknown error') if result else 'Unknown error'}")
        
        except Exception as e:
            print(f"エラー: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
    else:
        # GUI モード
        try:
            import tkinter as tk
            app = SocialAnalyzerApp()
            app.mainloop()
        except ImportError:
            print("GUI モードは利用できません。コマンドラインモードを使用してください。")
            print("使用例: python main.py PDFファイルパス --school 学校名 --year 年度")