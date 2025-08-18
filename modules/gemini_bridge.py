"""
Gemini API詳細分析のブリッジモジュール
analyze_with_gemini_detailed.pyの機能をGUIから利用可能にする
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# analyze_with_gemini_detailed.pyから機能をインポート
try:
    from analyze_with_gemini_detailed import GeminiDetailedAnalyzer
    GEMINI_DETAILED_AVAILABLE = True
except ImportError:
    GEMINI_DETAILED_AVAILABLE = False
    GeminiDetailedAnalyzer = None

# SocialQuestionクラスのインポート
from modules.social_analyzer import SocialQuestion, SocialField, ResourceType, QuestionFormat

logger = logging.getLogger(__name__)


class GeminiBridge:
    """
    GUI用のGemini分析ブリッジ
    analyze_with_gemini_detailed.pyの機能をGUIフレンドリーな形で提供
    """
    
    def __init__(self):
        """初期化"""
        self.analyzer = None
        self.is_available = GEMINI_DETAILED_AVAILABLE
        
        if self.is_available:
            try:
                self.analyzer = GeminiDetailedAnalyzer()
                logger.info("GeminiDetailedAnalyzer を正常に初期化しました")
            except Exception as e:
                logger.error(f"GeminiDetailedAnalyzer の初期化に失敗: {e}")
                self.is_available = False
    
    def check_availability(self) -> bool:
        """
        Gemini詳細分析が利用可能かチェック
        """
        if not self.is_available:
            return False
        
        # API キーの確認
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY が設定されていません")
            return False
        
        return True
    
    def analyze_pdf(self, pdf_path: str, callback=None) -> Dict[str, Any]:
        """
        PDFを分析（GUIのプログレスコールバック対応）
        
        Args:
            pdf_path: PDFファイルのパス
            callback: プログレス更新用のコールバック関数
        
        Returns:
            分析結果の辞書
        """
        if not self.check_availability():
            raise ValueError("Gemini詳細分析は利用できません")
        
        try:
            # プログレス通知
            if callback:
                callback("Gemini APIによる詳細分析を開始...")
            
            # 分析実行
            result = self.analyzer.analyze_pdf(pdf_path)
            
            # 結果をGUI用に変換
            converted_result = self._convert_to_gui_format(result)
            
            if callback:
                callback("分析完了")
            
            return converted_result
            
        except Exception as e:
            logger.error(f"Gemini分析エラー: {e}")
            raise
    
    def _convert_to_gui_format(self, gemini_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gemini分析結果をGUIで期待される形式に変換
        
        Args:
            gemini_result: Geminiの分析結果
        
        Returns:
            GUI用にフォーマットされた結果
        """
        try:
            # SocialQuestionオブジェクトのリストに変換
            questions = []
            
            for q_data in gemini_result.get('questions', []):
                # フィールドの変換
                field_map = {
                    '地理': SocialField.GEOGRAPHY,
                    '歴史': SocialField.HISTORY,
                    '公民': SocialField.CIVICS,
                    '時事問題': SocialField.CURRENT_AFFAIRS,
                    '総合': SocialField.MIXED,
                    '不明': SocialField.MIXED
                }
                field = field_map.get(q_data.get('field', ''), SocialField.MIXED)
                
                # リソースタイプの変換
                resource_types = []
                if resource_type := q_data.get('resource_type'):
                    if isinstance(resource_type, str):
                        resource_types = [self._convert_resource_type(resource_type)]
                    elif isinstance(resource_type, list):
                        resource_types = [self._convert_resource_type(r) for r in resource_type]
                
                # 出題形式の変換
                format_map = {
                    '選択式': QuestionFormat.MULTIPLE_CHOICE,
                    '記号選択': QuestionFormat.MULTIPLE_CHOICE,
                    '記述式': QuestionFormat.DESCRIPTIVE,
                    '短答式': QuestionFormat.SHORT_ANSWER,
                    '穴埋め': QuestionFormat.FILL_IN_BLANK,
                    '正誤判定': QuestionFormat.TRUE_FALSE,
                    '組み合わせ': QuestionFormat.COMBINATION
                }
                # question_formatとtypeの両方をチェック
                format_str = q_data.get('question_format') or q_data.get('type', '')
                question_format = format_map.get(format_str, QuestionFormat.OTHER)
                
                # SocialQuestionオブジェクトの作成
                question = SocialQuestion(
                    number=q_data.get('number', ''),
                    text=q_data.get('text', ''),
                    field=field,
                    resource_types=resource_types,
                    question_format=question_format,
                    is_current_affairs=(field == SocialField.CURRENT_AFFAIRS),
                    time_period=q_data.get('period_or_region'),
                    region=q_data.get('period_or_region'),
                    topic=q_data.get('theme'),
                    theme=q_data.get('theme'),  # themeプロパティも設定
                    keywords=q_data.get('keywords', [])
                )
                
                questions.append(question)
            
            # 統計情報も含めて返す
            return {
                'questions': questions,
                'statistics': gemini_result.get('statistics', {}),
                'total_questions': len(questions),
                'source': 'gemini_detailed'  # ソースを明示
            }
            
        except Exception as e:
            logger.error(f"結果変換エラー: {e}")
            # エラー時も最低限の変換を試みる
            try:
                # 辞書形式の問題を簡易的にSocialQuestionに変換
                questions = []
                for q_data in gemini_result.get('questions', []):
                    if isinstance(q_data, dict):
                        # 最低限の情報でSocialQuestionを作成
                        question = SocialQuestion(
                            number=str(q_data.get('number', '')),
                            text=str(q_data.get('text', '')),
                            field=SocialField.MIXED,  # デフォルト値
                            resource_types=[],
                            question_format=QuestionFormat.OTHER,
                            is_current_affairs=False,
                            keywords=q_data.get('keywords', [])
                        )
                        # themeプロパティを追加
                        if theme := q_data.get('theme'):
                            question.theme = theme
                        questions.append(question)
                
                return {
                    'questions': questions,
                    'statistics': gemini_result.get('statistics', {}),
                    'total_questions': len(questions),
                    'source': 'gemini_detailed_fallback'
                }
            except Exception as e2:
                logger.error(f"フォールバック変換も失敗: {e2}")
                # 最終的なフォールバック：空の結果
                return {
                    'questions': [],
                    'statistics': {},
                    'total_questions': 0,
                    'source': 'error'
                }
    
    def _convert_resource_type(self, resource_str: str) -> ResourceType:
        """
        リソースタイプ文字列をEnumに変換
        """
        resource_map = {
            '地図': ResourceType.MAP,
            'グラフ': ResourceType.GRAPH,
            '雨温図': ResourceType.GRAPH,
            '年表': ResourceType.TIMELINE,
            '表': ResourceType.TABLE,
            '写真': ResourceType.PHOTO,
            '画像': ResourceType.PHOTO,
            '文書': ResourceType.DOCUMENT,
            '地形図': ResourceType.MAP
        }
        
        for key, value in resource_map.items():
            if key in resource_str:
                return value
        
        return ResourceType.OTHER
    
    def get_summary_text(self, result: Dict[str, Any]) -> str:
        """
        分析結果のサマリーテキストを生成
        
        Args:
            result: 分析結果
        
        Returns:
            表示用のサマリーテキスト
        """
        try:
            lines = []
            lines.append("=" * 60)
            lines.append("【Gemini API詳細分析結果】")
            lines.append("=" * 60)
            
            # 基本情報
            total = result.get('total_questions', 0)
            lines.append(f"\n◆ 総問題数: {total}問")
            
            # 分野別分布
            if stats := result.get('statistics'):
                if field_dist := stats.get('field_distribution'):
                    lines.append("\n◆ 分野別分布:")
                    for field, data in sorted(field_dist.items()):
                        lines.append(f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
                
                # 出題形式分布
                if format_dist := stats.get('format_distribution'):
                    lines.append("\n◆ 出題形式分布:")
                    for fmt, data in sorted(format_dist.items(), key=lambda x: x[1]['count'], reverse=True):
                        lines.append(f"  {fmt:10s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
            
            # 各問題の概要（最初の10問）
            if questions := result.get('questions'):
                lines.append("\n◆ 検出された問題（抜粋）:")
                for q in questions[:10]:
                    number = getattr(q, 'number', 'N/A')
                    theme = getattr(q, 'theme', None) or getattr(q, 'topic', None) or '(テーマ未設定)'
                    field = getattr(q, 'field', None)
                    if hasattr(field, 'value'):
                        field_str = field.value
                    else:
                        field_str = str(field) if field else '不明'
                    
                    lines.append(f"  {number:12s}: {theme:25s} [{field_str}]")
                
                if len(questions) > 10:
                    lines.append(f"  ... 他 {len(questions) - 10} 問")
            
            lines.append("\n" + "=" * 60)
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"サマリー生成エラー: {e}")
            return "分析結果のサマリー生成に失敗しました"


# モジュールテスト用
if __name__ == "__main__":
    bridge = GeminiBridge()
    
    if bridge.check_availability():
        print("✅ Gemini Bridge は利用可能です")
        
        # テストPDF
        test_pdf = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf"
        
        if Path(test_pdf).exists():
            print(f"テストPDF: {Path(test_pdf).name}")
            
            def progress_callback(msg):
                print(f"  進捗: {msg}")
            
            try:
                result = bridge.analyze_pdf(test_pdf, progress_callback)
                summary = bridge.get_summary_text(result)
                print(summary)
            except Exception as e:
                print(f"❌ テスト失敗: {e}")
        else:
            print("テストPDFが見つかりません")
    else:
        print("❌ Gemini Bridge は利用できません")