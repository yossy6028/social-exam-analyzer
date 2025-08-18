#!/usr/bin/env python3
"""
実際の問題抽出過程の詳細デバッグ
"""

import re
from modules.ocr_handler import OCRHandler
from modules.social_analyzer_fixed import FixedSocialAnalyzer

def test_actual_extraction():
    """実際の問題抽出過程をステップごとに確認"""
    
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2025年日本工業大学駒場中学校問題_社会.pdf"
    
    # OCR処理
    ocr_handler = OCRHandler()
    ocr_text = ocr_handler.process_pdf(pdf_path)
    
    # アナライザー
    analyzer = FixedSocialAnalyzer()
    cleaned_text = analyzer._clean_ocr_text(ocr_text)
    
    print("=" * 80)
    print("実際の問題抽出過程デバッグ")
    print("=" * 80)
    
    # パターン2: 直接問番号でテスト
    pattern = re.compile(r'問(\d+)[^\n]*([\s\S]*?)(?=問\d+|$)', re.MULTILINE)
    matches = pattern.findall(cleaned_text)
    
    print(f"パターンマッチ結果: {len(matches)}件")
    print()
    
    valid_count = 0
    
    for i, (q_num, q_text) in enumerate(matches[:10]):  # 最初の10問のみ
        # フォーマット処理
        formatted_text = analyzer._format_question_text(q_text)
        is_valid = analyzer._is_valid_question(formatted_text)
        is_instruction = analyzer._is_instruction_text(formatted_text)
        has_content = analyzer._contains_question_content(formatted_text) if hasattr(analyzer, '_contains_question_content') else True
        
        status = "✅" if is_valid else "❌"
        print(f"{status} 問{q_num}:")
        print(f"    長さ: {len(formatted_text)}文字")
        print(f"    is_valid: {is_valid}")
        print(f"    is_instruction: {is_instruction}")
        print(f"    has_content: {has_content}")
        print(f"    テキスト: {formatted_text[:150]}...")
        print()
        
        if is_valid:
            valid_count += 1
    
    print(f"有効な問題数: {valid_count}/{len(matches[:10])}")

if __name__ == "__main__":
    test_actual_extraction()