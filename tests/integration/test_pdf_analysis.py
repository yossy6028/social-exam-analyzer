#!/usr/bin/env python3
"""
実際のPDFファイルで改善されたテーマ抽出をテスト
"""

import sys
from pathlib import Path
from modules.social_analyzer import SocialAnalyzer
from modules.ocr_handler import OCRHandler
from modules.text_formatter import TextFormatter
from modules.improved_theme_extractor import ImprovedThemeExtractor

def analyze_pdf_with_improved_extractor(pdf_path: str):
    """改善されたテーマ抽出でPDFを分析"""
    
    print(f"=== PDFファイル分析テスト ===")
    print(f"ファイル: {pdf_path}")
    print()
    
    # OCR処理
    ocr_handler = OCRHandler()
    text = ocr_handler.process_pdf(pdf_path)
    
    if not text:
        print("❌ PDFからテキストを抽出できませんでした")
        return
    
    print(f"✅ テキスト抽出成功: {len(text)} 文字")
    print()
    
    # 社会分析器で分析
    analyzer = SocialAnalyzer()
    questions = analyzer.analyze_text(text)
    
    print(f"検出された問題数: {len(questions)}問")
    print()
    
    # テーマの品質チェック
    print("=== テーマ抽出結果の評価 ===")
    print()
    
    good_themes = []
    bad_themes = []
    none_themes = []
    
    for q in questions:
        if q.topic is None:
            none_themes.append(q)
        elif any(bad in q.topic for bad in ['下線', 'この時期', '各都市', 'まちがっている', '正しい', '空らん', '空欄']):
            bad_themes.append((q.number, q.topic))
        elif len(q.topic) > 2:
            good_themes.append((q.number, q.topic))
        else:
            bad_themes.append((q.number, q.topic))
    
    # 良いテーマ
    print(f"✅ 良いテーマ: {len(good_themes)}問")
    if good_themes[:10]:  # 最初の10個を表示
        for num, topic in good_themes[:10]:
            print(f"   {num}: {topic}")
        if len(good_themes) > 10:
            print(f"   ...他{len(good_themes)-10}件")
    print()
    
    # 問題のあるテーマ
    print(f"❌ 問題のあるテーマ: {len(bad_themes)}問")
    if bad_themes:
        for num, topic in bad_themes[:10]:
            print(f"   {num}: {topic}")
        if len(bad_themes) > 10:
            print(f"   ...他{len(bad_themes)-10}件")
    print()
    
    # Noneのテーマ（適切に除外されたもの）
    print(f"⚫ 適切に除外（None）: {len(none_themes)}問")
    print()
    
    # 品質スコア
    total = len(questions)
    if total > 0:
        quality_score = (len(good_themes) + len(none_themes)) / total * 100
        print(f"品質スコア: {quality_score:.1f}%")
        print(f"（良いテーマ + 適切な除外）/ 総問題数")
    
    # テキストファイルとして保存
    print()
    print("=== テキストファイル保存テスト ===")
    
    output_dir = Path("/Users/yoshiikatsuhiko/Desktop/過去問_社会")
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    
    output_file = output_dir / "東京電機大学中学校_2020_社会_改善版.txt"
    
    formatter = TextFormatter()
    content = formatter.format_analysis(questions, "東京電機大学中学校", "2020")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ ファイル保存: {output_file}")
    
    # 保存されたファイルのテーマ部分を確認
    with open(output_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    in_theme_section = False
    theme_lines = []
    
    for line in lines:
        if '【出題テーマ一覧】' in line:
            in_theme_section = True
        elif in_theme_section:
            if line.startswith('【'):
                break
            if line.strip() and line.startswith('  問'):
                theme_lines.append(line.strip())
    
    print()
    print("保存されたテーマ一覧（最初の20件）:")
    for line in theme_lines[:20]:
        print(line)
    if len(theme_lines) > 20:
        print(f"...他{len(theme_lines)-20}件")

if __name__ == "__main__":
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/東京電機大学中学校/2020年東京電機大学中学校_社会.pdf"
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"❌ ファイルが見つかりません: {pdf_path}")
        sys.exit(1)
    
    analyze_pdf_with_improved_extractor(pdf_path)