#!/usr/bin/env python3
"""
GUI動作の簡易テスト（OCR処理をスキップ）
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# モジュールのインポート
from modules.social_analyzer import SocialAnalyzer, SocialQuestion, SocialField, ResourceType, QuestionFormat

def create_sample_data():
    """日工大駒場中2023年を模したサンプルデータを作成"""
    
    # サンプル問題データ（実際の問題を簡略化）
    questions = [
        SocialQuestion(
            number="大問1-問1",
            text="江戸時代の参勤交代制度について説明しなさい。",
            field=SocialField.HISTORY,
            resource_types=[ResourceType.NONE],
            question_format=QuestionFormat.DESCRIPTIVE,
            theme="江戸時代の参勤交代制度"
        ),
        SocialQuestion(
            number="大問1-問2", 
            text="明治維新の中心人物を3人挙げなさい。",
            field=SocialField.HISTORY,
            resource_types=[ResourceType.NONE],
            question_format=QuestionFormat.SHORT_ANSWER,
            theme="明治維新の中心人物"
        ),
        SocialQuestion(
            number="大問2-問1",
            text="日本国憲法の基本原則について説明しなさい。",
            field=SocialField.CIVICS,
            resource_types=[ResourceType.NONE],
            question_format=QuestionFormat.DESCRIPTIVE,
            theme="日本国憲法の基本原則"
        ),
        SocialQuestion(
            number="大問2-問2",
            text="選挙権の年齢について答えなさい。",
            field=SocialField.CIVICS,
            resource_types=[ResourceType.NONE],
            question_format=QuestionFormat.SHORT_ANSWER,
            theme="選挙権の年齢"
        ),
        SocialQuestion(
            number="大問3-問1",
            text="地図を見て、県庁所在地を答えなさい。",
            field=SocialField.GEOGRAPHY,
            resource_types=[ResourceType.MAP],
            question_format=QuestionFormat.SHORT_ANSWER,
            theme="県庁所在地"
        ),
        SocialQuestion(
            number="大問3-問2",
            text="グラフから読み取れる人口変化について述べなさい。",
            field=SocialField.GEOGRAPHY,
            resource_types=[ResourceType.GRAPH],
            question_format=QuestionFormat.DESCRIPTIVE,
            theme="人口変化の分析"
        ),
        SocialQuestion(
            number="大問4-問1",
            text="SDGsの目標について説明しなさい。",
            field=SocialField.CURRENT_AFFAIRS,
            resource_types=[ResourceType.NONE],
            question_format=QuestionFormat.DESCRIPTIVE,
            is_current_affairs=True,
            theme="SDGsの目標"
        ),
        SocialQuestion(
            number="大問4-問2",
            text="2023年の主要な出来事を答えなさい。",
            field=SocialField.CURRENT_AFFAIRS,
            resource_types=[ResourceType.NONE],
            question_format=QuestionFormat.SHORT_ANSWER,
            is_current_affairs=True,
            theme="2023年の時事問題"
        )
    ]
    
    return questions

def test_gui_display_logic():
    """GUI表示ロジックのテスト"""
    print("=== GUI表示ロジックのテスト ===\n")
    
    # サンプルデータ作成
    questions = create_sample_data()
    
    # アナライザーで統計計算
    analyzer = SocialAnalyzer()
    stats = analyzer._calculate_statistics(questions)
    
    # 分析結果の作成
    analysis_result = {
        'questions': questions,
        'statistics': stats,
        'total_questions': len(questions)
    }
    
    # 結果表示
    print(f"総問題数: {analysis_result['total_questions']}問\n")
    
    # 分野別分布
    print("【分野別出題状況】")
    if 'field_distribution' in stats and stats['field_distribution']:
        for field, data in stats['field_distribution'].items():
            if isinstance(data, dict) and 'count' in data:
                print(f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
    
    print("\n【資料活用状況】")
    if 'resource_usage' in stats and stats['resource_usage']:
        for resource, data in stats['resource_usage'].items():
            if isinstance(data, dict) and 'count' in data:
                print(f"  {resource:10s}: {data['count']:3d}回 ({data['percentage']:5.1f}%)")
    
    print("\n【出題形式分布】")
    if 'format_distribution' in stats and stats['format_distribution']:
        for fmt, data in stats['format_distribution'].items():
            if isinstance(data, dict) and 'count' in data:
                print(f"  {fmt:10s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
    
    print("\n【時事問題】")
    if 'current_affairs' in stats:
        print(f"  時事問題数: {stats['current_affairs']['count']}問 ({stats['current_affairs']['percentage']:.1f}%)")
    
    print("\n【検出された問題とテーマ】")
    for q in questions:
        field_value = q.field.value if hasattr(q.field, 'value') else str(q.field)
        print(f"  {q.number}: [{field_value}] {q.theme}")
    
    return analysis_result

def test_with_gui():
    """実際のGUIで表示テスト"""
    import tkinter as tk
    from tkinter import ttk
    
    # GUIウィンドウ作成
    root = tk.Tk()
    root.title("GUI表示テスト - 日工大駒場中2023年模擬データ")
    root.geometry("800x600")
    
    # テキストエリア作成
    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    text_widget = tk.Text(frame, height=30, width=90, wrap=tk.WORD)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar.set)
    
    text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    
    # サンプルデータで分析結果を作成
    questions = create_sample_data()
    analyzer = SocialAnalyzer()
    stats = analyzer._calculate_statistics(questions)
    
    # display_resultsの動作をシミュレート
    text_widget.insert(tk.END, "=" * 60 + "\n")
    text_widget.insert(tk.END, "分析結果サマリー（テストデータ）\n")
    text_widget.insert(tk.END, "=" * 60 + "\n\n")
    
    text_widget.insert(tk.END, f"総問題数: {len(questions)}問\n\n")
    
    # 分野別分布
    text_widget.insert(tk.END, "【分野別出題状況】\n")
    if 'field_distribution' in stats:
        for field, data in stats['field_distribution'].items():
            text_widget.insert(tk.END, 
                f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)\n")
    
    text_widget.insert(tk.END, "\n【資料活用状況】\n")
    if 'resource_usage' in stats:
        sorted_resources = sorted(stats['resource_usage'].items(), 
                                 key=lambda x: x[1]['count'], reverse=True)
        for resource, data in sorted_resources[:5]:
            text_widget.insert(tk.END, 
                f"  {resource:10s}: {data['count']:3d}回 ({data['percentage']:5.1f}%)\n")
    
    text_widget.insert(tk.END, "\n【出題形式分布】\n")
    if 'format_distribution' in stats:
        sorted_formats = sorted(stats['format_distribution'].items(),
                               key=lambda x: x[1]['count'], reverse=True)
        for fmt, data in sorted_formats[:5]:
            text_widget.insert(tk.END, 
                f"  {fmt:10s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)\n")
    
    text_widget.insert(tk.END, "\n【検出された問題とテーマ】\n")
    for q in questions:
        field_value = q.field.value if hasattr(q.field, 'value') else str(q.field)
        text_widget.insert(tk.END, f"  {q.number}: [{field_value}] {q.theme}\n")
    
    # 閉じるボタン
    close_button = ttk.Button(frame, text="閉じる", command=root.quit)
    close_button.grid(row=1, column=0, pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    print("1. コンソールでのテスト")
    print("-" * 60)
    test_gui_display_logic()
    
    print("\n" + "=" * 60)
    print("2. GUIウィンドウでのテスト")
    print("-" * 60)
    print("GUIウィンドウを起動中...")
    test_with_gui()