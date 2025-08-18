#!/usr/bin/env python3
"""
問題抽出器の詳細デバッグ
"""

import sys
import os
import logging
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.improved_question_extractor import ImprovedQuestionExtractor

def test_debug_extractor():
    """問題抽出器の詳細デバッグ"""
    
    print("=== 問題抽出器の詳細デバッグ ===\n")
    
    # ログレベルを設定
    logging.basicConfig(level=logging.DEBUG)
    
    # 実際のOCRテキストファイルを読み込み
    ocr_file = "logs/ocr_2023_日工大駒場_社会.txt"
    
    try:
        with open(ocr_file, 'r', encoding='utf-8') as f:
            ocr_text = f.read()
    except FileNotFoundError:
        print(f"❌ OCRファイルが見つかりません: {ocr_file}")
        return
    
    print(f"📁 OCRファイル: {ocr_file}")
    print(f"📊 ファイルサイズ: {len(ocr_text)} 文字")
    
    # 問題抽出器を初期化
    extractor = ImprovedQuestionExtractor()
    
    print("\n" + "="*50)
    print("大問パターンのテスト:")
    
    # 大問パターンを個別にテスト
    major_patterns = [
        re.compile(r'^(\d+)\s*次の各問いに答えなさい。', re.MULTILINE),
        re.compile(r'^(\d+)\s*次の年表を見て', re.MULTILINE),
        re.compile(r'^(\d+)\s*次の文章を読み、各問いに答えなさい。', re.MULTILINE),
    ]
    
    for i, pattern in enumerate(major_patterns, 1):
        matches = list(pattern.finditer(ocr_text))
        print(f"パターン {i}: {pattern.pattern}")
        print(f"  マッチ数: {len(matches)}")
        for match in matches:
            print(f"    マッチ: '{match.group(0)}' (位置 {match.start()})")
            # 前後の文脈を表示
            start = max(0, match.start() - 50)
            end = min(len(ocr_text), match.end() + 50)
            context = ocr_text[start:end]
            print(f"      文脈: ...{context}...")
    
    print("\n" + "="*50)
    print("問題抽出の実行:")
    
    # 問題抽出を実行
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

if __name__ == "__main__":
    test_debug_extractor()
