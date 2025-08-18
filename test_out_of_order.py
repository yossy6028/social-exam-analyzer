#!/usr/bin/env python3
"""
順序が乱れた問題配置をテスト
実際のOCRで起こりうる問題を再現
"""

import sys
sys.path.insert(0, '/Users/yoshiikatsuhiko/Desktop/02_開発 (Development)/social_exam_analyzer')

from patterns.hierarchical_extractor_fixed import HierarchicalExtractorFixed

# OCRで問題の順序が乱れた場合のテキスト
# 大問1の問9-11が大問2の後に現れるケース
disordered_text = """
社会

1 次の文章を読んで、以下の問いに答えなさい。

問1 日本の地形について説明しなさい。
問2 雨温図から都市を特定しなさい。
問3 農業について述べなさい。
問4 工業地帯の特徴を述べなさい。
問5 貿易について説明しなさい。
問6 地形図を読み取りなさい。
問7 農業の発展について述べなさい。
問8 環境問題について説明しなさい。

2 次の歴史に関する文章を読んで答えなさい。

問9 資源について述べなさい。
問10 交通について説明しなさい。
問11 都市問題について述べなさい。

問1 奈良時代について説明しなさい。
問2 平安時代の特徴を述べなさい。
問3 鎌倉時代の政治について説明しなさい。
問4 室町時代の文化について述べなさい。
問5 戦国時代の武将について説明しなさい。
問6 江戸時代の社会について述べなさい。
問7 明治維新について説明しなさい。
問8 大正デモクラシーについて述べなさい。
問9 昭和時代の戦争について説明しなさい。
問10 戦後の復興について述べなさい。
問11 高度経済成長について説明しなさい。
問12 現代の課題について述べなさい。
問13 国際関係について説明しなさい。

3 次の公民に関する文章を読んで答えなさい。

問1 日本国憲法について説明しなさい。
問2 基本的人権について述べなさい。
問3 国会の仕組みについて説明しなさい。
問4 内閣の役割について述べなさい。
問5 裁判所の機能について説明しなさい。
問6 地方自治について述べなさい。
問7 選挙制度について説明しなさい。
問8 政党について述べなさい。
問9 経済の仕組みについて説明しなさい。
問10 企業の役割について述べなさい。
問11 国際機関について説明しなさい。
問12 国際協力について述べなさい。
問13 環境問題について説明しなさい。

4 次の資料を見て答えなさい。

問1 グラフから読み取れることを述べなさい。
問2 地図から分かることを説明しなさい。
問3 年表から重要な出来事を挙げなさい。
問4 写真から読み取れることを述べなさい。
問5 統計データを分析しなさい。
"""

def test_disordered():
    """順序が乱れた場合のテスト"""
    extractor = HierarchicalExtractorFixed()
    structure = extractor.extract_structure(disordered_text)
    
    print("=" * 60)
    print("順序が乱れたテキストの階層構造抽出結果")
    print("=" * 60)
    print("\n【問題】大問1の問9-11が大問2の後に配置されている")
    
    total_questions = 0
    for major in structure:
        major_q_count = len(major.children)
        total_questions += major_q_count
        print(f"\n大問{major.number}: {major_q_count}問検出")
        
        # 問題番号を全て表示
        if major.children:
            q_numbers = [q.number for q in major.children]
            print(f"  問番号: {', '.join(q_numbers)}")
            
            # 重複や異常をチェック
            if len(q_numbers) != len(set(q_numbers)):
                print(f"  ⚠️ 重複あり！")
            
            # 期待される番号との差異をチェック
            if major.number == '1':
                expected = 11  # 本来は11問あるはず
                print(f"  期待: {expected}問、実際: {major_q_count}問")
                if major_q_count < expected:
                    print(f"  ⚠️ {expected - major_q_count}問不足")
            elif major.number == '2':
                expected = 13
                print(f"  期待: {expected}問、実際: {major_q_count}問")
                if major_q_count > expected:
                    print(f"  ⚠️ {major_q_count - expected}問過多")
    
    print(f"\n総問題数: {total_questions}")
    print("\n【診断結果】")
    print("大問1の問9-11が大問2セクションに配置されているため、")
    print("これらの問題が大問2に誤って割り当てられています。")
    
    return structure

if __name__ == "__main__":
    test_disordered()