#!/usr/bin/env python3
"""
2025年度東京電機大学中学校の社会科PDFを改善版で分析
"""

from pathlib import Path
from modules.social_analyzer import SocialAnalyzer
from modules.ocr_handler import OCRHandler
from modules.text_formatter import TextFormatter
from modules.improved_theme_extractor import ImprovedThemeExtractor

def analyze_2025_pdf():
    """2025年度のPDFを改善版で分析"""
    
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/東京電機大学中学校/2025年東京電機大学中学校問題_社会.pdf"
    
    print("=== 2025年度 東京電機大学中学校 社会科入試問題分析 ===")
    print(f"PDFファイル: {pdf_path}")
    print()
    
    # PDFが存在するか確認
    if not Path(pdf_path).exists():
        print(f"❌ ファイルが見つかりません: {pdf_path}")
        return
    
    print("✅ ファイルを確認しました")
    print()
    
    # OCR処理
    print("📄 PDFからテキストを抽出中...")
    ocr_handler = OCRHandler()
    text = ocr_handler.process_pdf(pdf_path)
    
    if not text:
        print("❌ PDFからテキストを抽出できませんでした")
        return
    
    print(f"✅ テキスト抽出成功: {len(text)} 文字")
    print()
    
    # 社会分析器で分析（改善版テーマ抽出器を内蔵）
    print("🔍 問題を分析中...")
    analyzer = SocialAnalyzer()
    analysis_result = analyzer.analyze_document(text)
    questions = analysis_result['questions']
    
    print(f"✅ 分析完了: {len(questions)}問を検出")
    print()
    
    # テーマの品質評価
    print("=== テーマ抽出品質評価 ===")
    
    good_themes = []
    bad_themes = []
    none_themes = []
    
    problematic_patterns = [
        '下線', 'この時期', '各都市', 'まちがっている', '正しい', 
        '空らん', '空欄', '次の図', '次の文章', 'の設問', 'について'
    ]
    
    for q in questions:
        if q.theme is None:
            none_themes.append(q)
        elif any(bad in str(q.theme) for bad in problematic_patterns):
            bad_themes.append((q.number, q.theme))
        elif len(str(q.theme)) > 2:
            good_themes.append((q.number, q.theme))
        else:
            bad_themes.append((q.number, q.theme))
    
    print(f"✅ 良質なテーマ: {len(good_themes)}問 ({len(good_themes)/len(questions)*100:.1f}%)")
    print(f"❌ 問題のあるテーマ: {len(bad_themes)}問 ({len(bad_themes)/len(questions)*100:.1f}%)")
    print(f"⚫ 適切に除外: {len(none_themes)}問 ({len(none_themes)/len(questions)*100:.1f}%)")
    print()
    
    # 良質なテーマのサンプル表示
    if good_themes:
        print("良質なテーマの例:")
        for num, topic in good_themes[:10]:
            print(f"  {num}: {topic}")
        if len(good_themes) > 10:
            print(f"  ...他{len(good_themes)-10}件")
        print()
    
    # 問題のあるテーマの表示
    if bad_themes:
        print("改善が必要なテーマ:")
        for num, topic in bad_themes[:10]:
            print(f"  {num}: {topic}")
        if len(bad_themes) > 10:
            print(f"  ...他{len(bad_themes)-10}件")
        print()
    
    # 品質スコア
    quality_score = (len(good_themes) + len(none_themes)) / len(questions) * 100
    print(f"📊 品質スコア: {quality_score:.1f}%")
    print("（良質なテーマ + 適切な除外）/ 総問題数")
    print()
    
    # テキストファイルとして保存
    print("=== テキストファイル保存 ===")
    
    output_dir = Path("/Users/yoshiikatsuhiko/Desktop/過去問_社会")
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    
    output_file = output_dir / "東京電機大学中学校_2025_社会_改善版.txt"
    
    formatter = TextFormatter()
    content = formatter.format_analysis(questions, "東京電機大学中学校", "2025")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ ファイル保存完了: {output_file}")
    print()
    
    # 改善前後の比較
    old_file = output_dir / "東京電機大学中学校_2025_社会.txt"
    if old_file.exists():
        print("=== 改善前後の比較 ===")
        
        with open(old_file, 'r', encoding='utf-8') as f:
            old_content = f.read()
        
        # 改善前の問題テーマを数える
        old_bad_count = 0
        for pattern in problematic_patterns:
            old_bad_count += old_content.count(f": {pattern}")
        
        print(f"改善前: 問題のあるテーマが約{old_bad_count}個")
        print(f"改善後: 問題のあるテーマが{len(bad_themes)}個")
        print(f"改善数: {old_bad_count - len(bad_themes)}個削減")
    
    print("\n✅ 分析完了")

if __name__ == "__main__":
    analyze_2025_pdf()