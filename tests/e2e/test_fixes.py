#!/usr/bin/env python3
"""
修正内容のテストスクリプト
大問番号とテーマ判定の修正を検証
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.improved_question_extractor import ImprovedQuestionExtractor
from modules.theme_knowledge_base import ThemeKnowledgeBase
from modules.social_analyzer_fixed import FixedSocialAnalyzer

def test_question_extractor():
    """問題抽出のテスト"""
    print("=== 問題抽出テスト ===")
    
    extractor = ImprovedQuestionExtractor()
    
    # テスト用の問題文（問題番号がリセットされるパターン）
    test_text = """
問1 縄文時代について説明しなさい。
問2 弥生時代の特徴を答えなさい。
問3 古墳時代の代表的な遺跡は？

問1 唐の政治制度について述べなさい。
問2 宋の文化について説明しなさい。
問3 元の社会について答えなさい。

問1 関東地方の気候について説明しなさい。
問2 近畿地方の産業について答えなさい。
"""
    
    questions = extractor.extract_questions(test_text)
    print(f"抽出された問題数: {len(questions)}")
    
    for q_num, q_text in questions:
        print(f"  {q_num}: {q_text[:50]}...")
    
    # 大問番号の妥当性チェック
    major_numbers = set()
    for q_num, _ in questions:
        if "大問" in q_num:
            major_num = int(q_num.split("大問")[1].split("-")[0])
            major_numbers.add(major_num)
    
    print(f"検出された大問番号: {sorted(major_numbers)}")
    
    # 異常な大問番号がないことを確認
    if max(major_numbers) <= 5:  # 大問5以下なら正常
        print("✅ 大問番号は正常です")
    else:
        print(f"❌ 異常な大問番号が検出されました: 最大{max(major_numbers)}")

def test_theme_knowledge():
    """テーマ知識ベースのテスト"""
    print("\n=== テーマ知識ベーステスト ===")
    
    kb = ThemeKnowledgeBase()
    
    # 中国王朝のテーマ判定テスト
    test_cases = [
        ("唐の政治制度について説明しなさい", "歴史"),
        ("宋の文化について述べなさい", "歴史"), 
        ("秦の統一について答えなさい", "歴史"),
        ("漢の社会について説明しなさい", "歴史"),
        ("政治制度の仕組みについて答えなさい", "公民"),  # 歴史的文脈がない場合
        ("関東地方の産業について説明しなさい", "地理")
    ]
    
    for text, expected_field in test_cases:
        theme = kb.determine_theme(text, expected_field)
        print(f"  テキスト: {text}")
        print(f"  期待分野: {expected_field}")
        print(f"  判定テーマ: {theme}")
        
        # 中国王朝が歴史として判定されるかチェック
        if any(dynasty in text for dynasty in ['唐', '宋', '秦', '漢']):
            if '歴史' in theme or any(dynasty in theme for dynasty in ['唐', '宋', '秦', '漢']):
                print("  ✅ 中国王朝が歴史として正しく判定されました")
            else:
                print("  ❌ 中国王朝が歴史として判定されませんでした")
        print()

def test_field_detection():
    """分野判定のテスト"""
    print("=== 分野判定テスト ===")
    
    analyzer = FixedSocialAnalyzer()
    
    # 問題となっていたケースのテスト
    test_cases = [
        ("唐の政治制度について説明しなさい", "歴史"),
        ("宋の文化について述べなさい", "歴史"),
        ("中国の王朝について答えなさい", "歴史"),
        ("秦の統一について説明しなさい", "歴史"),
        ("政治制度の仕組みについて答えなさい", "公民"),
        ("選挙制度について説明しなさい", "公民"),
        ("三権分立について述べなさい", "公民"),
        ("関東地方の産業について説明しなさい", "地理"),
        ("日本の気候について答えなさい", "地理")
    ]
    
    correct_count = 0
    total_count = len(test_cases)
    
    for text, expected in test_cases:
        detected_field = analyzer._detect_field(text)
        print(f"  テキスト: {text}")
        print(f"  期待分野: {expected}")
        print(f"  判定分野: {detected_field.value}")
        
        if detected_field.value.lower() == expected:
            print("  ✅ 正しく判定されました")
            correct_count += 1
        else:
            print("  ❌ 判定が間違っています")
        print()
    
    accuracy = correct_count / total_count * 100
    print(f"判定精度: {correct_count}/{total_count} ({accuracy:.1f}%)")

def main():
    """メインテスト実行"""
    print("修正内容のテストを開始します...\n")
    
    try:
        test_question_extractor()
        test_theme_knowledge()
        test_field_detection()
        
        print("\n=== テスト完了 ===")
        print("すべてのテストが実行されました。")
        print("上記の結果を確認してください。")
        
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()