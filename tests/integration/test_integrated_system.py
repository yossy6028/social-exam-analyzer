#!/usr/bin/env python3
"""
統合されたシステムのテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.improved_question_extractor import ImprovedQuestionExtractor

def test_integrated_system():
    """統合されたシステムをテスト"""
    
    print("=== 統合されたシステムのテスト ===\n")
    
    # ImprovedQuestionExtractorのインスタンスを作成
    extractor = ImprovedQuestionExtractor()
    
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
    print(f"📝 行数: {len(ocr_text.split())} 行")
    
    print("\n" + "="*60)
    print("統合システムでの問題抽出テスト:")
    print("="*60)
    
    # 統合システムで問題を抽出
    questions = extractor.extract_questions(ocr_text)
    
    print(f"抽出された問題数: {len(questions)}")
    
    if questions:
        print("\n各問題の詳細:")
        for i, (q_id, q_text) in enumerate(questions):
            print(f"{i+1}. {q_id}")
            print(f"   テキスト: {q_text[:100]}...")
            print()
        
        print("="*60)
        print("大問構造の分析:")
        print("="*60)
        
        # 大問ごとの問題数を分析
        major_counts = {}
        for q_id, _ in questions:
            major_part = q_id.split('-')[0]
            major_counts[major_part] = major_counts.get(major_part, 0) + 1
        
        for major, count in major_counts.items():
            print(f"{major}: {count}問")
        
        print(f"\n総大問数: {len(major_counts)}")
        print(f"総問題数: {len(questions)}")
        
        print("\n" + "="*60)
        print("期待値との比較:")
        print("="*60)
        
        expected_majors = 3
        expected_questions = 9
        
        major_match = len(major_counts) == expected_majors
        question_match = len(questions) == expected_questions
        
        print(f"大問数: {len(major_counts)}/{expected_majors} ({'✅' if major_match else '❌'})")
        print(f"問題数: {len(questions)}/{expected_questions} ({'✅' if question_match else '❌'})")
        
        if major_match and question_match:
            print("\n🎉 期待値を完全に達成！")
        elif question_match:
            print("\n✅ 問題数は期待値と一致")
        else:
            print(f"\n⚠️ 期待値との差: {abs(len(questions) - expected_questions)}問")
        
        print("\n" + "="*60)
        print("システムの動作モード:")
        print("="*60)
        
        # どのアプローチが使用されたかを判定
        if len(questions) >= 8 and len(questions) <= 12:
            print("従来の境界認識アプローチが使用されました")
        else:
            print("統計的アプローチが使用されました")
        
        print(f"期待値9問との差: {abs(len(questions) - 9)}問")
        
        if abs(len(questions) - 9) <= 1:
            print("✅ 期待値に近い結果を達成")
        else:
            print("⚠️ 期待値から外れた結果")
    
    else:
        print("❌ 問題が抽出されませんでした")

if __name__ == "__main__":
    test_integrated_system()
