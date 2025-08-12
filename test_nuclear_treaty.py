#\!/usr/bin/env python3
"""
核兵器禁止条約のテスト
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.social_analyzer_fixed import FixedSocialAnalyzer

analyzer = FixedSocialAnalyzer()

test_texts = [
    "核兵器禁止条約について答えなさい。",
    "核兵器禁止条約の内容を説明しなさい。",
    "NPTについて説明しなさい。",
    "国連の役割について述べなさい。",
]

for text in test_texts:
    question = analyzer.analyze_question(text)
    if question.topic:
        print(f"✅ {text} → {question.topic}")
    else:
        print(f"❌ {text} → テーマなし")
