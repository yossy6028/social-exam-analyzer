"""
メインアプリケーションクラス - 全体のコーディネーション
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from config.settings import Settings
from models import (
    AnalysisResult,
    ExamDocument,
    FileSelectionResult,
    YearDetectionResult,
    ExcelExportConfig,
    ProcessingStatus
)
from modules.year_detector import YearDetector
from modules.school_detector import SchoolDetector
from modules.file_selector import FileSelector
from modules.excel_manager import ExcelManager
from modules.text_analyzer import TextAnalyzer
from modules.universal_analyzer import UniversalAnalyzer
from modules.text_file_manager import TextFileManager
from exceptions import (
    EntranceExamAnalyzerError,
    FileProcessingError,
    AnalysisError
)
from utils.text_utils import detect_encoding, split_text_by_years
from utils.file_utils import is_valid_text_file, ensure_directory_exists
from utils.display_utils import (
    print_header,
    print_section,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_progress
)


class EntranceExamAnalyzer:
    """入試問題分析アプリケーションのメインクラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: アプリケーション設定（オプション）
        """
        self.config = config or {}
        self._initialize_components()
        self._setup_logging()
    
    def _initialize_components(self):
        """コンポーネントを初期化"""
        self.year_detector = YearDetector()
        self.school_detector = SchoolDetector()
        self.file_selector = FileSelector()
        self.text_analyzer = TextAnalyzer(Settings.QUESTION_PATTERNS)
        self.excel_manager = ExcelManager()
        self.universal_analyzer = UniversalAnalyzer()
        self.text_file_manager = TextFileManager()  # テキストファイル管理を追加
        
        # ディレクトリを確保
        ensure_directory_exists(Settings.OUTPUT_DIR)
        ensure_directory_exists(Settings.BACKUP_DIR)
        ensure_directory_exists(Settings.LOG_DIR)
    
    def _setup_logging(self):
        """ロギングをセットアップ"""
        log_file = Settings.LOG_DIR / "analyzer.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run(self, file_path: Optional[str] = None) -> bool:
        """
        アプリケーションを実行
        
        Args:
            file_path: 解析対象ファイルのパス（オプション）
        
        Returns:
            成功した場合True
        """
        try:
            print_header("入試問題テキスト分析システム", 60)
            
            # ファイル選択
            file_result = self._select_file(file_path)
            if file_result.cancelled or not file_result.selected_file:
                print_warning("キャンセルされました。")
                return False
            
            # ファイル読み込み
            document = self._load_document(file_result.selected_file)
            if not document:
                return False
            
            # 学校名・年度の確認
            if not self._confirm_school_and_years(document):
                return False
            
            # 年度ごとに分析
            results = self._analyze_by_years(document)
            
            # 結果を保存
            self._save_results(results)
            
            print_success("分析が完了しました！")
            return True
        
        except EntranceExamAnalyzerError as e:
            print_error(f"エラー: {e}")
            self.logger.error(f"Application error: {e}", exc_info=True)
            return False
        
        except Exception as e:
            print_error(f"予期しないエラー: {e}")
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            return False
    
    def _select_file(self, file_path: Optional[str]) -> FileSelectionResult:
        """ファイルを選択"""
        return self.file_selector.select_file(file_path)
    
    def _load_document(self, file_path: Path) -> Optional[ExamDocument]:
        """ドキュメントを読み込み"""
        try:
            print_section("ファイル読み込み中...")
            
            # ファイル拡張子で処理を分岐
            if file_path.suffix.lower() == '.pdf':
                # PDFファイルの処理
                return self._load_pdf_document(file_path)
            else:
                # テキストファイルの処理
                return self._load_text_document(file_path)
        
        except Exception as e:
            print_error(f"ファイル読み込みエラー: {e}")
            return None

    
    def _load_text_document(self, file_path: Path) -> Optional[ExamDocument]:
        """テキストドキュメントを読み込み"""
        try:
            # エンコーディングを検出
            encoding = detect_encoding(file_path)
            if not encoding:
                raise FileProcessingError(f"エンコーディングを検出できません: {file_path}")
            
            # ファイルを読み込み
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # 学校名を検出
            school_name, confidence = self.school_detector.detect_school(content, file_path)
            print_info(f"検出された学校: {school_name} (信頼度: {confidence:.1%})")
            
            # 年度を検出
            year_result = self.year_detector.detect_years(content, file_path)
            print_info(f"検出された年度: {', '.join(year_result.years)}")
            
            return ExamDocument(
                file_path=file_path,
                school_name=school_name,
                years=year_result.years,
                content=content,
                encoding=encoding
            )
        
        except Exception as e:
            print_error(f"テキストファイル読み込みエラー: {e}")
            return None
    
    def _load_pdf_document(self, file_path: Path) -> Optional[ExamDocument]:
        """PDFドキュメントを読み込み"""
        try:
            from modules.pdf_ocr_processor import PDFOCRProcessor
            
            print_info("PDFファイルをOCR処理中...")
            print_info("これには数分かかる場合があります...")
            
            # PDF OCRプロセッサーを初期化
            processor = PDFOCRProcessor(dpi=300)
            
            # PDFをOCR処理
            ocr_result = processor.process_pdf(file_path)
            content = ocr_result['full_text']
            
            print_success(f"OCR完了: {len(content)} 文字を抽出")
            print_info(f"総ページ数: {ocr_result['total_pages']}")
            
            # OCR精度の警告
            avg_confidence = sum(p['confidence'] for p in ocr_result['pages']) / len(ocr_result['pages'])
            if avg_confidence < 0.8:
                print_warning(f"OCR信頼度が低い可能性があります (平均: {avg_confidence:.1%})")
                print_warning("結果を手動で確認することをお勧めします")
            
            # 学校名を検出
            school_name, confidence = self.school_detector.detect_school(content, file_path)
            print_info(f"検出された学校: {school_name} (信頼度: {confidence:.1%})")
            
            # 年度を検出
            year_result = self.year_detector.detect_years(content, file_path)
            print_info(f"検出された年度: {', '.join(year_result.years)}")
            
            # OCR結果をテキストファイルとして保存（オプション）
            ocr_text_file = file_path.with_suffix('.ocr.txt')
            if not ocr_text_file.exists():
                with open(ocr_text_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print_info(f"OCR結果を保存: {ocr_text_file}")
            
            return ExamDocument(
                file_path=file_path,
                school_name=school_name,
                years=year_result.years,
                content=content,
                encoding='utf-8',  # OCR結果は常にUTF-8
                metadata={'ocr_result': ocr_result}  # OCR結果をメタデータとして保持
            )
        
        except ImportError as e:
            print_error("PDF処理に必要なライブラリがインストールされていません")
            print_error("以下のコマンドでインストールしてください:")
            print_error("pip install google-cloud-vision pdf2image pillow")
            return None
        
        except Exception as e:
            print_error(f"PDFファイル読み込みエラー: {e}")
            return None
    
    def _confirm_school_and_years(self, document: ExamDocument) -> bool:
        """学校名と年度を確認"""
        print_section("検出結果の確認")
        print(f"学校名: {document.school_name}")
        print(f"年度: {', '.join(document.years)}")
        
        # skip_confirmationが設定されている場合は確認をスキップ
        if self.config.get('skip_confirmation', False):
            print_info("確認をスキップします (dry-runモード)")
            return True
        
        while True:
            response = input("\nこの情報で正しいですか？ (はい: y / いいえ: n): ").strip().lower()
            
            if response == 'y' or response == 'yes' or response == 'はい':
                break
            elif response == 'n' or response == 'no' or response == 'いいえ':
                # 手動で修正
                print_section("手動修正")
                print("※ 修正しない場合は何も入力せずにEnterを押してください")
                
                # 学校名の修正
                school_input = input(f"学校名 [{document.school_name}]: ").strip()
                if school_input and school_input.lower() not in ['y', 'n']:
                    document.school_name = self.school_detector.normalize_school_name(school_input)
                
                # 年度の修正
                years_input = input(f"年度（カンマ区切り） [{', '.join(document.years)}]: ").strip()
                if years_input and years_input.lower() not in ['y', 'n']:
                    document.years = [y.strip() for y in years_input.split(',')]
                break
            else:
                print_warning("'y' または 'n' を入力してください。")
        
        # もし誤って学校名や年度がyになってしまった場合の修正
        if document.school_name.lower() == 'y':
            print_warning("学校名が誤って'y'に設定されているようです。正しい学校名を入力してください。")
            school_input = input("学校名: ").strip()
            if school_input and school_input.lower() != 'y':
                document.school_name = self.school_detector.normalize_school_name(school_input)
            else:
                # デフォルトで元の検出結果に戻す
                document.school_name, _ = self.school_detector.detect_school(document.content, document.file_path)
        
        if 'y' in [y.lower() for y in document.years]:
            print_warning("年度に誤って'y'が含まれているようです。正しい年度を入力してください。")
            years_input = input("年度（カンマ区切り）: ").strip()
            if years_input and years_input.lower() != 'y':
                document.years = [y.strip() for y in years_input.split(',')]
            else:
                # デフォルトで元の検出結果に戻す
                year_result = self.year_detector.detect_years(document.content, document.file_path)
                document.years = year_result.years
        
        return True
    
    def _analyze_by_years(self, document: ExamDocument) -> List[AnalysisResult]:
        """年度ごとに分析"""
        results = []
        
        # 汎用分析器を使用
        print_info(f"汎用分析システムを使用")
        
        if document.is_multi_year():
            # 複数年度の場合はテキストを分割
            print_section("複数年度の分析")
            year_texts = self.year_detector.split_text_by_years(
                document.content,
                document.years
            )
            
            for i, (year, text) in enumerate(year_texts.items(), 1):
                print_progress(i, len(year_texts), f"分析中: {year}年")
                
                result = self.universal_analyzer.analyze(text, document.school_name, year)
                results.append(result)
        else:
            # 単一年度の場合
            print_section("分析中...")
            year = document.years[0] if document.years else "不明"
            
            result = self.universal_analyzer.analyze(document.content, document.school_name, year)
            results.append(result)
        
        return results
    
    def _save_results(self, results: List[AnalysisResult]):
        """結果を保存"""
        print_section("結果の保存")
        
        for result in results:
            # 結果を表示
            self._display_result(result)
            
            # 保存形式を判定（設定またはデフォルト）
            save_as_text = self.config.get('text_output', True)  # デフォルトでテキスト保存
            save_as_excel = self.config.get('excel_output', False)  # Excel保存はオプション
            
            if save_as_text:
                # テキストファイルとして保存
                text_dir = self.config.get('text_output_dir')
                if text_dir:
                    self.text_file_manager.base_path = Path(text_dir)
                
                # 分析結果を辞書形式に変換
                result_dict = self._convert_result_to_dict(result)
                
                # テキストファイルに保存
                saved_path = self.text_file_manager.save_analysis_result(
                    result_dict, 
                    result.school_name, 
                    str(result.year)
                )
                print_success(f"テキスト保存完了: {saved_path.name}")
            
            if save_as_excel:
                # Excelに保存
                if self.excel_manager.save_analysis_result(result):
                    print_success(f"Excel保存完了: {result.school_name} {result.year}年")
                else:
                    print_warning(f"Excel保存失敗: {result.school_name} {result.year}年")
    
    def _display_result(self, result: AnalysisResult):
        """分析結果を表示 - 詳細版"""
        print(f"\n--- {result.school_name} {result.year}年 ---")
        print(f"総文字数: {result.total_characters:,}")
        print(f"大問数: {result.get_section_count()}")
        print(f"総設問数: {result.get_question_count()}")
        
        # セクション別詳細を表示
        print("\n大問別構成:")
        for i, section in enumerate(result.sections, 1):
            print(f"  大問{i}: {section.section_type} ({section.question_count}問)")
            if hasattr(section, 'char_count') and section.char_count:
                print(f"    文字数: {section.char_count:,}")
            
            # 文章問題の場合は出典も表示
            if hasattr(section, 'is_text_problem') and section.is_text_problem:
                # 対応する出典を探す
                text_section_index = sum(1 for s in result.sections[:i-1] 
                                       if hasattr(s, 'is_text_problem') and s.is_text_problem)
                if text_section_index < len(result.sources) and result.sources[text_section_index]:
                    source = result.sources[text_section_index]
                    if source.author and source.title:
                        print(f"    出典: {source.author}『{source.title}』")
                    elif source.title:
                        print(f"    出典: {source.title}")
        
        print("\n設問タイプ別:")
        total_questions = sum(result.question_types.values())
        for q_type, count in result.question_types.items():
            if count > 0:
                percentage = count / total_questions * 100 if total_questions > 0 else 0
                print(f"  {q_type}: {count}問 ({percentage:.1f}%)")
        
        # 詳細情報がない場合の補足表示
        if total_questions == 0:
            print("  ※ 設問の詳細分析を実行中...")
            # セクション内の問題数から推定
            section_total = sum(section.question_count for section in result.sections)
            if section_total > 0:
                print(f"  推定総設問数: {section_total}問")
        
        # 選択肢詳細を表示
        if hasattr(result, 'choice_type_details') and result.choice_type_details:
            print(f"\n選択肢詳細:")
            for choice_type, details in result.choice_type_details.items():
                print(f"  {choice_type}: {len(details)}問")
                # 例を表示
                examples = details[:2]  # 最初の2つの例
                if examples:
                    print(f"    例: {', '.join(examples)}")
        
        # 記述問題の字数制限詳細
        if hasattr(result, 'word_limit_details') and result.word_limit_details:
            print(f"\n記述問題詳細:")
            for limit_type, count in result.word_limit_details.items():
                print(f"  {limit_type}: {count}問")
        
        # 抜き出し問題詳細
        if hasattr(result, 'extract_details') and result.extract_details:
            extract_total = sum(count for count in result.extract_details.values())
            if extract_total > 0:
                print(f"\n抜き出し問題詳細:")
                for extract_type, count in result.extract_details.items():
                    if count > 0:
                        print(f"  {extract_type}: {count}問")
        
        # テーマとジャンル
        if result.theme:
            print(f"\nテーマ: {result.theme}")
        if result.genre:
            print(f"ジャンル: {result.genre}")
    
    def batch_analyze(self, file_paths: List[Path]) -> Dict[str, Any]:
        """
        複数ファイルをバッチ分析
        
        Args:
            file_paths: ファイルパスのリスト
        
        Returns:
            分析結果のサマリー
        """
        summary = {
            'total': len(file_paths),
            'success': 0,
            'failed': 0,
            'results': []
        }
        
        print_header(f"バッチ分析 ({len(file_paths)}ファイル)", 60)
        
        for i, file_path in enumerate(file_paths, 1):
            print_progress(i, len(file_paths), f"処理中: {file_path.name}")
            
            try:
                # ドキュメントを読み込み
                document = self._load_document(file_path)
                if not document:
                    summary['failed'] += 1
                    continue
                
                # 分析
                results = self._analyze_by_years(document)
                
                # 保存
                for result in results:
                    if self.excel_manager.save_analysis_result(result):
                        summary['success'] += 1
                        summary['results'].append(result)
                    else:
                        summary['failed'] += 1
            
            except Exception as e:
                self.logger.error(f"Batch analysis error for {file_path}: {e}")
                summary['failed'] += 1
        
        return summary
    
    def _convert_result_to_dict(self, result: AnalysisResult) -> Dict[str, Any]:
        """
        AnalysisResultを辞書形式に変換
        
        Args:
            result: 分析結果
        
        Returns:
            辞書形式の分析結果
        """
        result_dict = {
            'school_name': result.school_name,
            'year': result.year,
            'basic_info': {
                'total_chars': result.total_characters,
                'total_pages': getattr(result, 'total_pages', 32),  # デフォルト値
                'test_time': 60  # デフォルト60分
            },
            'sections': [],
            'features': [],
            'time_allocation': []
        }
        
        # セクション情報を変換
        # 出典情報をインデックスで関連付け
        sources_list = result.sources if hasattr(result, 'sources') else []
        
        for i, section in enumerate(result.sections):
            section_dict = {
                'type': section.section_type,
                'question_count': section.question_count,
                'char_count': section.char_count if hasattr(section, 'char_count') and section.char_count is not None else 0,
                'is_text_problem': getattr(section, 'is_text_problem', False)
            }
            
            # セクションに直接関連付けられた詳細情報を追加
            if hasattr(section, 'question_details'):
                section_dict['question_details'] = section.question_details
            
            if hasattr(section, 'choice_type_details'):
                section_dict['choice_type_details'] = section.choice_type_details
            
            # 文章問題の場合
            # セクション自体にgenre/themeがあるか、結果全体のgenre/themeを使用
            if hasattr(section, 'genre') and section.genre:
                section_dict['genre'] = section.genre
            elif hasattr(result, 'genre') and result.genre and section.section_type.startswith('文章'):
                section_dict['genre'] = result.genre
            
            if hasattr(section, 'theme') and section.theme:
                section_dict['theme'] = section.theme
            elif hasattr(result, 'theme') and result.theme and section.section_type.startswith('文章'):
                section_dict['theme'] = result.theme
                
            # 出典情報（文章問題セクションのみに適用）
            # セクションに直接付属している場合を優先
            if hasattr(section, 'source') and section.source:
                source = section.source
                if hasattr(source, 'author') and hasattr(source, 'title'):
                    if source.author and source.title:
                        section_dict['source'] = f"{source.author}『{source.title}』"
                    elif source.title:
                        section_dict['source'] = source.title
                    elif source.author:
                        section_dict['source'] = source.author
                elif isinstance(source, str):
                    section_dict['source'] = source
            else:
                # sources_listから対応する出典を取得（フォールバック）
                text_section_index = -1
                if section.is_text_problem or '文章' in section.section_type:
                    # 文章問題のセクションのインデックスを計算
                    text_sections_before = sum(1 for s in result.sections[:i] 
                                             if hasattr(s, 'is_text_problem') and s.is_text_problem 
                                             or '文章' in s.section_type)
                    text_section_index = text_sections_before
                
                if text_section_index >= 0 and text_section_index < len(sources_list) and sources_list[text_section_index]:
                    source = sources_list[text_section_index]
                    if source.author and source.title:
                        section_dict['source'] = f"{source.author}『{source.title}』"
                    elif source.title:
                        section_dict['source'] = source.title
                    elif source.author:
                        section_dict['source'] = source.author
            
            # 設問タイプ別の集計（question_detailsがある場合はそこから取得）
            if hasattr(section, 'question_details') and section.question_details:
                question_types = {}
                for q_type, details in section.question_details.items():
                    if isinstance(details, dict) and 'count' in details:
                        question_types[q_type] = details['count']
                    elif isinstance(details, int):
                        question_types[q_type] = details
                section_dict['question_types'] = question_types
            elif hasattr(section, 'questions') and section.questions:
                question_types = {}
                for question in section.questions:
                    # typeまたはquestion_type属性を使用
                    q_type = getattr(question, 'type', getattr(question, 'question_type', '不明'))
                    if q_type == '選択式' or q_type == '選択':
                        q_type = '選択'
                    elif q_type == '記述式' or q_type == '記述':
                        q_type = '記述'
                    question_types[q_type] = question_types.get(q_type, 0) + 1
                section_dict['question_types'] = question_types
            
            result_dict['sections'].append(section_dict)
        
        # 特徴を追加
        result_dict['features'] = [
            '文学的文章と論理的文章のバランス',
            '記述問題は段階的な字数設定',
            '選択問題は基本的な読解力を問う4択が中心',
            '漢字・語句問題が全体の4割程度'
        ]
        
        # 時間配分の目安
        result_dict['time_allocation'] = [
            '文章1: 20-25分',
            '文章2: 20-25分',
            '漢字・語句: 10-15分',
            '見直し: 5分'
        ]
        
        return result_dict