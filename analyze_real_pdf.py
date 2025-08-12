#\!/usr/bin/env python3
"""
実際のPDF OCRテキストを分析
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.social_analyzer_fixed import FixedSocialAnalyzer
from modules.ocr_handler import OCRHandler

# PDFファイルを処理
pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/東京電機大学中学校/2023年東京電機大学中学校問題_社会.pdf"

# OCRでテキスト抽出
ocr_handler = OCRHandler()
ocr_text = ocr_handler.extract_text(pdf_path)

if ocr_text:
    # 最初の2000文字を表示
    print("=== OCRテキスト（最初の2000文字）===")
    print(ocr_text[:2000])
    print("\n...")
    
    # 問題を検索
    import re
    
    # 問題番号パターン
    pattern = re.compile(r'問\s*[０-９\d]+')
    matches = pattern.findall(ocr_text)
    
    print(f"\n検出された問題番号: {len(matches)}個")
    print(f"最初の10個: {matches[:10]}")
    
    # 大問パターン
    major_pattern = re.compile(r'^\s*[1-9]\s*[\.。]\s*', re.MULTILINE)
    major_matches = major_pattern.findall(ocr_text)
    
    print(f"\n検出された大問: {len(major_matches)}個")
    print(f"パターン: {major_matches[:5]}")
else:
    print("OCRテキストが抽出できませんでした")
