#!/usr/bin/env python3
"""
重要語句抽出の問題を調査
"""
import logging
from modules.ocr_handler import OCRHandler
from modules.social_analyzer_fixed import FixedSocialAnalyzer

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

# テスト用のOCRテキスト（大問1-問1相当）
test_text = """
大問1
問1 次の文章が説明している平野を、地図中のア～カから1つ選び、記号で答えなさい。

県内を流れるいくつかの河川によって土砂が堆積してできた平野である。
南北約60kmにわたる範囲に広がるこの平野では、東京に野菜を出荷する
近郊農業が盛んである。また、ビニールハウスなどの施設を利用した
促成栽培も行われており、きゅうりやトマトなどが生産されている。
"""

print("=" * 60)
print("重要語句抽出の調査")
print("=" * 60)
print("\n【入力テキスト】")
print(test_text)
print("\n" + "=" * 60)

# 分析器を初期化
analyzer = FixedSocialAnalyzer()

# OCRテキストを正規化
ocr_handler = OCRHandler()
normalized_text = ocr_handler._normalize_ocr_text(test_text)

print("\n【正規化後のテキスト】")
print(normalized_text)
print("\n" + "=" * 60)

# 実際の分析を実行（1問だけ）
from modules.improved_question_analyzer import ImprovedQuestionAnalyzer

question_analyzer = ImprovedQuestionAnalyzer()

# analyze_questionメソッドがどのように動作するか確認
result = analyzer.analyze_question(normalized_text, "大問1-問1")

print("\n【分析結果】")
print(f"分野: {result.field}")
print(f"テーマ: {result.theme}")
print(f"キーワード: {result.keywords}")
print(f"資料タイプ: {result.resource_types}")

# 重要：どのメソッドが重要語句を抽出しているか
print("\n" + "=" * 60)
print("【問題の本質】")
print("1. OCRテキストには「促成栽培」が含まれている: ", "促成栽培" in normalized_text)
print("2. しかし重要語句として抽出されていない")
print("3. テーマにも反映されていない")
print("\n【原因】")
print("- analyze_questionメソッドが文脈を無視している可能性")
print("- subject_index.mdとの照合が不十分")
print("- キーワード抽出ロジックが弱い")
print("=" * 60)