"""
年度検出用パターン定義
"""
import re

YEAR_PATTERNS = {
    # 漢数字の西暦パターン（二〇二五年度など）
    'kanji': {
        'pattern': r'([一二三四五六七八九〇零壱弐参肆伍陸柒捌玖０-９]{4})年度?',
        'flags': 0,
        'priority': 11,
        'description': '4桁の漢数字年度'
    },
    
    # 漢数字2桁年度パターン
    'kanji_2digit': {
        'pattern': r'([一二三四五六七八九〇零壱弐参肆伍陸柒捌玖０-９]{2})年度?',
        'flags': 0,
        'priority': 10,
        'description': '2桁の漢数字年度'
    },
    
    # 西暦4桁パターン
    'year_4digit': {
        'pattern': r'(20\d{2})年度?',
        'flags': 0,
        'priority': 9,
        'description': '西暦4桁年度'
    },
    
    # 令和パターン
    'reiwa': {
        'pattern': r'令和(\d{1,2})年度?',
        'flags': 0,
        'priority': 8,
        'description': '令和年号'
    },
    
    # 平成パターン（数字）
    'heisei': {
        'pattern': r'平成(\d{1,2})年度?',
        'flags': 0,
        'priority': 7,
        'description': '平成年号（数字）'
    },
    
    # 平成パターン（漢数字）
    'heisei_kanji': {
        'pattern': r'平成([一二三四五六七八九十]{1,4})年度?',
        'flags': 0,
        'priority': 7,
        'description': '平成年号（漢数字）'
    },
    
    # 2桁年度パターン（括弧内を除外）
    'year_2digit': {
        'pattern': r'(?<![(\\d\\n平成令和])(\d{2})年度?(?![)\\d])',
        'flags': 0,
        'priority': 5,
        'description': '2桁年度（括弧内除外）'
    },
    
    # 学校名付き年度パターン
    'school_kaisei': {
        'pattern': r'開成(\d{2})年?度?',
        'flags': 0,
        'priority': 7,
        'description': '開成+2桁年度'
    },
    
    'school_musashi': {
        'pattern': r'武蔵(\d{2})年?度?',
        'flags': 0,
        'priority': 7,
        'description': '武蔵+2桁年度'
    },
    
    'school_ouin': {
        'pattern': r'桜[蔭陰](\d{2})年?度?',
        'flags': 0,
        'priority': 7,
        'description': '桜蔭+2桁年度'
    },
    
    'school_azabu': {
        'pattern': r'麻布(\d{2})年?度?',
        'flags': 0,
        'priority': 7,
        'description': '麻布+2桁年度'
    },
    
    'school_shibuya': {
        'pattern': r'渋[谷渋](\d{2})年?度?',
        'flags': 0,
        'priority': 7,
        'description': '渋谷系+2桁年度'
    },
    
    # ファイル名パターン
    'filename_range': {
        'pattern': r'(\d{2})-(\d{2})',
        'flags': 0,
        'priority': 6,
        'description': 'ファイル名の年度範囲'
    },
    
    'filename_4digit': {
        'pattern': r'20\d{2}',
        'flags': 0,
        'priority': 8,
        'description': 'ファイル名の4桁年度'
    }
}

# 漢数字変換マッピング
KANJI_TO_NUM = {
    '〇': '0', '０': '0', '零': '0',
    '一': '1', '１': '1', '壱': '1',
    '二': '2', '２': '2', '弐': '2',
    '三': '3', '３': '3', '参': '3',
    '四': '4', '４': '4', '肆': '4',
    '五': '5', '５': '5', '伍': '5',
    '六': '6', '６': '6', '陸': '6',
    '七': '7', '７': '7', '柒': '7',
    '八': '8', '８': '8', '捌': '8',
    '九': '9', '９': '9', '玖': '9',
    '十': '10'
}

# 年度の有効範囲
YEAR_RANGE = {
    'min_valid_year': 1990,
    'max_valid_year': 2030,
    'min_2digit': 90,  # 90-99は1990年代
    'max_2digit': 30   # 00-30は2000年代
}