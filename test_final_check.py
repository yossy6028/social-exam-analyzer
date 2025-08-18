#!/usr/bin/env python3
"""
最終動作確認テスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from analyze_with_gemini_detailed import GeminiDetailedAnalyzer

def final_check():
    """最終確認テスト（最初の10問のみ）"""
    
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf"
    
    analyzer = GeminiDetailedAnalyzer()
    
    print("=" * 60)
    print("最終動作確認（問題1-10のみ）")
    print("=" * 60)
    print()
    
    # OCR処理
    print("PDFからテキスト抽出中...")
    from modules.ocr_handler import OCRHandler
    ocr_handler = OCRHandler()
    text = ocr_handler.process_pdf(pdf_path)
    
    if not text:
        print("テキスト抽出失敗")
        return
    
    print(f"✅ {len(text)}文字を抽出\n")
    
    # 問題抽出（最初の10問のみ）
    print("問題を抽出中...")
    questions = analyzer.extract_questions_from_text(text)[:10]
    
    print(f"✅ {len(questions)}問を検出（最初の10問のみ）\n")
    
    # 各問題を分析
    print("各問題を分析中...\n")
    
    underline_count = 0
    for i, q in enumerate(questions, 1):
        result = analyzer.analyze_single_question(q)
        
        number = q.get('number', f'問{i}')
        theme = result.get('theme', '未設定')
        field = result.get('field', '不明')
        q_format = result.get('question_format', '不明')
        
        # 「下線部」が残っているかチェック
        if "下線部" in theme:
            underline_count += 1
            print(f"⚠️ {number}: テーマ: {theme} | ジャンル: {field} | 形式: {q_format}")
        else:
            print(f"✅ {number}: テーマ: {theme} | ジャンル: {field} | 形式: {q_format}")
    
    print()
    print("=" * 60)
    print("【結果サマリー】")
    print(f"総問題数: {len(questions)}問")
    print(f"下線部参照が残っている問題: {underline_count}問")
    
    if underline_count == 0:
        print("✅ すべての問題で下線部参照が解決されました！")
    else:
        print(f"⚠️ {underline_count}問で下線部参照が残っています")
    
    print("=" * 60)

if __name__ == "__main__":
    final_check()