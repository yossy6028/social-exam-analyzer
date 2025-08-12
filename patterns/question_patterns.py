"""
設問タイプ検出用パターン定義
"""
import re

QUESTION_PATTERNS = {
    # 記述問題パターン
    'description_explain': {
        'pattern': r'説明し[なさい|てください]|述べ[なさい|よ]',
        'flags': 0,
        'type': 'description',
        'description': '説明・論述'
    },
    
    'description_reason': {
        'pattern': r'理由を[書き|答え|述べ]',
        'flags': 0,
        'type': 'description',
        'description': '理由説明'
    },
    
    'description_chars': {
        'pattern': r'(\d+)字[以内で|程度で|で]',
        'flags': 0,
        'type': 'description',
        'description': '字数指定記述'
    },
    
    'description_summary': {
        'pattern': r'要約し[なさい|てください]|まとめ[なさい|て]',
        'flags': 0,
        'type': 'description',
        'description': '要約'
    },
    
    # 選択問題パターン
    'choice_select': {
        'pattern': r'選び[なさい|、]|選択し[なさい|て]',
        'flags': 0,
        'type': 'choice',
        'description': '選択'
    },
    
    'choice_abcd': {
        'pattern': r'[ア-エ]\s*[。、]',
        'flags': 0,
        'type': 'choice',
        'description': 'ア～エ選択肢'
    },
    
    'choice_number': {
        'pattern': r'[①-⑮].*[①-⑮]',
        'flags': 0,
        'type': 'choice',
        'description': '番号選択肢'
    },
    
    'choice_correct': {
        'pattern': r'正しいもの|適切なもの|ふさわしいもの',
        'flags': 0,
        'type': 'choice',
        'description': '正誤選択'
    },
    
    # 漢字・語句問題パターン
    'kanji_reading': {
        'pattern': r'読み[がな|を]|ひらがなで',
        'flags': 0,
        'type': 'kanji',
        'description': '漢字の読み'
    },
    
    'kanji_writing': {
        'pattern': r'漢字[で|に]|漢字一字',
        'flags': 0,
        'type': 'kanji',
        'description': '漢字の書き'
    },
    
    'kanji_section': {
        'pattern': r'^[三四五六]\s*(?:次の)?.*漢字',
        'flags': re.MULTILINE,
        'type': 'kanji',
        'description': '漢字セクション'
    },
    
    'vocabulary': {
        'pattern': r'意味|類義語|対義語|反対語',
        'flags': 0,
        'type': 'vocabulary',
        'description': '語句の意味'
    },
    
    # 抜き出し問題パターン
    'extract_chars': {
        'pattern': r'(\d+)字で[抜き出し|書き抜き]',
        'flags': 0,
        'type': 'extract',
        'description': '字数指定抜き出し'
    },
    
    'extract_text': {
        'pattern': r'本文[から|中から].*[抜き出し|書き抜き]',
        'flags': 0,
        'type': 'extract',
        'description': '本文抜き出し'
    },
    
    'extract_find': {
        'pattern': r'探し[て|、].*[書き|答え]',
        'flags': 0,
        'type': 'extract',
        'description': '探して書く'
    },
    
    # 空欄補充パターン
    'blank_fill': {
        'pattern': r'空[欄所][にを]|［\s*[あ-ん]\s*］|【\s*[あ-ん]\s*】',
        'flags': 0,
        'type': 'blank',
        'description': '空欄補充'
    },
    
    # 設問番号パターン
    'question_mon_arabic': {
        'pattern': r'問([０-９0-9]+)',
        'flags': 0,
        'type': 'number',
        'description': '問+算用数字'
    },
    
    'question_mon_kanji': {
        'pattern': r'問([一二三四五六七八九十]+)',
        'flags': 0,
        'type': 'number',
        'description': '問+漢数字'
    },
    
    'question_setsumon': {
        'pattern': r'設問([０-９0-9]+)',
        'flags': 0,
        'type': 'number',
        'description': '設問+数字'
    },
    
    'question_paren': {
        'pattern': r'\(([０-９0-9]+)\)',
        'flags': 0,
        'type': 'number',
        'description': '括弧内数字'
    },
    
    'question_circle': {
        'pattern': r'([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮])',
        'flags': 0,
        'type': 'number',
        'description': '丸数字'
    }
}

# 設問タイプ設定
QUESTION_CONFIG = {
    'priority_order': ['description', 'choice', 'kanji', 'extract', 'blank', 'vocabulary'],
    'default_type': 'other',
    'max_questions_per_section': 30,
    'min_question_length': 10  # 設問と認識する最小文字数
}

# 設問番号変換マッピング
QUESTION_NUMBER_MAP = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
    '①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5,
    '⑥': 6, '⑦': 7, '⑧': 8, '⑨': 9, '⑩': 10,
    '⑪': 11, '⑫': 12, '⑬': 13, '⑭': 14, '⑮': 15
}