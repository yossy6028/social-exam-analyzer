#!/usr/bin/env python3
"""
最終統合テスト
"""

import logging
logging.basicConfig(level=logging.INFO)

from modules.enhanced_theme_extractor import EnhancedThemeExtractor

def test_theme_extraction():
    """テーマ抽出の修正を確認"""
    extractor = EnhancedThemeExtractor()
    
    test_cases = [
        ("兵庫県明について", "歴史"),
        ("真鍋淑郎氏がノーベル賞を受賞", "歴史"),
        ("日宋貿易について", "歴史"),
        ("朱子学以外の学問", "歴史"),
        ("新詳日本史について", "歴史"),
        ("宣戦布告について", "歴史"),
        ("刑事事件について", "歴史"),
        ("太平洋地域について", "歴史"),
        ("社会保障制度について", "歴史"),
        ("新聞記事について", "歴史"),
    ]
    
    print("=== テーマ抽出テスト ===\n")
    
    for text, field in test_cases:
        result = extractor.extract_theme(text, field=field)
        theme = result.get('theme', 'なし')
        
        # 「業績」が含まれているかチェック
        if '業績' in theme:
            print(f"❌ {text[:20]:20} → {theme} (業績が残っている)")
        else:
            print(f"✅ {text[:20]:20} → {theme}")
    
    print("\n" + "="*50 + "\n")

def test_question_structure():
    """問題構造の検出を確認"""
    from modules.improved_question_extractor_v2 import ImprovedQuestionExtractorV2
    
    # より実際に近いサンプル
    sample = """
社会

1　次の地図を見て、各問いに答えなさい。
(1) 雨温図について
(2) 野菜栽培について
(3) 地形図について
(4) 津久井湖について
(5) 河川について
(6) 地形図の記号について
(7) 地形図の読み取りについて
(8) 川の流れについて
(9) 農業について
(10) 山地について
(11) 気候について

2　次の年表を見て、各問いに答えなさい。
(1) 平野について
(2) リサイクルについて
(3) 明治時代について
(4) 歴史の流れについて
(5) 兵庫県について
(6) 平等院について
(7) 工業について
(8) 日宋貿易について
(9) 鎌倉時代について
(10) 歴史年表について
(11) 文化について
(12) 歴史人物について
(13) 新聞記事について
"""
    
    extractor = ImprovedQuestionExtractorV2()
    questions = extractor.extract_questions(sample)
    
    print("=== 問題構造テスト ===\n")
    print(f"総問題数: {len(questions)}")
    
    # 大問ごとにカウント
    by_major = {}
    for q_id, _ in questions:
        if "大問" in q_id:
            parts = q_id.split("-")
            major = parts[0] if parts else q_id
            if major not in by_major:
                by_major[major] = 0
            by_major[major] += 1
    
    for major in sorted(by_major.keys()):
        print(f"{major}: {by_major[major]}問")
    
    expected = {"大問1": 11, "大問2": 13}
    for major, expected_count in expected.items():
        actual_count = by_major.get(major, 0)
        if actual_count == expected_count:
            print(f"  ✅ {major}: {actual_count}問 (正解)")
        else:
            print(f"  ❌ {major}: {actual_count}問 (期待値: {expected_count})")

if __name__ == "__main__":
    test_theme_extraction()
    test_question_structure()