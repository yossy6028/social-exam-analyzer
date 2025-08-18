#!/usr/bin/env python3
"""
実際のファイルで年度抽出をテスト
"""
import sys
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

def _extract_year_from_filename(filename: str) -> Optional[int]:
    """
    ファイル名から年度を抽出
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

def extract_school_name(filename: str) -> str:
    """学校名を抽出（年度情報を除去）"""
    school_name = filename
    # 年度パターンを削除（「度」も含めて削除）
    school_name = re.sub(r'20\d{2}年度?', '', school_name)
    school_name = re.sub(r'令和\d+年度?', '', school_name)
    school_name = re.sub(r'R\d+年?度?', '', school_name)
    school_name = re.sub(r'平成\d+年度?', '', school_name)
    school_name = re.sub(r'H\d+年?度?', '', school_name)
    school_name = re.sub(r'\d{2}年度?', '', school_name)
    # 前後の不要な文字（アンダースコア、ハイフン、スペース）を削除
    school_name = re.sub(r'^[_\-\s]+', '', school_name)
    school_name = re.sub(r'[_\-\s]+$', '', school_name)
    # アンダースコアで分割して最初の部分を取得
    school_name = school_name.split('_')[0] if '_' in school_name else school_name
    # 「問題」で分割して学校名部分のみ取得
    school_name = school_name.split('問題')[0] if '問題' in school_name else school_name
    # 最終的なクリーンアップ
    school_name = school_name.strip()
    return school_name

def main():
    # テスト対象のファイル
    test_file = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf"
    
    if Path(test_file).exists():
        print("=" * 60)
        print("実際のファイルでの年度・学校名抽出テスト")
        print("=" * 60)
        
        filename = Path(test_file).stem
        print(f"ファイル名: {filename}")
        print()
        
        # 年度抽出
        year = _extract_year_from_filename(filename)
        print(f"抽出された年度: {year}")
        if year == 2023:
            print("✅ 年度抽出成功！")
        else:
            print(f"❌ 年度抽出失敗（期待値: 2023）")
        
        print()
        
        # 学校名抽出
        school_name = extract_school_name(filename)
        print(f"抽出された学校名: {school_name}")
        if school_name == "日本工業大学駒場中学校":
            print("✅ 学校名抽出成功！")
        else:
            print(f"❌ 学校名抽出失敗（期待値: 日本工業大学駒場中学校）")
        
        print()
        print("=" * 60)
        print("【結論】")
        if year == 2023 and school_name == "日本工業大学駒場中学校":
            print("✅ ファイル名からの自動抽出機能は正常に動作しています！")
            print("→ GUIで「2023年日本工業大学駒場中学校問題_社会.pdf」を選択すると")
            print("  年度欄に「2023」、学校名欄に「日本工業大学駒場中学校」が")
            print("  自動的に入力されます。")
        else:
            print("⚠️ 抽出に問題があります。修正が必要です。")
        print("=" * 60)
    else:
        print(f"テストファイルが見つかりません: {test_file}")
        print("\n代替テストケース:")
        
        # いくつかのパターンをテスト
        test_cases = [
            "2023年日本工業大学駒場中学校問題_社会",
            "2025年開成中学校問題_国語",
            "令和5年度_麻布中学校",
            "平成31年度_筑波大学附属駒場中学校",
        ]
        
        for filename in test_cases:
            year = _extract_year_from_filename(filename)
            school = extract_school_name(filename)
            print(f"\n{filename}")
            print(f"  → 年度: {year}, 学校名: {school}")

if __name__ == "__main__":
    main()