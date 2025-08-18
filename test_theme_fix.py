#!/usr/bin/env python3
"""
テーマ抽出器の業績修正テスト
"""

from modules.enhanced_theme_extractor import EnhancedThemeExtractor

def test_gyoseki_fix():
    """業績パターンの修正をテスト"""
    extractor = EnhancedThemeExtractor()
    
    test_cases = [
        ("兵庫県明について説明しなさい", "兵庫県明の業績", "歴史"),
        ("真鍋淑郎氏がノーベル賞を受賞しました", "真鍋淑郎氏の業績", "歴史"),
        ("日宋貿易について答えなさい", "日宋貿易の業績", "歴史"),
        ("朱子学以外の学問", "朱子学以外の業績", "歴史"),
        ("新詳日本史について", "新詳日本史の業績", "歴史"),
    ]
    
    print("=== 業績パターン修正テスト ===\n")
    
    for text, original_theme, field in test_cases:
        # _is_invalid_themeのテスト
        is_invalid = extractor._is_invalid_theme(original_theme)
        
        # _fix_invalid_themeのテスト
        fixed_theme = extractor._fix_invalid_theme(original_theme, text, field)
        
        print(f"原文: {text[:30]}...")
        print(f"元テーマ: {original_theme}")
        print(f"無効判定: {is_invalid}")
        print(f"修正後: {fixed_theme}")
        print("-" * 40)
    
    # extract_theme全体のテスト
    print("\n=== extract_theme統合テスト ===\n")
    
    test_texts = [
        "兵庫県明について説明しなさい",
        "真鍋淑郎氏が2021年にノーベル物理学賞を受賞しました",
        "日宋貿易の特徴を答えなさい",
    ]
    
    for text in test_texts:
        result = extractor.extract_theme(text, field="歴史")
        print(f"入力: {text}")
        print(f"結果: {result}")
        print("-" * 40)

if __name__ == "__main__":
    test_gyoseki_fix()