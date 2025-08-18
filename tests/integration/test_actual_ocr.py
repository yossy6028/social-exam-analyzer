#!/usr/bin/env python3
"""
実際のOCRテキストで問題抽出器をテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.improved_question_extractor import ImprovedQuestionExtractor
from modules.theme_extractor_v2 import ThemeExtractorV2

def test_actual_ocr():
    """実際のOCRテキストでテスト"""
    
    print("=== 実際のOCRテキストでの問題抽出テスト ===\n")
    
    # 実際のOCRテキスト（一部）
    ocr_text = """
令和5年度第1回入試社会
(問題用紙)
注意
1. 指示があるまで、開けてはいけません。
2.問題は、1~4まであります。
3. 声を出して読んではいけません。
4.受験番号と氏名を解答用紙に必ず記入してください。
5. 答えはすべて解答用紙に記入してください。
日本工業大学駒場中学校
1 次の各問いに答えなさい。

問1 次の文章が説明している平野を、地図中ア~エから1つ選び記号で答えなさい。 また、その名称を漢字で答えなさい。
そくせい南北約60kmにわたる範囲に広がるこの平野には、県内を流れるいくつかの河川が流れ込んでいる。
近くを流れる暖流の影響で年間を通じて温暖であり、その気候を生かした促成栽培により、きゅうり・なす・ピーマンなどの夏野菜を春から初夏にかけて出荷している。

問2 次の雨温図は、地図中に示したA~Cの都市のいずれかのものです。このうちAの都市の雨温図ふに触れながら説明しなさい。
を、次のア~ウから1つ選び記号で答えなさい。また、その雨温図を選んだ理由を気温と降水量イ.

問3 次の表は、それぞれ藤、肉用若鶏の都道府県別頭数(2021年)の上位5道県を示しています。このうち、(x)に共通して入る県を、地図中 1 ~ 4から1つ選びなさい。

2 次の年表を見て、各問いに答えなさい。

問1 下線部◎に関して、この時代の発掘物である銅鐸に刻まれた次の絵で描かれていると考えられている、農作物をたくわえるための倉庫の名前を答えなさい。

問2 下線部6に関する次のア~エのできごとを年代順に並び替え、 解答らんに合うように答えなさい。
ア.百済から仏像や経典が送られるイ. 平等院鳳凰堂が建てられるウ. 東大寺に大仏がつくられるエ.空海が真言宗を伝える

問3 下線部©は日宋貿易をさかんに行いましたが、 その輸入品として最も適切なものを次のア~エから1つ選び記号で答えなさい。
ア. 金ウ. 刀剣イ.銅銭とうけんエ. 茶

3 次の表は、世界の地域別の人口と面積を示したものです。 この表から読み取れることとしてあやまっているものを、下のア~エから1つ選び記号で答えなさい。

問1 下線部の日本語の名称を次のア~エから1つ選び記号で答えなさい。
ア. 北大西洋条約機構ウ. ワルシャワ条約機構イ. 全欧安全保障協力会議エ. 欧州連合

問2 下線部6により、 日本の社会ではどのような人権が制限を受けることになったのか、 具体的な権利の名称を用いてその事例を説明しなさい。

問3 下線部に関連して 2021年1月22日に核兵器禁止条約が発効されました。 この条約は批准国に対し、核兵器の開発や保有、 核兵器を用いた脅しなどを禁止する内容を定めています。
"""
    
    print("OCRテキストの構造分析:")
    print("="*50)
    
    # 問題抽出器でテスト
    extractor = ImprovedQuestionExtractor()
    questions = extractor.extract_questions(ocr_text)
    
    print(f"抽出された問題数: {len(questions)}")
    print("\n各問題の詳細:")
    
    for i, (q_id, q_text) in enumerate(questions, 1):
        print(f"\n{i}. {q_id}")
        print(f"   テキスト: {q_text[:100]}...")
    
    # 大問構造の分析
    print("\n" + "="*50)
    print("大問構造の分析:")
    
    major_sections = {}
    for q_id, _ in questions:
        major_part = q_id.split('-')[0]
        major_sections[major_part] = major_sections.get(major_part, 0) + 1
    
    for major, count in major_sections.items():
        print(f"{major}: {count}問")
    
    print(f"\n総大問数: {len(major_sections)}")
    print(f"総問題数: {len(questions)}")
    
    # 期待値との比較
    expected_majors = 3
    expected_questions = 8  # 大問1: 3問, 大問2: 3問, 大問3: 2問
    
    print(f"\n期待値との比較:")
    print(f"大問数: {len(major_sections)}/{expected_majors} ({'✅' if len(major_sections) == expected_majors else '❌'})")
    print(f"問題数: {len(questions)}/{expected_questions} ({'✅' if len(questions) == expected_questions else '❌'})")
    
    # テーマ抽出のテスト
    print("\n" + "="*50)
    print("テーマ抽出のテスト:")
    
    theme_extractor = ThemeExtractorV2()
    
    # 重要な問題のテーマ抽出
    important_questions = [
        "促成栽培について説明しなさい。",
        "日宋貿易について説明しなさい。",
        "核兵器禁止条約について説明しなさい。",
    ]
    
    for i, question in enumerate(important_questions, 1):
        print(f"\nテスト {i}: {question}")
        result = theme_extractor.extract(question)
        print(f"  テーマ: {result.theme}")
        print(f"  カテゴリ: {result.category}")
        print(f"  信頼度: {result.confidence}")

if __name__ == "__main__":
    test_actual_ocr()
