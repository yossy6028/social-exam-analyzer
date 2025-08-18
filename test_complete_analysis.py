#!/usr/bin/env python3
"""
完全分析テスト（大問1-4、出題形式を含む）
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from analyze_with_gemini_detailed import GeminiDetailedAnalyzer

def test_complete_analysis():
    """完全な分析をテスト"""
    
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf"
    
    print("=" * 80)
    print("完全分析テスト")
    print("=" * 80)
    print()
    
    analyzer = GeminiDetailedAnalyzer()
    result = analyzer.analyze_pdf(pdf_path)
    
    # 検証
    print("\n" + "=" * 80)
    print("【検証結果】")
    print("=" * 80)
    
    # 1. 大問の確認
    print("\n1. 大問カバレッジ:")
    major_nums = set()
    for q in result.get('questions', []):
        if 'number' in q:
            import re
            match = re.match(r'大問(\d+)', q['number'])
            if match:
                major_nums.add(int(match.group(1)))
    
    print(f"  検出された大問: {sorted(major_nums)}")
    if major_nums == {1, 2, 3, 4}:
        print("  ✅ 大問1-4すべて検出")
    else:
        missing = set(range(1, 5)) - major_nums
        if missing:
            print(f"  ⚠️ 大問{missing}が不足")
    
    # 2. 出題形式の確認
    print("\n2. 出題形式分析:")
    format_counts = {}
    for q in result.get('questions', []):
        fmt = q.get('question_format', '未設定')
        format_counts[fmt] = format_counts.get(fmt, 0) + 1
    
    if format_counts:
        for fmt, count in sorted(format_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {fmt:12s}: {count:3d}問")
        
        if '未設定' not in format_counts or format_counts.get('未設定', 0) < 5:
            print("  ✅ 出題形式が適切に分析されています")
        else:
            print(f"  ⚠️ {format_counts.get('未設定', 0)}問が形式未設定")
    
    # 3. 問題数の確認
    print(f"\n3. 総問題数: {result.get('total_questions', 0)}問")
    if result.get('total_questions', 0) >= 30:
        print("  ✅ 十分な問題数を検出")
    else:
        print("  ⚠️ 問題数が少ない可能性")
    
    # 4. サンプル問題表示
    print("\n4. サンプル問題（大問ごとに1問）:")
    displayed_majors = set()
    for q in result.get('questions', []):
        if 'number' in q:
            match = re.match(r'大問(\d+)', q['number'])
            if match:
                major = int(match.group(1))
                if major not in displayed_majors:
                    displayed_majors.add(major)
                    print(f"\n  {q['number']}:")
                    print(f"    テーマ: {q.get('theme', '未設定')}")
                    print(f"    形式: {q.get('question_format', '未設定')}")
                    print(f"    分野: {q.get('field', '未設定')}")

if __name__ == "__main__":
    test_complete_analysis()