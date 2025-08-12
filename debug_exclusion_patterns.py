#!/usr/bin/env python3
"""
除外パターン動作テスト - デバッグ用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.theme_extractor_v2 import ThemeExtractorV2, ExtractedTheme
from modules.theme_extractor_enhanced import EnhancedThemeExtractor

def test_exclusion_patterns():
    """除外パターンの動作をテスト"""
    
    # 問題となっているテキストのサンプル
    problem_cases = [
        "次の雨温図は",
        "次の図は", 
        "次の表は",
        "【あ】にあてはまる人物名",
        "下線部",
        "下線部⑥", 
        "下線部の特徴",
        "にあてはまる人物名を漢字で答え",
        "読書感想文の特徴",
        "【い】にあてはまる語句",
        "【う】にあてはまる",
        "あにあてはまる人物名",  # 【】なしのケース
    ]
    
    # V2とEnhanced両方でテスト
    extractors = {
        'V2': ThemeExtractorV2(),
        'Enhanced': EnhancedThemeExtractor(enable_web_search=False)
    }
    
    print("=== 除外パターン動作テスト ===\n")
    
    for extractor_name, extractor in extractors.items():
        print(f"--- {extractor_name} Extractor ---")
        
        for case in problem_cases:
            result = extractor.extract(case)
            
            # 除外されるべきなのに抽出された場合は問題
            if result.theme is not None:
                print(f"❌ PROBLEM: '{case}' -> '{result.theme}' (should be None)")
            else:
                print(f"✅ OK: '{case}' -> None")
        
        print()
    
    # 除外パターンの詳細チェック
    print("=== 除外パターン詳細チェック ===")
    v2_extractor = ThemeExtractorV2()
    
    # 個別パターンのマッチングをテスト
    test_patterns = [
        ("【あ】にあてはまる人物名", r'【[あ-んア-ン]】にあてはまる'),
        ("にあてはまる人物名を漢字で答え", r'にあてはまる(人物名|語句|言葉|もの)'),
    ]
    
    import re
    for text, pattern_str in test_patterns:
        pattern = re.compile(pattern_str)
        match = pattern.search(text)
        print(f"Text: '{text}'")
        print(f"Pattern: {pattern_str}")
        print(f"Match: {bool(match)}")
        if match:
            print(f"Matched: '{match.group()}'")
        print()
    
    # _should_exclude メソッドの直接テスト
    print("=== _should_exclude メソッド直接テスト ===")
    for case in problem_cases:
        should_exclude = v2_extractor._should_exclude(case)
        print(f"'{case}' -> should_exclude: {should_exclude}")


if __name__ == '__main__':
    test_exclusion_patterns()