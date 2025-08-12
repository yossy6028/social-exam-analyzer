#\!/usr/bin/env python3
"""
問題抽出のデバッグ
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.improved_question_extractor import ImprovedQuestionExtractor

# 実際のOCRテキスト（東京電機大学の例）
sample_text = """
1. 次のA～Iは、 いろいろな時代に作られた歌です。 これについて、 各設問に答えなさい。

A. 春過ぎて 夏来にけらし 白妙の 衣干すちょう 天の香具山

問1 Aの歌の作者として正しい人物を選びなさい。

問2 次の系図は、B・Cの歌に関係するものです。

2. 広島県でG7サミットが開催されます。

問1 G7に参加する国を答えなさい。

問2 広島県の特徴について説明しなさい。
"""

extractor = ImprovedQuestionExtractor()
questions = extractor.extract_questions(sample_text)

print(f"抽出された問題数: {len(questions)}")
print("\n詳細:")
for q_num, q_text in questions[:5]:  # 最初の5問のみ
    print(f"\n{q_num}:")
    print(f"  {q_text[:100]}...")
