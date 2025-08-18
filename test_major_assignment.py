#!/usr/bin/env python3
"""
大問への問題割り当てを診断するテストスクリプト
"""

import sys
import os
sys.path.insert(0, '/Users/yoshiikatsuhiko/Desktop/02_開発 (Development)/social_exam_analyzer')

from patterns.hierarchical_extractor_fixed import HierarchicalExtractorFixed

# テスト用のサンプルテキスト（実際のPDFに似た構造）
sample_text = """
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
問9 資源について述べなさい。
問10 交通について説明しなさい。
問11 都市問題について述べなさい。

2 次の歴史に関する文章を読んで答えなさい。

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

def test_extraction():
    """階層抽出をテスト"""
    extractor = HierarchicalExtractorFixed()
    structure = extractor.extract_structure(sample_text)
    
    print("=" * 60)
    print("階層構造抽出結果")
    print("=" * 60)
    
    total_questions = 0
    for major in structure:
        major_q_count = len(major.children)
        total_questions += major_q_count
        print(f"\n大問{major.number}: {major_q_count}問")
        print(f"  位置: {major.position[0]}")
        print(f"  マーカータイプ: {major.marker_type}")
        
        # 最初の5問と最後の2問を表示
        if major.children:
            print(f"  問番号:")
            for i, q in enumerate(major.children):
                if i < 5 or i >= len(major.children) - 2:
                    print(f"    問{q.number} (位置: {q.position[0]})")
                elif i == 5:
                    print(f"    ...")
    
    print(f"\n総問題数: {total_questions}")
    
    # 問題の割り当てを確認
    print("\n" + "=" * 60)
    print("問題割り当ての診断")
    print("=" * 60)
    
    # 各大問の範囲を表示
    for i, major in enumerate(structure):
        start = major.position[0]
        end = structure[i + 1].position[0] if i + 1 < len(structure) else len(sample_text)
        print(f"\n大問{major.number}の範囲: {start} - {end}")
        
        # この範囲内の問を確認
        range_text = sample_text[start:end]
        import re
        question_matches = list(re.finditer(r'問(\d+)', range_text))
        print(f"  テキスト内で検出された問: {len(question_matches)}個")
        if question_matches:
            found_numbers = [m.group(1) for m in question_matches[:5]]
            print(f"  最初の5つ: 問{', 問'.join(found_numbers)}")
        
        print(f"  実際に割り当てられた問: {len(major.children)}個")
        if major.children:
            assigned_numbers = [q.number for q in major.children[:5]]
            print(f"  最初の5つ: 問{', 問'.join(assigned_numbers)}")

if __name__ == "__main__":
    test_extraction()