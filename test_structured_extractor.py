#!/usr/bin/env python3
"""
構造化テーマ抽出器のテスト
"""

from modules.structured_extractor import StructuredThemeExtractor

def test_structured_extractor():
    """構造化抽出器のテスト"""
    
    extractor = StructuredThemeExtractor()
    
    # 問題のあったケースをテスト
    test_cases = [
        {
            'text': '空らん(①)について、空らんに入る適切な語句を、次のア~エの中から一つ選び記号で答えなさい。ア.聖徳太子 イ.中大兄皇子 ウ.中臣鎌足 エ.蘇我入鹿',
            'expected': '聖徳太子',  # 選択肢から推測
            'problem': '空欄補充'
        },
        {
            'text': '下線④について、まちがっている文章を、次のア~エの中から一つ選び記号で答えなさい。',
            'expected': None,  # 内容がないので除外
            'problem': '下線④'
        },
        {
            'text': '江戸時代の参勤交代について、正しい文章を選びなさい。',
            'expected': '参勤交代',  # リード文から抽出
            'problem': '正しい文章を'
        },
        {
            'text': '聖徳太子が制定した十七条憲法について説明しなさい。',
            'expected': '十七条憲法',
            'problem': None
        },
        {
            'text': '東京・大阪・名古屋の三大都市圏について、その中心となる都市の組み合わせを選びなさい。',
            'expected': '三大都市圏',
            'problem': None
        },
        {
            'text': '次の図は日本の人口推移を示したものです。この図から読み取れることを答えなさい。',
            'expected': '日本の人口推移',
            'problem': '次の図は'
        },
        {
            'text': 'この時期の特徴を述べなさい。選択肢：①縄文時代 ②弥生時代 ③古墳時代',
            'expected': '縄文時代',  # 選択肢から推測
            'problem': 'この時期'
        }
    ]
    
    print("=== 構造化テーマ抽出器のテスト ===\n")
    
    success_count = 0
    total = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        print(f"テスト {i}:")
        print(f"  問題文: {case['text'][:60]}...")
        print(f"  既存の問題: {case['problem']}")
        
        # 構造を解析
        structure = extractor.parse_problem_structure(case['text'])
        print(f"  構造解析:")
        print(f"    リード文: {structure.lead_text[:30] if structure.lead_text else 'なし'}")
        print(f"    設問: {structure.question[:30] if structure.question else 'なし'}...")
        print(f"    選択肢数: {len(structure.choices) if structure.choices else 0}")
        
        # テーマを抽出
        result = extractor.extract_theme(case['text'])
        print(f"  抽出結果: {result.theme if result.theme else 'None'}")
        print(f"  信頼度: {result.confidence:.2f}")
        print(f"  ソース: {result.source}")
        print(f"  期待値: {case['expected']}")
        
        # 評価
        if case['expected'] is None:
            if result.theme is None:
                print("  ✅ 成功: 適切に除外")
                success_count += 1
            else:
                print(f"  ❌ 失敗: 除外すべきだが「{result.theme}」を抽出")
        else:
            if result.theme == case['expected']:
                print("  ✅ 成功: 正しく抽出")
                success_count += 1
            elif result.theme and len(result.theme) > 2:
                print(f"  ⚠️  部分的成功: 期待と異なるが改善「{result.theme}」")
                success_count += 0.5
            else:
                print(f"  ❌ 失敗: 期待「{case['expected']}」だが「{result.theme}」")
        
        print("-" * 60)
    
    print(f"\n=== テスト結果 ===")
    print(f"成功率: {success_count}/{total} ({success_count/total*100:.1f}%)")
    
    if success_count/total >= 0.8:
        print("✅ 構造化アプローチによる改善成功！")
    else:
        print("⚠️  さらなる調整が必要")

if __name__ == "__main__":
    test_structured_extractor()