#!/usr/bin/env python3
"""
OCRテキストの構造を詳しく分析
"""

import re

def debug_ocr_structure():
    """OCRテキストの構造を詳しく分析"""
    
    print("=== OCRテキストの構造詳細分析 ===\n")
    
    # 実際のOCRテキストファイルを読み込み
    ocr_file = "logs/ocr_2023_日工大駒場_社会.txt"
    
    try:
        with open(ocr_file, 'r', encoding='utf-8') as f:
            ocr_text = f.read()
    except FileNotFoundError:
        print(f"❌ OCRファイルが見つかりません: {ocr_file}")
        return
    
    print(f"📁 OCRファイル: {ocr_file}")
    print(f"📊 ファイルサイズ: {len(ocr_text)} 文字")
    
    # 行ごとの詳細分析
    lines = ocr_text.split('\n')
    print(f"📝 行数: {len(lines)} 行")
    
    print("\n" + "="*50)
    print("大問開始パターンの詳細分析:")
    
    # 大問開始の可能性がある行を特定
    major_candidates = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # 大問開始の可能性があるパターン
        if re.match(r'^\d+\s*次の', line):
            major_candidates.append((i, line))
        elif re.match(r'^\d+\s*$', line):
            # 単独の数字の行
            major_candidates.append((i, line))
    
    print("大問開始の候補:")
    for i, (line_num, line) in enumerate(major_candidates):
        print(f"  {i+1}. 行{line_num}: {line}")
    
    print("\n" + "="*50)
    print("小問パターンの詳細分析:")
    
    # 小問の詳細分析
    question_lines = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        if re.match(r'問\s*\d+', line):
            question_lines.append((i, line))
    
    print("小問の行:")
    for i, (line_num, line) in enumerate(question_lines):
        print(f"  {i+1}. 行{line_num}: {line[:80]}...")
    
    print("\n" + "="*50)
    print("大問境界の手動判定:")
    
    # 大問境界を手動で判定
    major_boundaries = []
    current_major = None
    current_questions = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # 大問の開始を検出
        major_match = re.match(r'^(\d+)\s*(?:次の|下記の|以下の)', line)
        if major_match:
            if current_major:
                major_boundaries.append((current_major, current_questions))
                print(f"大問{current_major}終了: {len(current_questions)}問")
            
            current_major = major_match.group(1)
            current_questions = []
            print(f"\n大問{current_major}開始: {line}")
        
        # 小問を検出
        question_match = re.match(r'問\s*(\d+)', line)
        if question_match and current_major:
            question_num = question_match.group(1)
            current_questions.append(question_num)
            print(f"  小問{question_num}: {line[:50]}...")
    
    # 最後の大問を追加
    if current_major:
        major_boundaries.append((current_major, current_questions))
        print(f"\n大問{current_major}終了: {len(current_questions)}問")
    
    print(f"\n検出された大問構造:")
    for major, questions in major_boundaries:
        print(f"大問{major}: {len(questions)}問 - {questions}")
    
    print("\n" + "="*50)
    print("問題抽出器のパターンマッチングテスト:")
    
    # 問題抽出器のパターンをテスト
    major_patterns = [
        re.compile(r'^(\d+)\s*次の各問いに答えなさい。', re.MULTILINE),
        re.compile(r'^(\d+)\s*次の年表を見て', re.MULTILINE),
        re.compile(r'^(\d+)\s*次の表は', re.MULTILINE),
        re.compile(r'^(\d+)\s*次の図は', re.MULTILINE),
        re.compile(r'^(\d+)\s*(?:次の|下記の|以下の)', re.MULTILINE),
        re.compile(r'^(\d+)\s*$', re.MULTILINE),
    ]
    
    for i, pattern in enumerate(major_patterns, 1):
        matches = list(pattern.finditer(ocr_text))
        print(f"パターン {i}: {pattern.pattern}")
        for match in matches:
            # マッチした行の前後の文脈を表示
            start = max(0, match.start() - 100)
            end = min(len(ocr_text), match.end() + 100)
            context = ocr_text[start:end]
            print(f"  マッチ: '{match.group(0)}' (位置 {match.start()})")
            print(f"    文脈: ...{context}...")

if __name__ == "__main__":
    debug_ocr_structure()
