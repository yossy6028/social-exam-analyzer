#!/usr/bin/env python3
"""
分析結果の問題をデバッグ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.theme_extractor_v2 import ThemeExtractorV2
from modules.terms_repository import TermsRepository

def test_problematic_themes():
    """問題のあるテーマをテスト"""
    
    print("=== 問題のあるテーマのデバッグ ===\n")
    
    # 問題のあるテーマの例
    problematic_texts = [
        "日宋貿易について説明しなさい。",
        "新聞記事を読んで答えなさい。",
        "社会保障制度について述べなさい。",
        "内閣の役割について説明しなさい。",
        "核兵器禁止条約について答えなさい。",
        "促成栽培について説明しなさい。",
    ]
    
    extractor = ThemeExtractorV2()
    
    for i, text in enumerate(problematic_texts, 1):
        print(f"テスト {i}: {text}")
        
        # テーマ抽出
        result = extractor.extract(text)
        print(f"  抽出テーマ: {result.theme}")
        print(f"  カテゴリ: {result.category}")
        print(f"  信頼度: {result.confidence}")
        
        if result.theme:
            print(f"  ✅ テーマ抽出成功")
        else:
            print(f"  ❌ テーマ抽出失敗")
        
        print()
    
    print("="*50)
    print("用語カタログの確認:")
    
    repo = TermsRepository()
    print(f"利用可能: {repo.available()}")
    print(f"地理用語数: {len(repo.terms.get('geography', [])) if repo.terms else 0}")
    
    # 特定の用語の確認
    test_terms = ["促成栽培", "日宋貿易", "社会保障", "内閣", "核兵器禁止条約"]
    for term in test_terms:
        terms = repo.find_terms_in_text(term)
        print(f"{term}: {terms}")

if __name__ == "__main__":
    test_problematic_themes()
