#!/usr/bin/env python3
"""
修正されたテーマ抽出器のテスト
空欄補充、選択肢問題、図表問題などでテーマが正しく検出されるかをテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.theme_extractor_v2 import ThemeExtractorV2

def test_theme_extraction():
    """テーマ抽出のテスト"""
    extractor = ThemeExtractorV2()
    
    print("=== 修正されたテーマ抽出器のテスト ===\n")
    
    # テストケース
    test_cases = [
        # 空欄補充・穴埋め問題
        ("空らん( ① )について、空らんに入る適切な語句を、次のア~エの中から一つ選び記号で答えなさい。", "空欄補充問題"),
        ("空欄( ② )について、空欄に入る適切な語句を選びなさい。", "空欄補充問題"),
        ("穴埋め( ③ )について、適切な語句を答えなさい。", "穴埋め問題"),
        
        # 選択肢問題
        ("次のア~エの中から正しいものを一つ選びなさい。ア.鎌倉幕府 イ.室町幕府 ウ.江戸幕府 エ.明治政府", "選択肢問題"),
        ("ア.桓武天皇が平安京に遷都を行った。 イ.朝廷によって墾田永年私財法が出された。", "選択肢問題"),
        ("次の選択肢から正しいものを選びなさい。", "選択肢問題"),
        
        # 図表問題
        ("次の図を読んで、都市の特徴を説明しなさい。", "図表問題"),
        ("表から読み取れることを説明しなさい。", "図表問題"),
        ("グラフを分析して、人口の変化を説明しなさい。", "図表問題"),
        ("地図中の都市について説明しなさい。", "図表問題"),
        ("写真から読み取れることを説明しなさい。", "図表問題"),
        ("資料を分析して、特徴を説明しなさい。", "図表問題"),
        
        # 歴史問題
        ("鎌倉幕府の成立について説明しなさい。", "歴史問題"),
        ("明治維新の改革について説明しなさい。", "歴史問題"),
        ("江戸時代の身分制度について説明しなさい。", "歴史問題"),
        
        # 地理問題
        ("日本の地形について説明しなさい。", "地理問題"),
        ("人口ピラミッドの分析をしなさい。", "地理問題"),
        ("雨温図の読み取りをしなさい。", "地理問題"),
        
        # 公民問題
        ("日本国憲法の内容について説明しなさい。", "公民問題"),
        ("選挙の仕組みについて説明しなさい。", "公民問題"),
        ("裁判員制度の仕組みについて説明しなさい。", "公民問題"),
        
        # 複合問題
        ("次の資料を読んで、各設問に答えなさい。", "複合問題"),
        ("図表を読み取って、歴史的背景を説明しなさい。", "複合問題"),
    ]
    
    for i, (text, description) in enumerate(test_cases, 1):
        print(f"テストケース {i}: {description}")
        print(f"テキスト: {text[:50]}...")
        
        try:
            result = extractor.extract(text)
            if result and result.theme:
                print(f"結果: ✓ テーマ抽出成功")
                print(f"  テーマ: {result.theme}")
                print(f"  カテゴリ: {result.category}")
                print(f"  信頼度: {result.confidence}")
            else:
                print(f"結果: ✗ テーマ抽出失敗")
                print(f"  テーマ: {result.theme if result else 'None'}")
                print(f"  カテゴリ: {result.category if result else 'None'}")
                print(f"  信頼度: {result.confidence if result else 'N/A'}")
        except Exception as e:
            print(f"結果: ✗ エラー発生: {e}")
        
        print("-" * 60)
    
    print("\n=== 除外パターンのテスト ===")
    
    # 除外されるべきテキスト
    exclusion_cases = [
        "空欄補充",  # 単独の空欄補充
        "穴埋め",    # 単独の穴埋め
        "選択肢",    # 単独の選択肢
        "問1",       # 問題番号のみ
        "下線部①",   # 下線部のみ
        "次の図",    # 図の紹介のみ
        "次の表",    # 表の紹介のみ
    ]
    
    for text in exclusion_cases:
        print(f"除外テスト: {text}")
        try:
            should_exclude = extractor._should_exclude(text)
            print(f"除外判定: {'✓ 除外' if should_exclude else '✗ 除外しない'}")
        except Exception as e:
            print(f"エラー: {e}")
        print("-" * 30)

if __name__ == "__main__":
    test_theme_extraction()
