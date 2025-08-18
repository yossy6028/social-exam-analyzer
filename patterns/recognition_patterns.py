"""
統合パターン定義モジュール
全ての認識パターンを一元管理
"""
import re

# ========================================
# 設問タイプ検出用パターン
# ========================================
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
        'pattern': r'問\s*([０-９0-9]+)',
        'flags': 0,
        'type': 'number',
        'description': '問+算用数字'
    },
    
    'question_mon_kanji': {
        'pattern': r'問\s*([一二三四五六七八九十]+)',
        'flags': 0,
        'type': 'number',
        'description': '問+漢数字'
    },
    
    'question_standalone_arabic': {
        'pattern': r'^\s*([１-９][０-９]?|[1-9][0-9]?)\s*[.．、。]',
        'flags': re.MULTILINE,
        'type': 'number',
        'description': '行頭の数字+句読点'
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

# ========================================
# セクション（大問）検出用パターン
# ========================================
SECTION_PATTERNS = {
    # 四角で囲まれた数字パターン（最優先）
    'boxed_number': {
        'pattern': r'[□■▢▣]\s*([１-９1-9一二三四五六七八九十])\s*[□■▢▣]',
        'flags': 0,
        'priority': 12,
        'description': '四角で囲まれた数字（□1□形式）'
    },
    
    'boxed_kanji': {
        'pattern': r'[\[［【〔]\s*([一二三四五六七八九十])\s*[\]］】〕]',
        'flags': 0,
        'priority': 11,
        'description': '括弧で囲まれた漢数字'
    },
    
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
    
    'standalone_kanji': {
        'pattern': r'^([一二三四五六七八九十])(?:\s|$)',
        'flags': re.MULTILINE,
        'priority': 6,
        'description': '独立した漢数字'
    },
    
    'bracket_kanji': {
        'pattern': r'^【([一二三四五六七八九十])】',
        'flags': re.MULTILINE,
        'priority': 8,
        'description': '【漢数字】形式'
    },
    
    'square_bracket_num': {
        'pattern': r'^\[([１２３４５６７８９])\]',
        'flags': re.MULTILINE,
        'priority': 7,
        'description': '[全角数字]形式'
    }
}

# セクション設定
SECTION_CONFIG = {
    'max_sections': 10,  # 最大セクション数
    'min_text_length': 100,  # セクションと認識する最小文字数
    'merge_threshold': 200,  # 短いセクションを統合する閾値
    'title_max_length': 150  # セクションタイトルの最大長
}

# セクション番号変換マッピング  
SECTION_NUMBER_MAP = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '１': 1, '２': 2, '３': 3, '４': 4, '５': 5,
    '６': 6, '７': 7, '８': 8, '９': 9
}

