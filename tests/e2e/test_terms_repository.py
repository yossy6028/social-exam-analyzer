#!/usr/bin/env python3
"""
TermsRepositoryの動作をテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.terms_repository import TermsRepository

def test_terms_repository():
    """TermsRepositoryのテスト"""
    repo = TermsRepository()
    
    print("=== TermsRepository テスト ===\n")
    
    print(f"利用可能: {repo.available()}")
    print(f"用語数: {len(repo.terms) if repo.terms else 0}")
    print(f"歴史用語数: {len(repo.terms.get('history', [])) if repo.terms else 0}")
    print(f"地理用語数: {len(repo.terms.get('geography', [])) if repo.terms else 0}")
    print(f"公民用語数: {len(repo.terms.get('civics', [])) if repo.terms else 0}")
    
    if repo.terms:
        print(f"\n歴史用語例: {repo.terms['history'][:5]}")
        print(f"地理用語例: {repo.terms['geography'][:5]}")
        print(f"公民用語例: {repo.terms['civics'][:5]}")
    
    print(f"\n時代インデックス: {len(repo.history_index) if repo.history_index else 0}")
    
    # テストテキスト
    test_texts = [
        "次の文章が説明している平野を、地図中ア~エから1つ選び記号で答えなさい。",
        "次の雨温図は、地図中に示したA~Cの都市のいずれかのものです。",
        "次の地形図を見て、以下の問いに答えなさい。",
        "次の表は、それぞれ藤、肉用若鶏の都道府県別頭数(2021年)の上位5道県を示しています。",
        "図中の11の地図記号は何を示しているか、次のア~エから1つ選び記号で答えなさい。",
        "地形図から読み取れることとして正しいものを、次のア~エから1つ選び記号で答えなさい。",
    ]
    
    print("\n=== 用語検索テスト ===")
    for i, text in enumerate(test_texts, 1):
        print(f"\nテスト {i}: {text[:50]}...")
        
        # 用語検索
        terms = repo.find_terms_in_text(text)
        print(f"  検出用語: {terms}")
        
        # 分野推定
        field = repo.best_field_for_text(text)
        print(f"  推定分野: {field}")
        
        # テーマ提案
        theme = repo.suggest_theme(text)
        print(f"  テーマ提案: {theme}")
        
        # 時代推定（歴史の場合）
        if field == 'history':
            period = repo.infer_history_period(text)
            print(f"  時代推定: {period}")

if __name__ == "__main__":
    test_terms_repository()
