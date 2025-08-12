#!/usr/bin/env python3
"""
問題抽出パターンマッチングのデバッグスクリプト
"""

import re
from modules.ocr_handler import OCRHandler
from modules.social_analyzer_fixed import FixedSocialAnalyzer

def debug_pattern_matching():
    """パターンマッチングの詳細デバッグ"""
    
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2025年日本工業大学駒場中学校問題_社会.pdf"
    
    # OCR処理
    ocr_handler = OCRHandler()
    ocr_text = ocr_handler.process_pdf(pdf_path)
    
    # アナライザーのクリーニング処理
    analyzer = FixedSocialAnalyzer()
    cleaned_text = analyzer._clean_ocr_text(ocr_text)
    
    print("=" * 80)
    print("パターンマッチングデバッグ")
    print("=" * 80)
    
    print(f"\n📄 クリーニング後テキスト全体（{len(cleaned_text)}文字）:")
    print("-" * 60)
    print(cleaned_text[:2000])  # 最初の2000文字
    print("-" * 60)
    
    # 各パターンを個別にテスト
    test_patterns = [
        # パターン1: 大問形式
        (r'^(\d+)\.\\s*次の.*?$', "大問形式"),
        
        # パターン2: 直接問番号
        (r'問(\d+)[^\n]*([\s\S]*?)(?=問\d+|$)', "直接問番号"),
        
        # パターン3: 番号付きセクション
        (r'^(\d+)\.([\\s\\S]*?)(?=^\d+\.|$)', "番号付きセクション"),
        
        # カスタムパターン（実際のテキスト構造に基づく）
        (r'問(\d+)([\s\S]*?)(?=問\d+|$)', "カスタム問番号"),
    ]
    
    for pattern, name in test_patterns:
        print(f"\n🔍 {name} パターンテスト: {pattern}")
        try:
            matches = re.findall(pattern, cleaned_text, re.MULTILINE)
            print(f"   マッチ数: {len(matches)}")
            
            for i, match in enumerate(matches[:3]):  # 最初の3つのみ
                if isinstance(match, tuple):
                    print(f"   マッチ{i+1}: {match[0][:50]}...")
                else:
                    print(f"   マッチ{i+1}: {match[:50]}...")
                    
        except Exception as e:
            print(f"   エラー: {e}")
    
    # 実際のテキストの中で問番号を探す
    print(f"\n🔎 「問」で始まる行を検索:")
    lines = cleaned_text.split('\n')
    question_lines = []
    for i, line in enumerate(lines):
        if '問' in line and re.search(r'問\d+', line):
            question_lines.append((i, line.strip()))
    
    for line_num, line in question_lines[:10]:  # 最初の10行のみ
        print(f"   行{line_num}: {line}")
    
    print(f"\n📊 統計:")
    print(f"   総行数: {len(lines)}")
    print(f"   「問」を含む行数: {len(question_lines)}")
    print(f"   「次の」を含む行数: {len([l for l in lines if '次の' in l])}")

if __name__ == "__main__":
    debug_pattern_matching()