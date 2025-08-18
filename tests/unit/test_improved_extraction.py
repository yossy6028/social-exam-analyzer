#!/usr/bin/env python3
"""
改善されたテーマ抽出機能のテスト
"""

import sys
from pathlib import Path

# モジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from modules.improved_theme_extractor import ImprovedThemeExtractor


def test_theme_extraction():
    """テーマ抽出のテスト"""
    extractor = ImprovedThemeExtractor()
    
    # テストケース
    test_cases = [
        {
            'name': '縄文時代のテスト',
            'text': '問1 下線部①について、竪穴式住居で土器を使い、土偶を作って生活していた時代を答えなさい。',
            'choices': ['ア 縄文時代', 'イ 弥生時代', 'ウ 古墳時代', 'エ 飛鳥時代'],
            'expected': '縄文時代'
        },
        {
            'name': '青森県のテスト',
            'text': '問2 空欄に当てはまる都道府県を答えなさい。りんごの生産量が日本一で、ねぶた祭りが有名な（　　）県。',
            'choices': ['ア 青森', 'イ 長野', 'ウ 山形', 'エ 秋田'],
            'expected': '青森'
        },
        {
            'name': '選挙制度のテスト',
            'text': '問3 参議院議員選挙において、比例代表制で投票する際の方法について正しいものを選びなさい。',
            'choices': [
                'ア 候補者名を書く',
                'イ 政党名を書く', 
                'ウ 候補者名か政党名を書く',
                'エ 記号で選ぶ'
            ],
            'expected': '選挙制度'
        },
        {
            'name': '明治維新のテスト',
            'text': '問4 下線部について、1868年に大政奉還が行われ、王政復古の大号令により始まった改革を何というか。',
            'choices': [],
            'expected': '明治維新'
        },
        {
            'name': '関東地方のテスト',
            'text': '問5 東京、神奈川、千葉、埼玉、茨城、栃木、群馬の7都県からなる地方を何というか。',
            'choices': [],
            'expected': '関東地方'
        },
        {
            'name': '三権分立のテスト',
            'text': '問6 国会、内閣、裁判所がそれぞれ立法、行政、司法の権限を持ち、互いにチェックし合う仕組みを何というか。',
            'choices': [],
            'expected': '三権分立'
        },
        {
            'name': '江戸時代のテスト（参勤交代）',
            'text': '問7 空欄を埋めなさい。江戸時代に大名が1年ごとに江戸と領地を往復する制度を（　　）という。',
            'choices': ['参勤交代', '鎖国', '天領', '幕藩体制'],
            'expected': '江戸時代'
        },
        {
            'name': '環境問題のテスト',
            'text': '問8 地球温暖化の原因となる温室効果ガスのうち、最も割合が高いCO2の削減について、京都議定書やパリ協定で定められた目標について述べなさい。',
            'choices': [],
            'expected': '環境問題'
        }
    ]
    
    print("=" * 70)
    print("改善されたテーマ抽出機能のテスト")
    print("=" * 70)
    print()
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"テスト {i}: {test_case['name']}")
        print(f"問題文: {test_case['text'][:50]}...")
        
        # テーマ抽出実行
        if test_case['choices']:
            result = extractor.extract_theme_with_choices(
                test_case['text'], 
                test_case['choices']
            )
        else:
            result = extractor.extract_theme(test_case['text'])
        
        print(f"抽出結果: {result.theme} (信頼度: {result.confidence:.2f}, カテゴリー: {result.category})")
        print(f"期待値: {test_case['expected']}")
        
        # 結果判定
        if result.theme == test_case['expected']:
            print("✅ 成功")
            success_count += 1
        elif result.theme and test_case['expected'] in result.theme:
            print("⚠️  部分一致")
            success_count += 0.5
        else:
            print("❌ 失敗")
        
        print("-" * 50)
    
    print()
    print(f"テスト結果: {success_count}/{len(test_cases)} 成功")
    print("=" * 70)


def test_with_real_problem():
    """実際の問題でのテスト"""
    extractor = ImprovedThemeExtractor()
    
    # 実際の問題例（複雑なケース）
    problem = """
    問題 次の文章を読んで、下の問いに答えなさい。
    
    日本列島には約1万5千年前から人が住み始め、（ア）土器を作り、
    竪穴式住居に住んで、狩猟・採集生活を送っていました。
    この時代の人々は、豊かな自然の恵みを受けながら、
    土偶などの呪術的な道具も作っていました。
    
    問1 文中の（ア）に入る土器の名前を答えなさい。
    
    選択肢:
    ア 縄文土器
    イ 弥生土器
    ウ 須恵器
    エ 土師器
    """
    
    print("\n実際の問題でのテスト:")
    print("=" * 70)
    print("問題文:")
    print(problem[:200] + "...")
    print()
    
    # 選択肢を抽出（簡易的に）
    choices = ['縄文土器', '弥生土器', '須恵器', '土師器']
    
    result = extractor.extract_theme_with_choices(problem, choices)
    
    print(f"抽出されたテーマ: {result.theme}")
    print(f"信頼度: {result.confidence:.2f}")
    print(f"カテゴリー: {result.category}")
    print()
    
    # キーワード分析を表示
    keywords = extractor._extract_keywords(problem)
    print("抽出されたキーワード:")
    for kw in keywords[:10]:  # 上位10個
        print(f"  - {kw}")


if __name__ == "__main__":
    test_theme_extraction()
    test_with_real_problem()