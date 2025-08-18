#\!/usr/bin/env python3
"""
実際のPDFから抽出されるような形式のテキストでテスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.social_analyzer_fixed import FixedSocialAnalyzer
import logging

# デバッグログを有効化
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_with_pdf_like_text():
    """PDFから抽出される形式のテキストでテスト"""
    
    # 実際のPDFテキスト風（改行やスペース、記号を含む）
    pdf_text = """令和5年度　第1回入試
社会 （問題用紙）

【注意】
1. 指示があるまで開けてはいけません。
2. 問題は10ページまであります。
3. 答えはすべて解答用紙に記入すること。

問題は次のページから始まります。

1．次の文章を読んで、問いに答えなさい。

問１　江戸時代の農業について説明しなさい。

問２　明治維新の改革について答えなさい。

問３　日本国憲法の三原則を説明しなさい。

問４　兵庫県の産業について述べなさい。

問５　阪神・淡路大震災の被害について説明しなさい。

2．次の地図を見て、問いに答えなさい。

問１　地図中のAの都市について答えなさい。

問２　関東地方の特徴について説明しなさい。

問３　SDGsの目標について答えなさい。

問４　地球温暖化の原因について説明しなさい。

問５　核兵器禁止条約について答えなさい。
"""
    
    analyzer = FixedSocialAnalyzer()
    
    print("=== PDFテキスト風データでのテスト ===\n")
    
    # 文書全体を分析
    result = analyzer.analyze_document(pdf_text)
    
    print(f"検出された問題数: {result['total_questions']}")
    print("\n【出題テーマ一覧】")
    print("-" * 40)
    
    theme_count = 0
    for question in result['questions']:
        if question.topic:
            print(f"  {question.number}: {question.topic}")
            theme_count += 1
        else:
            print(f"  {question.number}: （テーマ情報なし）")
    
    print(f"\nテーマ抽出率: {theme_count}/{result['total_questions']} ({theme_count*100/result['total_questions'] if result['total_questions'] > 0 else 0:.1f}%)")

if __name__ == "__main__":
    test_with_pdf_like_text()
