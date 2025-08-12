"""
設定検証モジュール
設定の妥当性をスキーマベースで検証
"""
from typing import Dict, Any, Optional, Union
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigValidator:
    """設定検証クラス"""
    
    # デフォルトスキーマ定義
    DEFAULT_SCHEMA = {
        "base_analyzer": {
            "type": "object",
            "properties": {
                "min_text_length": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1000000,
                    "default": 100
                },
                "max_text_length": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 10000000,
                    "default": 1000000
                },
                "propagate_errors": {
                    "type": "boolean",
                    "default": True
                },
                "enable_caching": {
                    "type": "boolean",
                    "default": True
                },
                "cache_ttl_seconds": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 86400,
                    "default": 3600
                }
            }
        },
        "file_manager": {
            "type": "object",
            "properties": {
                "max_cache_size_mb": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 100
                },
                "max_single_file_mb": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 500,
                    "default": 50
                },
                "cache_ttl_seconds": {
                    "type": "integer",
                    "minimum": 60,
                    "maximum": 86400,
                    "default": 3600
                },
                "backup_enabled": {
                    "type": "boolean",
                    "default": True
                },
                "allowed_extensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [".txt", ".pdf", ".json", ".csv", ".xlsx"]
                }
            }
        },
        "pattern_registry": {
            "type": "object",
            "properties": {
                "compile_on_init": {
                    "type": "boolean",
                    "default": False
                },
                "use_cache": {
                    "type": "boolean",
                    "default": True
                },
                "max_pattern_cache": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 1000,
                    "default": 200
                }
            }
        },
        "text_preprocessor": {
            "type": "object",
            "properties": {
                "remove_ocr_artifacts": {
                    "type": "boolean",
                    "default": True
                },
                "normalize_unicode": {
                    "type": "boolean",
                    "default": True
                },
                "fix_line_breaks": {
                    "type": "boolean",
                    "default": True
                },
                "remove_page_markers": {
                    "type": "boolean",
                    "default": True
                },
                "max_segment_length": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 10000,
                    "default": 1000
                }
            }
        }
    }
    
    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            schema: カスタムスキーマ（デフォルトスキーマを上書き）
        """
        self.schema = schema or self.DEFAULT_SCHEMA
    
    def validate(self, config: Dict[str, Any], 
                component: Optional[str] = None) -> Dict[str, Any]:
        """
        設定を検証し、デフォルト値を適用
        
        Args:
            config: 検証する設定
            component: 特定のコンポーネント名（Noneの場合は全体を検証）
            
        Returns:
            検証済みでデフォルト値が適用された設定
            
        Raises:
            ConfigurationError: 設定が無効な場合
        """
        from core.exceptions import ConfigurationError
        
        if component:
            # 特定コンポーネントの検証
            if component not in self.schema:
                logger.warning(f"No schema defined for component: {component}")
                return config
            
            component_schema = self.schema[component]
            validated = self._validate_component(config, component_schema, component)
        else:
            # 全体の検証
            validated = {}
            for comp_name, comp_schema in self.schema.items():
                comp_config = config.get(comp_name, {})
                validated[comp_name] = self._validate_component(
                    comp_config, comp_schema, comp_name
                )
        
        return validated
    
    def _validate_component(self, config: Dict[str, Any], 
                           schema: Dict[str, Any],
                           component_name: str) -> Dict[str, Any]:
        """
        コンポーネント設定を検証
        
        Args:
            config: コンポーネント設定
            schema: スキーマ定義
            component_name: コンポーネント名
            
        Returns:
            検証済み設定
        """
        from core.exceptions import ConfigurationError
        
        if schema.get("type") != "object":
            return config
        
        validated = {}
        properties = schema.get("properties", {})
        
        for prop_name, prop_schema in properties.items():
            if prop_name in config:
                # 値が存在する場合は検証
                value = config[prop_name]
                validated[prop_name] = self._validate_property(
                    value, prop_schema, f"{component_name}.{prop_name}"
                )
            else:
                # デフォルト値を適用
                if "default" in prop_schema:
                    validated[prop_name] = prop_schema["default"]
                    logger.debug(f"Applied default value for {component_name}.{prop_name}: "
                               f"{prop_schema['default']}")
        
        # 未定義のプロパティも保持（警告付き）
        for key in config:
            if key not in properties:
                logger.warning(f"Unknown configuration property: {component_name}.{key}")
                validated[key] = config[key]
        
        return validated
    
    def _validate_property(self, value: Any, schema: Dict[str, Any], 
                          property_path: str) -> Any:
        """
        個別プロパティを検証
        
        Args:
            value: プロパティ値
            schema: プロパティスキーマ
            property_path: プロパティパス（エラー報告用）
            
        Returns:
            検証済み値
            
        Raises:
            ConfigurationError: 値が無効な場合
        """
        from core.exceptions import ConfigurationError
        
        prop_type = schema.get("type")
        
        # 型チェック
        if prop_type == "integer":
            if not isinstance(value, int):
                raise ConfigurationError(
                    f"Invalid type for {property_path}: expected integer, got {type(value).__name__}",
                    property_path
                )
            # 範囲チェック
            if "minimum" in schema and value < schema["minimum"]:
                raise ConfigurationError(
                    f"Value for {property_path} is below minimum: {value} < {schema['minimum']}",
                    property_path
                )
            if "maximum" in schema and value > schema["maximum"]:
                raise ConfigurationError(
                    f"Value for {property_path} exceeds maximum: {value} > {schema['maximum']}",
                    property_path
                )
                
        elif prop_type == "number":
            if not isinstance(value, (int, float)):
                raise ConfigurationError(
                    f"Invalid type for {property_path}: expected number, got {type(value).__name__}",
                    property_path
                )
            # 範囲チェック
            if "minimum" in schema and value < schema["minimum"]:
                raise ConfigurationError(
                    f"Value for {property_path} is below minimum: {value} < {schema['minimum']}",
                    property_path
                )
            if "maximum" in schema and value > schema["maximum"]:
                raise ConfigurationError(
                    f"Value for {property_path} exceeds maximum: {value} > {schema['maximum']}",
                    property_path
                )
                
        elif prop_type == "boolean":
            if not isinstance(value, bool):
                raise ConfigurationError(
                    f"Invalid type for {property_path}: expected boolean, got {type(value).__name__}",
                    property_path
                )
                
        elif prop_type == "string":
            if not isinstance(value, str):
                raise ConfigurationError(
                    f"Invalid type for {property_path}: expected string, got {type(value).__name__}",
                    property_path
                )
            # パターンチェック（もしあれば）
            if "pattern" in schema:
                import re
                if not re.match(schema["pattern"], value):
                    raise ConfigurationError(
                        f"Value for {property_path} doesn't match pattern: {schema['pattern']}",
                        property_path
                    )
                    
        elif prop_type == "array":
            if not isinstance(value, list):
                raise ConfigurationError(
                    f"Invalid type for {property_path}: expected array, got {type(value).__name__}",
                    property_path
                )
            # 要素の検証（もしあれば）
            if "items" in schema:
                item_schema = schema["items"]
                for i, item in enumerate(value):
                    self._validate_property(item, item_schema, f"{property_path}[{i}]")
        
        return value
    
    def get_defaults(self, component: Optional[str] = None) -> Dict[str, Any]:
        """
        デフォルト設定を取得
        
        Args:
            component: 特定のコンポーネント名（Noneの場合は全体）
            
        Returns:
            デフォルト設定
        """
        defaults = {}
        
        if component:
            if component in self.schema:
                defaults = self._extract_defaults(self.schema[component])
        else:
            for comp_name, comp_schema in self.schema.items():
                defaults[comp_name] = self._extract_defaults(comp_schema)
        
        return defaults
    
    def _extract_defaults(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        スキーマからデフォルト値を抽出
        
        Args:
            schema: スキーマ定義
            
        Returns:
            デフォルト値の辞書
        """
        defaults = {}
        
        if schema.get("type") == "object" and "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                if "default" in prop_schema:
                    defaults[prop_name] = prop_schema["default"]
        
        return defaults
    
    def load_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        設定ファイルを読み込んで検証
        
        Args:
            file_path: 設定ファイルパス
            
        Returns:
            検証済み設定
            
        Raises:
            ConfigurationError: ファイルが読めないか設定が無効
        """
        from core.exceptions import ConfigurationError
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix == '.json':
                    config = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported file format: {file_path.suffix}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration file: {e}")
        
        # 検証して返す
        return self.validate(config)