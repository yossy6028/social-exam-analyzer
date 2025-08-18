#!/usr/bin/env python3
"""
Brave Search APIを使用した実際のテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.brave_search_client import BraveSearchClient, get_brave_client
from modules.theme_extractor_v2 import ThemeExtractorV2
import time


def test_brave_api_connection():
    """Brave Search API接続テスト"""
    print("=" * 60)
    print("Brave Search API接続テスト")
    print("=" * 60)
    
    # APIキーを設定してクライアント作成
    client = get_brave_client()
    
    # テスト検索
    test_queries = [
        "阪神淡路大震災 正式名称",
        "上米の制 江戸時代",
        "建武の新政 後醍醐天皇",
    ]
    
    for query in test_queries:
        print(f"\n検索: {query}")
        results = client.search(query, count=3, lang="ja")
        
        if results:
            print(f"  ✅ {len(results)}件の結果を取得")
            for i, result in enumerate(results[:2], 1):
                print(f"  {i}. {result.title[:50]}...")
                print(f"     {result.description[:80]}...")
        else:
            print("  ❌ 結果なし")
        
        time.sleep(0.5)  # レート制限対策


def test_social_term_correction():
    """社会科用語の修正テスト"""
    print("\n" + "=" * 60)
    print("社会科用語修正テスト")
    print("=" * 60)
    
    client = get_brave_client()
    
    # 誤った用語と正しい用語のペア
    test_cases = [
        ("青地大震災", "地震", "阪神・淡路大震災"),
        ("上げ米の制", "江戸時代の政策", "上米の制"),
        ("建武の改革", "後醍醐天皇", "建武の新政"),
        ("大東亜戦争", "太平洋", "太平洋戦争"),
    ]
    
    print("\n誤った用語の修正:")
    for wrong_term, context, expected in test_cases:
        result = client.search_social_term(wrong_term, context)
        
        print(f"\n入力: {wrong_term}")
        print(f"  期待: {expected}")
        
        if result:
            formal_name = result.get('formal_name', wrong_term)
            category = result.get('category', '不明')
            confidence = result.get('confidence', 0.0)
            
            is_correct = expected in formal_name or formal_name in expected
            status = "✅" if is_correct else "❌"
            
            print(f"  {status} 結果: {formal_name}")
            print(f"     分野: {category}")
            print(f"     信頼度: {confidence:.2f}")
        else:
            print("  ❌ 検索失敗")
        
        time.sleep(0.5)


def test_theme_extraction_with_brave():
    """Brave検索を使用したテーマ抽出の改善テスト"""
    print("\n" + "=" * 60)
    print("Brave検索統合テーマ抽出テスト")
    print("=" * 60)
    
    client = get_brave_client()
    extractor = ThemeExtractorV2()
    
    # 難しいケース
    difficult_cases = [
        "青地大震災について説明しなさい。",
        "上げ米の制を実施した人物を答えなさい。",
        "建武の改革が失敗した理由を述べよ。",
        "大東亜戦争の終結について説明しなさい。",
    ]
    
    print("\n困難なケースの処理:")
    for question in difficult_cases:
        print(f"\n問題: {question[:30]}...")
        
        # 基本の抽出
        base_result = extractor.extract(question)
        print(f"  基本抽出: {base_result.theme if base_result.theme else '（失敗）'}")
        
        # キーワード抽出
        import re
        keywords = re.findall(r'[一-龥ァ-ヴー]{3,}', question)
        main_keyword = None
        for keyword in keywords:
            if keyword not in ['について', '説明しなさい', '答えなさい', '述べよ']:
                main_keyword = keyword
                break
        
        if main_keyword:
            # Brave検索で改善
            search_result = client.search_social_term(main_keyword, question)
            if search_result:
                formal_name = search_result.get('formal_name', main_keyword)
                category = search_result.get('category', '総合')
                
                # 改善されたテーマを生成
                if '震災' in formal_name:
                    improved_theme = f"{formal_name}の被害"
                elif '戦争' in formal_name:
                    improved_theme = f"{formal_name}の経過"
                elif '改革' in formal_name or '新政' in formal_name:
                    improved_theme = f"{formal_name}の内容"
                else:
                    improved_theme = f"{formal_name}の{category}"
                
                print(f"  ✅ Brave改善: {improved_theme}")
            else:
                print(f"  ❌ Brave検索失敗")
        
        time.sleep(0.5)


def test_current_affairs_search():
    """時事問題の検索テスト"""
    print("\n" + "=" * 60)
    print("時事問題検索テスト")
    print("=" * 60)
    
    client = get_brave_client()
    
    # 最近の時事キーワード
    current_topics = [
        "SDGs 持続可能な開発目標",
        "カーボンニュートラル 2050年",
        "ウクライナ情勢 2024",
    ]
    
    print("\n時事問題の検索:")
    for topic in current_topics:
        print(f"\nトピック: {topic}")
        results = client.search(topic + " 日本 社会科", count=2, lang="ja")
        
        if results:
            print("  最新情報:")
            for result in results:
                print(f"  - {result.title[:60]}...")
                if '2024' in result.description or '2023' in result.description:
                    print("    → 最新の情報を含む")
        else:
            print("  情報なし")
        
        time.sleep(0.5)


def main():
    """メイン実行"""
    print("\n" + "=" * 60)
    print("Brave Search API実装テスト")
    print("=" * 60)
    print("APIキー: 設定済み")
    print("=" * 60)
    
    try:
        # API接続テスト
        test_brave_api_connection()
        
        # 用語修正テスト
        test_social_term_correction()
        
        # テーマ抽出改善テスト
        test_theme_extraction_with_brave()
        
        # 時事問題テスト
        test_current_affairs_search()
        
        print("\n" + "=" * 60)
        print("全テスト完了")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()