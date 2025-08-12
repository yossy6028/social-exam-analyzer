#!/usr/bin/env python3
"""
分野判定の改善テスト
70%以上のウェイトで特定分野に分類されることを確認
"""

import sys
from pathlib import Path

# モジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from modules.social_analyzer import SocialAnalyzer, SocialField


def test_field_detection():
    """分野判定のテスト"""
    analyzer = SocialAnalyzer()
    
    # テストケース
    test_cases = [
        {
            'name': '歴史に偏った問題群',
            'text': """
            問1 縄文時代の人々が使っていた土器の特徴を説明しなさい。
            問2 弥生時代に始まった稲作について述べなさい。
            問3 古墳時代の豪族について説明しなさい。
            問4 聖徳太子が制定した十七条憲法について説明しなさい。
            問5 平安時代の貴族の生活について述べなさい。
            問6 鎌倉幕府の成立について説明しなさい。
            問7 織田信長の政策について述べなさい。
            問8 明治維新の改革について説明しなさい。
            問9 日本の産業について述べなさい。（これだけ地理的要素）
            問10 太平洋戦争について説明しなさい。
            """,
            'expected_dominant': SocialField.HISTORY,
            'expected_mixed_count': 1  # 問9のみ
        },
        {
            'name': '地理に偏った問題群',
            'text': """
            問1 関東地方の都道府県を全て挙げなさい。
            問2 日本アルプスの山脈について説明しなさい。
            問3 瀬戸内海の気候の特徴を述べなさい。
            問4 北海道の農業について説明しなさい。
            問5 九州地方の工業について述べなさい。
            問6 東京の人口問題について説明しなさい。
            問7 沖縄の産業について述べなさい。
            問8 日本の貿易について説明しなさい。
            """,
            'expected_dominant': SocialField.GEOGRAPHY,
            'expected_mixed_count': 0
        },
        {
            'name': '公民に偏った問題群',
            'text': """
            問1 日本国憲法の三大原則を説明しなさい。
            問2 三権分立について述べなさい。
            問3 国会の仕組みについて説明しなさい。
            問4 内閣の役割について述べなさい。
            問5 裁判所の種類について説明しなさい。
            問6 選挙制度について説明しなさい。
            問7 地方自治について述べなさい。
            """,
            'expected_dominant': SocialField.CIVICS,
            'expected_mixed_count': 0
        },
        {
            'name': '混合型（70%未満）',
            'text': """
            問1 縄文時代について説明しなさい。
            問2 弥生時代について説明しなさい。
            問3 関東地方について説明しなさい。
            問4 近畿地方について説明しなさい。
            問5 日本国憲法について説明しなさい。
            問6 三権分立について説明しなさい。
            """,
            'expected_dominant': None,  # 各分野33%なので総合のまま
            'expected_mixed_count': 0  # ただし個別には分類される
        }
    ]
    
    print("=" * 70)
    print("分野判定の改善テスト（70%ルール）")
    print("=" * 70)
    print()
    
    for test_case in test_cases:
        print(f"テスト: {test_case['name']}")
        print("-" * 50)
        
        # 文書全体を分析
        result = analyzer.analyze_document(test_case['text'])
        
        # 分野別の集計
        field_counts = {}
        for q in result['questions']:
            field = q.field.value
            field_counts[field] = field_counts.get(field, 0) + 1
        
        print(f"問題数: {result['total_questions']}")
        print("分野別分布:")
        for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / result['total_questions']) * 100
            print(f"  {field:10s}: {count:2d}問 ({percentage:5.1f}%)")
        
        # 統計情報から確認
        stats = result['statistics']
        if 'field_distribution' in stats:
            print("\n統計情報の分野分布:")
            for field, data in stats['field_distribution'].items():
                print(f"  {field:10s}: {data['count']:2d}問 ({data['percentage']:5.1f}%)")
        
        # 判定結果の確認
        if test_case['expected_dominant']:
            dominant_field = max(field_counts.items(), key=lambda x: x[1])[0]
            if dominant_field == test_case['expected_dominant'].value:
                print(f"✅ 期待通り: {dominant_field}が支配的")
            else:
                print(f"❌ 期待と異なる: {dominant_field} (期待: {test_case['expected_dominant'].value})")
        
        mixed_count = field_counts.get('総合', 0)
        print(f"総合と判定された問題数: {mixed_count}")
        
        print()
    
    print("=" * 70)


def test_single_question():
    """個別問題の分野判定テスト"""
    analyzer = SocialAnalyzer()
    
    test_questions = [
        {
            'text': '織田信長が行った楽市楽座について、その目的と影響を説明しなさい。',
            'expected': SocialField.HISTORY
        },
        {
            'text': '東京、大阪、名古屋の三大都市圏について、それぞれの特徴を述べなさい。',
            'expected': SocialField.GEOGRAPHY
        },
        {
            'text': '参議院と衆議院の違いについて、選挙制度の観点から説明しなさい。',
            'expected': SocialField.CIVICS
        },
        {
            'text': 'SDGsの17の目標のうち、日本が特に取り組むべき課題を3つ選んで説明しなさい。',
            'expected': SocialField.CURRENT_AFFAIRS
        }
    ]
    
    print("\n個別問題の分野判定テスト")
    print("=" * 70)
    
    for i, test in enumerate(test_questions, 1):
        result = analyzer.analyze_question(test['text'], str(i))
        print(f"問{i}: {test['text'][:40]}...")
        print(f"  判定結果: {result.field.value}")
        print(f"  期待値: {test['expected'].value}")
        
        if result.field == test['expected']:
            print("  ✅ 成功")
        else:
            print("  ❌ 失敗")
        print()


if __name__ == "__main__":
    test_field_detection()
    test_single_question()