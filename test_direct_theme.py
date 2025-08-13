#!/usr/bin/env python3
"""直接テーマ抽出テスト"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.theme_extractor_v2 import ThemeExtractorV2

def test():
    extractor = ThemeExtractorV2()
    
    test_cases = [
        "鎌倉幕府の成立について説明しなさい。",
        "江戸時代の身分制度について答えなさい。",
        "日本国憲法の三原則について説明しなさい。",
    ]
    
    for text in test_cases:
        print(f"\n入力: {text}")
        
        # 除外チェック
        excluded = extractor._should_exclude(text)
        print(f"  除外判定: {excluded}")
        
        # refineメソッドを直接呼ぶ
        refined = extractor._refine_theme_from_keywords(text)
        if refined:
            print(f"  refineからのテーマ: {refined.theme}")
        else:
            print(f"  refineからのテーマ: None")
        
        # 全体の抽出
        result = extractor.extract(text)
        print(f"  最終テーマ: {result.theme}")
        print(f"  カテゴリ: {result.category}")
        print(f"  信頼度: {result.confidence}")

if __name__ == "__main__":
    test()