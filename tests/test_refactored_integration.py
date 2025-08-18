#!/usr/bin/env python3
"""
リファクタリング版の統合テスト
"""

import sys
import os
from pathlib import Path
import unittest

# プロジェクトルート追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.unified_settings import settings, AnalysisOptions
from services.analysis_service import AnalysisService, AnalysisRequest
from modules.unified_analyzer import UnifiedSocialAnalyzer, SocialField, QuestionFormat


class TestRefactoredIntegration(unittest.TestCase):
    """統合テスト"""
    
    def setUp(self):
        """セットアップ"""
        self.service = AnalysisService()
        self.analyzer = UnifiedSocialAnalyzer()
    
    def test_unified_settings(self):
        """統一設定のテスト"""
        # シングルトンパターンのテスト
        settings1 = settings
        settings2 = settings
        self.assertIs(settings1, settings2)
        
        # 設定値のテスト
        self.assertIsNotNone(settings.project_root)
        self.assertTrue(settings.data_dir.exists())
        self.assertTrue(settings.logs_dir.exists())
        
        # API設定のテスト
        if os.getenv('GEMINI_API_KEY'):
            self.assertIsNotNone(settings.api.gemini_api_key)
    
    def test_unified_analyzer(self):
        """統合アナライザーのテスト"""
        # テストテキスト
        test_text = """
        大問1 次の地図を見て、以下の問いに答えなさい。
        
        問1 高知県の促成栽培について説明しなさい。
        問2 太平洋ベルトの工業地帯を選びなさい。
        
        大問2 江戸時代について、以下の問いに答えなさい。
        
        問1 徳川家康が行った政策を説明しなさい。
        問2 参勤交代の目的を選択肢から選びなさい。
        """
        
        # 分析実行
        questions = self.analyzer.analyze_text(test_text)
        
        # 結果検証
        self.assertGreater(len(questions), 0)
        
        # 分野判定のテスト
        geo_questions = [q for q in questions if q.field == SocialField.GEOGRAPHY]
        hist_questions = [q for q in questions if q.field == SocialField.HISTORY]
        
        self.assertGreater(len(geo_questions), 0)
        self.assertGreater(len(hist_questions), 0)
        
        # 統計情報のテスト
        stats = self.analyzer.get_statistics()
        self.assertIn('total_questions', stats)
        self.assertIn('field_distribution', stats)
    
    def test_analysis_service(self):
        """分析サービスのテスト"""
        # モックPDFパス（実際のファイルは不要）
        test_pdf = "/test/dummy.pdf"
        
        # リクエスト作成
        request = AnalysisRequest(
            pdf_path=test_pdf,
            school_name="テスト中学校",
            year="2024",
            options=AnalysisOptions(
                analyze_geography=True,
                analyze_history=True,
                analyze_civics=False,
                analyze_current_affairs=False,
                use_gemini_detailed=False
            )
        )
        
        # リクエストの検証
        self.assertEqual(request.school_name, "テスト中学校")
        self.assertEqual(request.year, "2024")
        self.assertTrue(request.options.analyze_geography)
        self.assertFalse(request.options.analyze_civics)
    
    def test_question_format_detection(self):
        """出題形式検出のテスト"""
        test_cases = [
            ("答えなさい", QuestionFormat.SHORT_ANSWER),
            ("選びなさい", QuestionFormat.MULTIPLE_CHOICE),
            ("説明しなさい", QuestionFormat.DESCRIPTIVE),
            ("空欄に入る語句", QuestionFormat.FILL_IN_BLANK),
            ("正しいものを", QuestionFormat.TRUE_FALSE)
        ]
        
        for text, expected_format in test_cases:
            detected = self.analyzer._detect_format(text)
            self.assertEqual(detected, expected_format, f"Failed for: {text}")
    
    def test_field_determination(self):
        """分野判定のテスト"""
        test_cases = [
            ("地図を見て農業について", SocialField.GEOGRAPHY),
            ("江戸時代の徳川家康", SocialField.HISTORY),
            ("日本国憲法の基本的人権", SocialField.CIVICS),
            ("SDGsと環境問題", SocialField.CURRENT_AFFAIRS)
        ]
        
        for text, expected_field in test_cases:
            detected = self.analyzer._determine_field(text)
            self.assertEqual(detected, expected_field, f"Failed for: {text}")


def run_tests():
    """テスト実行"""
    print("=" * 60)
    print("リファクタリング版統合テスト")
    print("=" * 60)
    print()
    
    # テストスイート作成
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRefactoredIntegration)
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果サマリー
    print()
    print("=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"実行: {result.testsRun}件")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}件")
    print(f"失敗: {len(result.failures)}件")
    print(f"エラー: {len(result.errors)}件")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())