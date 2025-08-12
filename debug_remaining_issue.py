#!/usr/bin/env python3
"""
残り1件の問題をデバッグ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import re
from modules.theme_extractor_v2 import ThemeExtractorV2

def debug_remaining_issue():
    """残り1件の問題をデバッグ"""
    
    problematic_text = "次の資料は明治時代の工業について述べたものです"
    
    print(f"デバッグ対象: '{problematic_text}'")
    print()
    
    extractor = ThemeExtractorV2()
    
    # ステップ1: 除外パターンの個別チェック
    print("=== 除外パターンの個別チェック ===")
    
    # 新しく追加したパターンをテスト
    new_patterns = [
        r'^次の.*?について述べた(もの|内容)',
        r'^次の.*?に関する(資料|文章|記述)',
        r'^次の.*?を示した(もの|図|表|資料)',
    ]
    
    for pattern_str in new_patterns:
        pattern = re.compile(pattern_str)
        match = pattern.search(problematic_text)
        print(f"Pattern: {pattern_str}")
        print(f"Match: {bool(match)}")
        if match:
            print(f"Matched: '{match.group()}'")
        print()
    
    # ステップ2: _should_exclude メソッドの結果
    print("=== _should_exclude メソッドの結果 ===")
    should_exclude = extractor._should_exclude(problematic_text)
    print(f"should_exclude: {should_exclude}")
    print()
    
    # ステップ3: 各段階での処理状況を確認
    print("=== 抽出処理の段階別確認 ===")
    
    # 除外チェック
    if extractor._should_exclude(problematic_text):
        print("Stage 1: 除外チェック -> 除外される")
    else:
        print("Stage 1: 除外チェック -> 通過")
        
        # 具体的パターンマッチング
        specific = extractor._match_specific_patterns(problematic_text)
        if specific:
            print(f"Stage 2: 具体的パターン -> '{specific.theme}'")
        else:
            print("Stage 2: 具体的パターン -> マッチなし")
            
            # カテゴリパターンマッチング  
            category = extractor._match_category_patterns(problematic_text)
            if category:
                print(f"Stage 3: カテゴリパターン -> '{category.theme}'")
            else:
                print("Stage 3: カテゴリパターン -> マッチなし")
                
                # 抽象パターンマッチング
                abstract = extractor._match_abstract_patterns(problematic_text)
                if abstract:
                    print(f"Stage 4: 抽象パターン -> '{abstract.theme}'")
                else:
                    print("Stage 4: 抽象パターン -> マッチなし")
                    
                    # フォールバック
                    fallback = extractor._fallback_extraction(problematic_text)
                    print(f"Stage 5: フォールバック -> '{fallback.theme}'")
    
    print()
    
    # ステップ4: 最終結果
    result = extractor.extract(problematic_text)
    print(f"=== 最終結果 ===")
    print(f"Theme: '{result.theme}'")
    print(f"Category: '{result.category}'")
    print(f"Confidence: {result.confidence}")


if __name__ == '__main__':
    debug_remaining_issue()