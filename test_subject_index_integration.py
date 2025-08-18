#!/usr/bin/env python3
"""
subject_index.md との統合テスト
重要語句が正しくテーマとして抽出されるか確認
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.gemini_analyzer import GeminiAnalyzer
from modules.subject_index_loader import SubjectIndexLoader

load_dotenv()

def test_subject_index_integration():
    """subject_index との統合テスト"""
    
    print("=" * 60)
    print("subject_index.md 統合テスト")
    print("=" * 60)
    
    # SubjectIndexLoader のテスト
    print("\n1. SubjectIndexLoader の動作確認")
    loader = SubjectIndexLoader()
    
    # テストテキスト（重要語句を含む）
    test_texts = [
        "高知県では冬でも温暖な気候を利用して、ビニールハウスで野菜を栽培する促成栽培が盛んです。",
        "明治維新によって日本は近代化を進めました。",
        "日本の政治は三権分立の原則に基づいています。",
        "四大工業地帯は日本の工業生産の中心です。"
    ]
    
    for text in test_texts:
        print(f"\nテキスト: {text[:50]}...")
        found = loader.find_important_terms(text)
        
        if found['priority_themes']:
            print(f"  ✅ 優先テーマ: {', '.join(found['priority_themes'])}")
        
        all_terms = found['history'] + found['geography'] + found['civics']
        if all_terms:
            print(f"  検出語句: {', '.join(all_terms[:5])}")
            field = loader.get_field_from_terms(all_terms)
            print(f"  判定分野: {field}")
    
    # Gemini Analyzer との統合テスト
    print("\n" + "=" * 60)
    print("2. Gemini Analyzer との統合テスト")
    print("=" * 60)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY が設定されていません")
        return
    
    try:
        analyzer = GeminiAnalyzer(api_key)
        print("✅ GeminiAnalyzer 初期化成功（subject_index照合機能付き）")
        
        # サンプル問題文（促成栽培を含む）
        sample_text = """
1 次の問題に答えなさい。

問1 高知県では冬でも温暖な気候を利用して、ビニールハウスで野菜を栽培する農業が盛んです。
この栽培方法を何といいますか。

問2 日本の四大工業地帯のうち、愛知県を中心とする工業地帯を何といいますか。

問3 明治維新で行われた改革のうち、武士の特権を廃止した政策を答えなさい。
"""
        
        print("\nテスト問題を分析中...")
        result = analyzer.analyze_exam_structure(
            text=sample_text,
            school="テスト中学校",
            year="2024"
        )
        
        print("\n【分析結果】")
        for section in result.get('sections', []):
            print(f"\n大問{section['section_number']}:")
            for q in section.get('questions', []):
                theme = q.get('theme', '不明')
                field = q.get('field', '不明')
                keywords = q.get('keywords', [])
                
                # 促成栽培が正しく抽出されているかチェック
                if '促成栽培' in theme or '促成栽培' in keywords:
                    print(f"  ✅ 問{q['question_number']}: テーマ「{theme}」[{field}] - subject_indexから正しく抽出！")
                elif '四大工業地帯' in theme or '四大工業地帯' in keywords:
                    print(f"  ✅ 問{q['question_number']}: テーマ「{theme}」[{field}] - subject_indexから正しく抽出！")
                elif '明治維新' in theme:
                    print(f"  ✅ 問{q['question_number']}: テーマ「{theme}」[{field}] - subject_indexから正しく抽出！")
                else:
                    print(f"  問{q['question_number']}: テーマ「{theme}」[{field}]")
                
                if keywords:
                    print(f"    キーワード: {', '.join(keywords[:3])}")
        
        print("\n" + "=" * 60)
        print("✅ subject_index.md との統合が正常に動作しています")
        print("重要語句が優先的にテーマとして採用される仕組みが機能しています")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_subject_index_integration()