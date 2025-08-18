"""
社会科入試問題専用パターン定義
地理・歴史・公民の設問パターンを網羅
"""
import re

# 社会科特有の設問パターン
SOCIAL_QUESTION_PATTERNS = {
    # 小問番号パターン（社会科でよく使われる形式）
    'subquestion_alphabet_lower': {
        'pattern': r'^\s*\(([a-z])\)',  # (a), (b), (c)
        'flags': re.MULTILINE,
        'type': 'number',
        'description': '小問（アルファベット小文字）'
    },
    
    'subquestion_alphabet_upper': {
        'pattern': r'^\s*\(([A-Z])\)',  # (A), (B), (C)
        'flags': re.MULTILINE,
        'type': 'number',
        'description': '小問（アルファベット大文字）'
    },
    
    'subquestion_katakana': {
        'pattern': r'^\s*\(([ア-ン])\)',  # (ア), (イ), (ウ)
        'flags': re.MULTILINE,
        'type': 'number',
        'description': '小問（カタカナ）'
    },
    
    'subquestion_circle_katakana': {
        'pattern': r'^\s*([㋐-㋾])',  # ㋐, ㋑, ㋒
        'flags': re.MULTILINE,
        'type': 'number',
        'description': '小問（丸囲みカタカナ）'
    },
    
    'subquestion_number_paren': {
        'pattern': r'^\s*\(([1-9]|[1-9][0-9])\)',  # (1), (2), (10)
        'flags': re.MULTILINE,
        'type': 'number',
        'description': '小問（算用数字括弧）'
    },
    
    'subquestion_roman': {
        'pattern': r'^\s*\((i+|iv|v|vi+|ix|x+)\)',  # (i), (ii), (iii)
        'flags': re.MULTILINE | re.IGNORECASE,
        'type': 'number',
        'description': '小問（ローマ数字）'
    },
    
    # 選択肢パターン
    'choice_alphabet': {
        'pattern': r'^\s*([A-Zア-エ])\s*[\.．:]',  # A. B. ア. イ.
        'flags': re.MULTILINE,
        'type': 'choice',
        'description': '選択肢マーカー'
    },
    
    'choice_number': {
        'pattern': r'^\s*([①-⑳])',  # ①から⑳まで
        'flags': re.MULTILINE,
        'type': 'choice',
        'description': '選択肢（丸数字）'
    },
    
    # 空欄補充パターン（社会科特有）
    'blank_square': {
        'pattern': r'□|■|▢|▣',
        'flags': 0,
        'type': 'blank',
        'description': '四角空欄'
    },
    
    'blank_underline': {
        'pattern': r'＿{2,}|_{2,}|－{2,}',
        'flags': 0,
        'type': 'blank',
        'description': '下線空欄'
    },
    
    'blank_alphabet_square': {
        'pattern': r'[\[［]([A-Za-z])[\]］]',
        'flags': 0,
        'type': 'blank',
        'description': 'アルファベット空欄'
    },
    
    'blank_x_y_z': {
        'pattern': r'[XYZxyz](?=[にはがをのと、。])',
        'flags': 0,
        'type': 'blank',
        'description': 'XYZ形式の空欄'
    },
    
    # 資料参照パターン
    'reference_figure': {
        'pattern': r'図[１-９0-9]+|資料[１-９0-9]+|表[１-９0-9]+|グラフ[１-９0-9]+',
        'flags': 0,
        'type': 'reference',
        'description': '資料参照'
    },
    
    'reference_map': {
        'pattern': r'地図[１-９0-9]+|地形図[１-９0-9]+',
        'flags': 0,
        'type': 'reference',
        'description': '地図参照'
    },
    
    # 記述問題パターン（社会科特有）
    'description_explain': {
        'pattern': r'説明し[なさい|ましょう|てください]|述べ[なさい|ましょう|よ]',
        'flags': 0,
        'type': 'description',
        'description': '説明記述'
    },
    
    'description_reason': {
        'pattern': r'理由を[答え|書き|述べ]|なぜ.*か[。\s]',
        'flags': 0,
        'type': 'description',
        'description': '理由記述'
    },
    
    'description_difference': {
        'pattern': r'違い|相違|異なる|比較',
        'flags': 0,
        'type': 'description',
        'description': '比較記述'
    },
    
    'description_chars_limit': {
        'pattern': r'([0-9０-９]+)字[以内で|程度で|で]',
        'flags': 0,
        'type': 'description',
        'description': '字数制限記述'
    },
    
    # 正誤問題パターン
    'true_false': {
        'pattern': r'正しい|誤って|間違|適切|不適切|ふさわし',
        'flags': 0,
        'type': 'choice',
        'description': '正誤選択'
    },
    
    # 並び替え問題
    'order_chronological': {
        'pattern': r'古い.*順|新しい.*順|年代順',
        'flags': 0,
        'type': 'order',
        'description': '年代順並び替え'
    },
    
    # 計算問題（地理）
    'calculation': {
        'pattern': r'計算し|求め[なさい|よ]|算出',
        'flags': 0,
        'type': 'calculation',
        'description': '計算問題'
    }
}

