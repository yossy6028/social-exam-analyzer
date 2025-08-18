#!/usr/bin/env python3
"""
OCRテキストの問題抽出デバッグ
"""

import re

def debug_ocr_extraction():
    """OCRテキストの問題抽出をデバッグ"""
    
    print("=== OCRテキストの問題抽出デバッグ ===\n")
    
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
    
    print("OCRテキストの行ごとの分析:")
    print("="*50)
    
    lines = ocr_text.split('\n')
    for i, line in enumerate(lines):
        if line.strip():
            print(f"{i:3d}: {line}")
    
    print("\n" + "="*50)
    print("大問パターンのテスト:")
    
    # 大問パターンのテスト
    major_patterns = [
        re.compile(r'^(\d+)\s*次の各問いに答えなさい。', re.MULTILINE),
        re.compile(r'^(\d+)\s*次の年表を見て', re.MULTILINE),
        re.compile(r'^(\d+)\s*次の表は', re.MULTILINE),
        re.compile(r'^(\d+)\s*次の図は', re.MULTILINE),
        re.compile(r'^(\d+)\s*(?:次の|下記の|以下の)', re.MULTILINE),
        re.compile(r'^(\d+)\s*$', re.MULTILINE),
    ]
    
    for i, pattern in enumerate(major_patterns, 1):
        matches = list(pattern.finditer(ocr_text))
        print(f"パターン {i}: {pattern.pattern}")
        for match in matches:
            print(f"  マッチ: '{match.group(0)}' (行 {match.start()})")
    
    print("\n" + "="*50)
    print("小問パターンのテスト:")
    
    # 小問パターンのテスト
    minor_patterns = [
        re.compile(r'問\s*(\d+)\s*(.+?)(?=問\s*\d+|$)', re.DOTALL),
        re.compile(r'問\s*(\d+)(.+?)(?=問\s*\d+|$)', re.DOTALL),
    ]
    
    for i, pattern in enumerate(minor_patterns, 1):
        matches = list(pattern.finditer(ocr_text))
        print(f"パターン {i}: {pattern.pattern}")
        for match in matches:
            print(f"  マッチ: 問{match.group(1)} - {match.group(2)[:50]}...")
    
    print("\n" + "="*50)
    print("手動での問題構造分析:")
    
    # 手動での問題構造分析
    major_sections = []
    current_major = None
    current_questions = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 大問の開始を検出
        major_match = re.match(r'^(\d+)\s*(?:次の|下記の|以下の)', line)
        if major_match:
            if current_major:
                major_sections.append((current_major, current_questions))
            current_major = major_match.group(1)
            current_questions = []
            print(f"大問{current_major}開始: {line}")
        
        # 小問を検出
        question_match = re.match(r'問\s*(\d+)', line)
        if question_match and current_major:
            question_num = question_match.group(1)
            current_questions.append(question_num)
            print(f"  小問{question_num}: {line[:50]}...")
    
    # 最後の大問を追加
    if current_major:
        major_sections.append((current_major, current_questions))
    
    print(f"\n検出された大問構造:")
    for major, questions in major_sections:
        print(f"大問{major}: {len(questions)}問 - {questions}")

if __name__ == "__main__":
    debug_ocr_extraction()
