#!/usr/bin/env python3
"""
修正後のテスト
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
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_fix():
    """修正後のテスト"""
    
    # OCRテキストを読み込み
    ocr_file = project_root / "logs" / "ocr_2023_日工大駒場_社会.txt"
    
    with open(ocr_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    logger.info(f"OCRテキスト読み込み: {len(text)} 文字")
    
    # HierarchicalExtractorの修正後テスト
    logger.info("=== 修正後の HierarchicalExtractor テスト ===")
    extractor = HierarchicalExtractor()
    
    try:
        structure = extractor.extract_structure(text)
        logger.info(f"抽出された大問数: {len(structure)}")
        
        for i, major in enumerate(structure):
            logger.info(f"大問{major.number}: マーカー={major.marker_type}")
            logger.info(f"  位置: {major.position}")
            logger.info(f"  テキスト: {major.text[:100]}...")
            logger.info(f"  子問題数: {len(major.children)}")
            
            # 各大問の最初の数問を表示
            for j, question in enumerate(major.children[:5]):
                logger.info(f"    問{question.number}: {question.text[:50]}...")
        
        # カウント表示
        counts = extractor.count_all_questions(structure)
        logger.info(f"問題数: 大問{counts['major']}, 問{counts['question']}, 小問{counts['subquestion']}, 合計{counts['total']}")
        
    except Exception as e:
        logger.error(f"構造抽出エラー: {e}", exc_info=True)
    
    # ImprovedQuestionExtractorV2の修正後テスト
    logger.info("\n=== 修正後の ImprovedQuestionExtractorV2 テスト ===")
    improved_extractor = ImprovedQuestionExtractorV2()
    
    try:
        questions = improved_extractor.extract_questions(text)
        logger.info(f"抽出された問題数: {len(questions)}")
        
        # 最初の10問を表示
        for i, (q_id, q_text) in enumerate(questions[:10]):
            logger.info(f"  {i+1}. {q_id}: {q_text[:80]}...")
        
        if len(questions) > 10:
            logger.info(f"  ...他 {len(questions) - 10} 問")
        
    except Exception as e:
        logger.error(f"改善版抽出器エラー: {e}", exc_info=True)

if __name__ == "__main__":
    test_fix()