#!/usr/bin/env python3
"""
社会科目入試問題分析システム - CLI版
GUIなしでコマンドラインから実行可能
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import logging

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


def extract_major_number(number_str: str) -> str:
    """設問番号文字列から大問番号を抽出"""
    try:
        import re
        # パターン1: 大問X-問Y / 大問X
        m = re.search(r'大問(\d+)', number_str)
        if m:
            major_num = int(m.group(1))
            # 異常値チェック（中学入試で大問10以上は稀）
            if major_num > 10:
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


def infer_fallback_theme(text: str, field_label: str, theme_knowledge: ThemeKnowledgeBase) -> str:
    """テーマ未検出時の推定"""
    try:
        theme = theme_knowledge.determine_theme(text, field_label)
        return theme
    except Exception as e:
        logger.warning(f"テーマ推定エラー: {e}")
        return f"{field_label}問題"


def analyze_pdf(pdf_path: str, school_name: str, year: str):
    """PDFファイルを分析してテーマ一覧を保存"""
    
    print(f"\n分析開始: {Path(pdf_path).name}")
    print(f"学校名: {school_name}")
    print(f"年度: {year}")
    print("-" * 60)
    
    # アナライザーとハンドラーの初期化
    analyzer = SocialAnalyzer()
    ocr_handler = OCRHandler()
    theme_knowledge = ThemeKnowledgeBase()
    
    # PDFからテキスト抽出
    print("PDFからテキストを抽出中...")
    text = ocr_handler.process_pdf(pdf_path)
    
    if not text:
        print("エラー: テキストの抽出に失敗しました")
        return False
    
    print(f"テキスト抽出完了（{len(text)}文字）")
    
    # 分析実行
    print("問題を分析中...")
    analysis_result = analyzer.analyze_document(text)
    
    if not analysis_result:
        print("エラー: 分析に失敗しました")
        return False
    
    stats = analysis_result['statistics']
    
    # 結果表示
    print("\n" + "=" * 60)
    print("分析結果サマリー")
    print("=" * 60)
    print(f"総問題数: {analysis_result['total_questions']}問\n")
    
    # 分野別分布
    print("【分野別出題状況】")
    if 'field_distribution' in stats:
        for field, data in stats['field_distribution'].items():
            print(f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
    
    # 保存先ディレクトリを作成
    save_dir = Path("/Users/yoshiikatsuhiko/Desktop/過去問_社会")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # ファイル名を生成
    filename = f"{school_name}_{year}_テーマ一覧_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    file_path = save_dir / filename
    
    # テキストファイルとして保存
    print(f"\nテーマ一覧を保存中: {file_path}")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            # ヘッダー情報
            f.write("=" * 60 + "\n")
            f.write(f"社会科入試問題分析 - テーマ一覧\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"学校名: {school_name}\n")
            f.write(f"年度: {year}年\n")
            f.write(f"分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
            f.write(f"総問題数: {analysis_result['total_questions']}問\n\n")
            
            # 分野別出題状況
            f.write("【分野別出題状況】\n")
            if 'field_distribution' in stats:
                for field, data in stats['field_distribution'].items():
                    f.write(f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)\n")
            f.write("\n")
            
            # テーマ一覧（大問ごと）
            f.write("【出題テーマ一覧】\n")
            questions = analysis_result.get('questions', [])
            
            if questions:
                # 大問ごとにグループ化
                raw_groups = []
                for q in questions:
                    raw_major = extract_major_number(q.number)
                    raw_groups.append(raw_major)
                normalized_map = {}
                order = []
                for m in raw_groups:
                    if m not in normalized_map:
                        order.append(m)
                        normalized_map[m] = str(len(order))
                
                grouped_themes = {}
                for q in questions:
                    major_num_raw = extract_major_number(q.number)
                    major_num = normalized_map.get(major_num_raw, major_num_raw)
                    if major_num not in grouped_themes:
                        grouped_themes[major_num] = []
                    
                    # テーマがない場合は推定
                    topic = q.theme
                    if not topic:
                        base_text = getattr(q, 'original_text', None) or q.text
                        topic = infer_fallback_theme(base_text, q.field.value, theme_knowledge)
                    
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
        
        print(f"✅ テーマ一覧を保存しました: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"テキスト保存エラー: {e}")
        print(f"❌ 保存中にエラーが発生しました: {str(e)}")
        return False


if __name__ == "__main__":
    # PDFファイルのパス
    pdf_file = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2025年日本工業大学駒場中学校問題_社会.pdf"
    
    # 学校名と年度を抽出
    filename = Path(pdf_file).stem
    if "日本工業大学駒場" in filename:
        school_name = "日本工業大学駒場中学校"
    else:
        school_name = filename.split('_')[0] if '_' in filename else filename
    
    year = "2025"
    if "2025" in filename:
        year = "2025"
    
    # 分析実行
    success = analyze_pdf(pdf_file, school_name, year)
    
    if success:
        print("\n分析が正常に完了しました！")
    else:
        print("\n分析中にエラーが発生しました。")
        sys.exit(1)