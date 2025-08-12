"""
プラグインローダー - プラグインの動的読み込みと管理
"""
import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Optional, Type
import sys

from .base import SchoolAnalyzerPlugin, PluginInfo
from exceptions import ConfigurationError
from utils.display_utils import print_info, print_warning, print_error


class PluginLoader:
    """プラグインの読み込みと管理を行うクラス"""
    
    def __init__(self, plugin_dir: Optional[Path] = None):
        """
        初期化
        
        Args:
            plugin_dir: プラグインディレクトリ（省略時はplugins/）
        """
        self.plugin_dir = plugin_dir or Path(__file__).parent
        self.plugins: Dict[str, SchoolAnalyzerPlugin] = {}
        self.plugin_registry: Dict[str, List[SchoolAnalyzerPlugin]] = {}
        
        # デフォルトプラグインを読み込み
        self._load_default_plugins()
        
        # カスタムプラグインを読み込み（存在する場合）
        self._load_custom_plugins()
    
    def _load_default_plugins(self):
        """デフォルトプラグインを読み込み（互換性のため残す）"""
        # 新しい汎用分析システムではプラグインは不要
        # ただし互換性のためメソッドは残す
        pass
    
    def _load_custom_plugins(self):
        """カスタムプラグインを読み込み（custom_plugins/ ディレクトリから）"""
        custom_dir = self.plugin_dir / "custom_plugins"
        if not custom_dir.exists():
            return
        
        for plugin_file in custom_dir.glob("*_plugin.py"):
            if plugin_file.name.startswith('_'):
                continue
            
            try:
                module_name = plugin_file.stem
                self._load_plugin_from_file(plugin_file, module_name)
            except Exception as e:
                print_warning(f"カスタムプラグイン {plugin_file} の読み込みに失敗: {e}")
    
    def _load_plugin(self, module_name: str, class_name: str):
        """プラグインを読み込み"""
        try:
            # モジュールをインポート
            full_module_name = f"plugins.{module_name}"
            module = importlib.import_module(full_module_name)
            
            # クラスを取得
            plugin_class = getattr(module, class_name)
            
            # インスタンスを作成
            self._register_plugin(plugin_class)
            
        except Exception as e:
            raise ConfigurationError(f"プラグインの読み込みエラー: {module_name}.{class_name}: {e}")
    
    def _load_plugin_from_file(self, file_path: Path, module_name: str):
        """ファイルからプラグインを読み込み"""
        try:
            # モジュールを動的にインポート
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # SchoolAnalyzerPluginのサブクラスを探す
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, SchoolAnalyzerPlugin) and
                        obj != SchoolAnalyzerPlugin):
                        self._register_plugin(obj)
        
        except Exception as e:
            raise ConfigurationError(f"カスタムプラグインの読み込みエラー: {file_path}: {e}")
    
    def _register_plugin(self, plugin_class: Type[SchoolAnalyzerPlugin]):
        """プラグインを登録"""
        try:
            plugin_instance = plugin_class()
            plugin_info = plugin_instance.info
            
            # プラグイン名で登録
            self.plugins[plugin_info.name] = plugin_instance
            
            # 学校名ごとに登録
            for school_name in plugin_info.school_names:
                if school_name not in self.plugin_registry:
                    self.plugin_registry[school_name] = []
                self.plugin_registry[school_name].append(plugin_instance)
            
            print_info(f"プラグインを登録: {plugin_info.name} v{plugin_info.version}")
        
        except Exception as e:
            print_error(f"プラグインの登録に失敗: {plugin_class.__name__}: {e}")
    
    def get_plugin_for_school(self, school_name: str) -> SchoolAnalyzerPlugin:
        """
        学校に対応するプラグインを取得
        
        Args:
            school_name: 学校名
        
        Returns:
            対応するプラグイン（見つからない場合はデフォルト）
        """
        # 直接マッチするプラグインを検索
        if school_name in self.plugin_registry:
            # 優先度の高い順にソート
            plugins = sorted(
                self.plugin_registry[school_name],
                key=lambda p: p.info.priority,
                reverse=True
            )
            if plugins:
                return plugins[0]
        
        # ワイルドカード（*）プラグインを検索（デフォルト）
        if '*' in self.plugin_registry:
            return self.plugin_registry['*'][0]
        
        # 最後の手段としてDefaultPluginを返す
        from .default_plugin import DefaultPlugin
        return DefaultPlugin()
    
    def list_plugins(self) -> List[PluginInfo]:
        """
        登録されているすべてのプラグイン情報を取得
        
        Returns:
            プラグイン情報のリスト
        """
        return [plugin.info for plugin in self.plugins.values()]
    
    def get_supported_schools(self) -> List[str]:
        """
        サポートされている学校名のリストを取得
        
        Returns:
            学校名のリスト
        """
        schools = set()
        for plugin in self.plugins.values():
            for school_name in plugin.info.school_names:
                if school_name != '*':
                    schools.add(school_name)
        return sorted(list(schools))
    
    def reload_plugins(self):
        """プラグインを再読み込み"""
        # 既存のプラグインをクリア
        self.plugins.clear()
        self.plugin_registry.clear()
        
        # 再読み込み
        self._load_default_plugins()
        self._load_custom_plugins()
        
        print_info(f"プラグインを再読み込みしました: {len(self.plugins)}個")
    
    def add_custom_plugin(self, plugin_class: Type[SchoolAnalyzerPlugin]):
        """
        カスタムプラグインを動的に追加
        
        Args:
            plugin_class: プラグインクラス
        """
        self._register_plugin(plugin_class)
    
    def remove_plugin(self, plugin_name: str) -> bool:
        """
        プラグインを削除
        
        Args:
            plugin_name: プラグイン名
        
        Returns:
            削除に成功した場合True
        """
        if plugin_name not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_name]
        
        # レジストリから削除
        for school_name in plugin.info.school_names:
            if school_name in self.plugin_registry:
                self.plugin_registry[school_name] = [
                    p for p in self.plugin_registry[school_name]
                    if p.info.name != plugin_name
                ]
                if not self.plugin_registry[school_name]:
                    del self.plugin_registry[school_name]
        
        # プラグインリストから削除
        del self.plugins[plugin_name]
        
        return True


# シングルトンインスタンス
_plugin_loader_instance: Optional[PluginLoader] = None


def get_plugin_loader() -> PluginLoader:
    """プラグインローダーのシングルトンインスタンスを取得"""
    global _plugin_loader_instance
    if _plugin_loader_instance is None:
        _plugin_loader_instance = PluginLoader()
    return _plugin_loader_instance