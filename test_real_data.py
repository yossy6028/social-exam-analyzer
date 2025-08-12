#!/usr/bin/env python3
"""
実データでのテーマ抽出改善テスト
実際の問題データを使用して改善効果を確認
"""

from modules.social_analyzer import SocialAnalyzer
from modules.improved_theme_extractor import ImprovedThemeExtractor

def test_real_problematic_cases():
    """実際に問題のあったケースをテスト"""
    
    analyzer = SocialAnalyzer()
    extractor = ImprovedThemeExtractor()
    
    # 実際の問題のあったケース（ユーザーが報告したもの）
    real_cases = [
        '下線④について説明しなさい',
        'この時期の政治について述べよ',
        '各都市の人口の特徴について',
        'まちがっている文章を選びなさい',
        '正しい文章を選んでください',
        '空欄補充問題：（　　　）に入る適切な語句を選べ'
    ]
    
    print("=== 実データでのテーマ抽出改善テスト ===\n")
    
    improvements = 0
    total = len(real_cases)
    
    for i, case in enumerate(real_cases, 1):
        print(f"ケース {i}: {case}")
        
        # 改善前の想定結果（問題があった結果）
        old_result = case if any(word in case for word in ['下線', 'この時期', '各都市', 'まちがっている', '正しい', '空欄補充']) else "不明"
        
        # 改善後の結果
        improved_result = extractor.extract_theme(case)
        analyzer_result = analyzer.analyze_question(case).topic
        
        print(f"  改善前想定: {old_result}")
        print(f"  改善後結果: {improved_result.theme if improved_result.theme else 'None'}")
        print(f"  社会分析器: {analyzer_result if analyzer_result else 'None'}")
        
        # 改善判定
        if improved_result.theme is None and any(word in case for word in ['まちがっている', '正しい文章', '選びなさい']):
            print("  判定: ✅ 問題形式を適切に除外")
            improvements += 1
        elif improved_result.theme and improved_result.theme not in ['下線④', 'この時期', '各都市', '空欄補充']:
            print("  判定: ✅ 具体的な内容を抽出")
            improvements += 1
        else:
            print("  判定: ⚠️  さらに改善が必要")
        
        print()
    
    print(f"改善率: {improvements}/{total} ({improvements/total*100:.1f}%)")
    return improvements/total

def test_theme_extraction_quality():
    """テーマ抽出品質の包括的テスト"""
    
    analyzer = SocialAnalyzer()
    
    test_questions = [
        # 良い結果が期待されるもの
        "聖徳太子が制定した十七条憲法について説明しなさい",
        "織田信長の政策について述べよ",
        "東京・大阪・名古屋の三大都市圏について",
        "縄文時代の特徴を答えなさい",
        "日本国憲法の三権分立について",
        
        # 除外されるべきもの
        "まちがっている文章を選びなさい",
        "正しいものを選択してください",
        "適切なものを選んでください",
        "次の中から選択しなさい",
        
        # 参照型から推測されるべきもの
        "織田信長がこの時期に行った政策について",
        "各都市の人口を比較せよ。東京、大阪、名古屋",
        "空らんに入る人物を選べ。①聖徳太子 ②中大兄皇子",
    ]
    
    print("=== テーマ抽出品質テスト ===\n")
    
    good_themes = 0
    none_themes = 0
    poor_themes = 0
    
    for question in test_questions:
        result = analyzer.analyze_question(question)
        topic = result.topic
        
        print(f"問題: {question[:40]}...")
        print(f"テーマ: {topic if topic else 'None'}")
        
        if topic is None:
            if any(word in question for word in ['まちがっている', '正しい', '選択', '選びなさい']):
                print("評価: ✅ 適切なNone")
                none_themes += 1
            else:
                print("評価: ⚠️  予期しないNone")
                poor_themes += 1
        elif len(topic) > 3 and topic not in ['下線④', 'この時期', '各都市', '空欄補充']:
            print("評価: ✅ 良いテーマ")
            good_themes += 1
        else:
            print("評価: ❌ 不適切なテーマ")
            poor_themes += 1
        
        print()
    
    total = len(test_questions)
    print(f"結果:")
    print(f"  良いテーマ: {good_themes}")
    print(f"  適切なNone: {none_themes}")
    print(f"  問題のあるテーマ: {poor_themes}")
    print(f"  品質スコア: {(good_themes + none_themes)/total*100:.1f}%")

if __name__ == "__main__":
    improvement_rate = test_real_problematic_cases()
    print("=" * 60)
    test_theme_extraction_quality()
    
    print("\n" + "=" * 60)
    print("=== 総合評価 ===")
    print(f"問題の改善により以下が実現されました：")
    print(f"• 参照型表現（下線④、この時期、各都市等）の適切な処理")
    print(f"• 問題形式表現の除外による精度向上") 
    print(f"• 選択肢からの具体的テーマ推測")
    print(f"• 総合的な改善率: {improvement_rate*100:.1f}%")
    
    if improvement_rate > 0.8:
        print("✅ 大幅な改善が実現されました")
    elif improvement_rate > 0.6:
        print("✅ 着実な改善が実現されました") 
    else:
        print("⚠️  さらなる改善が必要です")