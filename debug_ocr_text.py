#!/usr/bin/env python3
"""
OCRテキストのデバッグ用スクリプト
実際の大問構造を確認
"""

import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.ocr_handler import OCRHandler

def analyze_ocr_text():
    """OCRテキストを分析して大問構造を確認"""
    
    pdf_path = '/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf'
    
    print("=" * 60)
    print("日本工業大学駒場中学校 2023年 社会 - OCR分析")
    print("=" * 60)
    
    # OCRテキストを取得
    ocr = OCRHandler()
    text = ocr.extract_text_from_pdf(pdf_path)
    
    if not text:
        print("エラー: OCRテキストを取得できませんでした")
        return
    
    print(f"\n総文字数: {len(text)}")
    
    # 大問マーカーを探す
    print("\n【大問マーカー検索】")
    
    # パターン1: シンプルな数字+次の
    pattern1 = re.compile(r'^([1-5])\s+次の', re.MULTILINE)
    matches1 = list(pattern1.finditer(text))
    print(f"\nパターン '1 次の' 形式: {len(matches1)}個")
    for m in matches1[:10]:
        start = max(0, m.start() - 20)
        end = min(len(text), m.end() + 50)
        context = text[start:end].replace('\n', ' ')
        print(f"  大問{m.group(1)}: ...{context}...")
    
    # パターン2: OCRエラー（13 -> 3など）
    pattern2 = re.compile(r'^1([1-5])\s+次の', re.MULTILINE)
    matches2 = list(pattern2.finditer(text))
    print(f"\nパターン '1X 次の' (OCRエラー): {len(matches2)}個")
    for m in matches2[:10]:
        actual_num = m.group(1)
        start = max(0, m.start() - 20)
        end = min(len(text), m.end() + 50)
        context = text[start:end].replace('\n', ' ')
        print(f"  大問{actual_num}（OCR: 1{actual_num}）: ...{context}...")
    
    # パターン3: 問X形式
    pattern3 = re.compile(r'問\s*([０-９0-9]+)', re.MULTILINE)
    matches3 = list(pattern3.finditer(text))
    print(f"\nパターン '問X' 形式: {len(matches3)}個")
    
    # 各大問の問題数をカウント
    print("\n【大問ごとの問題数カウント】")
    
    # 大問の位置を特定
    large_sections = []
    for m in matches1:
        large_sections.append(('normal', int(m.group(1)), m.start()))
    for m in matches2:
        large_sections.append(('ocr_error', int(m.group(1)), m.start()))
    
    # ソート
    large_sections.sort(key=lambda x: x[2])
    
    # 各大問内の問題をカウント
    for i, (type_, num, pos) in enumerate(large_sections):
        # 次の大問までの範囲
        if i < len(large_sections) - 1:
            next_pos = large_sections[i + 1][2]
        else:
            next_pos = len(text)
        
        section_text = text[pos:next_pos]
        
        # この大問内の「問」をカウント
        questions = re.findall(r'問\s*([０-９0-9]+)', section_text)
        unique_questions = set(questions)
        
        print(f"\n大問{num} ({type_}):")
        print(f"  位置: {pos}")
        print(f"  問題数: {len(unique_questions)}問")
        if unique_questions:
            # 番号を正規化してソート
            def normalize(q):
                # 全角を半角に
                q = q.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
                return int(q) if q.isdigit() else 0
            
            sorted_q = sorted(unique_questions, key=normalize)
            print(f"  問題番号: {', '.join(sorted_q[:20])}")
            if len(sorted_q) > 20:
                print(f"  ... 他{len(sorted_q) - 20}問")
    
    # 受験番号欄の誤認識チェック
    print("\n【受験番号欄の誤認識チェック】")
    patterns_to_check = [
        (r'受験番号', '受験番号'),
        (r'氏\s*名', '氏名'),
        (r'得\s*点', '得点'),
        (r'採\s*点', '採点'),
    ]
    
    for pattern, label in patterns_to_check:
        matches = re.findall(pattern, text)
        if matches:
            print(f"  {label}: {len(matches)}回出現")
            # 最後の出現位置を確認
            last_match = list(re.finditer(pattern, text))[-1]
            pos = last_match.start()
            context = text[max(0, pos-50):min(len(text), pos+100)].replace('\n', ' ')
            print(f"    最後の出現: ...{context}...")
    
    # 実際の最後の部分を確認
    print("\n【テキストの最後の500文字】")
    print(text[-500:])

if __name__ == "__main__":
    analyze_ocr_text()