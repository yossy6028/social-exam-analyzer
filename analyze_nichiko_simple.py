#!/usr/bin/env python3
"""
日本工業大学駒場中学校2023年社会科PDFの簡易分析
OCRテキストを直接分析
"""

import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.ocr_handler import OCRHandler
from modules.social_analyzer import SocialAnalyzer

def simple_analyze():
    """シンプルな分析"""
    
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf"
    
    print("=" * 80)
    print("日本工業大学駒場中学校 2023年度 社会科 - 簡易分析")
    print("=" * 80)
    print()
    
    # OCRハンドラーの初期化
    ocr_handler = OCRHandler()
    
    # PDFからテキスト抽出
    print("【OCRテキスト抽出】")
    text = ocr_handler.process_pdf(pdf_path)
    
    if not text:
        print("❌ テキスト抽出失敗")
        return
    
    print(f"✅ {len(text)}文字を抽出")
    print()
    
    # テキストを表示して問題を確認
    print("【抽出されたテキスト（最初の2000文字）】")
    print("-" * 80)
    print(text[:2000])
    print("-" * 80)
    print()
    
    # 簡単なパターンで問題を抽出
    print("【問題の抽出（簡易パターン）】")
    
    # 問題パターン
    patterns = [
        r'問\s*(\d+)[^\d]',  # 問1, 問2など
        r'問\s*([一二三四五六七八九十]+)',  # 問一, 問二など
        r'\(\s*(\d+)\s*\)',  # (1), (2)など
        r'[①②③④⑤⑥⑦⑧⑨⑩]',  # 丸数字
    ]
    
    found_questions = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            print(f"  パターン '{pattern}' で {len(matches)} 個の問題番号を発見")
            found_questions.extend(matches[:10])  # 最初の10個まで
    
    print()
    
    # テキストを行で分割して問題を探す
    print("【行ベースでの問題検出】")
    lines = text.split('\n')
    question_lines = []
    
    for i, line in enumerate(lines):
        if '問' in line and len(line) < 200:  # 問を含む短い行
            question_lines.append((i, line.strip()))
    
    print(f"'問'を含む行: {len(question_lines)}行")
    for idx, (line_num, line) in enumerate(question_lines[:20]):  # 最初の20行
        print(f"  L{line_num:4d}: {line[:80]}...")
    
    print()
    
    # 実際の問題文を抽出（問1から問10まで）
    print("【問題文の抽出】")
    questions = []
    
    for i in range(1, 11):  # 問1から問10まで
        pattern = rf'問\s*{i}\s*([^問]+?)(?=問\s*\d+|$)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            q_text = match.group(1).strip()[:200]  # 最初の200文字
            questions.append((f"問{i}", q_text))
    
    if questions:
        print(f"抽出された問題: {len(questions)}問")
        for q_num, q_text in questions[:5]:  # 最初の5問
            print(f"\n  {q_num}:")
            print(f"    {q_text[:150]}...")
    else:
        print("問題が抽出できませんでした")
    
    print()
    
    # 社会科分析器で分析
    print("【社会科分析】")
    analyzer = SocialAnalyzer()
    
    if questions:
        for q_num, q_text in questions[:5]:  # 最初の5問を分析
            result = analyzer.analyze_question(q_text, q_num)
            
            field = result.field.value if hasattr(result.field, 'value') else str(result.field)
            theme = result.theme if result.theme else "（テーマ未設定）"
            keywords = ', '.join(result.keywords[:3]) if result.keywords else "（キーワードなし）"
            
            print(f"\n  {q_num}:")
            print(f"    分野: {field}")
            print(f"    テーマ: {theme}")
            print(f"    キーワード: {keywords}")
    
    print()
    
    # 大問構造を探す
    print("【大問構造の検出】")
    major_patterns = [
        r'[1-4]\s+次の',  # "1 次の"
        r'第[1-4]問',  # "第1問"
        r'[１２３４]\s*[．.]',  # "１．"
    ]
    
    for pattern in major_patterns:
        matches = re.findall(pattern, text)
        if matches:
            print(f"  パターン '{pattern}' で {len(matches)} 個の大問を発見")
            for match in matches[:5]:
                print(f"    {match}")
    
    print()
    print("=" * 80)
    print("簡易分析完了")
    print("=" * 80)

if __name__ == "__main__":
    simple_analyze()