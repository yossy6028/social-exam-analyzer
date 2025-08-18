#!/usr/bin/env python3
"""テキスト出力機能のテストスクリプト"""

import sys
import os
from pathlib import Path

# プロジェクトのパスを追加
sys.path.insert(0, str(Path(__file__).parent))

# from core.analyzer import Analyzer
# from utils.formatter import Formatter
from enum import Enum

class FieldType(Enum):
    GEOGRAPHY = "地理"
    HISTORY = "歴史"
    CIVICS = "公民"
    CURRENT_AFFAIRS = "時事"
    RESOURCE = "資料"

def test_text_output():
    """テキスト出力機能をテスト"""
    
    # ダミーの分析結果を作成
    class DummyQuestion:
        def __init__(self, number, topic, field):
            self.number = number
            self.theme = topic
            self.field = field
            self.text = f"問題文 {number}"
    
    analysis_result = {
        'total_questions': 5,
        'questions': [
            DummyQuestion("大問1-問1", "江戸時代の政治", FieldType.HISTORY),
            DummyQuestion("大問1-問2", "明治維新", FieldType.HISTORY),
            DummyQuestion("大問2-問1", "日本の地形", FieldType.GEOGRAPHY),
            DummyQuestion("大問2-問2", "気候と農業", FieldType.GEOGRAPHY),
            DummyQuestion("大問3-問1", "国会のしくみ", FieldType.CIVICS),
        ],
        'statistics': {
            'field_distribution': {
                '地理': {'count': 2, 'percentage': 40.0},
                '歴史': {'count': 2, 'percentage': 40.0},
                '公民': {'count': 1, 'percentage': 20.0},
            }
        }
    }
    
    # テキスト出力を生成
    output = []
    output.append("=" * 60)
    output.append("社会科入試問題分析 - テーマ一覧")
    output.append("=" * 60)
    output.append("")
    output.append("学校名: テスト学校")
    output.append("年度: 2025年")
    output.append(f"総問題数: {analysis_result['total_questions']}問")
    output.append("")
    
    # 分野別出題状況
    stats = analysis_result['statistics']
    output.append("【分野別出題状況】")
    if 'field_distribution' in stats:
        for field, data in stats['field_distribution'].items():
            output.append(f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
    output.append("")
    
    # テーマ一覧
    output.append("【出題テーマ一覧】")
    questions = analysis_result.get('questions', [])
    
    if questions:
        # 大問ごとにグループ化
        grouped_themes = {}
        for q in questions:
            # 大問番号を抽出
            import re
            m = re.match(r'大問(\d+)', q.number)
            if m:
                major_num = m.group(1)
            else:
                major_num = '1'
            
            if major_num not in grouped_themes:
                grouped_themes[major_num] = []
            
            grouped_themes[major_num].append((q.number, q.theme, q.field.value))
        
        # 大問ごとに出力
        for major_num in sorted(grouped_themes.keys()):
            output.append(f"\n▼ 大問 {major_num}")
            output.append("-" * 40)
            
            themes = grouped_themes[major_num]
            for num, theme, field in themes:
                # 問題番号を整形
                display_num = num
                m = re.search(r'大問\d+[\-－‐]?問?\s*(.+)', num)
                if m:
                    display_num = f"問{m.group(1)}"
                output.append(f"  {display_num}: {theme} [{field}]")
    
    output.append("")
    output.append("=" * 60)
    output.append("分析終了")
    
    # 出力を表示
    result = "\n".join(output)
    print(result)
    
    # テストファイルに保存
    test_file = "test_output.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"\n\nテストファイルを保存しました: {test_file}")
    
    # ファイルの内容を確認
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print("\n保存されたファイルの内容:")
        print(content[:500] + "..." if len(content) > 500 else content)

if __name__ == "__main__":
    test_text_output()