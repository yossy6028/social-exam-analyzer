"""
出典抽出用パターン定義
"""
import re

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
    
    'paren_author_quote_yori': {
        'pattern': r'（([^\s『「）]+)\s*「([^」]+)」\s*より）',
        'flags': 0,
        'priority': 8,
        'description': '（著者「タイトル」より）'
    },
    
    'author_title_yori': {
        'pattern': r'([^\s『「（）]+)\s*『([^』]+)』\s*より',
        'flags': 0,
        'priority': 7,
        'description': '著者『タイトル』より'
    },
    
    # 「から」パターン
    'author_title_kara': {
        'pattern': r'([^\s『「（）]+)\s*『([^』]+)』\s*から',
        'flags': 0,
        'priority': 6,
        'description': '著者『タイトル』から'
    },
    
    'title_author_kara': {
        'pattern': r'『([^』]+)』\s*（([^）]+)）\s*から',
        'flags': 0,
        'priority': 6,
        'description': '『タイトル』（著者）から'
    },
    
    # 出典ラベル付き
    'source_label_author_title': {
        'pattern': r'出典\s*[：:]\s*([^\s『「（）]+)\s*『([^』]+)』',
        'flags': 0,
        'priority': 5,
        'description': '出典：著者『タイトル』'
    },
    
    'source_label_title_author': {
        'pattern': r'出典\s*[：:]\s*『([^』]+)』\s*（([^）]+)）',
        'flags': 0,
        'priority': 5,
        'description': '出典：『タイトル』（著者）'
    },
    
    'asterisk_author_title': {
        'pattern': r'※\s*([^\s『「（）]+)\s*『([^』]+)』',
        'flags': 0,
        'priority': 5,
        'description': '※著者『タイトル』'
    },
    
    # 説明文付き
    'description_author_title': {
        'pattern': r'次の文章は[、，]\s*([^\s『「（）]+)の『([^』]+)』',
        'flags': 0,
        'priority': 4,
        'description': '次の文章は、著者の『タイトル』'
    },
    
    'author_title_excerpt': {
        'pattern': r'([^\s『「（）]+)『([^』]+)』の一節',
        'flags': 0,
        'priority': 4,
        'description': '著者『タイトル』の一節'
    },
    
    # 古典・無著者パターン
    'title_only_niyoru': {
        'pattern': r'『([^』]+)』\s*による',
        'flags': 0,
        'priority': 3,
        'description': '『タイトル』による（著者なし）'
    },
    
    'title_only_yori': {
        'pattern': r'『([^』]+)』\s*より',
        'flags': 0,
        'priority': 3,
        'description': '『タイトル』より（著者なし）'
    },
    
    # 文章・文による
    'author_text_niyoru': {
        'pattern': r'([^\s『「（）]+)の文\s*による',
        'flags': 0,
        'priority': 2,
        'description': '著者の文による'
    },
    
    'author_bunshō_niyoru': {
        'pattern': r'([^\s『「（）]+)の文章\s*による',
        'flags': 0,
        'priority': 2,
        'description': '著者の文章による'
    }
}

# 出典抽出設定
SOURCE_CONFIG = {
    'max_sources_per_section': 5,  # セクションごとの最大出典数
    'search_range_end': 2000,  # セクション末尾から検索する文字数
    'search_range_start': 500,  # セクション冒頭から検索する文字数
    'max_total_sources': 10  # 全体の最大出典数
}