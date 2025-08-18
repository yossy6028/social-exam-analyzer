#!/usr/bin/env python3
"""
デバッグ修正のテストスクリプト
"""

import logging
from pathlib import Path
from modules.ocr_handler import OCRHandler
from modules.social_analyzer_fixed import FixedSocialAnalyzer

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_fixed_analyzer():
    """修正されたアナライザーのテスト"""
    
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2025年日本工業大学駒場中学校問題_社会.pdf"
    
    print("=" * 80)
    print("日本工業大学駒場中学校 2025年度問題の再分析テスト")
    print("=" * 80)
    
    # 1. OCR処理
    print("\n1. OCR処理開始...")
    ocr_handler = OCRHandler()
    ocr_text = ocr_handler.process_pdf(pdf_path)
    
    if not ocr_text:
        print("❌ OCR処理に失敗しました")
        return
    
    print(f"✅ OCR処理成功: {len(ocr_text)}文字")
    
    # OCR生テキストの最初の部分を表示
    print(f"\n📄 OCR生テキスト（最初の800文字）:")
    print("-" * 60)
    print(ocr_text[:800])
    print("-" * 60)
    
    # 2. 修正されたアナライザーで分析
    print("\n2. 修正されたアナライザーで分析開始...")
    analyzer = FixedSocialAnalyzer()
    
    # 学校名・年度抽出
    school_name, year = ocr_handler.extract_school_year_from_filename(pdf_path)
    print(f"📍 学校名: {school_name}, 年度: {year}")
    
    # 分析実行
    try:
        results = analyzer.analyze_document(ocr_text)
        
        print(f"\n3. 分析結果:")
        print(f"   総問題数: {results.get('total_questions', 0)}問")
        
        if 'questions' in results:
            print(f"   抽出された問題:")
            for i, (q_id, q_text) in enumerate(results['questions'][:5]):  # 最初の5問のみ
                print(f"     {q_id}: {q_text[:100]}..." if len(q_text) > 100 else f"     {q_id}: {q_text}")
        
        # 統計情報
        if 'statistics' in results:
            stats = results['statistics']
            print(f"\n   分野別出題状況:")
            if 'field_distribution' in stats:
                for field, data in stats['field_distribution'].items():
                    print(f"     {field}: {data['count']}問 ({data['percentage']:.1f}%)")
        
        print("\n✅ 修正されたアナライザーのテスト完了")
        
    except Exception as e:
        print(f"❌ 分析エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_analyzer()