# ========================================
# 出典抽出用パターン
# ========================================
SOURCE_PATTERNS = {
    # 「による」パターン（最優先）
    'author_title_niyoru': {
        'pattern': r'([^\s『「（）]+)\s*『([^』]+)』\s*による',
        'flags': 0,
        'priority': 10,
        'description': '著者『タイトル』による'
    },
    
    'author_quote_niyoru': {
        'pattern': r'([^\s『「（）]+)\s*「([^」]+)」\s*による',
        'flags': 0,
        'priority': 10,
        'description': '著者「タイトル」による'
    },
    
    # 雑誌掲載作品パターン
    'magazine_full_zen': {
        'pattern': r'([^\s『「（）\(\)]+)\s*「([^」]+)」\s*（\s*『([^』]+)』\s*(?:第[^）]*号\s*)?所収\s*）\s*による',
        'flags': 0,
        'priority': 9,
        'description': '著者「作品」（『雑誌』所収）による（全角括弧）'
    },
    
    'magazine_full_han': {
        'pattern': r'([^\s『「（）\(\)]+)\s*「([^」]+)」\s*\(\s*『([^』]+)』\s*(?:第[^\)]*号\s*)?所収\s*\)\s*による',
        'flags': 0,
        'priority': 9,
        'description': '著者「作品」(『雑誌』所収)による（半角括弧）'
    },
    
    'magazine_bracket': {
        'pattern': r'([^\s『「（）]+)\s*「([^」]+)」\s*［\s*『([^』]+)』\s*所収\s*］\s*による',
        'flags': 0,
        'priority': 9,
        'description': '著者「作品」［『雑誌』所収］による'
    },
    
    # 「より」パターン
    'paren_author_title_yori': {
        'pattern': r'（([^\s『「）]+)\s*『([^』]+)』\s*より）',
        'flags': 0,
        'priority': 8,
        'description': '（著者『タイトル』より）'
    },
    
    'author_title_yori': {
        'pattern': r'([^\s『「（）]+)\s*『([^』]+)』\s*より',
        'flags': 0,
        'priority': 7,
        'description': '著者『タイトル』より'
    },
    
    'author_quote_yori': {
        'pattern': r'([^\s『「（）]+)\s*「([^」]+)」\s*より',
        'flags': 0,
        'priority': 7,
        'description': '著者「タイトル」より'
    },
    
    # タイトル単独パターン
    'title_niyoru': {
        'pattern': r'『([^』]+)』\s*による',
        'flags': 0,
        'priority': 6,
        'description': '『タイトル』による'
    },
    
    'quote_niyoru': {
        'pattern': r'「([^」]+)」\s*による',
        'flags': 0,
        'priority': 6,
        'description': '「タイトル」による'
    },
    
    'title_yori': {
        'pattern': r'『([^』]+)』\s*より',
        'flags': 0,
        'priority': 5,
        'description': '『タイトル』より'
    },
    
    'quote_yori': {
        'pattern': r'「([^」]+)」\s*より',
        'flags': 0,
        'priority': 5,
        'description': '「タイトル」より'
    },
    
    # 「から」パターン
    'title_kara': {
        'pattern': r'『([^』]+)』\s*から',
        'flags': 0,
        'priority': 4,
        'description': '『タイトル』から'
    },
    
    'quote_kara': {
        'pattern': r'「([^」]+)」\s*から',
        'flags': 0,
        'priority': 4,
        'description': '「タイトル」から'
    }
}

# 出典設定
SOURCE_CONFIG = {
    'max_distance_from_text': 500,  # 本文との最大距離（文字数）
    'min_title_length': 2,  # タイトルの最小文字数
    'max_title_length': 100,  # タイトルの最大文字数
    'max_author_length': 50  # 著者名の最大文字数
}

# ========================================
# 年度検出用パターン
# ========================================
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
    
    # 2桁年度（21年など）
    'year_2digit': {
        'pattern': r'(\d{2})年度?',
        'flags': 0,
        'priority': 5,
        'description': '2桁年度'
    },
    
    # ファイル名からの年度抽出
    'filename_year': {
        'pattern': r'(19|20)\d{2}',
        'flags': 0,
        'priority': 4,
        'description': 'ファイル名年度'
    }
}

# 年度変換設定
YEAR_CONFIG = {
    'default_century': 2000,  # 2桁年度のデフォルト世紀
    'kanji_digit_map': {
        '〇': '0', '零': '0', '０': '0',
        '一': '1', '壱': '1', '１': '1',
        '二': '2', '弐': '2', '２': '2',
        '三': '3', '参': '3', '３': '3',
        '四': '4', '肆': '4', '４': '4',
        '五': '5', '伍': '5', '５': '5',
        '六': '6', '陸': '6', '６': '6',
        '七': '7', '柒': '7', '７': '7',
        '八': '8', '捌': '8', '８': '8',
        '九': '9', '玖': '9', '９': '9'
    },
    'era_conversion': {
        'reiwa_base': 2018,  # 令和元年 = 2019
        'heisei_base': 1988,  # 平成元年 = 1989
        'showa_base': 1925   # 昭和元年 = 1926
    }
}

