"""
テキスト処理関連のユーティリティ関数
"""
import re
import unicodedata
from typing import List, Dict, Optional, Tuple
from pathlib import Path


def detect_encoding(file_path: Path) -> Optional[str]:
    """
    ファイルのエンコーディングを検出
    
    Args:
        file_path: 検出対象のファイルパス
    
    Returns:
        検出されたエンコーディング名、検出失敗時はNone
    """
    encodings = ['utf-8', 'shift-jis', 'euc-jp', 'cp932', 'iso-2022-jp', 'utf-16']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(100)  # 最初の100文字だけ読んで確認
            return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    return None


def normalize_text(text: str) -> str:
    """
    テキストの正規化（全角・半角統一、空白文字の処理など）
    
    Args:
        text: 正規化対象のテキスト
    
    Returns:
        正規化されたテキスト
    """
    # Unicode正規化
    text = unicodedata.normalize('NFKC', text)
    
    # 連続する空白を1つに
    text = re.sub(r'\s+', ' ', text)
    
    # 前後の空白を削除
    text = text.strip()
    
    return text


def extract_number_from_string(text: str, pattern: str = r'\d+') -> Optional[int]:
    """
    文字列から数値を抽出
    
    Args:
        text: 抽出元のテキスト
        pattern: 抽出用の正規表現パターン
    
    Returns:
        抽出された数値、見つからない場合はNone
    """
    match = re.search(pattern, text)
    if match:
        try:
            return int(match.group())
        except ValueError:
            return None
    return None


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    2つのテキストの類似度を計算（簡易版）
    
    Args:
        text1: 比較テキスト1
        text2: 比較テキスト2
    
    Returns:
        類似度（0.0-1.0）
    """
    if not text1 or not text2:
        return 0.0
    
    # 正規化
    text1 = normalize_text(text1.lower())
    text2 = normalize_text(text2.lower())
    
    # 単語セットの作成
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    # Jaccard係数
    if not words1 and not words2:
        return 1.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def split_text_by_years(text: str, year_markers: List[str]) -> Dict[str, str]:
    """
    年度マーカーでテキストを分割
    
    Args:
        text: 分割対象のテキスト
        year_markers: 年度マーカーのリスト（例: ['武蔵14', '武蔵15']）
    
    Returns:
        年度ごとに分割されたテキストの辞書
    """
    if not year_markers:
        return {}
    
    result = {}
    positions = []
    
    # 各マーカーの位置を記録
    for marker in year_markers:
        pos = text.find(marker)
        if pos != -1:
            positions.append((pos, marker))
    
    # 位置でソート
    positions.sort()
    
    # 各年度のテキストを抽出
    for i, (pos, marker) in enumerate(positions):
        if i < len(positions) - 1:
            # 次のマーカーまでのテキスト
            next_pos = positions[i + 1][0]
            year_text = text[pos:next_pos]
        else:
            # 最後のマーカーから文末まで
            year_text = text[pos:]
        
        # マーカーから年度を抽出
        year_match = re.search(r'\d+', marker)
        if year_match:
            year = year_match.group()
            result[year] = year_text
    
    return result


def clean_path_string(path_string: str) -> str:
    """
    パス文字列をクリーンアップ（エスケープ文字の処理など）
    
    Args:
        path_string: クリーンアップ対象のパス文字列
    
    Returns:
        クリーンアップされたパス文字列
    """
    # 前後の空白と引用符を削除
    path_string = path_string.strip().strip('\'"')
    
    # バックスラッシュエスケープを処理
    # スペースのエスケープ
    path_string = path_string.replace(r'\ ', ' ')
    
    # 括弧のエスケープ
    path_string = path_string.replace(r'\(', '(')
    path_string = path_string.replace(r'\)', ')')
    
    # 二重バックスラッシュを単一に
    path_string = path_string.replace('\\\\', '\\')
    
    return path_string


def extract_character_limit(text: str) -> Optional[Tuple[int, int]]:
    """
    設問から文字数制限を抽出
    
    Args:
        text: 設問テキスト
    
    Returns:
        (最小文字数, 最大文字数)のタプル、見つからない場合はNone
    """
    patterns = [
        r'(\d+)字以上(\d+)字以内',
        r'(\d+)〜(\d+)字',
        r'(\d+)字から(\d+)字',
        r'(\d+)字以内',  # 最大のみ
        r'(\d+)字で',    # 固定
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return (int(groups[0]), int(groups[1]))
            elif len(groups) == 1:
                limit = int(groups[0])
                if '以内' in pattern:
                    return (0, limit)
                else:
                    return (limit, limit)
    
    return None