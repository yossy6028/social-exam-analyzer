#!/usr/bin/env python3
"""
下線部参照問題の修正テスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from analyze_with_gemini_detailed import GeminiDetailedAnalyzer

def test_underline_reference():
    """下線部参照の解決テスト"""
    
    analyzer = GeminiDetailedAnalyzer()
    
    # テスト用の問題（下線部を含む）
    test_questions = [
        {
            'number': '大問2-問8',
            'text': '下線部⑥について、この地域の気候の特徴として正しいものを選びなさい。なお、下線部⑥は「高知県の促成栽培」を指している。',
            'type': '選択式'
        },
        {
            'number': '大問4-問2',
            'text': '下線部⑥の憲法に関して、基本的人権が制限される場合について50字以内で説明しなさい。下線部⑥は「日本国憲法第13条の公共の福祉」を指す。',
            'type': '記述式'
        }
    ]
    
    print("=" * 60)
    print("下線部参照の解決テスト")
    print("=" * 60)
    print()
    
    for q in test_questions:
        print(f"【テスト】 {q['number']}")
        print(f"問題文: {q['text'][:50]}...")
        
        # 分析実行
        result = analyzer.analyze_single_question(q)
        
        theme = result.get('theme', '未設定')
        field = result.get('field', '未設定')
        q_format = result.get('question_format', '未設定')
        
        print(f"分析結果:")
        print(f"  テーマ: {theme}")
        print(f"  分野: {field}")
        print(f"  形式: {q_format}")
        
        # 「下線部」が残っていないかチェック
        if "下線部" in theme:
            print("  ⚠️ 警告: テーマに「下線部」が残っています")
        else:
            print("  ✅ 成功: 具体的なテーマに変換されました")
        
        print()
    
    print("=" * 60)
    print("テスト完了")

if __name__ == "__main__":
    test_underline_reference()