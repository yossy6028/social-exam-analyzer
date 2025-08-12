#!/usr/bin/env python3
"""大問検出のテスト"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.social_analyzer_fixed import FixedSocialAnalyzer
from modules.theme_extractor_v2 import ThemeExtractorV2

def test_large_section_detection():
    """大問検出機能のテスト"""
    
    # テストケース：4つの大問がある試験
    test_text = """
    問1 次の文章を読んで答えなさい。
    江戸時代の政治について説明します。
    
    問2 徳川家康について正しいものを選びなさい。
    
    問3 参勤交代の目的を答えなさい。
    
    問4 鎖国政策の内容を説明しなさい。
    
    問5 江戸幕府の仕組みを答えなさい。
    
    問1 明治維新について次の問いに答えなさい。
    
    問2 大政奉還の意味を説明しなさい。
    
    問3 廃藩置県の目的を答えなさい。
    
    問1 第二次世界大戦について説明しなさい。
    
    問2 太平洋戦争の原因を答えなさい。
    
    問3 終戦の経緯を説明しなさい。
    
    問1 現代の日本について次の問いに答えなさい。
    
    問2 高度経済成長期の特徴を答えなさい。
    """
    
    analyzer = FixedSocialAnalyzer()
    questions = analyzer._extract_with_reset_detection(test_text)
    
    print("=" * 60)
    print("大問検出テスト")
    print("=" * 60)
    
    # 大問ごとに問題を集計
    large_sections = {}
    for q_id, q_text in questions:
        if '-' in q_id:
            large_num = q_id.split('-')[0]
            if large_num not in large_sections:
                large_sections[large_num] = []
            large_sections[large_num].append(q_id)
    
    print(f"\n検出された大問数: {len(large_sections)}")
    for section, items in sorted(large_sections.items()):
        print(f"\n{section}: {len(items)}問")
        for item in items[:3]:  # 最初の3問だけ表示
            print(f"  - {item}")
    
    # アサーション
    assert len(large_sections) >= 3, f"大問が3つ以上検出されるべきですが、{len(large_sections)}つしか検出されませんでした"
    print("\n✅ 大問検出テスト成功！")

def test_theme_exclusion():
    """除外パターンのテスト"""
    
    extractor = ThemeExtractorV2()
    
    # 除外されるべきテーマ
    excluded_cases = [
        "気象庁ホームページの内容",
        "電気機械器具の説明",
        "【い】にあてはまる語句",
        "河川部の内容",
        "ホームページの内容",
        "空欄補充問題",
    ]
    
    print("\n" + "=" * 60)
    print("除外パターンテスト")
    print("=" * 60)
    
    for text in excluded_cases:
        result = extractor.extract(text)
        status = "✅" if result.theme is None else "❌"
        print(f"{status} {text} → {result.theme}")
    
    # 除外されないべきテーマ
    valid_cases = [
        "江戸時代の政治",
        "明治維新の影響",
        "地図の読み取り",
        "平安時代の文学",
    ]
    
    print("\n有効なテーマ:")
    for text in valid_cases:
        result = extractor.extract(text)
        status = "✅" if result.theme is not None else "❌"
        print(f"{status} {text} → {result.theme}")

if __name__ == "__main__":
    test_large_section_detection()
    test_theme_exclusion()