"""
セクション（大問）検出用パターン定義
"""
import re

SECTION_PATTERNS = {
    # 大問マーカーパターン（優先度順）
    'kanji_comma_next': {
        'pattern': r'^([一二三四五六七八九十])[、，]\s*次の',
        'flags': re.MULTILINE,
        'priority': 10,
        'description': '漢数字+読点+「次の」'
    },
    
    'daimon_kanji': {
        'pattern': r'^大問\s*([一二三四五六七八九十])',
        'flags': re.MULTILINE,
        'priority': 9,
        'description': '「大問」+漢数字'
    },
    
    'dai_kanji_mon': {
        'pattern': r'^第([一二三四五六七八九十])問',
        'flags': re.MULTILINE,
        'priority': 9,
        'description': '「第」+漢数字+「問」'
    },
    
    'mon_kanji': {
        'pattern': r'^問([一二三四五六七八九十])(?:[^\\d]|$)',
        'flags': re.MULTILINE,
        'priority': 8,
        'description': '「問」+漢数字（小問除外）'
    },
    
    'number_punct': {
        'pattern': r'^([１２３４５６７８９])[、．.]',
        'flags': re.MULTILINE,
        'priority': 7,
        'description': '全角数字+句読点'
    },
    
    # 特殊パターン（早稲田実業など）
    'dash_next_text': {
        'pattern': r'^[-|一]\s*次の文章',
        'flags': re.MULTILINE,
        'priority': 8,
        'description': 'ダッシュまたは「一」+「次の文章」'
    },
    
    'ni_next_text': {
        'pattern': r'^二\s*次の文章',
        'flags': re.MULTILINE,
        'priority': 8,
        'description': '「二」+「次の文章」'
    },
    
    'san_next_question': {
        'pattern': r'^三\s*次の[問題問い]',
        'flags': re.MULTILINE,
        'priority': 8,
        'description': '「三」+「次の問題/問い」'
    },
    
    # セクションタイプ判定パターン
    'type_kanji': {
        'pattern': r'漢字|カタカナ|語句|言葉',
        'flags': 0,
        'description': '漢字・語句問題の判定'
    },
    
    'type_reading': {
        'pattern': r'次の文章|文章を読んで|以下の文章',
        'flags': 0,
        'description': '文章読解問題の判定'
    },
    
    'type_poetry': {
        'pattern': r'詩|俳句|短歌|韻文',
        'flags': 0,
        'description': '詩・韻文問題の判定'
    },
    
    # 設問番号リセットパターン
    'question_reset_arabic': {
        'pattern': r'問([０-９0-9]+)',
        'flags': 0,
        'description': '問+算用数字'
    },
    
    'question_reset_kanji': {
        'pattern': r'問([一二三四五六七八九十]+)',
        'flags': 0,
        'description': '問+漢数字'
    },
    
    'question_reset_paren': {
        'pattern': r'\(([０-９0-9]+)\)',
        'flags': 0,
        'description': '括弧内数字'
    },
    
    'question_reset_circle': {
        'pattern': r'([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮])',
        'flags': 0,
        'description': '丸数字'
    }
}

# セクション検出設定
SECTION_CONFIG = {
    'min_section_length': 100,  # セクションの最小文字数
    'question_reset_distance': 500,  # 設問リセット検出の最小距離
    'max_sections': 10,  # 最大セクション数
    'default_section_type': '文章読解'  # デフォルトのセクションタイプ
}

# 漢数字変換マッピング（セクション番号用）
SECTION_NUMBER_MAP = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '１': 1, '２': 2, '３': 3, '４': 4, '５': 5,
    '６': 6, '７': 7, '８': 8, '９': 9
}