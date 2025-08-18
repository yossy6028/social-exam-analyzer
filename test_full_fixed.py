#!/usr/bin/env python3
"""
完全修正版のテスト
"""

import sys
import logging
from pathlib import Path

# ロギング設定
logging.basicConfig(level=logging.INFO)

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def main():
    # PDFファイルパス
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf"
    
    # OCR処理
    from modules.ocr_handler import OCRHandler
    ocr = OCRHandler()
    print("PDFをOCR処理中...")
    text = ocr.process_pdf(pdf_path)
    
    # 分析器を初期化
    from modules.social_analyzer_fixed import FixedSocialAnalyzer
    analyzer = FixedSocialAnalyzer()
    
    # 分析実行
    print("分析中...")
    results = analyzer.analyze_document(text)
    
    # 問題構造を表示
    questions = results.get('questions', [])
    print(f"\n総問題数: {len(questions)}")
    
    # 大問ごとにカウント
    by_major = {}
    for q in questions:
        q_id = q.get('number', '')
        if "大問" in q_id:
            parts = q_id.split("-")
            major = parts[0] if parts else q_id
            if major not in by_major:
                by_major[major] = []
            by_major[major].append(q)
    
    print("\n=== 各大問の問題数 ===")
    for major in sorted(by_major.keys()):
        print(f"{major}: {len(by_major[major])}問")
    
    print("\n=== テーマのサンプル（業績チェック）===")
    # 「業績」を含むテーマを探す
    gyoseki_count = 0
    for q in questions:
        topic = q.get('topic', '')
        if '業績' in topic:
            gyoseki_count += 1
            print(f"  ❌ {q.get('number', '')}: {topic}")
    
    if gyoseki_count == 0:
        print("  ✅ 「業績」を含むテーマはありません！")
    else:
        print(f"  ❌ {gyoseki_count}個の「業績」テーマが残っています")
    
    # 特定のテーマを確認
    print("\n=== 特定テーマの確認 ===")
    check_keywords = ['真鍋', '兵庫', '日宋', '朱子', '宣戦']
    for q in questions:
        topic = q.get('topic', '')
        for keyword in check_keywords:
            if keyword in topic:
                print(f"  {q.get('number', '')}: {topic}")
                break

if __name__ == "__main__":
    main()