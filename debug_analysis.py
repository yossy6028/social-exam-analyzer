#!/usr/bin/env python3
"""
分析結果のデバッグスクリプト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.social_analyzer import SocialAnalyzer
from modules.hierarchical_question_manager import HierarchicalQuestionManager

def debug_analysis():
    """分析処理をデバッグ"""
    
    # サンプルテキスト（実際の問題に近い形式）
    test_text = """
第1問
問1 日本の農業について、次の（1）～（3）に答えなさい。
（1）高知県のビニールハウスで冬に野菜を栽培する農業を何といいますか。
（2）都市の近くで新鮮な野菜を栽培する農業を何といいますか。

問2 次の憲法に関する問題に答えなさい。
（1）内閣総理大臣になるための資格は何ですか。

第2問
問1 弥生時代について答えなさい。
（1）稲を保存するために使われた建物を何といいますか。
（2）祭りで使われた青銅器を何といいますか。

問2 仏教について答えなさい。
（1）仏教を日本に伝えた国はどこですか。
    """
    
    print("=== デバッグ開始 ===\n")
    
    # 階層的問題抽出
    print("1. 階層的問題抽出")
    hierarchy_manager = HierarchicalQuestionManager()
    hierarchical_questions = hierarchy_manager.extract_hierarchical_questions(test_text)
    flattened_questions = hierarchy_manager.get_flattened_questions()
    
    print(f"  抽出された問題数: {len(flattened_questions)}")
    for q in flattened_questions[:5]:
        print(f"    {q.get('number', 'N/A')}: {q.get('text', '')[:50]}...")
    
    # 分析実行
    print("\n2. 問題分析")
    analyzer = SocialAnalyzer()
    
    # 通常の分析
    result = analyzer.analyze_document(test_text)
    
    if 'questions' in result:
        print(f"  分析された問題数: {len(result['questions'])}")
        for q in result['questions'][:10]:
            # テーマとフィールドの確認
            theme = getattr(q, 'theme', 'なし')
            field = getattr(q, 'field', 'なし')
            if hasattr(field, 'value'):
                field = field.value
            number = getattr(q, 'number', 'N/A')
            
            print(f"    {number}: テーマ={theme}, 分野={field}")
            
            # テーマが「地理/歴史/公民/時事問題」になっている原因を調査
            if theme == "地理/歴史/公民/時事問題":
                text = getattr(q, 'text', '')
                print(f"      問題文: {text[:100]}...")
                print(f"      ⚠️ デフォルトテーマが使用されています")
    
    # テーマ抽出の詳細確認
    print("\n3. テーマ抽出の詳細")
    from modules.theme_extractor_v2 import ThemeExtractorV2
    extractor = ThemeExtractorV2()
    
    sample_texts = [
        "高知県のビニールハウスで冬に野菜を栽培する農業を何といいますか。",
        "内閣総理大臣になるための資格は何ですか。",
        "弥生時代の稲を保存するための建物を何といいますか。"
    ]
    
    for text in sample_texts:
        theme = extractor.extract_theme(text)
        print(f"  テキスト: {text[:50]}...")
        if hasattr(theme, 'main_theme'):
            print(f"    抽出テーマ: {theme.main_theme}")
        else:
            print(f"    抽出テーマ: {theme}")

def check_default_values():
    """デフォルト値の確認"""
    print("\n=== デフォルト値の確認 ===")
    
    from modules.social_analyzer import SocialQuestion, SocialField
    
    # デフォルトの問題を作成
    q = SocialQuestion(
        number="テスト",
        text="テスト問題"
    )
    
    print(f"デフォルトfield: {q.field} ({q.field.value})")
    print(f"デフォルトtheme: {q.theme}")
    print(f"デフォルトtopic: {q.topic}")
    
    # analyze_questionメソッドの動作確認
    analyzer = SocialAnalyzer()
    analyzed = analyzer.analyze_question("江戸時代の農業について説明しなさい。", "問1")
    
    print(f"\n分析後:")
    print(f"  field: {analyzed.field.value}")
    print(f"  theme: {analyzed.theme}")
    print(f"  keywords: {analyzed.keywords}")

if __name__ == "__main__":
    debug_analysis()
    check_default_values()