# ========================================
# ユーティリティ関数
# ========================================
def compile_patterns(pattern_dict):
    """パターン辞書をコンパイル済み正規表現に変換"""
    compiled = {}
    for key, pattern_info in pattern_dict.items():
        compiled[key] = {
            'regex': re.compile(pattern_info['pattern'], pattern_info.get('flags', 0)),
            'priority': pattern_info.get('priority', 0),
            'type': pattern_info.get('type', ''),
            'description': pattern_info.get('description', '')
        }
    return compiled

def get_pattern_by_priority(pattern_dict):
    """優先度順にソートされたパターンリストを取得"""
    return sorted(
        pattern_dict.items(),
        key=lambda x: x[1].get('priority', 0),
        reverse=True
    )

def convert_kanji_to_number(kanji_str, mapping):
    """漢数字を算用数字に変換"""
    return mapping.get(kanji_str, None)

def normalize_year(year_str, config=YEAR_CONFIG):
    """年度文字列を西暦4桁に正規化"""
    # 漢数字を算用数字に変換
    normalized = ''
    for char in year_str:
        normalized += config['kanji_digit_map'].get(char, char)
    
    # 数字のみ抽出
    digits = re.findall(r'\d+', normalized)
    if not digits:
        return None
    
    year = int(digits[0])
    
    # 2桁年度の場合
    if year < 100:
        if year < 50:
            year += 2000
        else:
            year += 1900
    
    return year

def extract_source_info(text):
    """テキストから出典情報を抽出"""
    results = []
    compiled = compile_patterns(SOURCE_PATTERNS)
    
    for pattern_name, pattern_info in get_pattern_by_priority(compiled):
        matches = pattern_info['regex'].finditer(text)
        for match in matches:
            groups = match.groups()
            source_info = {
                'pattern': pattern_name,
                'priority': pattern_info['priority'],
                'description': pattern_info['description'],
                'position': match.span(),
                'raw_text': match.group(0)
            }
            
            # パターンに応じて著者・タイトル・雑誌を抽出
            if len(groups) >= 3:  # 雑誌掲載作品
                source_info['author'] = groups[0].strip()
                source_info['title'] = groups[1].strip()
                source_info['magazine'] = groups[2].strip()
            elif len(groups) >= 2:  # 著者とタイトル
                source_info['author'] = groups[0].strip()
                source_info['title'] = groups[1].strip()
            elif len(groups) >= 1:  # タイトルのみ
                source_info['title'] = groups[0].strip()
            
            results.append(source_info)
    
    # 優先度順にソート
    results.sort(key=lambda x: x['priority'], reverse=True)
    
    return results

def extract_sections(text):
    """テキストからセクション（大問）を抽出"""
    results = []
    compiled = compile_patterns(SECTION_PATTERNS)
    
    for pattern_name, pattern_info in get_pattern_by_priority(compiled):
        matches = pattern_info['regex'].finditer(text)
        for match in matches:
            section_info = {
                'pattern': pattern_name,
                'priority': pattern_info['priority'],
                'description': pattern_info['description'],
                'position': match.span(),
                'raw_text': match.group(0),
                'section_number': None
            }
            
            # セクション番号を抽出
            groups = match.groups()
            if groups:
                number_str = groups[0]
                section_info['section_number'] = convert_kanji_to_number(
                    number_str, SECTION_NUMBER_MAP
                ) or number_str
            
            results.append(section_info)
    
    # 位置順にソート（優先度も考慮）
    results.sort(key=lambda x: (x['position'][0], -x['priority']))
    
    return results

def extract_questions(text):
    """テキストから設問を抽出"""
    results = []
    compiled = compile_patterns(QUESTION_PATTERNS)
    
    for pattern_name, pattern_info in compiled.items():
        matches = pattern_info['regex'].finditer(text)
        for match in matches:
            question_info = {
                'pattern': pattern_name,
                'type': pattern_info['type'],
                'description': pattern_info['description'],
                'position': match.span(),
                'raw_text': match.group(0)
            }
            
            # 設問番号を抽出（番号パターンの場合）
            if pattern_info['type'] == 'number':
                groups = match.groups()
                if groups:
                    number_str = groups[0]
                    question_info['question_number'] = convert_kanji_to_number(
                        number_str, QUESTION_NUMBER_MAP
                    ) or number_str
            
            results.append(question_info)
    
    # 位置順にソート
    results.sort(key=lambda x: x['position'][0])
    
    return results

