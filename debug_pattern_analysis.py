#!/usr/bin/env python3
"""
パターンマッチングの詳細分析
なぜ大問パターンが検出されないかを特定
"""

import re
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def analyze_pattern_matching():
    """パターンマッチングの詳細分析"""
    
    # OCRテキストを読み込み
    ocr_file = Path(__file__).parent / "logs" / "ocr_2023_日工大駒場_社会.txt"
    
    with open(ocr_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 実際の大問行を取得
    lines = text.split('\n')
    major_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line and line[0] in '1234１２３４一二三四':
            if '次の' in line or 'を読み' in line or 'について' in line:
                major_lines.append((i+1, line))
    
    logger.info(f"特定された大問行: {len(major_lines)} 件")
    for line_num, line in major_lines:
        logger.info(f"  行{line_num}: '{line}'")
    
    # HierarchicalExtractorのパターンをテスト
    major_patterns = [
        # 四角で囲まれた数字
        (r'□\s*([１-９1-9一-九])\s*□', 'boxed_square'),
        (r'■\s*([１-９1-9一-九])\s*■', 'boxed_filled'),
        (r'▢\s*([１-９1-9一-九])\s*▢', 'boxed_white'),
        (r'▣\s*([１-９1-9一-九])\s*▣', 'boxed_pattern'),
        # 括弧系
        (r'\[\s*([１-９1-9一-九])\s*\]', 'bracket'),
        (r'【\s*([一-九])\s*】', 'thick_bracket'),
        (r'〔\s*([１-９1-9一-九])\s*〕', 'round_bracket'),
        # その他の大問マーカー
        (r'^大問\s*([一-九１-９1-9])', 'daimon'),
        (r'^第([一-九１-９1-9])問', 'dai_mon'),
        (r'^([一-九])[、，]\s*次の', 'kanji_next'),
        # 独立した漢数字（行頭）
        (r'^([一-九])\s', 'standalone_kanji'),
    ]
    
    logger.info("\n=== パターンマッチング結果 ===")
    
    for pattern_str, marker_type in major_patterns:
        logger.info(f"\nパターン: {pattern_str} ({marker_type})")
        
        # 行単位でテスト
        matches_per_line = []
        for line_num, line in major_lines:
            matches = list(re.finditer(pattern_str, line, re.MULTILINE))
            if matches:
                matches_per_line.append((line_num, line, matches))
        
        if matches_per_line:
            logger.info(f"  ✓ マッチ: {len(matches_per_line)} 行")
            for line_num, line, matches in matches_per_line:
                for match in matches:
                    logger.info(f"    行{line_num}: '{match.group()}' in '{line}'")
        else:
            logger.info(f"  ✗ マッチなし")
    
    # 新しいパターンを試す
    logger.info("\n=== 新しいパターンのテスト ===")
    
    # 行頭の数字+空白+次の
    new_patterns = [
        (r'^([1-4])\s+次の', 'number_space_tsugi'),
        (r'^([１-４])\s+次の', 'fullwidth_space_tsugi'),
        (r'^([一-四])\s+次の', 'kanji_space_tsugi'),
        (r'^([1-4])\s*次の', 'number_optional_space_tsugi'),
        (r'^([1-4])\s', 'simple_number_space'),
    ]
    
    for pattern_str, marker_type in new_patterns:
        logger.info(f"\nテストパターン: {pattern_str} ({marker_type})")
        
        matches_per_line = []
        for line_num, line in major_lines:
            matches = list(re.finditer(pattern_str, line, re.MULTILINE))
            if matches:
                matches_per_line.append((line_num, line, matches))
        
        if matches_per_line:
            logger.info(f"  ✓ マッチ: {len(matches_per_line)} 行")
            for line_num, line, matches in matches_per_line:
                for match in matches:
                    logger.info(f"    行{line_num}: '{match.group()}' in '{line}'")
        else:
            logger.info(f"  ✗ マッチなし")
    
    # 全体的なマッチングも確認
    logger.info("\n=== 全文でのマッチング確認 ===")
    
    working_pattern = r'^([1-4])\s+次の'
    all_matches = list(re.finditer(working_pattern, text, re.MULTILINE))
    logger.info(f"全文での '{working_pattern}' マッチ: {len(all_matches)} 件")
    
    for i, match in enumerate(all_matches):
        start_line = text[:match.start()].count('\n') + 1
        context = text[match.start():match.end()+50].replace('\n', ' ')
        logger.info(f"  {i+1}. 行{start_line}: '{context}...'")

if __name__ == "__main__":
    analyze_pattern_matching()