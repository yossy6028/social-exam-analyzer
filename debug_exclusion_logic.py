#!/usr/bin/env python3
"""
除外ロジックの詳細デバッグ
問題のあるテーマが除外されない原因を特定
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.theme_extractor_v2 import ThemeExtractorV2
from modules.theme_extractor_enhanced import EnhancedThemeExtractor

def test_problematic_themes():
    """問題のあるテーマで除外ロジックをテスト"""
    
    # テスト対象の問題テーマ
    problematic_themes = [
        "下線部⑥",
        "下線部の史料として正しいものを",
        "下線部の特徴",
        "【い】にあてはまる人物名",
        "にあてはまる人物名を次のア",
        "具体的な権利の名称を用いてその事例"
    ]
    
    # V2抽出器をテスト
    print("=== ThemeExtractorV2 テスト ===")
    extractor_v2 = ThemeExtractorV2()
    
    for theme in problematic_themes:
        print(f"\n--- テスト: '{theme}' ---")
        
        # 除外チェック
        should_exclude = extractor_v2._should_exclude(theme)
        print(f"除外判定: {should_exclude}")
        
        # パターン別チェック
        print("マッチした除外パターン:")
        for i, pattern in enumerate(extractor_v2.exclusion_patterns):
            if pattern.search(theme):
                print(f"  - パターン{i}: {pattern.pattern}")
        
        # 実際の抽出結果
        result = extractor_v2.extract(theme)
        print(f"抽出結果: theme={result.theme}, confidence={result.confidence}")
        
        if result.theme is not None:
            print("❌ 除外されるべきだが抽出されている")
        else:
            print("✅ 正常に除外されている")
    
    # Enhanced抽出器もテスト
    print("\n\n=== EnhancedThemeExtractor テスト ===")
    extractor_enhanced = EnhancedThemeExtractor(enable_web_search=False)
    
    for theme in problematic_themes:
        print(f"\n--- テスト: '{theme}' ---")
        result = extractor_enhanced.extract(theme)
        print(f"抽出結果: theme={result.theme}, confidence={result.confidence}")
        
        if result.theme is not None:
            print("❌ 除外されるべきだが抽出されている")
        else:
            print("✅ 正常に除外されている")

def analyze_pattern_effectiveness():
    """除外パターンの効果を分析"""
    
    extractor = ThemeExtractorV2()
    
    print("=== 除外パターン分析 ===")
    
    # 下線部関連のパターンをテスト
    underline_tests = [
        "下線部⑥",
        "下線部⑦",  
        "下線部の特徴",
        "下線部について",
        "下線部に関して",
        "下線部の内容",
        "下線部の説明"
    ]
    
    print("\n下線部関連:")
    for test in underline_tests:
        matches = []
        for i, pattern in enumerate(extractor.exclusion_patterns):
            if pattern.search(test):
                matches.append(i)
        
        should_exclude = extractor._should_exclude(test)
        print(f"'{test}' -> 除外:{should_exclude}, マッチパターン:{matches}")
    
    # あてはまる関連のパターンをテスト
    atehamaru_tests = [
        "にあてはまる人物名",
        "【い】にあてはまる人物名", 
        "にあてはまる人物名を次のア",
        "あてはまる語句",
        "あてはまるもの"
    ]
    
    print("\nあてはまる関連:")
    for test in atehamaru_tests:
        matches = []
        for i, pattern in enumerate(extractor.exclusion_patterns):
            if pattern.search(test):
                matches.append(i)
        
        should_exclude = extractor._should_exclude(test)
        print(f"'{test}' -> 除外:{should_exclude}, マッチパターン:{matches}")

if __name__ == "__main__":
    test_problematic_themes()
    print("\n" + "="*60 + "\n")
    analyze_pattern_effectiveness()