#!/usr/bin/env python3
"""
問題検出の詳細デバッグ
1問しか検出されない原因を特定
"""

import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.improved_question_extractor_v2 import ImprovedQuestionExtractorV2
from patterns.hierarchical_extractor import HierarchicalExtractor

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def debug_question_extraction():
    """問題抽出のデバッグ"""
    
    # OCRテキストを読み込み
    ocr_file = project_root / "logs" / "ocr_2023_日工大駒場_社会.txt"
    
    if not ocr_file.exists():
        logger.error(f"OCRファイルが見つかりません: {ocr_file}")
        return
    
    with open(ocr_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    logger.info(f"OCRテキスト読み込み完了: {len(text)} 文字")
    
    # Step 1: HierarchicalExtractorの直接テスト
    logger.info("=== Step 1: HierarchicalExtractor直接テスト ===")
    extractor = HierarchicalExtractor()
    
    # パターンマッチングの詳細確認
    logger.info("大問パターンのマッチを確認:")
    import re
    for pattern, marker_type in extractor.major_patterns:
        matches = list(re.finditer(pattern, text, re.MULTILINE))
        if matches:
            logger.info(f"  {marker_type}: {len(matches)} 件マッチ")
            for i, match in enumerate(matches[:3]):  # 最初の3件
                preview = text[match.end():match.end()+50].replace('\n', ' ')
                logger.info(f"    {i+1}. 位置{match.span()}: '{match.group()}' -> '{preview}...'")
    
    # Step 2: 構造抽出の詳細確認
    logger.info("\n=== Step 2: 構造抽出の詳細確認 ===")
    try:
        structure = extractor.extract_structure(text)
        logger.info(f"抽出された大問数: {len(structure)}")
        
        for i, major in enumerate(structure):
            logger.info(f"大問{i+1}: 番号={major.number}, マーカー={major.marker_type}")
            logger.info(f"  位置: {major.position}")
            logger.info(f"  テキスト: {major.text[:100]}...")
            logger.info(f"  子問題数: {len(major.children)}")
            
            for j, question in enumerate(major.children[:3]):  # 最初の3問
                logger.info(f"    問{j+1}: 番号={question.number}, マーカー={question.marker_type}")
                logger.info(f"      位置: {question.position}")
                logger.info(f"      テキスト: {question.text[:50]}...")
                logger.info(f"      小問数: {len(question.children)}")
    
    except Exception as e:
        logger.error(f"構造抽出でエラー: {e}", exc_info=True)
    
    # Step 3: ImprovedQuestionExtractorV2のテスト
    logger.info("\n=== Step 3: ImprovedQuestionExtractorV2のテスト ===")
    improved_extractor = ImprovedQuestionExtractorV2()
    
    try:
        questions = improved_extractor.extract_questions(text)
        logger.info(f"抽出された問題数: {len(questions)}")
        
        for i, (q_id, q_text) in enumerate(questions):
            logger.info(f"問題{i+1}: {q_id}")
            logger.info(f"  テキスト: {q_text[:100]}...")
    
    except Exception as e:
        logger.error(f"改善版抽出器でエラー: {e}", exc_info=True)
    
    # Step 4: 手動での大問検索
    logger.info("\n=== Step 4: 手動での大問検索 ===")
    
    # 実際のテキストで「問題は、1~4まであります」を確認
    if "1~4まであります" in text:
        logger.info("✓ 確認: 問題は1~4まであることが明記されている")
    
    # 行頭の数字パターンを検索
    lines = text.split('\n')
    major_candidates = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line and line[0] in '1234１２３４一二三四':
            if '次の' in line or 'を読み' in line or 'について' in line:
                major_candidates.append((i+1, line))
    
    logger.info(f"大問候補: {len(major_candidates)} 件")
    for line_num, line in major_candidates:
        logger.info(f"  行{line_num}: {line[:80]}...")
    
    # Step 5: 問パターンの検索
    logger.info("\n=== Step 5: 問パターンの検索 ===")
    problem_pattern = re.compile(r'問\s*([０-９0-9]+)')
    problem_matches = list(problem_pattern.finditer(text))
    
    logger.info(f"「問N」パターンのマッチ: {len(problem_matches)} 件")
    for i, match in enumerate(problem_matches[:10]):  # 最初の10件
        context = text[max(0, match.start()-20):match.end()+50].replace('\n', ' ')
        logger.info(f"  {i+1}. {match.group()} at {match.span()}: ...{context}...")

if __name__ == "__main__":
    debug_question_extraction()