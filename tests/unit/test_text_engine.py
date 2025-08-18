"""
TextEngineの単体テスト
"""

import unittest
from pathlib import Path
import sys

# テストヘルパーをインポート
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.test_helpers import (
    TestDataProvider,
    MockFactory,
    AssertionHelper,
    setup_test_environment,
    teardown_test_environment
)

from core.text_engine import TextEngine, QuestionType, ProcessedText


class TestTextEngine(unittest.TestCase):
    """TextEngineのテストクラス"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスのセットアップ"""
        cls.temp_dir = setup_test_environment()
    
    @classmethod
    def tearDownClass(cls):
        """テストクラスのクリーンアップ"""
        teardown_test_environment(cls.temp_dir)
    
    def setUp(self):
        """各テストのセットアップ"""
        self.config = MockFactory.create_mock_config()
        self.engine = TextEngine(self.config)
        self.sample_text = TestDataProvider.get_sample_text()
    
    def test_process_text_basic(self):
        """基本的なテキスト処理のテスト"""
        result = self.engine.process_text(self.sample_text)
        
        self.assertIsInstance(result, ProcessedText)
        self.assertIsNotNone(result.sections)
        self.assertGreater(len(result.sections), 0)
        self.assertGreater(result.total_characters, 0)
    
    def test_question_extraction(self):
        """設問抽出のテスト"""
        result = self.engine.process_text(self.sample_text)
        
        # 設問が抽出されていることを確認
        total_questions = sum(len(s.questions) for s in result.sections)
        self.assertGreater(total_questions, 0)
        
        # 設問タイプが正しく分類されていることを確認
        for section in result.sections:
            for question in section.questions:
                self.assertIsInstance(question.type, QuestionType)
    
    def test_source_extraction(self):
        """出典情報抽出のテスト"""
        result = self.engine.process_text(self.sample_text)
        
        # 少なくとも1つのセクションに出典情報があることを確認
        has_source = any(s.source is not None for s in result.sections)
        self.assertTrue(has_source)
    
    def test_school_detection(self):
        """学校名検出のテスト"""
        # ファイル名から学校名を検出
        result = self.engine.process_text(
            self.sample_text,
            filename="開成_2025_国語.pdf"
        )
        
        self.assertEqual(result.school, '開成中学校')
    
    def test_year_extraction(self):
        """年度抽出のテスト"""
        text_with_year = "2025年度入学試験\n" + self.sample_text
        result = self.engine.process_text(text_with_year)
        
        self.assertEqual(result.year, 2025)
    
    def test_cache_functionality(self):
        """キャッシュ機能のテスト"""
        # キャッシュを有効にして設定
        self.config.processing.cache_enabled = True
        engine_with_cache = TextEngine(self.config)
        
        # 1回目の処理
        result1 = engine_with_cache.process_text(self.sample_text)
        
        # 2回目の処理（キャッシュから取得されるはず）
        result2 = engine_with_cache.process_text(self.sample_text)
        
        # 結果が同じオブジェクトであることを確認
        self.assertIs(result1, result2)
    
    def test_export_to_dict(self):
        """辞書形式へのエクスポートテスト"""
        result = self.engine.process_text(self.sample_text)
        exported = self.engine.export_to_dict(result)
        
        self.assertIsInstance(exported, dict)
        self.assertIn('school', exported)
        self.assertIn('year', exported)
        self.assertIn('sections', exported)
        self.assertIn('total_characters', exported)
    
    def test_format_for_display(self):
        """表示用フォーマットのテスト"""
        result = self.engine.process_text(self.sample_text)
        formatted = self.engine.format_for_display(result)
        
        self.assertIsInstance(formatted, str)
        self.assertIn('総文字数', formatted)
        self.assertIn('総設問数', formatted)
    
    def test_question_type_counting(self):
        """設問タイプ別集計のテスト"""
        result = self.engine.process_text(self.sample_text)
        
        # 設問タイプカウントが正しく集計されていることを確認
        self.assertIsInstance(result.question_type_counts, dict)
        
        # 全てのQuestionTypeが含まれていることを確認
        for q_type in QuestionType:
            self.assertIn(q_type, result.question_type_counts)
        
        # カウントの合計が総設問数と一致することを確認
        total_from_counts = sum(result.question_type_counts.values())
        self.assertEqual(total_from_counts, result.total_questions)
    
    def test_empty_text_handling(self):
        """空テキストの処理テスト"""
        result = self.engine.process_text("")
        
        self.assertIsInstance(result, ProcessedText)
        self.assertEqual(result.total_characters, 0)
        self.assertGreater(len(result.sections), 0)  # デフォルトセクションが作成される
    
    def test_backward_compatibility(self):
        """後方互換性のテスト"""
        from core.text_engine import FinalContentExtractor, ContentExtractor
        
        # FinalContentExtractorの互換性
        extractor1 = FinalContentExtractor(self.config)
        result1 = extractor1.extract_all_content(self.sample_text)
        self.assertIsInstance(result1, dict)
        
        # ContentExtractorの互換性
        extractor2 = ContentExtractor(self.config)
        result2 = extractor2.extract_content(self.sample_text)
        self.assertIsInstance(result2, dict)


if __name__ == '__main__':
    unittest.main()