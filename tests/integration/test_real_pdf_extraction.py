#\!/usr/bin/env python3
"""
実際のPDFデータでテーマ抽出をテスト
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.social_analyzer_fixed import FixedSocialAnalyzer
import logging

# デバッグログを有効化
logging.basicConfig(level=logging.DEBUG)

def test_real_extraction():
    """実際のデータでテスト"""
    
    # 実際にPDFから抽出されるようなテキストサンプル
    sample_text = """
    大問1
    問1 次の地図中のAの都市について答えなさい。
    問2 江戸時代の産業について説明しなさい。
    問3 明治維新後の変化について述べなさい。
    
    大問2
    問1 兵庫県の特徴について答えなさい。
    問2 日本国憲法の三原則を説明しなさい。
    問3 国連の役割について述べなさい。
    問4 阪神・淡路大震災の被害について説明しなさい。
    問5 核兵器禁止条約について答えなさい。
    """
    
    analyzer = FixedSocialAnalyzer()
    
    print("=== 実際のPDFテキストでのテスト ===\n")
    
    # 文書全体を分析
    result = analyzer.analyze_document(sample_text)
    
    print(f"検出された問題数: {result['total_questions']}")
    print("\n【出題テーマ一覧】")
    print("-" * 40)
    
    theme_count = 0
    for question in result['questions']:
        if question.theme:
            print(f"  {question.number}: {question.theme}")
            theme_count += 1
        else:
            print(f"  {question.number}: （テーマ情報なし）")
    
    print(f"\nテーマ抽出率: {theme_count}/{result['total_questions']} ({theme_count*100/result['total_questions']:.1f}%)")
    
    # 個別にテスト
    print("\n=== 個別テスト ===")
    test_texts = [
        "兵庫県の特徴について答えなさい。",
        "日本国憲法の三原則を説明しなさい。",
        "阪神・淡路大震災の被害について説明しなさい。",
        "核兵器禁止条約について答えなさい。",
        "国連の役割について述べなさい。",
    ]
    
    for text in test_texts:
        question = analyzer.analyze_question(text)
        if question.theme:
            print(f"✅ {text[:30]}... → {question.theme}")
        else:
            print(f"❌ {text[:30]}... → テーマなし")

if __name__ == "__main__":
    test_real_extraction()
