"""
統一された例外クラス定義
"""


class AnalyzerError(Exception):
    """アナライザーの基底例外クラス"""
    
    def __init__(self, message: str, details: dict = None):
        """
        初期化
        
        Args:
            message: エラーメッセージ
            details: 詳細情報の辞書
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            # 機密情報をフィルタリング
            sensitive_keys = ['password', 'api_key', 'token', 'secret', 'credential']
            safe_details = {}
            
            for k, v in self.details.items():
                # キー名に機密情報関連の文字列が含まれている場合
                if any(sensitive in k.lower() for sensitive in sensitive_keys):
                    safe_details[k] = '[REDACTED]'
                else:
                    # 値が文字列で長すぎる場合は省略
                    if isinstance(v, str) and len(v) > 100:
                        safe_details[k] = v[:50] + '...' + v[-20:]
                    else:
                        safe_details[k] = v
            
            details_str = ", ".join(f"{k}={v}" for k, v in safe_details.items())
            return f"{self.message} ({details_str})"
        return self.message


class YearDetectionError(AnalyzerError):
    """年度検出エラー"""
    
    def __init__(self, message: str, attempted_patterns: list = None):
        """
        初期化
        
        Args:
            message: エラーメッセージ
            attempted_patterns: 試行したパターンのリスト
        """
        details = {'attempted_patterns': attempted_patterns} if attempted_patterns else {}
        super().__init__(message, details)


class SectionDetectionError(AnalyzerError):
    """セクション検出エラー"""
    
    def __init__(self, message: str, found_count: int = 0, expected_count: int = None):
        """
        初期化
        
        Args:
            message: エラーメッセージ
            found_count: 検出されたセクション数
            expected_count: 期待されるセクション数
        """
        details = {'found': found_count}
        if expected_count is not None:
            details['expected'] = expected_count
        super().__init__(message, details)


class SourceExtractionError(AnalyzerError):
    """出典抽出エラー"""
    
    def __init__(self, message: str, section_number: int = None):
        """
        初期化
        
        Args:
            message: エラーメッセージ
            section_number: セクション番号
        """
        details = {'section': section_number} if section_number else {}
        super().__init__(message, details)


class ValidationError(AnalyzerError):
    """バリデーションエラー"""
    
    def __init__(self, message: str, field: str = None, value: any = None):
        """
        初期化
        
        Args:
            message: エラーメッセージ
            field: フィールド名
            value: 無効な値
        """
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
        super().__init__(message, details)


class ConfigurationError(AnalyzerError):
    """設定エラー"""
    
    def __init__(self, message: str, config_key: str = None):
        """
        初期化
        
        Args:
            message: エラーメッセージ
            config_key: 設定キー
        """
        details = {'config_key': config_key} if config_key else {}
        super().__init__(message, details)


class PatternError(AnalyzerError):
    """パターンエラー"""
    
    def __init__(self, message: str, pattern_name: str = None, pattern: str = None):
        """
        初期化
        
        Args:
            message: エラーメッセージ
            pattern_name: パターン名
            pattern: パターン文字列
        """
        details = {}
        if pattern_name:
            details['pattern_name'] = pattern_name
        if pattern:
            details['pattern'] = pattern
        super().__init__(message, details)


class ProcessingError(AnalyzerError):
    """処理エラー"""
    
    def __init__(self, message: str, stage: str = None, input_type: str = None):
        """
        初期化
        
        Args:
            message: エラーメッセージ
            stage: 処理ステージ
            input_type: 入力タイプ
        """
        details = {}
        if stage:
            details['stage'] = stage
        if input_type:
            details['input_type'] = input_type
        super().__init__(message, details)