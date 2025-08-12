#!/usr/bin/env python3
"""
実際のPDF処理テスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.ocr_handler import OCRHandler
from modules.social_analyzer import SocialAnalyzer

def test_real_pdf():
    """実際のPDFファイルでテスト"""
    
    # テスト用PDFパス
    test_pdfs = [
        "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/東京電機大学中学校/2020年東京電機大学中学校問題_社会.pdf",
        "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/東京電機大学中学校/2022年東京電機大学中学校問題_社会.pdf",
    ]
    
    ocr = OCRHandler()
    analyzer = SocialAnalyzer()
    
    for pdf_path in test_pdfs:
        if Path(pdf_path).exists():
            print(f"\n{'='*70}")
            print(f"PDFファイル: {Path(pdf_path).name}")
            print('='*70)
            
            # テキスト抽出
            print("テキスト抽出中...")
            text = ocr.process_pdf(pdf_path)
            
            if text:
                # 最初の500文字を表示
                print(f"\n抽出されたテキスト（最初の500文字）:")
                print("-" * 40)
                print(text[:500])
                print("-" * 40)
                
                # 簡単な分析
                print("\n簡単な分析:")
                print(f"総文字数: {len(text)}")
                print(f"行数: {len(text.splitlines())}")
                
                # ダミーテキストかどうかチェック
                if "社会科入学試験問題" in text[:100]:
                    print("⚠️ ダミーテキストが検出されました")
                else:
                    print("✅ 実際のテキストが抽出されました")
                
                # 問題分析
                result = analyzer.analyze_document(text)
                print(f"\n問題数: {result['total_questions']}")
                
                if result['statistics']:
                    stats = result['statistics']
                    if 'field_distribution' in stats:
                        print("\n分野別:")
                        for field, data in stats['field_distribution'].items():
                            print(f"  {field}: {data['count']}問")
            else:
                print("❌ テキスト抽出に失敗しました")
        else:
            print(f"❌ ファイルが見つかりません: {pdf_path}")

if __name__ == "__main__":
    test_real_pdf()