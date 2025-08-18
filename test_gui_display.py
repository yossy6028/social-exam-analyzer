#!/usr/bin/env python3
"""
GUI表示問題のデバッグ用テストスクリプト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.social_analyzer import SocialAnalyzer, SocialField, ResourceType, QuestionFormat
from modules.social_analyzer import SocialQuestion

# アナライザーの初期化
analyzer = SocialAnalyzer()

# サンプル問題を作成
questions = [
    SocialQuestion(
        number="問1",
        text="江戸時代の農業について説明しなさい。",
        field=SocialField.HISTORY,
        resource_types=[ResourceType.NONE],
        question_format=QuestionFormat.DESCRIPTIVE,
        is_current_affairs=False,
        theme="江戸時代の農業"
    ),
    SocialQuestion(
        number="問2",
        text="明治維新の改革について述べなさい。",
        field=SocialField.HISTORY,
        resource_types=[ResourceType.NONE],
        question_format=QuestionFormat.DESCRIPTIVE,
        is_current_affairs=False,
        theme="明治維新"
    ),
    SocialQuestion(
        number="問3",
        text="日本国憲法の三原則を答えなさい。",
        field=SocialField.CIVICS,
        resource_types=[ResourceType.NONE],
        question_format=QuestionFormat.SHORT_ANSWER,
        is_current_affairs=False,
        theme="日本国憲法"
    ),
    SocialQuestion(
        number="問4",
        text="地図を見て、県庁所在地を答えなさい。",
        field=SocialField.GEOGRAPHY,
        resource_types=[ResourceType.MAP],
        question_format=QuestionFormat.SHORT_ANSWER,
        is_current_affairs=False,
        theme="県庁所在地"
    ),
]

# 統計情報を計算
stats = analyzer._calculate_statistics(questions)

print("=== 統計データの確認 ===")
print("\n1. statsの内容:")
print(f"  キー: {stats.keys()}")

print("\n2. field_distribution:")
if 'field_distribution' in stats:
    for field, data in stats['field_distribution'].items():
        print(f"  {field}: {data}")
else:
    print("  field_distributionが存在しません")

print("\n3. resource_usage:")
if 'resource_usage' in stats:
    for resource, data in stats['resource_usage'].items():
        print(f"  {resource}: {data}")
else:
    print("  resource_usageが存在しません")

print("\n4. format_distribution:")
if 'format_distribution' in stats:
    for format_type, data in stats['format_distribution'].items():
        print(f"  {format_type}: {data}")
else:
    print("  format_distributionが存在しません")

# フィールド値の型確認
print("\n=== Enum値の確認 ===")
for q in questions:
    print(f"問題: {q.number}")
    print(f"  field型: {type(q.field)}, 値: {q.field}, .value: {q.field.value}")
    print(f"  format型: {type(q.question_format)}, 値: {q.question_format}, .value: {q.question_format.value}")
    if q.resource_types:
        for r in q.resource_types:
            print(f"  resource型: {type(r)}, 値: {r}, .value: {r.value}")

# 分析結果の作成
analysis_result = {
    'questions': questions,
    'statistics': stats,
    'total_questions': len(questions)
}

print("\n=== 最終的な分析結果 ===")
print(f"total_questions: {analysis_result['total_questions']}")
print(f"statisticsのキー: {analysis_result['statistics'].keys()}")