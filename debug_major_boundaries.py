#!/usr/bin/env python3
"""
大問境界の詳細分析
"""

import re

def debug_major_boundaries():
    """大問境界の詳細分析"""
    
    print("=== 大問境界の詳細分析 ===\n")
    
    # 実際のOCRテキストファイルを読み込み
    ocr_file = "logs/ocr_2023_日工大駒場_社会.txt"
    
    try:
        with open(ocr_file, 'r', encoding='utf-8') as f:
            ocr_text = f.read()
    except FileNotFoundError:
        print(f"❌ OCRファイルが見つかりません: {ocr_file}")
        return
    
    print(f"📁 OCRファイル: {ocr_file}")
    
    # 大問開始の可能性がある行を特定
    lines = ocr_text.split('\n')
    
    print("大問開始の候補（詳細）:")
    print("="*50)
    
    major_candidates = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # 大問開始の可能性があるパターン
        if re.match(r'^\d+\s*次の', line):
            major_candidates.append((i, line, "次のパターン"))
        elif re.match(r'^\d+\s*$', line):
            # 単独の数字の行
            major_candidates.append((i, line, "単独数字"))
    
    for i, (line_num, line, pattern_type) in enumerate(major_candidates):
        print(f"  {i+1}. 行{line_num}: {line} ({pattern_type})")
        
        # 前後の文脈を表示
        start_line = max(0, line_num - 2)
        end_line = min(len(lines), line_num + 3)
        
        print(f"     前後の文脈:")
        for j in range(start_line, end_line):
            marker = "→ " if j == line_num else "   "
            print(f"     {marker}行{j}: {lines[j][:80]}...")
        print()
    
    print("="*50)
    print("期待される大問構造:")
    print("大問1: 地理分野（農業・工業）")
    print("大問2: 歴史分野（年表）")
    print("大問3: 公民分野（憲法・人権）")
    
    print("\n" + "="*50)
    print("実際の大問開始位置の分析:")
    
    # 実際の大問開始位置を特定
    actual_majors = []
    
    # 大問1の開始
    major1_start = None
    for i, line in enumerate(lines):
        if "1 次の各問いに答えなさい。" in line:
            major1_start = i
            break
    
    if major1_start is not None:
        print(f"大問1開始: 行{major1_start}")
        actual_majors.append(("大問1", major1_start))
    
    # 大問2の開始（年表）
    major2_start = None
    for i, line in enumerate(lines):
        if "2 次の年表を見て" in line:
            major2_start = i
            break
    
    if major2_start is not None:
        print(f"大問2開始: 行{major2_start}")
        actual_majors.append(("大問2", major2_start))
    
    # 大問3の開始（表）
    major3_start = None
    for i, line in enumerate(lines):
        if "3 次の表は" in line:
            major3_start = i
            break
    
    if major3_start is not None:
        print(f"大問3開始: 行{major3_start}")
        actual_majors.append(("大問3", major3_start))
    
    print(f"\n検出された大問数: {len(actual_majors)}")
    
    # 大問境界の検証
    if len(actual_majors) >= 2:
        print("\n大問境界の検証:")
        for i in range(len(actual_majors) - 1):
            current_major, current_start = actual_majors[i]
            next_major, next_start = actual_majors[i + 1]
            
            # 大問間の行数を計算
            lines_between = next_start - current_start
            print(f"{current_major} → {next_major}: {lines_between}行")
            
            # 大問間の内容を確認
            print(f"  {current_major}の内容（行{current_start}〜{next_start-1}）:")
            for j in range(current_start, min(current_start + 5, next_start)):
                print(f"    行{j}: {lines[j][:60]}...")

if __name__ == "__main__":
    debug_major_boundaries()
