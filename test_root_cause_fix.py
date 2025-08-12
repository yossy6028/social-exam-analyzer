#!/usr/bin/env python3
"""
根本原因修正後のテスト
除外されるべきテーマが確実に除外されているかを確認
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.social_analyzer_fixed import FixedSocialAnalyzer
import logging

# ログレベル設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_root_cause_fix():
    """根本原因修正のテスト"""
    
    # 修正版アナライザーを初期化
    analyzer = FixedSocialAnalyzer()
    
    # 問題のあるテーマを含む問題文
    problematic_questions = [
        "下線部⑥について答えなさい",
        "下線部の史料として正しいものを選びなさい",
        "下線部の特徴を説明しなさい",
        "【い】にあてはまる人物名を答えなさい",
        "にあてはまる人物名を次のア～エから選びなさい",
        "具体的な権利の名称を用いてその事例を説明しなさい",
        "8字で答えなさい",
        "正しいものを選びなさい",
        "まちがっているものを選びなさい"
    ]
    
    print("=== 根本原因修正後のテスト ===")
    
    for i, question in enumerate(problematic_questions, 1):
        print(f"\n--- テスト {i}: '{question}' ---")
        
        # 問題を分析
        analyzed_question = analyzer.analyze_question(question, f"問{i}")
        
        print(f"抽出されたトピック: {analyzed_question.topic}")
        
        if analyzed_question.topic is None:
            print("✅ 正常に除外されている")
        else:
            print("❌ 除外されるべきだが抽出されている")
            # デバッグ用: 抽出器を直接テスト
            if hasattr(analyzer, 'theme_extractor') and analyzer.theme_extractor:
                direct_result = analyzer.theme_extractor.extract(question)
                print(f"   直接抽出結果: theme={direct_result.theme}, confidence={direct_result.confidence}")

def test_valid_themes():
    """有効なテーマが正しく抽出されるかテスト"""
    
    analyzer = FixedSocialAnalyzer()
    
    # 有効なテーマを含む問題文
    valid_questions = [
        "鎌倉幕府の成立について説明しなさい",
        "明治維新の改革内容について答えなさい",
        "関東地方の産業について説明しなさい",
        "日本国憲法の三原則について述べなさい",
        "太平洋戦争の経過について答えなさい"
    ]
    
    print("\n=== 有効テーマの抽出テスト ===")
    
    for i, question in enumerate(valid_questions, 1):
        print(f"\n--- テスト {i}: '{question}' ---")
        
        analyzed_question = analyzer.analyze_question(question, f"問{i}")
        
        print(f"抽出されたトピック: {analyzed_question.topic}")
        print(f"分野: {analyzed_question.field.value}")
        
        if analyzed_question.topic:
            print("✅ 正常にテーマが抽出されている")
        else:
            print("❌ テーマが抽出されていない（問題の可能性）")

if __name__ == "__main__":
    test_root_cause_fix()
    test_valid_themes()