#!/usr/bin/env python3
"""
GeminiBridge単体テスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.gemini_bridge import GeminiBridge

bridge = GeminiBridge()

if bridge.check_availability():
    print("✅ GeminiBridge 利用可能")
    
    # テストデータ（Gemini APIから返される形式）
    test_result = {
        'questions': [
            {
                'number': '大問1-問1',
                'text': 'テスト問題',
                'field': '地理',
                'theme': 'テストテーマ',
                'keywords': ['キーワード1'],
                'type': '選択式'
            }
        ],
        'statistics': {},
        'total_questions': 1
    }
    
    # 変換テスト
    converted = bridge._convert_to_gui_format(test_result)
    
    print(f"変換後の問題数: {len(converted['questions'])}")
    
    if converted['questions']:
        q = converted['questions'][0]
        print(f"問題オブジェクトの型: {type(q)}")
        print(f"属性チェック:")
        print(f"  - number: {hasattr(q, 'number')} -> {getattr(q, 'number', None)}")
        print(f"  - text: {hasattr(q, 'text')} -> {getattr(q, 'text', '')[:30]}")
        print(f"  - field: {hasattr(q, 'field')} -> {getattr(q, 'field', None)}")
        print(f"  - theme: {hasattr(q, 'theme')} -> {getattr(q, 'theme', None)}")
else:
    print("❌ GeminiBridge 利用不可")