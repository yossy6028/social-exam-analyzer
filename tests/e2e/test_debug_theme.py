#!/usr/bin/env python3
"""テーマ抽出のデバッグ"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.theme_extractor_v2 import ThemeExtractorV2
import logging

# ロギング設定 - DEBUGレベル
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def test_theme_extraction():
    """テーマ抽出のデバッグ"""
    
    test_cases = [
        "鎌倉幕府の成立について説明しなさい。",
        "江戸時代の身分制度について答えなさい。",
        "日本国憲法の三原則について説明しなさい。",
        "人口ピラミッドを見て答えなさい。",
        "兵庫県の特徴について説明しなさい。",
    ]
    
    extractor = ThemeExtractorV2()
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"ケース{i}: {text}")
        print('='*60)
        
        # デバッグ情報を表示しながら抽出
        result = extractor.extract(text)
        
        print(f"結果:")
        print(f"  テーマ: {result.theme}")
        print(f"  カテゴリ: {result.category}")
        print(f"  信頼度: {result.confidence}")
        
        # 手動で_refine_theme_from_keywordsを呼んでみる
        print(f"\n_refine_theme_from_keywordsの結果:")
        refined = extractor._refine_theme_from_keywords(text)
        if refined:
            print(f"  テーマ: {refined.theme}")
            print(f"  カテゴリ: {refined.category}")
            print(f"  信頼度: {refined.confidence}")
        else:
            print("  Noneが返されました")

if __name__ == "__main__":
    test_theme_extraction()