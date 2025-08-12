"""
テキストファイル管理モジュール
分析結果を年度別・学校別のテキストファイルとして保存
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
# Rich consoleは必須ではないので、利用可能な場合のみ使用
try:
    from rich.console import Console
    console = Console()
    USE_RICH = True
except ImportError:
    USE_RICH = False
    
def print_success(message: str):
    """成功メッセージを出力"""
    if USE_RICH:
        console.print(f"[green]✓[/green] {message}")
    else:
        print(f"✓ {message}")

class TextFileManager:
    """テキストファイル管理クラス"""
    
    def __init__(self, base_path: str = None):
        """
        初期化
        
        Args:
            base_path: 保存先の基本パス（デフォルト: ~/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問）
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            # デフォルトの保存先
            self.base_path = Path.home() / "Desktop" / "01_仕事 (Work)" / "オンライン家庭教師資料" / "過去問"
        
        # ディレクトリが存在しない場合は作成
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_analysis_result(self, result: Dict[str, Any], school_name: str, year: str) -> Path:
        """
        分析結果をテキストファイルとして保存
        
        Args:
            result: 分析結果
            school_name: 学校名
            year: 年度
        
        Returns:
            保存したファイルのパス
        """
        # ファイル名を生成（例: 2025年度聖光学院.txt）
        filename = f"{year}年度{school_name}.txt"
        file_path = self.base_path / filename
        
        # テキスト内容を生成
        content = self._generate_text_content(result, school_name, year)
        
        # ファイルに保存
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_success(f"分析結果を保存しました: {file_path}")
        return file_path
    
    def _generate_text_content(self, result: Dict[str, Any], school_name: str, year: str) -> str:
        """
        分析結果からテキスト内容を生成
        
        Args:
            result: 分析結果
            school_name: 学校名
            year: 年度
        
        Returns:
            フォーマットされたテキスト内容
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"{school_name} {year}年度 国語入試問題 詳細分析結果")
        lines.append("=" * 70)
        lines.append("")
        
        # 基本情報
        lines.append("【基本情報】")
        lines.append(f"学校名: {school_name}")
        lines.append(f"年度: {year}年")
        lines.append(f"分析日: {datetime.now().strftime('%Y年%m月%d日')}")
        
        if 'basic_info' in result:
            info = result['basic_info']
            if 'test_time' in info:
                lines.append(f"試験時間: {info['test_time']}分")
            if 'total_pages' in info:
                lines.append(f"総ページ数: {info['total_pages']}ページ")
            if 'total_chars' in info:
                lines.append(f"総文字数: 約{info['total_chars']:,}文字")
        lines.append("")
        
        # 文章問題の詳細分析
        lines.append("【文章問題の詳細分析】")
        lines.append("")
        
        text_sections = []
        other_sections = []
        
        # セクションを分類
        for section in result.get('sections', []):
            if self._is_text_section_for_report(section):
                text_sections.append(section)
            else:
                other_sections.append(section)
        
        # 文章問題を出力
        for i, section in enumerate(text_sections, 1):
            lines.append("━" * 70)
            lines.append(f"■ 文章{i}: {section.get('genre', section.get('type', '不明'))}")
            lines.append("━" * 70)
            
            if 'source' in section:
                lines.append(f"  出典: {section['source']}")
            if 'genre' in section:
                lines.append(f"  ジャンル: {section['genre']}")
            if 'char_count' in section:
                lines.append(f"  文字数: 約{section['char_count']:,}文字")
            lines.append("")
            
            # テーマ・要旨
            if 'theme' in section or 'summary' in section:
                lines.append("  【テーマ・要旨】")
                if 'theme' in section:
                    lines.append(f"  主題: {section['theme']}")
                if 'summary' in section:
                    lines.append(f"  要旨: {section['summary']}")
                lines.append("")
            
            # 設問分析
            lines.append(f"  【設問分析】（全{section.get('question_count', 0)}問）")
            
            # 問題タイプ別の集計（question_detailsがある場合はそれを優先）
            if 'question_details' in section:
                question_details = section['question_details']
                question_types = {}
                
                # 各タイプから問題数を集計
                if '選択' in question_details:
                    question_types['選択'] = question_details['選択'].get('count', 0)
                if '記述' in question_details:
                    question_types['記述'] = question_details['記述'].get('count', 0)
                if '抜き出し' in question_details:
                    question_types['抜き出し'] = question_details['抜き出し'].get('count', 0)
                if '漢字' in question_details:
                    question_types['漢字'] = question_details['漢字'].get('count', 0)
                if '語句' in question_details:
                    question_types['語句'] = question_details['語句'].get('count', 0)
            else:
                question_types = section.get('question_types', {})
            
            # 選択式
            if question_types.get('選択', 0) > 0:
                lines.append(f"  1. 選択式問題: {question_types['選択']}問")
                # question_detailsから詳細を取得
                if 'question_details' in section and '選択' in section['question_details']:
                    choice_details = section['question_details']['選択'].get('details', {})
                    if choice_details:
                        for choice_type, count in choice_details.items():
                            if count > 0:
                                lines.append(f"     - {choice_type}: {count}問")
                elif 'choice_details' in section:
                    for choice_type, count in section['choice_details'].items():
                        lines.append(f"     - {choice_type}: {count}問")
            
            # 記述式
            if question_types.get('記述', 0) > 0:
                lines.append(f"  2. 記述式問題: {question_types['記述']}問")
                # question_detailsから詳細を取得
                if 'question_details' in section and '記述' in section['question_details']:
                    written_details = section['question_details']['記述']
                    if written_details.get('word_limit_details'):
                        for limit_type, count in written_details['word_limit_details'].items():
                            lines.append(f"     - {limit_type}: {count}問")
                    
                    # 字数指定ありとなしの内訳も表示
                    with_limit = written_details.get('with_limit', 0)
                    without_limit = written_details.get('without_limit', 0)
                    
                    # word_limit_detailsがない場合、または字数指定なしがある場合
                    if without_limit > 0:
                        lines.append(f"     - 字数指定なし: {without_limit}問")
                elif 'description_lengths' in section:
                    for length_info in section['description_lengths']:
                        lines.append(f"     - {length_info}")
            
            # 抜き出し
            if question_types.get('抜き出し', 0) > 0:
                lines.append(f"  3. 抜き出し問題: {question_types['抜き出し']}問")
                # question_detailsから詳細を取得
                if 'question_details' in section and '抜き出し' in section['question_details']:
                    extract_details = section['question_details']['抜き出し'].get('details', {})
                    if extract_details:
                        for extract_type, count in extract_details.items():
                            if count > 0:
                                lines.append(f"     - {extract_type}: {count}問")
                elif 'extract_lengths' in section:
                    for length_info in section['extract_lengths']:
                        lines.append(f"     - {length_info}")
            
            # その他
            if question_types.get('その他', 0) > 0:
                lines.append(f"  4. その他: {question_types['その他']}問")
                if 'other_types' in section:
                    for other_info in section['other_types']:
                        lines.append(f"     - {other_info}")
            
            lines.append("")
        
        # その他の問題
        if other_sections:
            lines.append("━" * 70)
            lines.append("■ その他: 漢字・語句問題")
            lines.append("━" * 70)
            
            for section in other_sections:
                lines.append(f"  【出題内容】（全{section.get('question_count', 0)}問）")
                if 'content_types' in section:
                    for j, content_type in enumerate(section['content_types'], 1):
                        lines.append(f"  {j}. {content_type}")
                lines.append("")
        
        # 全体分析
        lines.append("【全体分析】")
        lines.append("─" * 70)
        
        total_questions = sum(s.get('question_count', 0) for s in result.get('sections', []))
        text_questions = sum(s.get('question_count', 0) for s in text_sections)
        other_questions = sum(s.get('question_count', 0) for s in other_sections)
        
        lines.append(f"◆ 総設問数: {total_questions}問")
        if text_questions > 0:
            lines.append(f"  文章問題: {text_questions}問（{text_questions/total_questions*100:.1f}%）")
        if other_questions > 0:
            lines.append(f"  漢字・語句: {other_questions}問（{other_questions/total_questions*100:.1f}%）")
        lines.append("")
        
        # 記述問題の字数分布
        all_description_lengths = []
        for section in text_sections:
            if 'description_lengths' in section:
                all_description_lengths.extend(section['description_lengths'])
        
        if all_description_lengths:
            lines.append("◆ 記述問題の字数分布")
            for length_info in all_description_lengths:
                lines.append(f"  {length_info}")
            lines.append(f"  合計: {len(all_description_lengths)}問")
            lines.append("")
        
        # 選択問題の選択肢数
        all_choice_details = {}
        for section in text_sections:
            if 'choice_details' in section:
                for choice_type, count in section['choice_details'].items():
                    all_choice_details[choice_type] = all_choice_details.get(choice_type, 0) + count
        
        if all_choice_details:
            lines.append("◆ 選択問題の選択肢数")
            for choice_type, count in sorted(all_choice_details.items()):
                lines.append(f"  {choice_type}: {count}問")
            lines.append(f"  合計: {sum(all_choice_details.values())}問")
            lines.append("")
        
        # 出題の特徴と傾向
        if 'features' in result:
            lines.append("【出題の特徴と傾向】")
            lines.append("─" * 70)
            for i, feature in enumerate(result['features'], 1):
                lines.append(f"{i}. {feature}")
            lines.append("")
        
        # 時間配分の目安
        if 'time_allocation' in result:
            lines.append("【時間配分の目安】")
            for item in result['time_allocation']:
                lines.append(f"  • {item}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _is_text_section_for_report(self, section: Dict[str, Any]) -> bool:
        """
        セクションが文章問題かどうかを判定（レポート用）
        
        Args:
            section: セクション情報
        
        Returns:
            文章問題の場合True
        """
        # is_text_problemフラグがある場合は最優先
        if section.get('is_text_problem', False):
            return True
            
        # セクションタイプで判定
        section_type = section.get('type', '').lower()
        
        # 文章系のキーワード
        text_keywords = ['文章', '小説', '物語', '論説', '説明', '随筆', 'エッセイ', '評論']
        
        # その他系のキーワード
        other_keywords = ['漢字', '語句', '言葉', 'ことば', '慣用句', 'ことわざ', '文法']
        
        # キーワードマッチング
        for keyword in text_keywords:
            if keyword in section_type:
                return True
        
        for keyword in other_keywords:
            if keyword in section_type:
                return False
        
        # ジャンルがある場合は文章問題
        if 'genre' in section and section['genre']:
            return True
        
        # 出典がある場合は文章問題
        if 'source' in section and section['source']:
            return True
        
        # 文字数が多い場合は文章問題
        char_count = section.get('char_count')
        if char_count is not None and char_count > 1000:
            return True
        
        return False
    
    def list_saved_files(self) -> List[Path]:
        """
        保存されているファイルの一覧を取得
        
        Returns:
            ファイルパスのリスト
        """
        files = sorted(self.base_path.glob("*年度*.txt"))
        return files
    
    def read_saved_file(self, school_name: str, year: str) -> Optional[str]:
        """
        保存されたファイルを読み込む
        
        Args:
            school_name: 学校名
            year: 年度
        
        Returns:
            ファイル内容（存在しない場合はNone）
        """
        filename = f"{year}年度{school_name}.txt"
        file_path = self.base_path / filename
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None