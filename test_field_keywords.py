#!/usr/bin/env python3
"""
分野別主要語機能のテスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from analyze_with_gemini_detailed import GeminiDetailedAnalyzer

def test_field_keywords():
    """分野別主要語収集のテスト"""
    
    # テスト用のサンプルデータ
    test_questions = [
        {
            'number': '大問1-問1',
            'field': '地理',
            'theme': '日本の農業',
            'keywords': ['促成栽培', '高知県', 'ハウス栽培', 'ビニールハウス'],
            'question_format': '記号選択'
        },
        {
            'number': '大問1-問2',
            'field': '地理',
            'theme': '工業地帯',
            'keywords': ['太平洋ベルト', '京浜工業地帯', '重化学工業'],
            'question_format': '短答式'
        },
        {
            'number': '大問2-問1',
            'field': '歴史',
            'theme': '江戸時代の政治',
            'keywords': ['徳川家康', '江戸幕府', '参勤交代', '鎖国'],
            'question_format': '記号選択'
        },
        {
            'number': '大問2-問2',
            'field': '歴史',
            'theme': '明治維新',
            'keywords': ['明治維新', '文明開化', '富国強兵', '殖産興業'],
            'question_format': '記述式'
        },
        {
            'number': '大問3-問1',
            'field': '公民',
            'theme': '日本国憲法',
            'keywords': ['基本的人権', '国民主権', '平和主義'],
            'question_format': '穴埋め'
        },
        {
            'number': '大問4-問1',
            'field': '時事問題',
            'theme': 'SDGs',
            'keywords': ['持続可能', '温室効果ガス', '再生可能エネルギー'],
            'question_format': '記号選択'
        }
    ]
    
    analyzer = GeminiDetailedAnalyzer()
    
    # 統計計算のテスト
    stats = analyzer._calculate_statistics(test_questions)
    
    print("=" * 60)
    print("分野別主要語収集テスト")
    print("=" * 60)
    print()
    
    # 分野別主要語の確認
    if field_keywords := stats.get('field_keywords'):
        print("◆ 分野別主要語一覧:")
        for field in ['地理', '歴史', '公民', '時事問題', 'その他']:
            if keywords := field_keywords.get(field):
                print(f"\n【{field}】")
                # 5個ずつ改行して表示
                for i in range(0, len(keywords), 5):
                    batch = keywords[i:i+5]
                    print(f"  {', '.join(batch)}")
    else:
        print("分野別主要語が収集されていません")
    
    print()
    print("=" * 60)
    
    # 個別問題表示のテスト（キーワードなし）
    print("\n◆ 問題別詳細（キーワードなしで表示）:")
    print("-" * 60)
    
    for q in test_questions[:3]:
        number = q['number']
        theme = q['theme']
        field = q['field']
        q_format = q['question_format']
        
        print(f"\n▼ {number}")
        print(f"  テーマ: {theme} | ジャンル: {field} | 出題形式: {q_format}")
    
    print()
    print("=" * 60)
    print("テスト完了")

if __name__ == "__main__":
    test_field_keywords()