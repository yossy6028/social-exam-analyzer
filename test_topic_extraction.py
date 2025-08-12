#!/usr/bin/env python3
"""
実際のPDFでテーマ抽出テスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.ocr_handler import OCRHandler
from modules.social_analyzer import SocialAnalyzer

def test_topic_extraction():
    """実際のPDFからテーマ抽出をテスト"""
    
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/東京電機大学中学校/2020年東京電機大学中学校問題_社会.pdf"
    
    if not Path(pdf_path).exists():
        print(f"PDFファイルが見つかりません: {pdf_path}")
        return
    
    ocr = OCRHandler()
    analyzer = SocialAnalyzer()
    
    print("PDFからテキスト抽出中...")
    text = ocr.process_pdf(pdf_path)
    
    if not text:
        print("テキスト抽出に失敗しました")
        return
    
    # 問題を分析
    result = analyzer.analyze_document(text)
    questions = result.get('questions', [])
    
    print(f"\n{'='*70}")
    print("テーマ抽出結果（最初の20問）")
    print('='*70)
    
    for q in questions[:20]:
        # 問題文の最初の部分
        text_preview = q.text[:80].replace('\n', ' ')
        
        print(f"\n{q.number}:")
        print(f"  問題文: {text_preview}...")
        print(f"  抽出テーマ: {q.topic if q.topic else '（なし）'}")
        print(f"  分野: {q.field.value}")
        
        # キーワードも表示（参考）
        if q.keywords and len(q.keywords) > 0:
            keywords_str = ', '.join(q.keywords[:5])
            print(f"  キーワード: {keywords_str}")

if __name__ == "__main__":
    test_topic_extraction()