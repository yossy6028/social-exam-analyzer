#!/usr/bin/env python3
"""
テーマ抽出問題の修正スクリプト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def analyze_theme_issue():
    """テーマが適切に抽出されない問題を分析"""
    
    from modules.social_analyzer import SocialAnalyzer
    from modules.theme_extractor_v2 import ThemeExtractorV2
    
    # テスト問題
    test_questions = [
        "問1 高知県のビニールハウスで冬に野菜を栽培する農業を何といいますか。",
        "問2 内閣総理大臣になるための資格は何ですか。",
        "問3 弥生時代に稲を保存するために使われた建物を何といいますか。",
        "問4 織田信長が行った経済政策の名称を答えなさい。",
        "問5 日本国憲法の三原則を答えなさい。",
        "問6 SDGsの目標について説明しなさい。"
    ]
    
    print("=== テーマ抽出のデバッグ ===\n")
    
    # ThemeExtractorV2の動作確認
    print("1. ThemeExtractorV2の動作:")
    extractor = ThemeExtractorV2()
    
    for q in test_questions[:3]:
        result = extractor.extract(q)
        print(f"  Q: {q[:50]}...")
        print(f"    theme: {result.theme}")
        print(f"    category: {result.category}")
        print(f"    confidence: {result.confidence}")
        print()
    
    # SocialAnalyzerの動作確認
    print("\n2. SocialAnalyzerの動作:")
    analyzer = SocialAnalyzer()
    
    for i, q in enumerate(test_questions, 1):
        analyzed = analyzer.analyze_question(q, f"問{i}")
        
        print(f"  Q: {q[:50]}...")
        print(f"    field: {analyzed.field.value}")
        print(f"    theme: {analyzed.theme}")
        
        # themeがNoneまたは不適切な場合の詳細確認
        if not analyzed.theme or "/" in str(analyzed.theme):
            print(f"    ⚠️ テーマが適切に抽出されていません")
            
            # _extract_topicを直接呼び出してデバッグ
            extracted = analyzer._extract_topic(q)
            print(f"    _extract_topic結果: {extracted}")
        print()

def check_question_formats():
    """実際のGUI表示で使用される形式を確認"""
    
    print("\n=== 表示形式の確認 ===\n")
    
    from modules.social_analyzer import SocialQuestion, SocialField
    
    # サンプル問題を作成
    questions = [
        SocialQuestion(
            number="問1",
            text="促成栽培について",
            field=SocialField.GEOGRAPHY,
            theme="促成栽培"
        ),
        SocialQuestion(
            number="問2",
            text="内閣総理大臣について",
            field=SocialField.CIVICS,
            theme=None  # themeがNoneの場合
        ),
        SocialQuestion(
            number="問3",
            text="弥生時代について",
            field=SocialField.HISTORY,
            theme=""  # themeが空文字の場合
        )
    ]
    
    # 表示形式を確認
    for q in questions:
        # GUIでの表示をシミュレート
        field_str = q.field.value if hasattr(q.field, 'value') else str(q.field)
        theme_str = q.theme if q.theme else "（テーマなし）"
        
        print(f"  {q.number}: {theme_str} [{field_str}]")
        
        # 実際の値を確認
        print(f"    実際のtheme値: {repr(q.theme)}")
        print(f"    bool(theme): {bool(q.theme)}")
        print()

def fix_theme_extraction():
    """テーマ抽出を改善する修正案"""
    
    print("\n=== 修正案 ===\n")
    
    print("1. _extract_topicメソッドのフォールバック処理を改善")
    print("   - Noneを返す代わりに、問題文から重要キーワードを抽出")
    print("   - 最低限、分野に応じた汎用テーマを設定")
    print()
    
    print("2. ThemeExtractorV2の_should_excludeメソッドを調整")
    print("   - 除外条件を緩和して、より多くの問題でテーマを抽出")
    print()
    
    print("3. GUI表示部分で、分野とテーマの表示を改善")
    print("   - テーマがない場合は分野情報を活用")
    print("   - 「地理/歴史/公民/時事問題」のような汎用表示を避ける")

if __name__ == "__main__":
    analyze_theme_issue()
    check_question_formats()
    fix_theme_extraction()