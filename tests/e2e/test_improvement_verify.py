#!/usr/bin/env python3
"""改善の検証テスト"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.social_analyzer_fixed import FixedSocialAnalyzer
from modules.theme_extractor_v2 import ThemeExtractorV2
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)

def test_improvements():
    """改善点の検証"""
    
    # テストケース1: 大問番号の異常値修正
    print("=" * 60)
    print("テスト1: 大問番号の異常値修正")
    print("=" * 60)
    
    test_text_1 = """
    問22 江戸時代の身分制度について説明しなさい。
    問23 明治維新について説明しなさい。
    問24 大日本帝国憲法について説明しなさい。
    """
    
    analyzer = FixedSocialAnalyzer()
    questions_1 = analyzer._extract_with_reset_detection(test_text_1)
    
    for q_id, q_text in questions_1:
        print(f"  {q_id}: {q_text[:50]}...")
    
    # 大問22ではなく大問3になるべき
    assert not any("大問22" in q[0] for q in questions_1), "大問22が検出されました（修正失敗）"
    print("✅ 大問番号の異常値が正しく修正されました")
    
    # テストケース2: 具体的なテーマ抽出
    print("\n" + "=" * 60)
    print("テスト2: 具体的なテーマ抽出")
    print("=" * 60)
    
    test_cases = [
        ("鎌倉幕府の成立について説明しなさい。", "鎌倉幕府の成立"),
        ("江戸時代の身分制度について答えなさい。", "江戸時代の特徴"),
        ("日本国憲法の三原則について説明しなさい。", "日本国憲法"),
        ("人口ピラミッドを見て答えなさい。", "人口ピラミッドの分析"),
        ("兵庫県の特徴について説明しなさい。", "兵庫県の特徴"),
    ]
    
    extractor = ThemeExtractorV2()
    
    for text, expected in test_cases:
        result = extractor.extract(text)
        theme = result.theme if result.theme else "（テーマなし）"
        print(f"  入力: {text[:30]}...")
        print(f"  抽出: {theme}")
        print(f"  期待: {expected}")
        if expected in theme or theme in expected:
            print("  ✅ OK")
        else:
            print("  ⚠️ 要改善")
    
    # テストケース3: 問題とテーマの対応
    print("\n" + "=" * 60)
    print("テスト3: 31問検出時のテーマ抽出率")
    print("=" * 60)
    
    # 実際の入試問題風のテキスト
    test_text_3 = """
    1. 次の文章を読んで答えなさい。
    
    問1 鎌倉幕府の成立について説明しなさい。
    問2 室町幕府の政治について述べなさい。
    問3 江戸時代の身分制度について答えなさい。
    問4 明治維新の改革について説明しなさい。
    問5 大日本帝国憲法の特徴を述べなさい。
    問6 太平洋戦争の経過について答えなさい。
    問7 日本国憲法の三原則を説明しなさい。
    問8 高度経済成長期の特徴を述べなさい。
    
    2. 次の地図を見て答えなさい。
    
    問1 関東平野の特徴について説明しなさい。
    問2 日本の気候区分について述べなさい。
    問3 工業地帯の分布について答えなさい。
    問4 人口ピラミッドを分析しなさい。
    問5 都市化の問題について説明しなさい。
    問6 農業の特色について述べなさい。
    問7 交通網の発達について答えなさい。
    問8 環境問題の対策について説明しなさい。
    
    3. 公民分野について答えなさい。
    
    問1 国会の仕組みについて説明しなさい。
    問2 内閣の役割について述べなさい。
    問3 裁判所の種類について答えなさい。
    問4 選挙制度について説明しなさい。
    問5 地方自治の仕組みを述べなさい。
    問6 国際連合の役割について答えなさい。
    問7 SDGsの目標について説明しなさい。
    """
    
    questions_3 = analyzer._extract_with_reset_detection(test_text_3)
    
    total_questions = len(questions_3)
    themes_extracted = 0
    
    for q_id, q_text in questions_3:
        result = extractor.extract(q_text)
        if result.theme:
            themes_extracted += 1
    
    extraction_rate = (themes_extracted / total_questions * 100) if total_questions > 0 else 0
    
    print(f"  総問題数: {total_questions}問")
    print(f"  テーマ抽出成功: {themes_extracted}問")
    print(f"  抽出率: {extraction_rate:.1f}%")
    
    if extraction_rate >= 80:
        print("  ✅ 高い抽出率を達成")
    elif extraction_rate >= 60:
        print("  ⚠️ 改善の余地あり")
    else:
        print("  ❌ さらなる改善が必要")
    
    print("\n" + "=" * 60)
    print("改善検証完了")
    print("=" * 60)

if __name__ == "__main__":
    test_improvements()