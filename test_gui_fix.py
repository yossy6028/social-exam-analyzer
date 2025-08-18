#!/usr/bin/env python3
"""
GUI修正のテストスクリプト
"""

import sys
import os
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# モジュールのインポート
from modules.social_analyzer import SocialAnalyzer
from modules.hierarchical_question_manager import HierarchicalQuestionManager

def test_analysis_with_statistics():
    """統計情報生成のテスト"""
    print("=== 統計情報生成テスト ===\n")
    
    # サンプルテキスト
    test_text = """
    大問1
    問1 江戸時代の主要な改革について説明しなさい。
    問2 明治維新による近代化の影響を述べなさい。
    
    大問2
    問1 日本国憲法の三原則を答えなさい。
    問2 選挙制度について説明しなさい。
    
    大問3
    問1 日本の気候の特徴を説明しなさい。
    問2 グラフを見て、人口変化について答えなさい。
    """
    
    # アナライザーの初期化
    analyzer = SocialAnalyzer()
    
    # 階層管理システムで問題を抽出
    hierarchy_manager = HierarchicalQuestionManager()
    hierarchical_questions = hierarchy_manager.extract_hierarchical_questions(test_text)
    flattened_questions = hierarchy_manager.get_flattened_questions()
    
    print(f"検出された問題数: {len(flattened_questions)}")
    
    # 分析実行
    if hasattr(analyzer, 'analyze_document_with_hierarchy'):
        result = analyzer.analyze_document_with_hierarchy(test_text, flattened_questions)
    else:
        result = analyzer.analyze_document(test_text)
    
    # 結果の確認
    print(f"\n分析結果のキー: {result.keys()}")
    
    if 'statistics' in result:
        print("✅ statistics が存在します")
        stats = result['statistics']
        print(f"  統計情報のキー: {stats.keys()}")
        
        if 'field_distribution' in stats:
            print("\n  分野別分布:")
            for field, data in stats['field_distribution'].items():
                print(f"    {field}: {data}")
        
        if 'format_distribution' in stats:
            print("\n  出題形式分布:")
            for fmt, data in stats['format_distribution'].items():
                print(f"    {fmt}: {data}")
    else:
        print("❌ statistics が存在しません")
        
        # 手動で統計を計算
        if 'questions' in result:
            print("\n手動で統計を計算中...")
            stats = analyzer._calculate_statistics(result['questions'])
            print(f"  計算された統計のキー: {stats.keys()}")
            result['statistics'] = stats
            print("✅ statistics を追加しました")

def test_gui_display():
    """GUI表示のシミュレーション"""
    print("\n=== GUI表示シミュレーション ===\n")
    
    # サンプルデータを作成
    analysis_result = {
        'total_questions': 6,
        'questions': [],  # 簡略化のため省略
        'statistics': {
            'field_distribution': {
                '歴史': {'count': 2, 'percentage': 33.3},
                '公民': {'count': 2, 'percentage': 33.3},
                '地理': {'count': 2, 'percentage': 33.3}
            },
            'resource_usage': {
                '資料なし': {'count': 5, 'percentage': 83.3},
                'グラフ': {'count': 1, 'percentage': 16.7}
            },
            'format_distribution': {
                '記述式': {'count': 4, 'percentage': 66.7},
                '短答式': {'count': 2, 'percentage': 33.3}
            },
            'current_affairs': {
                'count': 0,
                'percentage': 0.0
            }
        }
    }
    
    # display_resultsのロジックをシミュレート
    if not analysis_result:
        print("分析結果がありません")
        return
    
    if 'statistics' not in analysis_result:
        print("統計情報が存在しません")
        if 'total_questions' in analysis_result:
            print(f"総問題数: {analysis_result['total_questions']}問")
        return
    
    stats = analysis_result['statistics']
    
    print(f"総問題数: {analysis_result['total_questions']}問\n")
    
    # 分野別分布
    print("【分野別出題状況】")
    if 'field_distribution' in stats and stats['field_distribution']:
        for field, data in stats['field_distribution'].items():
            if isinstance(data, dict) and 'count' in data and 'percentage' in data:
                print(f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
    else:
        print("  （データなし）")
    
    print("\n【資料活用状況】")
    if 'resource_usage' in stats and stats['resource_usage']:
        valid_resources = [(k, v) for k, v in stats['resource_usage'].items() 
                          if isinstance(v, dict) and 'count' in v]
        if valid_resources:
            for resource, data in sorted(valid_resources, 
                                        key=lambda x: x[1].get('count', 0), 
                                        reverse=True)[:5]:
                print(f"  {resource:10s}: {data['count']:3d}回 ({data['percentage']:5.1f}%)")
        else:
            print("  （データなし）")
    else:
        print("  （データなし）")
    
    print("\n✅ GUI表示シミュレーション完了")

if __name__ == "__main__":
    test_analysis_with_statistics()
    test_gui_display()
    print("\n✅ すべてのテストが完了しました")