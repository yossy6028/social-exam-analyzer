"""
設定ファイル - すべての定数とコンフィグをここに集約
"""
from pathlib import Path
from typing import List, Dict, Any

class Settings:
    """アプリケーション全体の設定"""
    
    # ファイル関連
    MAX_FILES_TO_DISPLAY = 50  # ファイル選択時の最大表示数
    MAX_FILES_PER_SCHOOL = 5   # 学校ごとの最大表示ファイル数
    MIN_PATH_DISPLAY_LENGTH = 60  # パス表示の最小長
    DEFAULT_ENCODING_LIST = ['utf-8', 'shift-jis', 'euc-jp', 'cp932', 'iso-2022-jp', 'utf-16']
    
    # 年度関連
    MIN_YEAR_2DIGIT = 14        # 2桁年度の最小値（2014年）
    MAX_YEAR_2DIGIT = 25        # 2桁年度の最大値（2025年）
    MIN_VALID_YEAR = 1990       # 有効年度の最小値
    MAX_VALID_YEAR = 2030       # 有効年度の最大値
    
    # テキスト分析関連
    MIN_SECTION_DISTANCE = 500  # セクション間の最小文字数
    MIN_SECTION_CONTENT = 50    # 有効なセクションの最小文字数
    MIN_QUESTION_DISTANCE = 30  # 設問間の最小文字数
    MIN_VALID_SECTION_SIZE = 200  # 有効なセクションの最小サイズ
    
    # 学校名パターン
    SCHOOL_PATTERNS = {
        r'開成': '開成中学校',
        r'桜蔭|桜陰': '桜蔭中学校',
        r'麻布': '麻布中学校',
        r'武蔵': '武蔵中学校',
        r'女子学院|JG': '女子学院中学校',
        r'雙葉|双葉': '雙葉中学校',
        r'筑駒|筑波大.*駒場': '筑波大学附属駒場中学校',
        r'渋(?:谷)?教?(?:育)?(?:学園)?渋谷?|渋渋|渋幕': '渋谷教育学園渋谷中学校',
        r'聖光(?:学院)?': '聖光学院中学校',
        r'栄光(?:学園)?': '栄光学園中学校',
        r'慶應|慶応': '慶應義塾中等部',
        r'早稲田実業|早実': '早稲田実業学校中等部',
        r'豊島岡|豊島': '豊島岡女子学園中学校',
        r'海城': '海城中学校',
        r'駒場東邦|駒東': '駒場東邦中学校',
        r'灘': '灘中学校',
    }
    
    # 年度パターン
    YEAR_PATTERNS = [
        r'(20\d{2})年度',
        r'(20\d{2})年',
        r'令和(\d{1,2})年度',
        r'平成(\d{1,2})年度',
        r'(20\d{2})\s*入学試験',
        r'(20\d{2})\s*年\s*入試',
    ]
    
    # 学校別年度パターン
    SCHOOL_YEAR_PATTERNS = [
        r'武蔵(\d{2})',
        r'開成(\d{2})',
        r'麻布(\d{2})',
        r'桜蔭(\d{2})',
        r'女子学院(\d{2})',
        r'雙葉(\d{2})',
        r'渋渋(\d{2})',
        r'渋谷(\d{2})',
        r'慶應(\d{2})',
        r'早実(\d{2})',
    ]
    
    # 設問パターン
    QUESTION_PATTERNS = {
        '記述': [
            r'〜について、.*書[きけ]なさい',
            r'〜について.*説明[しせ]よ',
            r'〜について.*述[べべ]なさい',
            r'.*字以内.*書[きけ]',
            r'.*字で.*書[きけ]',
            r'.*説明[しせ]よ',
            r'.*理由.*書[きけ]',
            r'.*どう思[うい].*書[きけ]'
        ],
        '選択': [
            r'次のうち.*正[しい]',
            r'選[びば]なさい',
            r'どれ[かか]',
            r'[ア-オ].*選[びば]',
            r'記号.*選[びば]',
            r'最[もも]適当.*[ア-オ]'
        ],
        '漢字・語句': [
            r'漢字.*読[みみ]',
            r'ひらがな.*書[きけ]',
            r'カタカナ.*書[きけ]',
            r'漢字.*書[きけ]',
            r'語句.*意味',
            r'言葉.*意味'
        ],
        '抜き出し': [
            r'抜[きき]出[しし]',
            r'そのまま.*書[きけ]',
            r'文中.*[から].*探[しし]',
            r'該当.*箇所'
        ]
    }
    
    # 出典パターン（学校別）
    SOURCE_PATTERNS = {
        'musashi': [  # 武蔵特有
            r'（([^）]+)の文による）',
            r'（([^）]+)著）',
            r'『([^』]+)』.*（([^）]+)）',
            r'『([^』]+)』',
            r'「([^」]+)」.*（([^）]+)）',
        ],
        'default': [  # 標準
            r'『([^』]+)』\s*([^\s]+)',
            r'「([^」]+)」\s*([^\s]+)',
            r'([^\s]+)\s*著\s*『([^』]+)』',
            r'([^\s]+)\s*『([^』]+)』',
            r'（([^）]+)）',
        ]
    }
    
    # ディレクトリ設定
    OUTPUT_DIR = Path("data/output")
    BACKUP_DIR = Path("data/backups")
    LOG_DIR = Path("logs")
    
    # Excel設定
    EXCEL_ENGINE = 'openpyxl'
    # デフォルトパスは環境変数またはapp_configから取得
    DEFAULT_DB_FILENAME = None  # app_config.pyで動的に設定
    
    @classmethod
    def get_search_directories(cls) -> List[Path]:
        """検索対象ディレクトリのリストを返す"""
        import os
        directories = [
            Path.cwd(),
            Path.home() / "Desktop",
        ]
        
        # 環境変数で追加ディレクトリを指定可能
        if os.getenv('ENTRANCE_EXAM_SEARCH_DIRS'):
            for dir_str in os.getenv('ENTRANCE_EXAM_SEARCH_DIRS').split(':'):
                directories.append(Path(dir_str))
        else:
            # デフォルトの検索パス（ユーザー固有情報を含まない）
            directories.extend([
                Path.home() / "Desktop" / "01_仕事 (Work)" / "オンライン家庭教師資料" / "過去問",
                Path.home() / "Desktop" / "過去問のエイリアス",
            ])
        
        return directories
    
    @classmethod
    def get_allowed_directories(cls) -> List[Path]:
        """セキュリティ: アクセス許可ディレクトリのリストを返す"""
        import os
        allowed = [
            Path.home().resolve(),
            Path.cwd().resolve(),
        ]
        if os.name == 'posix':
            allowed.append(Path("/tmp").resolve())
        else:
            temp_dir = os.environ.get('TEMP', '')
            if temp_dir:
                allowed.append(Path(temp_dir).resolve())
        return allowed