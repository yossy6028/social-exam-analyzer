#!/usr/bin/env python3
"""
除外パターン修正後のテスト
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.social_analyzer_fixed import FixedSocialAnalyzer

def test_exclusion_patterns():
    """除外パターンのテスト"""
    analyzer = FixedSocialAnalyzer()
    
    # 除外すべきテキスト
    exclude_texts = [
        "下線部⑥",
        "下線部の特徴",
        "下線部の史料として正しいものを",
        "【い】にあてはまる人物名",
        "にあてはまる人物名を次のア",
        "次の雨温図は",
        "次の図は",
        "次の表は",
        "具体的な権利の名称を用いてその事例",
        "以下のうち正しいもの",
        "次のア～エから選べ",
    ]
    
    # 有効なテキスト（除外してはいけない）
    include_texts = [
        "江戸時代の農業政策",
        "明治維新の影響",
        "阪神・淡路大震災の被害",
        "源頼朝",
        "日本国憲法",
        "米騒動",
        "環境問題",
        "北大西洋条約",
    ]
    
    print("=" * 60)
    print("除外パターンテスト")
    print("=" * 60)
    
    # 除外テスト
    print("\n【除外すべきテキスト】")
    excluded_count = 0
    for text in exclude_texts:
        result = analyzer.theme_extractor.extract(text)
        if result.theme is None:
            print(f"✅ 除外成功: {text}")
            excluded_count += 1
        else:
            print(f"❌ 除外失敗: {text} → {result.theme}")
    
    print(f"\n除外成功率: {excluded_count}/{len(exclude_texts)} ({excluded_count*100/len(exclude_texts):.1f}%)")
    
    # 抽出テスト
    print("\n【抽出すべきテキスト】")
    extracted_count = 0
    for text in include_texts:
        result = analyzer.theme_extractor.extract(text)
        if result.theme is not None:
            print(f"✅ 抽出成功: {text} → {result.theme}")
            extracted_count += 1
        else:
            print(f"❌ 抽出失敗: {text}")
    
    print(f"\n抽出成功率: {extracted_count}/{len(include_texts)} ({extracted_count*100/len(include_texts):.1f}%)")
    
    print("\n" + "=" * 60)
    if excluded_count == len(exclude_texts) and extracted_count >= len(include_texts) * 0.8:
        print("✅ テスト合格: 除外パターンが正しく機能しています")
    else:
        print("❌ テスト不合格: さらなる修正が必要です")
    print("=" * 60)

if __name__ == "__main__":
    test_exclusion_patterns()