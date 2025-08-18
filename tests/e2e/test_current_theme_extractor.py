#!/usr/bin/env python3
"""
現在のテーマ抽出器の動作をテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.theme_extractor_v2 import ThemeExtractorV2

def test_current_extractor():
    """現在のテーマ抽出器をテスト"""
    extractor = ThemeExtractorV2()
    
    print("=== 現在のテーマ抽出器のテスト ===\n")
    
    # 実際のテキストファイルから抽出した問題文
    test_cases = [
        ("次の文章が説明している平野を、地図中ア~エから1つ選び記号で答えなさい。", "平野問題"),
        ("次の雨温図は、地図中に示したA~Cの都市のいずれかのものです。", "雨温図問題"),
        ("次の地形図を見て、以下の問いに答えなさい。", "地形図問題"),
        ("次の表は、それぞれ藤、肉用若鶏の都道府県別頭数(2021年)の上位5道県を示しています。", "統計表問題"),
        ("図中の11の地図記号は何を示しているか、次のア~エから1つ選び記号で答えなさい。", "地図記号問題"),
        ("地形図から読み取れることとして正しいものを、次のア~エから1つ選び記号で答えなさい。", "地形図読み取り問題"),
    ]
    
    for i, (text, description) in enumerate(test_cases, 1):
        print(f"テストケース {i}: {description}")
        print(f"テキスト: {text}")
        
        try:
            result = extractor.extract(text)
            if result and result.theme:
                print(f"結果: ✓ テーマ抽出成功")
                print(f"  テーマ: {result.theme}")
                print(f"  カテゴリ: {result.category}")
                print(f"  信頼度: {result.confidence}")
            else:
                print(f"結果: ✗ テーマ抽出失敗")
                print(f"  テーマ: {result.theme if result else 'None'}")
                print(f"  カテゴリ: {result.category if result else 'None'}")
                print(f"  信頼度: {result.confidence if result else 'N/A'}")
        except Exception as e:
            print(f"結果: ✗ エラー発生: {e}")
        
        print("-" * 60)

if __name__ == "__main__":
    test_current_extractor()
