#!/usr/bin/env python3
"""
社会科目入試問題分析システム CLIバージョン
tkinterを使用しないコマンドライン版
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# モジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent))

try:
    from modules.social_analyzer_fixed import FixedSocialAnalyzer as SocialAnalyzer
except ImportError:
    try:
        from modules.social_analyzer_improved import ImprovedSocialAnalyzer as SocialAnalyzer
    except ImportError:
        from modules.social_analyzer import SocialAnalyzer
from modules.text_formatter import TextFormatter
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


class SocialExamAnalyzerCLI:
    """社会科目入試問題分析CLIアプリケーション"""
    
    def __init__(self):
        self.analyzer = SocialAnalyzer()
        self.formatter = TextFormatter()
        self.ocr_handler = OCRHandler()
        
    def print_header(self):
        """ヘッダー表示"""
        print("\n" + "="*70)
        print("               社会科目入試問題分析システム CLI版")
        print("="*70)
        print("\n【分析機能】")
        print("  1. 分野別分析（地理・歴史・公民）")
        print("  2. 資料活用状況（地図・グラフ・年表等）")
        print("  3. 時事問題検出（SDGs・環境・国際情勢等）")
        print("  4. 出題形式分析（短答式・選択式・記述式等）")
        print("-"*70 + "\n")
    
    def get_pdf_file(self) -> Optional[str]:
        """PDFファイルパスを取得"""
        print("PDFファイルのパスを入力してください:")
        print("（例: /Users/username/Desktop/開成中学校_2025.pdf）")
        print("※ ファイルをドラッグ&ドロップするか、パスをコピー&ペーストしてください")
        print("※ 'q'を入力すると終了します")
        
        while True:
            file_path = input("\nファイルパス: ").strip()
            
            if file_path.lower() == 'q':
                return None
            
            # クォートを除去
            file_path = file_path.strip('"').strip("'")
            
            # エスケープ文字の処理
            # バックスラッシュでエスケープされた文字を処理
            file_path = file_path.replace('\\ ', ' ')
            file_path = file_path.replace('\\(', '(')
            file_path = file_path.replace('\\)', ')')
            file_path = file_path.replace('\\[', '[')
            file_path = file_path.replace('\\]', ']')
            file_path = file_path.replace('\\{', '{')
            file_path = file_path.replace('\\}', '}')
            file_path = file_path.replace("\\'", "'")
            file_path = file_path.replace('\\"', '"')
            
            # ファイルの存在確認
            if os.path.exists(file_path):
                if file_path.lower().endswith('.pdf'):
                    print(f"✓ ファイルを確認しました: {os.path.basename(file_path)}")
                    return file_path
                else:
                    print("エラー: PDFファイルを指定してください")
            else:
                # エスケープなしでも試す
                file_path_alt = file_path.replace('\\', '')
                if os.path.exists(file_path_alt):
                    if file_path_alt.lower().endswith('.pdf'):
                        print(f"✓ ファイルを確認しました: {os.path.basename(file_path_alt)}")
                        return file_path_alt
                    else:
                        print("エラー: PDFファイルを指定してください")
                else:
                    print(f"エラー: ファイルが見つかりません")
                    print(f"  入力されたパス: {file_path}")
                    print("  ヒント: Finderからファイルをドラッグ&ドロップしてみてください")
    
    def get_school_info(self, pdf_path: str = None) -> tuple:
        """学校情報を取得（ファイル名から自動判定）"""
        
        # ファイル名から自動判定を試みる
        if pdf_path:
            filename = os.path.basename(pdf_path)
            auto_school, auto_year = self.ocr_handler.extract_school_year_from_filename(filename)
            
            print(f"\n📝 ファイル名から自動判定:")
            print(f"   学校名: {auto_school}")
            print(f"   年度: {auto_year}")
            print("\n※ 自動判定が間違っている場合は、以下で修正してください")
            print("  （Enterキーで自動判定値を使用）")
        else:
            auto_school = ""
            auto_year = "2025"
        
        print("\n学校情報を入力してください:")
        
        # 学校名（デフォルトは自動判定値）
        prompt = f"学校名 [{auto_school}]: " if auto_school else "学校名（例: 開成中学校）: "
        school_name = input(prompt).strip()
        if not school_name:
            school_name = auto_school if auto_school else "不明"
        
        # 年度（デフォルトは自動判定値）
        prompt = f"年度 [{auto_year}]: "
        year = input(prompt).strip()
        if not year:
            year = auto_year
        
        return school_name, year
    
    def display_results(self, analysis_result: dict, school_name: str, year: str):
        """分析結果を表示"""
        stats = analysis_result['statistics']
        
        print("\n" + "="*70)
        print(f"              {school_name} {year}年度 分析結果")
        print("="*70)
        
        print(f"\n総問題数: {analysis_result['total_questions']}問")
        
        # 分野別分布
        print("\n【分野別出題状況】")
        if 'field_distribution' in stats:
            for field, data in stats['field_distribution'].items():
                bar = "■" * int(data['percentage'] / 5)
                print(f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%) {bar}")
        
        # 資料活用状況
        print("\n【資料活用状況】")
        if 'resource_usage' in stats:
            sorted_resources = sorted(stats['resource_usage'].items(), 
                                    key=lambda x: x[1]['count'], 
                                    reverse=True)
            for resource, data in sorted_resources[:5]:
                print(f"  {resource:12s}: {data['count']:3d}回 ({data['percentage']:5.1f}%)")
        
        # 出題形式
        print("\n【出題形式分布】")
        if 'format_distribution' in stats:
            sorted_formats = sorted(stats['format_distribution'].items(),
                                   key=lambda x: x[1]['count'],
                                   reverse=True)
            for format_type, data in sorted_formats[:5]:
                print(f"  {format_type:10s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
        
        # 時事問題
        print("\n【時事問題】")
        if 'current_affairs' in stats:
            print(f"  時事問題: {stats['current_affairs']['count']}問 "
                  f"({stats['current_affairs']['percentage']:.1f}%)")
        
        # テーマ一覧（大問ごとに区切って表示）
        print("\n【出題テーマ一覧】")
        questions = analysis_result.get('questions', [])
        
        if questions:
            # 大問ごとにグループ化
            grouped_themes = {}
            for q in questions:
                # 問題番号から大問番号を推定
                if '問' in q.number:
                    # "問1", "問2" のような形式から大問番号を推定
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
                    print(f"\n  ▼ 大問 {major_num}")
                    print("  " + "-" * 40)
                
                themes = grouped_themes[major_num]
                if themes:
                    for num, theme, field in themes:
                        # 分野も併記してより分かりやすく
                        print(f"    {num}: {theme} [{field}]")
                else:
                    print("    （テーマ情報なし）")
        else:
            print("  （問題が検出されませんでした）")
        
        print("\n" + "="*70)
    
    def save_text_report(self, analysis_result: dict, school_name: str, year: str):
        """テキスト形式でレポートを保存"""
        print("\n分析結果をテキストファイルに保存しています...")
        
        try:
            # テキストレポート作成
            report_text = self.formatter.create_text_report(
                analysis_result,
                school_name,
                year
            )
            
            # 保存
            saved_path = self.formatter.save_text_report(
                report_text,
                school_name,
                year
            )
            
            print(f"\n✅ 分析結果を保存しました:")
            print(f"   {saved_path}")
            
        except Exception as e:
            logger.error(f"テキスト保存エラー: {e}")
            print(f"\n❌ 保存中にエラーが発生しました: {str(e)}")
    
    def run(self):
        """メイン処理"""
        self.print_header()
        
        while True:
            # PDFファイル選択
            pdf_file = self.get_pdf_file()
            if not pdf_file:
                print("\n終了します。")
                break
            
            # 学校情報取得（ファイル名から自動判定）
            school_name, year = self.get_school_info(pdf_file)
            
            try:
                print("\n分析を開始しています...")
                print("PDFからテキストを抽出中...")
                
                # PDFからテキスト抽出
                text = self.ocr_handler.process_pdf(pdf_file)
                
                if not text:
                    print("エラー: テキストの抽出に失敗しました")
                    continue
                
                print(f"テキスト抽出完了（{len(text)}文字）")
                print("問題を分析中...")
                
                # 分析実行
                analysis_result = self.analyzer.analyze_document(text)
                
                # 結果表示
                self.display_results(analysis_result, school_name, year)
                
                # テキスト保存（自動）
                self.save_text_report(analysis_result, school_name, year)
                
            except Exception as e:
                logger.error(f"分析エラー: {e}")
                print(f"\nエラーが発生しました: {str(e)}")
            
            # 続行確認
            print("\n別のファイルを分析しますか? (y/n): ", end="")
            if input().strip().lower() != 'y':
                break
        
        print("\nご利用ありがとうございました。")


def main():
    """メイン関数"""
    # ログディレクトリ作成
    log_dir = Path("logs")
    if not log_dir.exists():
        log_dir.mkdir()
    
    # CLIアプリケーション実行
    app = SocialExamAnalyzerCLI()
    app.run()


if __name__ == "__main__":
    main()