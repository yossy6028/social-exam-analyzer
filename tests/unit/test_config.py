"""
設定管理モジュールの単体テスト
"""

import unittest
import json
import tempfile
from pathlib import Path
import sys
import os

# テストヘルパーをインポート
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.test_helpers import (
    FileTestHelper,
    setup_test_environment,
    teardown_test_environment
)

from core.config import (
    MainConfig,
    FileConfig,
    YearConfig,
    TextAnalysisConfig,
    get_config,
    reset_config,
    Settings,
    AppConfig
)


class TestMainConfig(unittest.TestCase):
    """MainConfigのテストクラス"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスのセットアップ"""
        cls.temp_dir = setup_test_environment()
    
    @classmethod
    def tearDownClass(cls):
        """テストクラスのクリーンアップ"""
        teardown_test_environment(cls.temp_dir)
    
    def test_default_initialization(self):
        """デフォルト初期化のテスト"""
        config = MainConfig()
        
        self.assertIsInstance(config.file, FileConfig)
        self.assertIsInstance(config.year, YearConfig)
        self.assertIsInstance(config.text_analysis, TextAnalysisConfig)
        self.assertIsNotNone(config.project_root)
        self.assertIsNotNone(config.data_dir)
    
    def test_to_dict_conversion(self):
        """辞書変換のテスト"""
        config = MainConfig()
        config_dict = config.to_dict()
        
        self.assertIsInstance(config_dict, dict)
        self.assertIn('file', config_dict)
        self.assertIn('year', config_dict)
        self.assertIn('text_analysis', config_dict)
    
    def test_from_dict_creation(self):
        """辞書からの作成テスト"""
        data = {
            'file': {
                'max_files_to_display': 100,
                'max_file_size_mb': 500
            },
            'year': {
                'min_valid_year': 2000,
                'max_valid_year': 2030
            }
        }
        
        config = MainConfig.from_dict(data)
        
        self.assertEqual(config.file.max_files_to_display, 100)
        self.assertEqual(config.file.max_file_size_mb, 500)
        self.assertEqual(config.year.min_valid_year, 2000)
    
    def test_save_and_load(self):
        """保存と読み込みのテスト"""
        config = MainConfig()
        config.file.max_files_to_display = 999
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            config.save(Path(tmp.name))
            
            # 読み込み
            loaded_config = MainConfig.load(Path(tmp.name))
            
            self.assertEqual(loaded_config.file.max_files_to_display, 999)
            
            # クリーンアップ
            Path(tmp.name).unlink()
    
    def test_environment_variable_loading(self):
        """環境変数からの読み込みテスト"""
        # 環境変数を設定
        os.environ['ENTRANCE_EXAM_DATA_DIR'] = '/tmp/test_data'
        os.environ['ENTRANCE_EXAM_LOG_LEVEL'] = 'DEBUG'
        os.environ['ENTRANCE_EXAM_PARALLEL'] = 'true'
        
        config = MainConfig()
        config.load_environment_variables()
        
        self.assertEqual(str(config.data_dir), '/tmp/test_data')
        self.assertEqual(config.logging.level, 'DEBUG')
        self.assertTrue(config.processing.parallel_processing)
        
        # クリーンアップ
        del os.environ['ENTRANCE_EXAM_DATA_DIR']
        del os.environ['ENTRANCE_EXAM_LOG_LEVEL']
        del os.environ['ENTRANCE_EXAM_PARALLEL']
    
    def test_path_resolution(self):
        """パス解決のテスト"""
        config = MainConfig()
        
        # パスが絶対パスに解決されていることを確認
        self.assertTrue(config.paths.output_dir.is_absolute())
        self.assertTrue(config.paths.backup_dir.is_absolute())
        self.assertTrue(config.paths.log_dir.is_absolute())
    
    def test_get_excel_path(self):
        """Excelパス取得のテスト"""
        config = MainConfig()
        excel_path = config.get_excel_path()
        
        self.assertIsInstance(excel_path, Path)
        self.assertTrue(str(excel_path).endswith('.xlsx'))
    
    def test_get_search_directories(self):
        """検索ディレクトリ取得のテスト"""
        config = MainConfig()
        dirs = config.get_search_directories()
        
        self.assertIsInstance(dirs, list)
        self.assertGreater(len(dirs), 0)
        self.assertIsInstance(dirs[0], Path)
    
    def test_backward_compatibility_settings(self):
        """Settings後方互換性のテスト"""
        settings = Settings()
        
        # 旧設定名でアクセス
        self.assertIsInstance(settings.MAX_FILES_TO_DISPLAY, int)
        self.assertIsInstance(settings.MIN_VALID_YEAR, int)
        self.assertIsInstance(settings.SCHOOL_PATTERNS, dict)
    
    def test_backward_compatibility_appconfig(self):
        """AppConfig後方互換性のテスト"""
        app_config = AppConfig()
        
        # ドット記法でのアクセス
        value = app_config.get('file.max_files_to_display')
        self.assertIsNotNone(value)
        
        # メソッドの互換性
        excel_path = app_config.get_excel_path()
        self.assertIsInstance(excel_path, Path)


class TestConfigComponents(unittest.TestCase):
    """設定コンポーネントのテストクラス"""
    
    def test_file_config(self):
        """FileConfigのテスト"""
        config = FileConfig(
            max_files_to_display=100,
            max_file_size_mb=500
        )
        
        self.assertEqual(config.max_files_to_display, 100)
        self.assertEqual(config.max_file_size_mb, 500)
        self.assertIsInstance(config.default_encoding_list, list)
    
    def test_year_config(self):
        """YearConfigのテスト"""
        config = YearConfig()
        
        self.assertIsInstance(config.kanji_digit_map, dict)
        self.assertEqual(config.kanji_digit_map['一'], '1')
        self.assertEqual(config.era_conversion['reiwa_base'], 2018)
    
    def test_text_analysis_config(self):
        """TextAnalysisConfigのテスト"""
        config = TextAnalysisConfig(
            max_sections=20,
            max_text_length=2000000
        )
        
        self.assertEqual(config.max_sections, 20)
        self.assertEqual(config.max_text_length, 2000000)


class TestGlobalConfig(unittest.TestCase):
    """グローバル設定関数のテストクラス"""
    
    def test_get_config(self):
        """get_configのテスト"""
        config1 = get_config()
        config2 = get_config()
        
        # 同じインスタンスが返されることを確認
        self.assertIs(config1, config2)
    
    def test_reset_config(self):
        """reset_configのテスト"""
        # 設定を変更
        config1 = get_config()
        original_value = config1.file.max_files_to_display
        config1.file.max_files_to_display = 999
        
        # リセット
        config2 = reset_config()
        
        # 新しいインスタンスが作成され、デフォルト値に戻ることを確認
        self.assertIsNot(config1, config2)
        self.assertEqual(config2.file.max_files_to_display, 50)  # デフォルト値


if __name__ == '__main__':
    unittest.main()