#!/usr/bin/env python3
"""
社会科目分析システムのテストスクリプト
"""

import sys
from pathlib import Path

# モジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from modules.social_analyzer import SocialAnalyzer

def test_analyzer():
    """アナライザーのテスト"""
    analyzer = SocialAnalyzer()
    
    # テスト用の問題文
    test_questions = [
        "問1. 江戸時代の参勤交代について説明しなさい。",
        "問2. 地図を見て、日本の四大工業地帯を答えなさい。",
        "問3. 日本国憲法の三大原則を選びなさい。ア 国民主権 イ 平和主義 ウ 基本的人権の尊重",
        "問4. SDGsの17の目標のうち、環境に関するものを3つ挙げなさい。",
        "問5. 2024年のウクライナ情勢について、国際連合の対応を述べなさい。",
    ]
    
    print("=" * 60)
    print("社会科目分析システム - テスト実行")
    print("=" * 60)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n【テスト{i}】")
        print(f"問題文: {question}")
        
        result = analyzer.analyze_question(question, f"問{i}")
        
        print(f"  分野: {result.field.value}")
        print(f"  資料: {', '.join([r.value for r in result.resource_types])}")
        print(f"  形式: {result.question_format.value}")
        print(f"  時事: {'○' if result.is_current_affairs else '×'}")
        
        if result.time_period:
            print(f"  時代: {result.time_period}")
        if result.region:
            print(f"  地域: {result.region}")
        if result.keywords:
            print(f"  キーワード: {', '.join(result.keywords[:3])}")
    
    print("\n" + "=" * 60)
    print("テスト完了！")
    print("=" * 60)

if __name__ == "__main__":
    test_analyzer()