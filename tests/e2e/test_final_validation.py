#!/usr/bin/env python3
"""最終的な動作確認テスト"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.social_analyzer_fixed import FixedSocialAnalyzer
from modules.theme_extractor_v2 import ThemeExtractorV2
from modules.theme_extraction_rules import ThemeExtractionRules, ThemeCategory

def test_japanese_accuracy():
    """日本語の正確性テスト"""
    print("=" * 60)
    print("日本語正確性テスト")
    print("=" * 60)
    
    extractor = ThemeExtractorV2()
    
    # 正式名称のテスト
    test_cases = [
        ("阪神・淡路大震災について説明しなさい", "阪神・淡路大震災"),
        ("上米の制について述べよ", "上米の制"),
        ("墾田永年私財法の内容を答えなさい", "墾田永年私財法"),
    ]
    
    for text, expected_keyword in test_cases:
        result = extractor.extract(text)
        if result.theme and expected_keyword in result.theme:
            status = "✅"
        else:
            status = "❌"
        print(f"{status} {text[:30]}...")
        print(f"   期待: {expected_keyword}を含む")
        print(f"   結果: {result.theme}")
    
    print()

def test_exclusion_completeness():
    """除外パターンの完全性テスト"""
    print("=" * 60)
    print("除外パターン完全性テスト")
    print("=" * 60)
    
    extractor = ThemeExtractorV2()
    
    # ユーザーが指摘した全ての問題ケース
    problematic_cases = [
        "下線部の内容",
        "【い】にあてはまる人物名",
        "新聞記事の内容",
        "同年アメリカ合衆国の仕組み",
        "河川部の内容",
        "グリーンマークの内容",
        "気象庁ホームページの内容",
        "電気機械器具の説明",
        "にあてはまる人物名を次のア",
        "NATOに加盟する国は以下の表にある取り決め",
    ]
    
    success_count = 0
    for text in problematic_cases:
        result = extractor.extract(text)
        if result.theme is None:
            status = "✅"
            success_count += 1
        else:
            status = "❌"
        print(f"{status} {text} → {result.theme if result.theme else '(除外成功)'}")
    
    print(f"\n除外成功率: {success_count}/{len(problematic_cases)} = {success_count*100/len(problematic_cases):.0f}%")
    print()

def test_large_section_detection():
    """大問検出の正確性テスト"""
    print("=" * 60) 
    print("大問検出テスト")
    print("=" * 60)
    
    analyzer = FixedSocialAnalyzer()
    
    # 4つの大問を含むテキスト
    test_text = """
    1. 次の問いに答えなさい。
    問1 江戸時代について
    問2 明治維新について
    問3 大正デモクラシーについて
    問4 昭和時代について
    問5 平成時代について
    
    2. 地理について答えなさい。
    問1 関東地方について
    問2 近畿地方について
    問3 九州地方について
    
    3. 公民について答えなさい。
    問1 日本国憲法について
    問2 国会について
    問3 内閣について
    
    4. 時事問題について答えなさい。
    問1 SDGsについて
    問2 地球温暖化について
    """
    
    questions = analyzer._extract_with_reset_detection(test_text)
    
    # 大問ごとに集計
    large_sections = {}
    for q_id, q_text in questions:
        if '-' in q_id:
            large_num = q_id.split('-')[0]
            if large_num not in large_sections:
                large_sections[large_num] = 0
            large_sections[large_num] += 1
    
    expected_sections = 3  # 最低3つの大問を期待
    actual_sections = len(large_sections)
    
    if actual_sections >= expected_sections:
        print(f"✅ 大問検出成功: {actual_sections}個の大問を検出")
    else:
        print(f"❌ 大問検出失敗: {actual_sections}個しか検出されず（期待: {expected_sections}個以上）")
    
    for section, count in sorted(large_sections.items()):
        print(f"   {section}: {count}問")
    print()

def test_theme_quality():
    """テーマの品質テスト"""
    print("=" * 60)
    print("テーマ品質テスト")
    print("=" * 60)
    
    extractor = ThemeExtractorV2()
    rules = ThemeExtractionRules()
    
    # 有効なテーマのテストケース
    valid_cases = [
        ("江戸時代の政治について説明しなさい", "江戸時代の政治"),
        ("鎌倉幕府の成立について答えなさい", "鎌倉幕府の成立"),
        ("日本国憲法の三原則について答えなさい", "日本国憲法の三原則"),
        ("内閣総理大臣の役割について説明しなさい", "内閣総理大臣"),
        ("明治維新の影響について述べなさい", "明治維新"),
    ]
    
    success_count = 0
    for text, expected_keyword in valid_cases:
        result = extractor.extract(text)
        if result.theme and expected_keyword in result.theme:
            # 2文節形式チェック
            is_valid = rules.validate_theme(result.theme)
            if is_valid:
                status = "✅"
                success_count += 1
            else:
                status = "⚠️"
        else:
            status = "❌"
        
        print(f"{status} {text[:30]}...")
        print(f"   結果: {result.theme}")
    
    print(f"\nテーマ品質: {success_count}/{len(valid_cases)} = {success_count*100/len(valid_cases):.0f}%")
    print()

def main():
    """メインテスト実行"""
    print("\n" + "=" * 60)
    print("社会科入試問題分析システム - 最終動作確認")
    print("=" * 60 + "\n")
    
    test_japanese_accuracy()
    test_exclusion_completeness()
    test_large_section_detection()
    test_theme_quality()
    
    print("=" * 60)
    print("テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    main()