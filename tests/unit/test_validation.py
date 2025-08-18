#!/usr/bin/env python3
"""
問題文バリデーションのテスト
"""

import re
from modules.social_analyzer_fixed import FixedSocialAnalyzer

def test_validation():
    """バリデーション機能のテスト"""
    
    analyzer = FixedSocialAnalyzer()
    
    # テストケース
    test_cases = [
        ("", "空文字"),
        ("短い", "短すぎる"),
        ("次の文章が説明している湖を地図中のア~エから1つ選び記号で答えなさい", "正常な問題文"),
        ("123 456 789", "数値のみ"),
        ("次の雨温図は、地図中に示したA~Dの都市のいずれかのものです。", "問いなし"),
        ("答えなさい", "キーワードのみ"),
    ]
    
    print("=" * 60)
    print("問題文バリデーションテスト")
    print("=" * 60)
    
    for text, description in test_cases:
        is_valid = analyzer._is_valid_question(text)
        print(f"{'✅' if is_valid else '❌'} {description}: {is_valid}")
        print(f"    テキスト: \"{text[:50]}...\"" if len(text) > 50 else f"    テキスト: \"{text}\"")
        print()

if __name__ == "__main__":
    test_validation()