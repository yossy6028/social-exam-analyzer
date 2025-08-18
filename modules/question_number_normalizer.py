"""
問題番号の正規化モジュール
OCRエラーによる重複や誤認識を修正
"""
import re
import logging

logger = logging.getLogger(__name__)

def normalize_question_number(number: str) -> str:
    """
    問題番号を正規化
    
    Args:
        number: 正規化前の問題番号
        
    Returns:
        正規化された問題番号
    """
    if not number:
        return number
    
    original = number
    
    # 「問問」の重複を修正
    number = re.sub(r'問問+', '問', number)
    
    # 「間」を「問」に修正（OCR誤認識）
    number = re.sub(r'間(\d)', r'問\1', number)
    
    # 全角数字を半角に変換
    number = number.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    
    # 「問None」を適切な番号に修正
    if 'None' in number:
        # 大問番号だけ残す
        number = re.sub(r'問None', '', number)
        if not number:
            number = '問0'  # デフォルト
    
    # ローマ数字を算用数字に変換
    roman_map = {
        'Ⅰ': '1', 'Ⅱ': '2', 'Ⅲ': '3', 'Ⅳ': '4', 'Ⅴ': '5',
        'Ⅵ': '6', 'Ⅶ': '7', 'Ⅷ': '8', 'Ⅸ': '9', 'Ⅹ': '10',
        'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
        'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10'
    }
    for roman, arabic in roman_map.items():
        number = number.replace(roman, arabic)
    
    # 括弧の統一
    number = re.sub(r'[（(](\d+)[）)]', r'(\1)', number)
    
    # 問題番号のフォーマット統一
    # 「大問1-問2」形式に統一
    match = re.match(r'大問(\d+)[^\d]*問(\d+)', number)
    if match:
        number = f"大問{match.group(1)}-問{match.group(2)}"
    elif re.match(r'^問\d+$', number):
        # 「問1」のみの場合はそのまま
        pass
    elif re.match(r'^\d+$', number):
        # 数字のみの場合は「問」を付ける
        number = f"問{number}"
    
    if original != number:
        logger.debug(f"問題番号正規化: {original} → {number}")
    
    return number


def fix_duplicate_numbers(questions: list) -> list:
    """
    重複した問題番号を修正
    
    Args:
        questions: 問題リスト
        
    Returns:
        修正された問題リスト
    """
    seen_numbers = {}
    
    for q in questions:
        if hasattr(q, 'number'):
            original = q.number
            normalized = normalize_question_number(original)
            
            # 重複チェック
            if normalized in seen_numbers:
                # 重複の場合は連番を付ける
                count = 2
                while f"{normalized}_{count}" in seen_numbers:
                    count += 1
                normalized = f"{normalized}_{count}"
                logger.warning(f"重複問題番号を修正: {original} → {normalized}")
            
            seen_numbers[normalized] = True
            q.number = normalized
    
    return questions


def extract_major_question_number(number: str) -> tuple:
    """
    問題番号から大問番号と小問番号を抽出
    
    Args:
        number: 問題番号
        
    Returns:
        (大問番号, 小問番号) のタプル
    """
    # まず正規化
    number = normalize_question_number(number)
    
    # パターンマッチング
    # 「大問1-問2」形式
    match = re.match(r'大問(\d+)[^\d]*問(\d+)', number)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    
    # 「1-2」形式
    match = re.match(r'(\d+)[^\d]+(\d+)', number)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    
    # 「問1」のみ（大問なし）
    match = re.match(r'問(\d+)', number)
    if match:
        return (None, int(match.group(1)))
    
    # 数字のみ
    match = re.match(r'^(\d+)$', number)
    if match:
        return (None, int(match.group(1)))
    
    return (None, None)


def group_by_major_question(questions: list) -> dict:
    """
    大問ごとに問題をグループ化
    
    Args:
        questions: 問題リスト
        
    Returns:
        大問番号をキーとした辞書
    """
    grouped = {}
    
    for q in questions:
        if hasattr(q, 'number'):
            major, minor = extract_major_question_number(q.number)
            if major is None:
                major = 0  # 大問番号なしは0番にグループ化
            
            if major not in grouped:
                grouped[major] = []
            grouped[major].append(q)
    
    # 各グループ内で小問番号でソート
    for major in grouped:
        grouped[major].sort(key=lambda q: extract_major_question_number(q.number)[1] or 0)
    
    return grouped