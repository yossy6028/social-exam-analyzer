#!/usr/bin/env python3
"""refineメソッドのデバッグ"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.theme_extractor_v2 import ThemeExtractorV2

def test():
    extractor = ThemeExtractorV2()
    
    text = "鎌倉幕府の成立について説明しなさい。"
    print(f"テキスト: {text}")
    print(f"'鎌倉幕府' in text: {'鎌倉幕府' in text}")
    
    # refineメソッドの中身を手動で実行
    if '鎌倉幕府' in text:
        print("  -> 鎌倉幕府マッチ！")
        from modules.theme_extractor_v2 import ExtractedTheme
        result = ExtractedTheme('鎌倉幕府の成立', '歴史', 0.9)
        print(f"  -> 結果: {result.theme}")
    
    # メソッドを直接呼ぶ
    print("\nメソッド呼び出し:")
    refined = extractor._refine_theme_from_keywords(text)
    if refined:
        print(f"  テーマ: {refined.theme}")
    else:
        print("  None返却")

if __name__ == "__main__":
    test()