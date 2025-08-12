#!/usr/bin/env python3
"""
既存のテキストファイルから問題文を読み取り、改善版でテーマを再抽出
"""

from modules.social_analyzer import SocialAnalyzer
from modules.improved_theme_extractor import ImprovedThemeExtractor

def test_problematic_themes():
    """問題のあったテーマを改善版で再テスト"""
    
    # 実際のテキストファイルから問題文を抽出
    with open("/Users/yoshiikatsuhiko/Desktop/過去問_社会/東京電機大学中学校_2020_社会.txt", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 問題文を抽出（簡易版）
    test_cases = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if line.startswith('◆ 問'):
            # 問題文セクションを探す
            problem_text = ""
            for j in range(i+1, min(i+10, len(lines))):
                if lines[j].startswith('  問題文:'):
                    problem_text = lines[j][9:].strip()
                    # 次の行も取得
                    if j+1 < len(lines) and not lines[j+1].startswith('◆'):
                        problem_text += " " + lines[j+1].strip()
                    break
            
            # 主題を探す
            topic = ""
            for j in range(i+1, min(i+10, len(lines))):
                if lines[j].startswith('  主題:'):
                    topic = lines[j][7:].strip()
                    break
            
            if problem_text and topic:
                test_cases.append({
                    'number': line[2:].strip(),
                    'text': problem_text[:200],  # 最初の200文字
                    'old_topic': topic
                })
    
    # 改善版でテスト
    analyzer = SocialAnalyzer()
    extractor = ImprovedThemeExtractor()
    
    print("=== 問題のあったテーマの改善テスト ===\n")
    
    improvements = 0
    total = 0
    problematic_topics = ['下線④', '空欄補充', 'この時期', '各都市', 'まちがっている文章を', '正しい文章を']
    
    for case in test_cases:
        if case['old_topic'] in problematic_topics:
            total += 1
            print(f"問題: {case['number']}")
            print(f"  テキスト: {case['text'][:80]}...")
            print(f"  既存テーマ: {case['old_topic']}")
            
            # 改善版で再抽出
            result = extractor.extract_theme(case['text'])
            new_topic = result.theme if result.theme else None
            
            # 社会分析器でも確認
            question = analyzer.analyze_question(case['text'])
            analyzer_topic = question.topic if question else None
            
            print(f"  改善版テーマ: {new_topic}")
            print(f"  信頼度: {result.confidence:.2f}")
            
            # 改善判定
            if new_topic is None and case['old_topic'] in ['まちがっている文章を', '正しい文章を']:
                print("  ✅ 適切に除外")
                improvements += 1
            elif new_topic and new_topic not in problematic_topics:
                print("  ✅ 具体的な内容に改善")
                improvements += 1
            else:
                print("  ⚠️  さらなる改善が必要")
            
            print("-" * 60)
    
    print(f"\n改善結果: {improvements}/{total} ({improvements/total*100:.1f}%)")
    
    # 全体のテーマ品質をチェック
    print("\n=== 全体のテーマ品質チェック ===\n")
    
    all_good = 0
    all_bad = 0
    all_none = 0
    
    for case in test_cases:
        result = extractor.extract_theme(case['text'])
        new_topic = result.theme
        
        if new_topic is None:
            all_none += 1
        elif any(bad in str(new_topic) for bad in problematic_topics):
            all_bad += 1
            print(f"❌ まだ問題あり: {case['number']} -> {new_topic}")
        else:
            all_good += 1
    
    total_all = len(test_cases)
    if total_all > 0:
        print(f"\n統計:")
        print(f"  良いテーマ: {all_good}問 ({all_good/total_all*100:.1f}%)")
        print(f"  問題のあるテーマ: {all_bad}問 ({all_bad/total_all*100:.1f}%)")
        print(f"  適切な除外(None): {all_none}問 ({all_none/total_all*100:.1f}%)")
        print(f"  品質スコア: {(all_good + all_none)/total_all*100:.1f}%")

if __name__ == "__main__":
    test_problematic_themes()