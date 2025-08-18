#\!/usr/bin/env python3
"""
テーマ抽出の詳細テスト
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.social_analyzer_fixed import FixedSocialAnalyzer

def test_theme_extraction():
    """様々な問題文でテーマ抽出をテスト"""
    
    analyzer = FixedSocialAnalyzer()
    
    # 実際の問題文の例
    test_texts = [
        "江戸時代の農業について説明しなさい。",
        "明治維新の影響を述べなさい。",
        "下線部⑥について答えなさい。",
        "太平洋戦争の原因について説明しなさい。",
        "関東地方の工業の特徴を述べなさい。",
        "日本国憲法の三原則について答えなさい。",
        "地図中のAの都市名を答えなさい。",
        "次の表から読み取れることを説明しなさい。",
        "源頼朝が鎌倉に幕府を開いた理由を述べなさい。",
        "環境問題への対策について説明しなさい。",
        "少子高齢化の影響について述べなさい。",
        "三権分立の仕組みについて説明しなさい。",
        "室町時代の文化の特徴を答えなさい。",
        "阪神・淡路大震災の被害について述べなさい。",
        "SDGsの目標について説明しなさい。",
        "大化の改新の内容を説明しなさい。",
        "北海道の農業の特徴を述べなさい。",
        "選挙制度について説明しなさい。",
        "平安時代の文学について述べなさい。",
        "地球温暖化の原因について説明しなさい。",
    ]
    
    print("=== テーマ抽出テスト ===\n")
    
    extracted_count = 0
    for text in test_texts:
        result = analyzer.theme_extractor.extract(text)
        
        if result.theme:
            print(f"✅ {text[:30]}... → {result.theme}")
            extracted_count += 1
        else:
            print(f"❌ {text[:30]}... → 抽出失敗")
    
    print(f"\n抽出成功率: {extracted_count}/{len(test_texts)} ({extracted_count*100/len(test_texts):.1f}%)")
    
    # 期待値は80%以上
    if extracted_count >= len(test_texts) * 0.8:
        print("✅ テスト成功")
    else:
        print("❌ 抽出率が低すぎます")

if __name__ == "__main__":
    test_theme_extraction()