# 社会科の分野判定パターン
SOCIAL_FIELD_PATTERNS = {
    'geography': [
        r'地図|地形図|等高線|地図記号',
        r'気候|雨温図|降水量|気温',
        r'農業|工業|産業|貿易',
        r'人口|都市|過疎',
        r'河川|山脈|平野|盆地',
        r'県|都道府県|地方|地域',
        r'緯度|経度|時差'
    ],
    'history': [
        r'時代|世紀|年',
        r'天皇|将軍|大名|武士',
        r'戦争|戦い|乱|変',
        r'条約|同盟|協定',
        r'改革|政策|法|令',
        r'文化|仏教|神道',
        r'遺跡|古墳|城'
    ],
    'civics': [
        r'憲法|法律|条文',
        r'国会|内閣|裁判所',
        r'選挙|投票|議員',
        r'権利|義務|自由',
        r'国際連合|国連|安全保障',
        r'経済|金融|財政',
        r'税|社会保障|福祉'
    ]
}

def extract_social_questions(text: str) -> list:
    """
    社会科特有のパターンで設問を抽出
    
    Args:
        text: 分析対象のテキスト
        
    Returns:
        設問リスト
    """
    questions = []
    
    # 全パターンでマッチング
    for pattern_name, pattern_info in SOCIAL_QUESTION_PATTERNS.items():
        regex = re.compile(pattern_info['pattern'], pattern_info.get('flags', 0))
        
        for match in regex.finditer(text):
            questions.append({
                'pattern': pattern_name,
                'type': pattern_info['type'],
                'description': pattern_info['description'],
                'position': match.span(),
                'text': match.group(0),
                'match_groups': match.groups()
            })
    
    # 位置順にソート
    questions.sort(key=lambda x: x['position'][0])
    
    return questions

def identify_social_field(text: str) -> dict:
    """
    テキストから社会科の分野を判定
    
    Args:
        text: 分析対象のテキスト
        
    Returns:
        分野ごとのスコア
    """
    scores = {
        'geography': 0,
        'history': 0,
        'civics': 0
    }
    
    for field, patterns in SOCIAL_FIELD_PATTERNS.items():
        for pattern in patterns:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            scores[field] += matches
    
    # 最も高いスコアの分野を主分野とする
    main_field = max(scores, key=scores.get) if max(scores.values()) > 0 else 'unknown'
    
    return {
        'scores': scores,
        'main_field': main_field,
        'confidence': max(scores.values()) / sum(scores.values()) if sum(scores.values()) > 0 else 0
    }

def extract_subquestions(text: str, parent_question_pos: tuple) -> list:
    """
    親設問の下にある小問を抽出
    
    Args:
        text: 分析対象のテキスト
        parent_question_pos: 親設問の位置（開始, 終了）
        
    Returns:
        小問リスト
    """
    # 親設問の後のテキストを取得
    sub_text = text[parent_question_pos[1]:]
    
    # 次の大問までのテキストを取得（大問パターンで区切る）
    next_main_match = re.search(r'^[一二三四五六七八九十]\s*[、．.]|^問[一二三四五六七八九十]', 
                                sub_text, re.MULTILINE)
    if next_main_match:
        sub_text = sub_text[:next_main_match.start()]
    
    # 小問パターンを検索
    subquestions = []
    patterns = [
        (r'\(([a-z])\)', 'alphabet_lower'),
        (r'\(([A-Z])\)', 'alphabet_upper'),
        (r'\(([ア-ン])\)', 'katakana'),
        (r'\(([1-9][0-9]?)\)', 'number'),
        (r'([①-⑳])', 'circle_number'),
        (r'([㋐-㋾])', 'circle_katakana')
    ]
    
    for pattern, pattern_type in patterns:
        for match in re.finditer(pattern, sub_text):
            subquestions.append({
                'type': pattern_type,
                'marker': match.group(1),
                'position': (parent_question_pos[1] + match.start(), 
                           parent_question_pos[1] + match.end()),
                'text': match.group(0)
            })
    
    # 位置順にソート
    subquestions.sort(key=lambda x: x['position'][0])
    
    return subquestions

def count_all_questions(text: str) -> dict:
    """
    全設問数を正確にカウント
    
    Args:
        text: 分析対象のテキスト
        
    Returns:
        設問数の詳細
    """
    # 大問を検出
    main_questions = re.findall(r'問[一二三四五六七八九十]|^[一二三四五六七八九十]\s*[、．.]', 
                                text, re.MULTILINE)
    
    # 全ての小問パターンを検出
    subquestion_patterns = [
        (r'\([a-z]\)', 'alphabet_lower'),
        (r'\([A-Z]\)', 'alphabet_upper'),
        (r'\([ア-ン]\)', 'katakana'),
        (r'\([1-9][0-9]?\)', 'number'),
        (r'[①-⑳]', 'circle_number'),
        (r'[㋐-㋾]', 'circle_katakana'),
        (r'[\[［][A-Za-z][\]］]', 'blank_alphabet'),
        (r'[□■▢▣]', 'blank_square')
    ]
    
    subquestion_count = {}
    total_subquestions = 0
    
    for pattern, pattern_type in subquestion_patterns:
        matches = re.findall(pattern, text)
        count = len(matches)
        if count > 0:
            subquestion_count[pattern_type] = count
            total_subquestions += count
    
    return {
        'main_questions': len(main_questions),
        'subquestions': total_subquestions,
        'total': len(main_questions) + total_subquestions,
        'subquestion_breakdown': subquestion_count
    }