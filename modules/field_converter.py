"""
フィールド型変換ユーティリティ
Gemini APIレスポンスとEnum型の相互変換を安全に行う
"""
import logging
from typing import Union
from enum import Enum

logger = logging.getLogger(__name__)

# SocialFieldの定義（social_analyzer.pyから）
class SocialField(Enum):
    """社会科目の分野"""
    GEOGRAPHY = "地理"
    HISTORY = "歴史"
    CIVICS = "公民"
    CURRENT_AFFAIRS = "時事問題"
    MIXED = "総合"


def safe_get_field_value(field: Union[str, SocialField]) -> str:
    """
    文字列またはEnumから安全に文字列値を取得
    
    Args:
        field: SocialFieldのEnumまたは文字列
        
    Returns:
        フィールドの文字列値
    """
    if isinstance(field, str):
        return field
    elif hasattr(field, 'value'):
        return field.value
    else:
        logger.warning(f"Unknown field type: {type(field)}, value: {field}")
        return str(field)


def convert_to_enum(field_value: Union[str, SocialField]) -> SocialField:
    """
    文字列またはEnumをSocialField Enumに変換
    
    Args:
        field_value: 変換対象の値
        
    Returns:
        SocialField Enum
    """
    # すでにEnumの場合はそのまま返す
    if isinstance(field_value, SocialField):
        return field_value
    
    # 文字列の場合は対応するEnumを探す
    if isinstance(field_value, str):
        # 値から直接Enumを取得
        for field in SocialField:
            if field.value == field_value:
                return field
        
        # 大文字小文字を無視してマッチング
        field_value_lower = field_value.lower()
        for field in SocialField:
            if field.value.lower() == field_value_lower:
                logger.info(f"Case-insensitive match: {field_value} -> {field.value}")
                return field
        
        # 部分一致を試みる（最も類似度の高いものを選択）
        best_match = find_closest_field(field_value)
        if best_match:
            logger.warning(f"Fuzzy match: {field_value} -> {best_match.value}")
            return best_match
        
        # マッチしない場合はMIXEDにフォールバック
        logger.warning(f"Unknown field value: {field_value}, defaulting to MIXED")
        return SocialField.MIXED
    
    # その他の型の場合
    logger.error(f"Invalid field type: {type(field_value)}")
    return SocialField.MIXED


def find_closest_field(field_value: str) -> SocialField:
    """
    文字列の類似度で最も近いフィールドを見つける
    
    Args:
        field_value: 検索対象の文字列
        
    Returns:
        最も類似度の高いSocialField、見つからない場合はNone
    """
    if not field_value:
        return None
    
    field_value_lower = field_value.lower()
    
    # キーワードベースのマッチング
    keyword_map = {
        '地理': SocialField.GEOGRAPHY,
        '地形': SocialField.GEOGRAPHY,
        '気候': SocialField.GEOGRAPHY,
        '産業': SocialField.GEOGRAPHY,
        '農業': SocialField.GEOGRAPHY,
        '工業': SocialField.GEOGRAPHY,
        '歴史': SocialField.HISTORY,
        '時代': SocialField.HISTORY,
        '戦争': SocialField.HISTORY,
        '改革': SocialField.HISTORY,
        '幕府': SocialField.HISTORY,
        '公民': SocialField.CIVICS,
        '政治': SocialField.CIVICS,
        '憲法': SocialField.CIVICS,
        '選挙': SocialField.CIVICS,
        '経済': SocialField.CIVICS,
        '時事': SocialField.CURRENT_AFFAIRS,
        'ニュース': SocialField.CURRENT_AFFAIRS,
        '現代': SocialField.CURRENT_AFFAIRS,
        '総合': SocialField.MIXED,
        '混合': SocialField.MIXED,
    }
    
    for keyword, field_enum in keyword_map.items():
        if keyword in field_value_lower:
            return field_enum
    
    return None


def field_to_gemini_string(field: SocialField) -> str:
    """
    SocialField EnumをGemini API用の文字列に変換
    
    Args:
        field: SocialField Enum
        
    Returns:
        Gemini APIに送信する文字列
    """
    if isinstance(field, SocialField):
        return field.value
    else:
        # Enumでない場合も文字列として扱う
        return str(field)


def normalize_gemini_response(response_dict: dict) -> dict:
    """
    Gemini APIレスポンスの型を正規化
    
    Args:
        response_dict: Geminiからのレスポンス辞書
        
    Returns:
        正規化されたレスポンス辞書
    """
    if 'field' in response_dict:
        # fieldを文字列からEnumに変換
        response_dict['field'] = convert_to_enum(response_dict['field'])
    
    # その他のフィールドも必要に応じて正規化
    return response_dict