#!/usr/bin/env python3
"""
実際のOCRテキストファイル全体で問題抽出器をテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.improved_question_extractor import ImprovedQuestionExtractor
from modules.theme_extractor_v2 import ThemeExtractorV2

def test_full_ocr():
    """実際のOCRテキストファイル全体でテスト"""
    
    print("=== 実際のOCRテキストファイル全体でのテスト ===\n")
    
    # 実際のOCRテキストファイルを読み込み
    ocr_file = "logs/ocr_2023_日工大駒場_社会.txt"
    
    if not os.path.exists(ocr_file):
        print(f"❌ OCRファイルが見つかりません: {ocr_file}")
        return
    
    print(f"📁 OCRファイル: {ocr_file}")
    
    # ファイルを読み込み
    with open(ocr_file, 'r', encoding='utf-8') as f:
        ocr_text = f.read()
    
    print(f"📊 ファイルサイズ: {len(ocr_text)} 文字")
    print(f"📝 行数: {len(ocr_text.split(chr(10)))} 行")
    
    print("\n" + "="*50)
    print("問題抽出のテスト:")
    
    # 問題抽出器でテスト
    extractor = ImprovedQuestionExtractor()
    questions = extractor.extract_questions(ocr_text)
    
    print(f"抽出された問題数: {len(questions)}")
    print("\n各問題の詳細:")
    
    for i, (q_id, q_text) in enumerate(questions, 1):
        print(f"\n{i}. {q_id}")
        print(f"   テキスト: {q_text[:100]}...")
    
    # 大問構造の分析
    print("\n" + "="*50)
    print("大問構造の分析:")
    
    major_sections = {}
    for q_id, _ in questions:
        major_part = q_id.split('-')[0]
        major_sections[major_part] = major_sections.get(major_part, 0) + 1
    
    for major, count in major_sections.items():
        print(f"{major}: {count}問")
    
    print(f"\n総大問数: {len(major_sections)}")
    print(f"総問題数: {len(questions)}")
    
    # 期待値との比較
    expected_majors = 3
    expected_questions = 9  # 大問1: 3問, 大問2: 3問, 大問3: 3問
    
    print(f"\n期待値との比較:")
    print(f"大問数: {len(major_sections)}/{expected_majors} ({'✅' if len(major_sections) == expected_majors else '❌'})")
    print(f"問題数: {len(questions)}/{expected_questions} ({'✅' if len(questions) == expected_questions else '❌'})")
    
    # テーマ抽出のテスト
    print("\n" + "="*50)
    print("重要な問題のテーマ抽出テスト:")
    
    theme_extractor = ThemeExtractorV2()
    
    # 重要な問題のテーマ抽出
    important_questions = [
        "促成栽培について説明しなさい。",
        "日宋貿易について説明しなさい。",
        "核兵器禁止条約について説明しなさい。",
        "内閣の役割について説明しなさい。",
        "社会保障制度について説明しなさい。",
    ]
    
    for i, question in enumerate(important_questions, 1):
        print(f"\nテスト {i}: {question}")
        result = theme_extractor.extract(question)
        print(f"  テーマ: {result.theme}")
        print(f"  カテゴリ: {result.category}")
        print(f"  信頼度: {result.confidence}")
        
        if result.theme:
            print(f"  ✅ テーマ抽出成功")
        else:
            print(f"  ❌ テーマ抽出失敗")
    
    # OCRテキスト内の重要な用語の検出
    print("\n" + "="*50)
    print("OCRテキスト内の重要な用語の検出:")
    
    from modules.terms_repository import TermsRepository
    repo = TermsRepository()
    
    # 重要な用語の検出
    important_terms = ["促成栽培", "日宋貿易", "核兵器禁止条約", "内閣", "社会保障"]
    
    for term in important_terms:
        if term in ocr_text:
            terms_found = repo.find_terms_in_text(term)
            print(f"✅ {term}: OCRテキストに存在 - 用語カタログ: {terms_found}")
        else:
            print(f"❌ {term}: OCRテキストに存在しない")

if __name__ == "__main__":
    test_full_ocr()
