#!/usr/bin/env python3
"""
強化版テーマ抽出器のテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.theme_extractor_enhanced import EnhancedThemeExtractor, create_enhanced_extractor
from modules.theme_extractor_v2 import ThemeExtractorV2


def test_error_correction():
    """誤記の自動修正テスト"""
    print("=" * 60)
    print("誤記の自動修正テスト")
    print("=" * 60)
    
    extractor = create_enhanced_extractor()
    
    # 誤記を含む問題文
    error_cases = [
        ("青地大震災について説明しなさい", "阪神・淡路大震災の被害"),
        ("青地大地震の被害について述べよ", "阪神・淡路大震災の被害"),
        ("上げ米の制について答えなさい", "上米の制の仕組み"),
        ("建武の改革の失敗理由を説明せよ", "建武の新政の内容"),
        ("大東亜戦争の終結について述べよ", "太平洋戦争の経過"),
        ("応仁の戦について説明しなさい", "応仁の乱の背景"),
    ]
    
    print("\n誤記を含む問題の処理:")
    for text, expected in error_cases:
        result = extractor.extract(text)
        
        is_correct = result.theme and expected in result.theme
        status = "✅" if is_correct else "❌"
        
        print(f"\n{status} 入力: {text}")
        print(f"  期待: {expected}")
        print(f"  結果: {result.theme if result.theme else '（抽出失敗）'}")
        print(f"  信頼度: {result.confidence:.2f}")


def test_comparison_with_base():
    """基本版との比較テスト"""
    print("\n" + "=" * 60)
    print("基本版との比較テスト")
    print("=" * 60)
    
    base_extractor = ThemeExtractorV2()
    enhanced_extractor = create_enhanced_extractor()
    
    # 難しいケース
    difficult_cases = [
        "青地大震災が起きた年を答えなさい。",
        "上げ米の制を実施した将軍は誰か。",
        "建武の改革が失敗した理由を述べよ。",
        "応仁の戦が起きた原因を説明せよ。",
        "大東亜戦争と呼ばれた戦争について述べよ。",
    ]
    
    print("\n基本版 vs 強化版:")
    for i, text in enumerate(difficult_cases, 1):
        base_result = base_extractor.extract(text)
        enhanced_result = enhanced_extractor.extract(text)
        
        print(f"\n問{i}: {text[:30]}...")
        print(f"  基本版: {base_result.theme if base_result.theme else '（抽出失敗）'}")
        print(f"  強化版: {enhanced_result.theme if enhanced_result.theme else '（抽出失敗）'}")
        
        # 改善度を評価
        if not base_result.theme and enhanced_result.theme:
            print("  → ✅ 強化版で改善")
        elif base_result.theme and enhanced_result.theme:
            if enhanced_result.confidence > base_result.confidence:
                print(f"  → ✅ 信頼度向上 ({base_result.confidence:.2f} → {enhanced_result.confidence:.2f})")


def test_standard_cases():
    """標準的なケースでの動作確認"""
    print("\n" + "=" * 60)
    print("標準ケースでの動作確認")
    print("=" * 60)
    
    extractor = create_enhanced_extractor()
    
    # 正常なケース（修正不要）
    normal_cases = [
        ("江戸時代の政治について説明しなさい", "江戸時代の政治"),
        ("日本国憲法の三原則について答えなさい", "日本国憲法の三原則"),
        ("鎌倉幕府の成立について述べなさい", "鎌倉幕府の成立"),
        ("内閣総理大臣の役割を説明しなさい", "内閣総理大臣の仕組み"),
    ]
    
    print("\n正常なケースの処理:")
    for text, expected_keyword in normal_cases:
        result = extractor.extract(text)
        
        is_correct = result.theme and expected_keyword in result.theme
        status = "✅" if is_correct else "❌"
        
        print(f"\n{status} {text[:30]}...")
        print(f"  結果: {result.theme}")
        print(f"  分野: {result.category}")


def test_exclusion_patterns():
    """除外パターンの動作確認"""
    print("\n" + "=" * 60)
    print("除外パターンテスト")
    print("=" * 60)
    
    extractor = create_enhanced_extractor()
    
    # 除外すべきケース
    exclude_cases = [
        "下線部の内容を説明しなさい",
        "【い】にあてはまる人物名を答えよ",
        "新聞記事の内容について述べよ",
        "グリーンマークの意味を説明せよ",
        "ホームページで確認できる情報を答えよ",
    ]
    
    print("\n除外パターンの確認:")
    success_count = 0
    for text in exclude_cases:
        result = extractor.extract(text)
        
        if result.theme is None:
            status = "✅"
            success_count += 1
        else:
            status = "❌"
        
        print(f"{status} {text} → {result.theme if result.theme else '（正しく除外）'}")
    
    print(f"\n除外成功率: {success_count}/{len(exclude_cases)} = {success_count*100/len(exclude_cases):.0f}%")


def main():
    """メイン実行"""
    print("\n" + "=" * 60)
    print("強化版テーマ抽出システムテスト")
    print("=" * 60)
    
    # 各種テスト実行
    test_error_correction()
    test_comparison_with_base()
    test_standard_cases()
    test_exclusion_patterns()
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)


if __name__ == "__main__":
    main()