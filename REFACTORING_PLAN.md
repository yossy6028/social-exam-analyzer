# 社会科目入試問題分析システム - リファクタリングプラン

## 現状の問題点

### 1. コードの肥大化
- `main.py`: 1214行（UI、ビジネスロジック、データ処理が混在）
- `social_analyzer.py`: 1371行
- `social_analyzer_fixed.py`: 1995行（重複）

### 2. モジュールの重複
多数の類似モジュールが存在：
- **Extractors**: 18個の異なるextractorモジュール
  - content_extractor.py
  - enhanced_content_extractor.py
  - improved_content_extractor.py
  - final_content_extractor.py
  - など...
  
- **Analyzers**: 8個の異なるanalyzerモジュール
  - social_analyzer.py
  - social_analyzer_fixed.py
  - social_analyzer_improved.py
  - gemini_analyzer.py
  - など...

### 3. 責任の不明確さ
- UIとビジネスロジックの混在
- データ処理とプレゼンテーションの結合
- 設定管理の分散

## リファクタリング戦略

### フェーズ1: 重複の削除と統合（優先度: 高）

#### 1.1 Extractorモジュールの統合
```python
# modules/unified_extractor.py
class UnifiedExtractor:
    """すべての抽出機能を統合"""
    def extract_content(self, text: str, options: ExtractionOptions)
    def extract_questions(self, text: str)
    def extract_themes(self, questions: List[Question])
```

#### 1.2 Analyzerモジュールの統合
```python
# modules/unified_analyzer.py
class UnifiedAnalyzer:
    """すべての分析機能を統合"""
    def analyze(self, pdf_path: str, options: AnalysisOptions)
    def analyze_with_gemini(self, text: str)
    def analyze_with_patterns(self, text: str)
```

### フェーズ2: アーキテクチャの再構築（優先度: 高）

#### 2.1 レイヤード・アーキテクチャの導入
```
presentation/
├── gui/
│   ├── main_window.py      # メインウィンドウ
│   ├── analysis_panel.py   # 分析パネル
│   └── result_panel.py     # 結果表示パネル
│
domain/
├── models/
│   ├── question.py         # 問題モデル
│   ├── analysis_result.py # 分析結果モデル
│   └── statistics.py      # 統計モデル
│
├── services/
│   ├── analysis_service.py    # 分析サービス
│   ├── gemini_service.py      # Gemini APIサービス
│   └── ocr_service.py         # OCRサービス
│
infrastructure/
├── repositories/
│   ├── pdf_repository.py      # PDF処理
│   └── excel_repository.py    # Excel出力
│
└── external/
    ├── gemini_client.py       # Gemini APIクライアント
    └── vision_client.py       # Vision APIクライアント
```

### フェーズ3: 設定管理の統一（優先度: 中）

#### 3.1 設定ファイルの統合
```python
# config/app_settings.py
class AppSettings:
    # すべての設定を一元管理
    GEMINI_API_KEY: str
    DEFAULT_OPTIONS: AnalysisOptions
    UI_SETTINGS: UISettings
```

#### 3.2 環境変数の管理
```python
# config/environment.py
class Environment:
    @classmethod
    def load_from_env_file(cls)
    @classmethod
    def validate(cls)
```

### フェーズ4: テスタビリティの向上（優先度: 中）

#### 4.1 依存性注入の実装
```python
# core/dependency_injection.py
class Container:
    def register_services(self)
    def resolve[T](self, service_type: Type[T]) -> T
```

#### 4.2 モックフレンドリーな設計
```python
# interfaces/
├── i_ocr_service.py
├── i_analysis_service.py
└── i_excel_service.py
```

### フェーズ5: パフォーマンス最適化（優先度: 低）

#### 5.1 キャッシング戦略
```python
# core/cache.py
class ResultCache:
    def get_or_compute(self, key: str, compute_func: Callable)
```

#### 5.2 並列処理の改善
```python
# core/parallel_processor.py
class ParallelProcessor:
    def process_batch(self, items: List, processor: Callable)
```

## 実装順序

### 週1（即座に実施すべき）
1. **重複モジュールの削除**
   - 使用していないextractor/analyzerの削除
   - バックアップファイル(*_backup.py, *_fixed.py)の削除

2. **main.pyの分割**
   - UIコンポーネントを別ファイルに分離
   - ビジネスロジックをサービス層に移動

### 週2（基盤整備）
3. **統合モジュールの作成**
   - UnifiedExtractorの実装
   - UnifiedAnalyzerの実装

4. **設定管理の統一**
   - すべての設定を一箇所に集約
   - 環境変数の適切な管理

### 週3（品質向上）
5. **テスト基盤の構築**
   - 単体テストの追加
   - 統合テストの整備

6. **ドキュメントの更新**
   - APIドキュメント
   - アーキテクチャ図

## メトリクス目標

- **ファイルサイズ**: すべてのファイルを500行以下に
- **重複コード**: 10%以下に削減
- **テストカバレッジ**: 70%以上
- **循環的複雑度**: 10以下

## リスクと対策

### リスク
- 既存機能の破壊
- パフォーマンスの劣化
- 移行期間中の保守性低下

### 対策
- 段階的な移行（機能ごと）
- 包括的なテストスイート
- 古いコードと新しいコードの並行運用期間を設ける