def extract_year(text, filename=''):
    """テキストまたはファイル名から年度を抽出"""
    compiled = compile_patterns(YEAR_PATTERNS)
    candidates = []
    
    # テキストから抽出
    for pattern_name, pattern_info in get_pattern_by_priority(compiled):
        matches = pattern_info['regex'].finditer(text)
        for match in matches:
            year_str = match.group(1)
            
            # 特別な処理：令和・平成年号
            if 'reiwa' in pattern_name:
                era_year = int(year_str)
                normalized = 2018 + era_year  # 令和元年 = 2019
            elif 'heisei' in pattern_name:
                if year_str.isdigit():
                    era_year = int(year_str)
                else:
                    # 漢数字の平成年号を処理
                    era_year = convert_kanji_number_to_int(year_str)
                if era_year:
                    normalized = 1988 + era_year  # 平成元年 = 1989
                else:
                    continue
            else:
                # 通常の年度処理
                normalized = normalize_year(year_str)
            
            if normalized:
                candidates.append({
                    'year': normalized,
                    'priority': pattern_info['priority'],
                    'source': 'text',
                    'raw': match.group(0),
                    'pattern': pattern_name
                })
    
    # ファイル名から抽出
    if filename:
        for pattern_name, pattern_info in compiled.items():
            if 'filename' in pattern_name:
                matches = pattern_info['regex'].finditer(filename)
                for match in matches:
                    year = int(match.group(0))
                    candidates.append({
                        'year': year,
                        'priority': pattern_info['priority'],
                        'source': 'filename',
                        'raw': match.group(0),
                        'pattern': pattern_name
                    })
    
    # 優先度順にソート
    candidates.sort(key=lambda x: x['priority'], reverse=True)
    
    return candidates[0]['year'] if candidates else None


def convert_kanji_number_to_int(kanji_str):
    """漢数字文字列を整数に変換"""
    kanji_digits = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '壱': 1, '弐': 2, '参': 3, '肆': 4, '伍': 5,
        '陸': 6, '柒': 7, '捌': 8, '玖': 9
    }
    
    if len(kanji_str) == 1:
        return kanji_digits.get(kanji_str, None)
    
    # 複雑な漢数字は簡単な処理
    if '十' in kanji_str:
        if kanji_str == '十':
            return 10
        elif kanji_str.startswith('十'):
            # 十五 -> 15
            return 10 + kanji_digits.get(kanji_str[1], 0)
        elif kanji_str.endswith('十'):
            # 二十 -> 20
            return kanji_digits.get(kanji_str[0], 0) * 10
        else:
            # 二十五 -> 25
            parts = kanji_str.split('十')
            tens = kanji_digits.get(parts[0], 0) * 10
            ones = kanji_digits.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
            return tens + ones
    
    return None

# ========================================
# パターンレジストリ（互換性のため）
# ========================================
class PatternRegistry:
    """パターンの統合管理クラス"""
    
    def __init__(self):
        self.question_patterns = compile_patterns(QUESTION_PATTERNS)
        self.section_patterns = compile_patterns(SECTION_PATTERNS)
        self.source_patterns = compile_patterns(SOURCE_PATTERNS)
        self.year_patterns = compile_patterns(YEAR_PATTERNS)
    
    def get_all_patterns(self):
        """全パターンを取得"""
        return {
            'questions': self.question_patterns,
            'sections': self.section_patterns,
            'sources': self.source_patterns,
            'years': self.year_patterns
        }
    
    def extract_all(self, text, filename=''):
        """テキストから全情報を抽出"""
        return {
            'sections': extract_sections(text),
            'questions': extract_questions(text),
            'sources': extract_source_info(text),
            'year': extract_year(text, filename)
        }

# デフォルトレジストリインスタンス
default_registry = PatternRegistry()