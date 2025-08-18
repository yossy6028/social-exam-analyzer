#!/usr/bin/env python3
"""
農業用語の検出テスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.terms_repository import TermsRepository
from modules.theme_extractor_v2 import ThemeExtractorV2

def test_agriculture_terms():
    """農業用語の検出テスト"""
    
    print("=== 農業用語検出テスト ===\n")
    
    # テストテキスト（日本工業大学附属駒場2023年度の問題を想定）
    test_texts = [
        "次の文章が説明している促成栽培について、適切なものを選びなさい。",
        "促成栽培は、野菜や果物を通常より早い時期に収穫する農業技術です。",
        "次の表は、促成栽培による収穫量の変化を示しています。",
        "促成栽培と抑制栽培の違いについて説明しなさい。",
        "施設園芸における促成栽培の特徴を述べなさい。",
        "次の地図を見て、促成栽培が盛んな地域を答えなさい。",
    ]
    
    # TermsRepositoryのテスト
    print("1. TermsRepository テスト")
    repo = TermsRepository()
    print(f"  利用可能: {repo.available()}")
    print(f"  地理用語数: {len(repo.terms.get('geography', [])) if repo.terms else 0}")
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n  テスト {i}: {text[:50]}...")
        
        # 用語検索
        terms = repo.find_terms_in_text(text)
        print(f"    検出用語: {terms}")
        
        # 分野推定
        field = repo.best_field_for_text(text)
        print(f"    推定分野: {field}")
        
        # テーマ提案
        theme = repo.suggest_theme(text)
        print(f"    テーマ提案: {theme}")
    
    print("\n" + "="*50 + "\n")
    
    # ThemeExtractorV2のテスト
    print("2. ThemeExtractorV2 テスト")
    extractor = ThemeExtractorV2()
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n  テスト {i}: {text[:50]}...")
        
        # テーマ抽出
        result = extractor.extract(text)
        print(f"    テーマ: {result.theme}")
        print(f"    カテゴリ: {result.category}")
        print(f"    信頼度: {result.confidence}")
        
        if result.theme:
            print(f"    ✅ テーマ抽出成功")
        else:
            print(f"    ❌ テーマ抽出失敗")

if __name__ == "__main__":
    test_agriculture_terms()
