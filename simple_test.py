#\!/usr/bin/env python3
"""
シンプルなテスト - 基本に戻る
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# 元のSocialAnalyzerを使用
from modules.social_analyzer import SocialAnalyzer

analyzer = SocialAnalyzer()

# シンプルな問題文
test_text = """
問1 江戸時代の農業について説明しなさい。
問2 明治維新の改革について述べなさい。
問3 日本国憲法の三原則を答えなさい。
"""

result = analyzer.analyze_document(test_text)

print(f"検出された問題数: {result['total_questions']}")
print("\nテーマ一覧:")
for q in result['questions']:
    print(f"  {q.number}: {q.theme if q.theme else '（なし）'}")
