#!/usr/bin/env python3
"""
テーマ表示の改善テスト（大問ごとの区切り）
"""

import sys
from pathlib import Path

# モジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from modules.social_analyzer import SocialAnalyzer, SocialQuestion, SocialField
from modules.improved_theme_extractor import ImprovedThemeExtractor


def create_sample_data():
    """サンプルデータを作成"""
    analyzer = SocialAnalyzer()
    
    # サンプル問題を作成
    sample_text = """
    大問1
    問1 縄文時代の人々が使っていた土器について説明しなさい。
    問2 弥生時代に始まった稲作について述べなさい。
    問3 古墳時代の豪族について説明しなさい。
    
    大問2
    問11 関東地方の都道府県を全て挙げなさい。
    問12 日本アルプスの山脈について説明しなさい。
    問13 瀬戸内海の気候の特徴を述べなさい。
    
    大問3
    問21 日本国憲法の三大原則を説明しなさい。
    問22 三権分立について述べなさい。
    問23 国会の仕組みについて説明しなさい。
    """
    
    # 分析実行
    result = analyzer.analyze_document(sample_text)
    
    return result


def display_themes_grouped(analysis_result):
    """テーマを大問ごとに区切って表示（改善版）"""
    print("\n" + "=" * 70)
    print("【出題テーマ一覧】（大問ごとに区切り表示）")
    print("=" * 70)
    
    questions = analysis_result.get('questions', [])
    
    if questions:
        # 大問ごとにグループ化
        grouped_themes = {}
        for q in questions:
            # 問題番号から大問番号を推定
            if '問' in q.number:
                q_num = q.number.replace('問', '').strip()
                if '-' in q_num or '.' in q_num:
                    # "1-1", "1.1" のような形式
                    major_num = q_num.split('-')[0].split('.')[0]
                else:
                    # 単純な番号の場合、10問ごとに大問として区切る
                    try:
                        num_val = int(q_num)
                        major_num = str((num_val - 1) // 10 + 1)
                    except:
                        major_num = '1'
            else:
                major_num = '1'
            
            if major_num not in grouped_themes:
                grouped_themes[major_num] = []
            
            if q.topic:
                grouped_themes[major_num].append((q.number, q.topic, q.field.value))
        
        # 大問ごとに表示
        for major_num in sorted(grouped_themes.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            if len(grouped_themes) > 1:
                print(f"\n▼ 大問 {major_num}")
                print("-" * 40)
            
            themes = grouped_themes[major_num]
            if themes:
                for num, theme, field in themes:
                    # 分野も併記してより分かりやすく
                    print(f"  {num}: {theme} [{field}]")
            else:
                print("  （テーマ情報なし）")
    else:
        print("  （問題が検出されませんでした）")
    
    print("\n" + "=" * 70)


def display_themes_old(analysis_result):
    """従来の表示方法（比較用）"""
    print("\n【従来の表示方法】")
    print("-" * 40)
    
    questions = analysis_result.get('questions', [])
    themes = []
    for q in questions:
        if q.topic:
            themes.append((q.number, q.topic))
    
    if themes:
        for num, theme in themes:
            print(f"  {num}: {theme}")
    else:
        print("  （テーマ情報なし）")


def main():
    """メイン処理"""
    print("テーマ表示の改善テスト")
    print("=" * 70)
    
    # サンプルデータ作成
    print("サンプルデータを作成中...")
    result = create_sample_data()
    
    # 問題数と分野分布を表示
    print(f"\n総問題数: {result['total_questions']}問")
    
    stats = result['statistics']
    if 'field_distribution' in stats:
        print("\n分野別分布:")
        for field, data in stats['field_distribution'].items():
            print(f"  {field}: {data['count']}問 ({data['percentage']:.1f}%)")
    
    # 従来の表示方法
    display_themes_old(result)
    
    # 改善された表示方法
    display_themes_grouped(result)
    
    print("\n✅ 改善内容:")
    print("  1. 大問ごとに区切り線を入れて視覚的に分離")
    print("  2. 大問番号を明示（▼ 大問 1, ▼ 大問 2 など）")
    print("  3. 各テーマに分野情報を追加 [歴史], [地理], [公民]")
    print("  4. インデントを調整して階層構造を明確化")


if __name__ == "__main__":
    main()