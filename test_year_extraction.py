#!/usr/bin/env python3
"""
年度抽出機能のテスト
"""
import re
from datetime import datetime
from typing import Optional

def _extract_year_from_filename(filename: str) -> Optional[int]:
    """
    ファイル名から年度を抽出
    
    対応パターン:
    - 2023年、2023
    - 令和5年、令和5、R5
    - 平成31年、平成31、H31
    - 23年（2000年代として解釈）
    """
    # 現在の年を取得（上限チェック用）
    current_year = datetime.now().year
    
    # 1. 4桁の西暦年（2020年、2020など）
    match = re.search(r'(20\d{2})年?', filename)
    if match:
        year = int(match.group(1))
        if 2000 <= year <= current_year + 1:  # 未来の入試問題も考慮
            return year
    
    # 2. 令和年号（令和5年、令和5、R5など）
    match = re.search(r'令和(\d+)年?', filename)
    if match:
        reiwa_year = int(match.group(1))
        return 2018 + reiwa_year  # 令和元年 = 2019年
    
    match = re.search(r'R(\d+)年?', filename)
    if match:
        reiwa_year = int(match.group(1))
        return 2018 + reiwa_year
    
    # 3. 平成年号（平成31年、平成31、H31など）
    match = re.search(r'平成(\d+)年?', filename)
    if match:
        heisei_year = int(match.group(1))
        return 1988 + heisei_year  # 平成元年 = 1989年
    
    match = re.search(r'H(\d+)年?', filename)
    if match:
        heisei_year = int(match.group(1))
        return 1988 + heisei_year
    
    # 4. 2桁の年（23年など）- 2000年代として解釈
    match = re.search(r'(\d{2})年', filename)
    if match:
        two_digit_year = int(match.group(1))
        # 00-99の範囲で、現在の年の下2桁より大きければ1900年代、そうでなければ2000年代
        current_two_digit = current_year % 100
        if two_digit_year <= current_two_digit + 1:
            return 2000 + two_digit_year
        elif two_digit_year >= 90:  # 90年代は1990年代と解釈
            return 1900 + two_digit_year
        else:
            return 2000 + two_digit_year
    
    # 年度が見つからない場合はNoneを返す
    return None

def test_year_extraction():
    """年度抽出テスト"""
    print("=" * 60)
    print("年度抽出機能テスト")
    print("=" * 60)
    
    # テストケース
    test_cases = [
        # 西暦4桁
        ("2023年日本工業大学駒場中学校問題_社会.pdf", 2023),
        ("2025年開成中学校問題_国語.pdf", 2025),
        ("開成中学校_2024.pdf", 2024),
        ("2020年東京電機大学中学校問題_社会.pdf", 2020),
        
        # 令和
        ("令和5年度入試問題.pdf", 2023),
        ("R5_麻布中学校.pdf", 2023),
        ("令和6年桜蔭中学校.pdf", 2024),
        ("R4年度_武蔵中学校.pdf", 2022),
        
        # 平成
        ("平成31年度入試.pdf", 2019),
        ("H31_慶應中等部.pdf", 2019),
        ("平成30年早稲田実業.pdf", 2018),
        
        # 2桁年
        ("23年筑駒入試.pdf", 2023),
        ("25年度入試予想問題.pdf", 2025),
        ("99年過去問.pdf", 1999),
        
        # 年度なし
        ("開成中学校入試問題.pdf", None),
        ("社会科入試分析.pdf", None),
    ]
    
    passed = 0
    failed = 0
    
    for filename, expected in test_cases:
        result = _extract_year_from_filename(filename)
        if result == expected:
            print(f"✅ {filename:40} → {result}")
            passed += 1
        else:
            print(f"❌ {filename:40} → {result} (期待値: {expected})")
            failed += 1
    
    # 学校名抽出のテスト（年度を除去）
    print("\n" + "=" * 60)
    print("学校名抽出テスト（年度除去後）")
    print("=" * 60)
    
    school_test_cases = [
        ("2023年日本工業大学駒場中学校問題_社会", "日本工業大学駒場中学校"),
        ("令和5年開成中学校_国語", "開成中学校_国語"),
        ("R5_麻布中学校", "_麻布中学校"),
        ("平成31年度_筑波大学附属駒場中学校", "度_筑波大学附属駒場中学校"),
    ]
    
    for original, expected_pattern in school_test_cases:
        # 年度パターンを削除
        school_name = original
        school_name = re.sub(r'20\d{2}年?', '', school_name)
        school_name = re.sub(r'令和\d+年?', '', school_name)
        school_name = re.sub(r'R\d+年?', '', school_name)
        school_name = re.sub(r'平成\d+年?', '', school_name)
        school_name = re.sub(r'H\d+年?', '', school_name)
        school_name = re.sub(r'\d{2}年', '', school_name)
        # 前後の不要な文字を削除
        school_name = re.sub(r'^[_\-\s]+|[_\-\s]+$', '', school_name)
        school_name = school_name.split('_')[0] if '_' in school_name else school_name
        school_name = school_name.split('問題')[0] if '問題' in school_name else school_name
        
        print(f"  {original:40} → {school_name}")
    
    print("\n" + "=" * 60)
    print(f"テスト結果: {passed}/{passed+failed} 成功")
    if failed == 0:
        print("✅ すべてのテストに合格しました！")
    else:
        print(f"⚠️ {failed}件のテストが失敗しました")
    print("=" * 60)

if __name__ == "__main__":
    test_year_extraction()