#!/usr/bin/env python3
"""
コマンドファイル統合テスト
改善された機能が正しく動作するかテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.social_analyzer_fixed import FixedSocialAnalyzer


def test_integration():
    """統合テスト"""
    print("=" * 60)
    print("コマンドファイル統合テスト")
    print("=" * 60)
    
    # アナライザーの初期化
    analyzer = FixedSocialAnalyzer()
    
    # 強化版テーマ抽出器の確認
    if hasattr(analyzer, 'theme_extractor'):
        if analyzer.theme_extractor:
            print("✅ 強化版テーマ抽出器が統合されています")
            
            # テスト用のテキスト
            test_cases = [
                "青地大震災について説明しなさい",
                "上げ米の制について答えなさい",
                "建武の改革について述べなさい",
            ]
            
            print("\n誤記修正機能のテスト:")
            for text in test_cases:
                result = analyzer.theme_extractor.extract(text)
                print(f"  入力: {text}")
                print(f"  → {result.theme if result.theme else '（抽出失敗）'}")
        else:
            print("❌ テーマ抽出器が初期化されていません")
    else:
        print("❌ theme_extractorが定義されていません")
    
    # 大問検出機能のテスト
    print("\n大問検出機能のテスト:")
    test_text = """
    問1 江戸時代について
    問2 明治維新について
    問3 大正時代について
    問1 地理について
    問2 気候について
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
    
    if len(large_sections) >= 2:
        print(f"  ✅ {len(large_sections)}個の大問を検出")
    else:
        print(f"  ❌ {len(large_sections)}個しか検出されず")
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)


if __name__ == "__main__":
    test_integration()