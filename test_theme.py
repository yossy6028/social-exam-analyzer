#!/usr/bin/env python3
"""
テーマ抽出機能のテスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.social_analyzer import SocialAnalyzer

def test_theme_extraction():
    """テーマ抽出のテスト"""
    analyzer = SocialAnalyzer()
    
    test_questions = [
        "次の地図を見て、日本の四大工業地帯の名称をすべて答えなさい。",
        "江戸時代の参勤交代制度について、その目的と影響を説明しなさい。",
        "日本国憲法の三大原則を選びなさい。",
        "SDGsの17の目標のうち、環境に関連する目標を3つ挙げなさい。",
        "地球温暖化の原因と対策について述べなさい。",
        "明治維新の中心人物を3人挙げ、それぞれの功績を述べなさい。",
        "国際連合の主要機関を5つ答えなさい。",
        "少子高齢化について説明しなさい。",
        "織田信長の政策について述べなさい。",
        "参議院の役割について説明しなさい。",
        "関東地方の特産品を3つ挙げなさい。",
        "太平洋戦争の影響について述べなさい。",
        "日米安全保障条約について説明しなさい。",
        "応仁の乱について、その原因と結果を述べなさい。",
        "三権分立の仕組みについて説明しなさい。",
    ]
    
    print("【テーマ抽出テスト結果】")
    print("=" * 70)
    
    for i, text in enumerate(test_questions, 1):
        question = analyzer.analyze_question(text, f"問{i}")
        print(f"\n問{i}:")
        print(f"  問題文: {text[:50]}...")
        print(f"  抽出テーマ: {question.topic if question.topic else '（抽出できず）'}")
        print(f"  分野: {question.field.value}")
        if question.keywords:
            print(f"  キーワード: {', '.join(question.keywords[:5])}")
    
    print("\n" + "=" * 70)
    print("テスト完了")

if __name__ == "__main__":
    test_theme_extraction()