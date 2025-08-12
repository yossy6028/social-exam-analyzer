#!/usr/bin/env python3
"""
実際のテーマ抽出をテスト - 修正後の検証
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.social_analyzer_fixed import FixedSocialAnalyzer
from modules.theme_extractor_enhanced import EnhancedThemeExtractor
from modules.theme_extractor_v2 import ThemeExtractorV2

def test_with_real_problematic_cases():
    """実際に問題となっているケースでテスト"""
    
    # 実際の問題となっているテーマのサンプル
    problematic_cases = [
        "次の雨温図は",
        "次の図は", 
        "次の表は",
        "【あ】にあてはまる人物名",
        "下線部",
        "下線部⑥", 
        "下線部の特徴",
        "にあてはまる人物名を漢字で答え",
        "読書感想文の特徴",
        "次の資料は明治時代の工業について述べたものです",
        "下線部アについて説明しなさい",
        "地図中のAの都市名を答えなさい",
        "同年におこった出来事",
        "この当時の政治制度",
        "ホームページで調べた内容",
        "電気機械器具の生産",
        "実験の結果",
        "方程式を解く",
    ]
    
    # 正当なテーマのサンプル
    valid_cases = [
        "明治維新の改革内容について",
        "江戸幕府の政治制度",
        "関東地方の産業の特徴",
        "日本国憲法の三原則",
        "阪神・淡路大震災の被害",
        "鎌倉幕府の成立過程",
        "北海道の気候の特徴",
        "選挙制度の仕組み",
        "太平洋戦争の経過",
        "少子高齢化の影響",
    ]
    
    print("=== 実際のテーマ抽出テスト ===\n")
    
    # FixedSocialAnalyzerを使用（実際のワークフローと同じ）
    analyzer = FixedSocialAnalyzer()
    extractor = analyzer.theme_extractor
    
    print("--- 除外すべきケース（問題パターン） ---")
    problem_count = 0
    for case in problematic_cases:
        result = extractor.extract(case)
        if result.theme is not None:
            print(f"❌ PROBLEM: '{case}' -> '{result.theme}' (should be None)")
            problem_count += 1
        else:
            print(f"✅ OK: '{case}' -> None")
    
    print(f"\n問題パターン: {problem_count}/{len(problematic_cases)} 件が不適切に抽出")
    
    print("\n--- 抽出すべきケース（正当パターン） ---")
    valid_count = 0
    for case in valid_cases:
        result = extractor.extract(case)
        if result.theme is not None:
            print(f"✅ OK: '{case}' -> '{result.theme}' ({result.confidence:.2f})")
            valid_count += 1
        else:
            print(f"❌ MISSING: '{case}' -> None (should extract theme)")
    
    print(f"\n正当パターン: {valid_count}/{len(valid_cases)} 件が正常に抽出")
    
    # 結果サマリー
    print(f"\n=== テスト結果サマリー ===")
    print(f"除外精度: {(len(problematic_cases) - problem_count)/len(problematic_cases)*100:.1f}%")
    print(f"抽出精度: {valid_count/len(valid_cases)*100:.1f}%")
    
    if problem_count == 0:
        print("🎉 除外パターンが完全に機能しています！")
    else:
        print(f"⚠️ {problem_count}件の問題パターンが残っています")


def test_enhanced_vs_v2():
    """Enhanced版とV2版の動作比較"""
    print("\n=== Enhanced vs V2 比較テスト ===")
    
    v2_extractor = ThemeExtractorV2()
    enhanced_extractor = EnhancedThemeExtractor(enable_web_search=False)
    
    test_cases = [
        "次の雨温図は気候の特徴を示しています",
        "明治維新による社会変化",
        "【あ】にあてはまる人物名を答えなさい",
        "下線部の改革について説明しなさい",
    ]
    
    for case in test_cases:
        v2_result = v2_extractor.extract(case)
        enhanced_result = enhanced_extractor.extract(case)
        
        print(f"\nCase: '{case}'")
        print(f"V2:       '{v2_result.theme}' (conf: {v2_result.confidence:.2f})")
        print(f"Enhanced: '{enhanced_result.theme}' (conf: {enhanced_result.confidence:.2f})")
        
        if v2_result.theme != enhanced_result.theme:
            print("⚠️ 結果が異なります")


if __name__ == '__main__':
    test_with_real_problematic_cases()
    test_enhanced_vs_v2()