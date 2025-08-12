#!/usr/bin/env python3
"""問題のあるテーマのテスト"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.theme_extractor_v2 import ThemeExtractorV2

def test_problematic_themes():
    """ユーザーが指摘した問題のあるテーマをテスト"""
    
    extractor = ThemeExtractorV2()
    
    # ユーザーが指摘した問題のあるケース
    problematic_cases = [
        ("下線部の内容", "文脈なしでは意味不明"),
        ("【い】にあてはまる人物名", "記号参照は意味不明"),
        ("新聞記事の内容", "文脈なしでは意味不明"),
        ("同年アメリカ合衆国の仕組み", "同年は文脈依存"),
        ("河川部の内容", "不明瞭な表現"),
        ("NATOに加盟する国は以下の表にある取り決め", "不完全な文"),
        ("グリーンマークの内容", "社会科と無関係"),
        ("気象庁ホームページの内容", "ホームページは除外"),
        ("電気機械器具の説明", "社会科と無関係"),
        ("にあてはまる人物名を次のア", "不完全な表現"),
    ]
    
    print("=" * 60)
    print("問題のあるテーマの除外テスト")
    print("=" * 60)
    
    success_count = 0
    for text, reason in problematic_cases:
        result = extractor.extract(text)
        theme = result.theme
        
        if theme is None:
            status = "✅"
            success_count += 1
        else:
            status = "❌"
        
        print(f"{status} {text}")
        print(f"   → {theme if theme else '（正しく除外）'} ({reason})")
        print()
    
    # 有効なテーマのテスト
    valid_cases = [
        ("江戸時代の政治について説明しなさい", "江戸時代の政治"),
        ("鎌倉幕府の成立について答えなさい", "鎌倉幕府の歴史"),
        ("日本国憲法の三原則について答えなさい", "日本国憲法の仕組み"),
        ("阪神淡路大震災について述べなさい", "阪神淡路大震災"),
        ("内閣総理大臣の役割について説明しなさい", "内閣総理大臣の仕組み"),
    ]
    
    print("\n有効なテーマの保持テスト")
    print("=" * 60)
    
    valid_count = 0
    for text, expected in valid_cases:
        result = extractor.extract(text)
        theme = result.theme
        
        if theme is not None:
            status = "✅"
            valid_count += 1
        else:
            status = "❌"
        
        print(f"{status} {text}")
        print(f"   期待: {expected}")
        print(f"   結果: {theme if theme else '（テーマなし）'}")
        print()
    
    print(f"\n問題ケース除外率: {success_count}/{len(problematic_cases)} ({success_count*100/len(problematic_cases):.1f}%)")
    print(f"有効ケース保持率: {valid_count}/{len(valid_cases)} ({valid_count*100/len(valid_cases):.1f}%)")

if __name__ == "__main__":
    test_problematic_themes()