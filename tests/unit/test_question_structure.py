#!/usr/bin/env python3
"""
大問・小問の構造認識テスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.improved_question_extractor import ImprovedQuestionExtractor

def test_question_structure():
    """大問・小問の構造認識テスト"""
    
    print("=== 大問・小問の構造認識テスト ===\n")
    
    # 日本工業大学附属駒場2023年度の問題構造を想定
    test_text = """
令和5年度 日本工業大学附属駒場中学校 入学試験問題
社会

1. 次の文章を読んで、各設問に答えなさい。

促成栽培は、野菜や果物を通常より早い時期に収穫する農業技術です。ビニールハウスや温室を利用して、温度や湿度を管理し、作物の生育を促進します。

問1. 促成栽培について、適切なものを次のア~エから1つ選び記号で答えなさい。
ア. 作物の生育を遅らせる技術
イ. 作物の生育を促進する技術
ウ. 作物の品質を向上させる技術
エ. 作物の収穫量を増やす技術

問2. 促成栽培で使用される施設として適切なものを次のア~エから1つ選び記号で答えなさい。
ア. 農機具
イ. ビニールハウス
ウ. 肥料
エ. 農薬

2. 次の地図を見て、各設問に答えなさい。

関東地方の農業地域を示した地図です。促成栽培が盛んな地域が色分けされています。

問1. 促成栽培が最も盛んな地域を次のア~エから1つ選び記号で答えなさい。
ア. 千葉県
イ. 埼玉県
ウ. 茨城県
エ. 群馬県

問2. 促成栽培が盛んな理由として適切なものを次のア~エから1つ選び記号で答えなさい。
ア. 気候が温暖
イ. 交通が便利
ウ. 人口が多い
エ. 工業が発達

3. 次の表は、促成栽培による収穫量の変化を示しています。

問1. 表から読み取れることとして正しいものを次のア~エから1つ選び記号で答えなさい。
ア. 収穫量は年々減少している
イ. 収穫量は年々増加している
ウ. 収穫量は変化がない
エ. 収穫量は変動が大きい

問2. 促成栽培の特徴として適切なものを次のア~エから1つ選び記号で答えなさい。
ア. 自然の気候に依存する
イ. 人工的に環境を制御する
ウ. 収穫時期が限られる
エ. 栽培面積が狭い
"""
    
    print("テストテキスト:")
    print(test_text[:200] + "...")
    print("\n" + "="*50 + "\n")
    
    # 問題抽出器でテスト
    extractor = ImprovedQuestionExtractor()
    
    print("問題抽出結果:")
    questions = extractor.extract_questions(test_text)
    
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
    expected_questions = 8
    
    print(f"\n期待値との比較:")
    print(f"大問数: {len(major_sections)}/{expected_majors} ({'✅' if len(major_sections) == expected_majors else '❌'})")
    print(f"問題数: {len(questions)}/{expected_questions} ({'✅' if len(questions) == expected_questions else '❌'})")
    
    # デバッグ: 大問1の説明文抽出を確認
    print("\n" + "="*50)
    print("デバッグ: 大問1の説明文抽出:")
    
    # 大問1のセクションを手動で抽出
    major1_start = test_text.find("1. 次の文章を読んで、各設問に答えなさい。")
    if major1_start >= 0:
        major1_end = test_text.find("2. 次の地図を見て、各設問に答えなさい。")
        if major1_end >= 0:
            major1_section = test_text[major1_start:major1_end]
            print(f"大問1セクション: {major1_section[:200]}...")
            
            # 説明文の位置を確認
            question1_start = major1_section.find("問1")
            if question1_start > 0:
                context = major1_section[:question1_start]
                print(f"説明文: {context}")
                print(f"説明文の長さ: {len(context)}文字")
            else:
                print("問1が見つかりません")
        else:
            print("大問2の開始が見つかりません")
    else:
        print("大問1の開始が見つかりません")

if __name__ == "__main__":
    test_question_structure()
