#!/usr/bin/env python3
"""
Web検索を使用したテーマ抽出のテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.theme_extractor_with_web import ThemeExtractorWithWeb
from modules.web_search_integration import SocialTermWebSearcher
import asyncio


def test_web_search_extraction():
    """Web検索を使用したテーマ抽出テスト"""
    
    print("=" * 60)
    print("Web検索統合テスト")
    print("=" * 60)
    
    # Web検索対応の抽出器を作成
    extractor = ThemeExtractorWithWeb(enable_web_search=True)
    
    # 判定が難しいケース
    difficult_cases = [
        "青地大地震について説明しなさい",  # 誤記（阪神・淡路大震災）
        "上げ米の制について述べよ",         # 誤記（上米の制）
        "建武の改革について答えなさい",      # 不正確（建武の新政）
        "大東亜戦争について説明しなさい",    # 別名（太平洋戦争）
        "令和の改元について述べよ",          # 最新の時事
    ]
    
    print("\n困難なケースのテスト:")
    for text in difficult_cases:
        result = extractor.extract(text)
        
        print(f"\n入力: {text}")
        print(f"  基本抽出: {result.theme if result.theme else '（抽出失敗）'}")
        print(f"  信頼度: {result.confidence:.2f}")
        
        # Web検索が必要と判定された場合
        if extractor._needs_web_verification(text, result):
            print("  → Web検索で改善を試みます...")
            # 実際のWeb検索結果（モック）
            web_result = extractor._search_and_verify(text, result)
            if web_result and web_result.correct_expression:
                print(f"  ✅ 改善結果: {web_result.correct_expression}")
            else:
                print("  ❌ Web検索でも改善できず")


async def test_async_web_search():
    """非同期Web検索のテスト"""
    
    print("\n" + "=" * 60)
    print("非同期Web検索テスト")
    print("=" * 60)
    
    searcher = SocialTermWebSearcher(use_brave=True)
    
    # テスト用語
    terms = [
        ("阪神淡路", "大震災について"),
        ("上げ米", "江戸時代の制度"),
        ("建武", "後醍醐天皇の政治"),
    ]
    
    print("\n用語の正式名称検索:")
    for term, context in terms:
        result = await searcher.search_term(term, context)
        if result:
            print(f"\n検索語: {term}")
            print(f"  正式名称: {result.formal_name}")
            print(f"  カテゴリー: {result.category}")
            print(f"  信頼度: {result.confidence:.2f}")
        else:
            print(f"\n検索語: {term} → 結果なし")


def test_practical_integration():
    """実用的な統合テスト"""
    
    print("\n" + "=" * 60)
    print("実用統合テスト")
    print("=" * 60)
    
    # 実際の入試問題例
    test_questions = [
        "阪神大震災が起きた年について答えなさい。",
        "上げ米の制を実施した将軍は誰か。",
        "建武の改革が失敗した理由を述べよ。",
        "グリーンマークの意味を説明しなさい。",
        "気象庁ホームページで確認できる情報について述べよ。",
    ]
    
    extractor = ThemeExtractorWithWeb(enable_web_search=True)
    
    print("\n実際の問題文での抽出:")
    for i, question in enumerate(test_questions, 1):
        result = extractor.extract(question)
        
        print(f"\n問{i}: {question[:30]}...")
        
        if result.theme:
            print(f"  テーマ: {result.theme}")
            print(f"  分野: {result.category}")
            print(f"  信頼度: {result.confidence:.2f}")
        else:
            print("  テーマ: （除外または抽出不可）")
            
            # 除外理由を推測
            if any(ng in question for ng in ['グリーンマーク', 'ホームページ', '気象庁']):
                print("  理由: 社会科に不適切な用語")
            else:
                print("  理由: 文脈不足または不完全な表現")


def main():
    """メイン実行"""
    print("\n" + "=" * 60)
    print("Web検索を活用したテーマ抽出システムテスト")
    print("=" * 60)
    
    # 基本テスト
    test_web_search_extraction()
    
    # 非同期テスト
    print("\n非同期処理のテスト（スキップ - 実装時に有効化）")
    # asyncio.run(test_async_web_search())
    
    # 実用テスト
    test_practical_integration()
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)


if __name__ == "__main__":
    main()