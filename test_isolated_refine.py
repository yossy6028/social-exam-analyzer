#!/usr/bin/env python3
"""refineメソッドを分離してテスト"""

import re
from typing import Optional
from dataclasses import dataclass

@dataclass
class ExtractedTheme:
    """抽出されたテーマ"""
    theme: Optional[str]
    category: Optional[str]
    confidence: float

def _refine_theme_from_keywords(text: str) -> Optional[ExtractedTheme]:
    """キーワードから具体的なテーマを生成"""
    
    print(f"入力テキスト: '{text}'")
    
    # まず特定のキーワードを直接マッチング
    if '鎌倉幕府' in text:
        print("  '鎌倉幕府'がマッチ!")
        result = ExtractedTheme('鎌倉幕府の成立', '歴史', 0.9)
        print(f"  結果: {result}")
        return result
    
    if '日本国憲法' in text:
        print("  '日本国憲法'がマッチ!")
        return ExtractedTheme('日本国憲法の内容', '公民', 0.9)
    
    print("  マッチなし")
    return None

# テスト
test_cases = [
    "鎌倉幕府の成立について説明しなさい。",
    "日本国憲法の三原則について説明しなさい。",
    "関係ないテキスト",
]

for text in test_cases:
    print(f"\nテスト: {text}")
    result = _refine_theme_from_keywords(text)
    if result:
        print(f"→ テーマ: {result.theme}")
    else:
        print("→ None")