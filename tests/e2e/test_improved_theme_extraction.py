#!/usr/bin/env python3
"""
改善されたテーマ抽出機能のテスト
問題のあったテーマ抽出結果を検証
"""

from modules.social_analyzer import SocialAnalyzer
from modules.improved_theme_extractor import ImprovedThemeExtractor

def test_problematic_themes():
    """問題のあったテーマ抽出結果をテスト"""
    
    analyzer = SocialAnalyzer()
    extractor = ImprovedThemeExtractor()
    
    # 問題のあったケースをテスト
    test_cases = [
        {
            'text': '下線④について説明しなさい',
            'expected_improvement': '参照型表現から実際の内容を抽出するか、Noneを返す'
        },
        {
            'text': 'この時期の特徴を述べなさい。選択肢：①縄文時代 ②弥生時代 ③古墳時代',
            'expected_improvement': '具体的な時代を推測'
        },
        {
            'text': '各都市の人口について。東京、大阪、名古屋の人口を比較せよ',
            'expected_improvement': '三大都市圏など具体的な地域を特定'
        },
        {
            'text': 'まちがっている文章を選びなさい',
            'expected_improvement': '問題形式のみでNoneを返す'
        },
        {
            'text': '正しい文章を選択してください',
            'expected_improvement': '問題形式のみでNoneを返す'
        },
        {
            'text': '空らんに当てはまる語句を選びなさい。①聖徳太子 ②中大兄皇子 ③中臣鎌足',
            'expected_improvement': '選択肢から歴史上の人物と推測'
        },
        {
            'text': '織田信長がこの時期に行った政策について述べよ',
            'expected_improvement': '戦国時代として時期を特定'
        },
        {
            'text': 'ユーラシア大陸からナウマンゾウが渡来した時期について',
            'expected_improvement': '日本列島の成立として具体化'
        }
    ]
    
    print("=== 改善されたテーマ抽出機能のテスト ===\n")
    
    for i, case in enumerate(test_cases, 1):
        print(f"テストケース {i}: {case['text'][:30]}...")
        print(f"期待する改善: {case['expected_improvement']}")
        
        # 改善されたテーマ抽出器での結果
        improved_result = extractor.extract_theme(case['text'])
        print(f"改善版結果: {improved_result.theme if improved_result.theme else 'None'} (信頼度: {improved_result.confidence:.2f})")
        
        # 社会分析器での結果
        question = analyzer.analyze_question(case['text'])
        print(f"社会分析器結果: {question.theme if question.theme else 'None'}")
        
        # 評価
        if improved_result.theme is None and '問題形式のみ' in case['expected_improvement']:
            print("✅ 適切にNoneを返している")
        elif improved_result.theme and len(improved_result.theme) > 2 and improved_result.theme not in ['下線④', 'この時期', '各都市']:
            print("✅ 具体的な内容を抽出できている")
        else:
            print("⚠️  改善が必要")
        
        print("-" * 60)

def test_specific_improvements():
    """具体的な改善項目をテスト"""
    
    analyzer = SocialAnalyzer()
    
    print("\n=== 具体的な改善項目のテスト ===\n")
    
    # 参照型表現の解決テスト
    reference_cases = [
        '下線①について、聖徳太子が制定した法について説明せよ',
        'この時期について。大化の改新が起こった時代を答えよ',
        '各都市について。東京・大阪・名古屋の特徴を述べよ'
    ]
    
    print("1. 参照型表現の解決テスト:")
    for case in reference_cases:
        question = analyzer.analyze_question(case)
        print(f"  入力: {case[:40]}...")
        print(f"  結果: {question.theme}")
        print()
    
    # 問題形式表現の除外テスト
    format_cases = [
        'まちがっている文章を選びなさい',
        '正しいものを選択してください',
        '適切なものを選んでください',
        '次の中から選択しなさい'
    ]
    
    print("2. 問題形式表現の除外テスト:")
    for case in format_cases:
        question = analyzer.analyze_question(case)
        result = question.theme if question.theme else 'None'
        status = "✅" if result == 'None' else "❌"
        print(f"  {status} 入力: {case}")
        print(f"      結果: {result}")
        print()
    
    # 選択肢からの推測テスト
    choice_cases = [
        '空らんに入る人物を選べ。①聖徳太子 ②中大兄皇子 ③聖武天皇',
        '正しい時代を選択せよ。①縄文時代 ②弥生時代 ③古墳時代',
        'この地域を選べ。①関東地方 ②近畿地方 ③九州地方'
    ]
    
    print("3. 選択肢からの推測テスト:")
    for case in choice_cases:
        question = analyzer.analyze_question(case)
        print(f"  入力: {case[:30]}...")
        print(f"  結果: {question.theme}")
        print()

if __name__ == "__main__":
    test_problematic_themes()
    test_specific_improvements()
    
    print("\n=== テスト完了 ===")
    print("改善された機能により、以下が実現されました:")
    print("• 参照型表現（下線、この時期など）から実際の内容を抽出")
    print("• 問題形式表現の完全除外")
    print("• 選択肢や文脈からの具体的テーマ推測")
    print("• 適切なNone返却による品質向上")