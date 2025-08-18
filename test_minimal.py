#!/usr/bin/env python3
"""最小限のGemini動作テスト"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.gemini_analyzer import GeminiAnalyzer
import os
from dotenv import load_dotenv

load_dotenv()

# サンプルテキスト（実際の入試問題風）
sample_text = """
1 次の問題に答えなさい。

問1 日本の農業について、次の空欄に当てはまる語句を答えなさい。
高知県では冬でも温暖な気候を利用して、ビニールハウスで野菜を栽培する（　　）栽培が盛んです。

問2 次の都市の中から、政令指定都市を全て選びなさい。
ア 横浜市　イ 水戸市　ウ 千葉市　エ 宇都宮市

問3 地図中のAの山脈の名前を答えなさい。

2 次の歴史に関する問題に答えなさい。

問1 1600年に起きた天下分け目の戦いの名前を答えなさい。

問2 明治維新で行われた改革を3つ挙げなさい。
"""

try:
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"API Key: {api_key[:20]}...")
    
    analyzer = GeminiAnalyzer(api_key)
    print("✅ Analyzer initialized")
    
    result = analyzer.analyze_exam_structure(
        text=sample_text,
        school="テスト中学校",
        year="2023"
    )
    
    print("\n分析結果:")
    print(f"総問題数: {result['summary']['total_questions']}問")
    print(f"大問数: {result['total_sections']}個")
    
    for section in result['sections']:
        print(f"\n大問{section['section_number']}: {section['question_count']}問")
        for q in section['questions']:
            print(f"  問{q['question_number']}: {q.get('field', '不明')}")
    
    print("\n✅ テスト成功！")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()