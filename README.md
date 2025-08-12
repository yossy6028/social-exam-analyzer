# 入試問題分析システム (Entrance Exam Analyzer)

日本の中学入試国語問題を自動分析し、Excelデータベースに保存する高度な分析システムです。

## 主な機能

### 1. テキスト分析機能
- 著者名・作品名の自動抽出
- 文章ジャンル分類（小説・物語、論説文、随筆、説明文）
- 設問タイプ分類（記述、選択、漢字・語句など）
- 選択肢数の自動検出（3択〜6択、複数選択）
- 記述問題の字数制限抽出

### 2. 一括処理機能
- フォルダ内の複数テキストファイルを自動分析
- 学校名・年度の自動認識
- バッチ処理によるExcel一括保存

### 3. データベース管理
- 学校ごとにExcelシートを自動作成
- 年度順での自動ソート
- バックアップ機能付き

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/entrance-exam-analyzer.git
cd entrance-exam-analyzer

# 依存関係のインストール
pip install -r requirements.txt
```

## 使用方法

### 単一ファイルの分析
```python
python analyze_kaisei_2025.py      # 開成2025年の分析
python analyze_ouin_2025.py        # 桜蔭2025年の分析
python analyze_shibushibu_2025.py  # 渋渋2025年の分析
```

### 複数ファイルの一括分析
```bash
# 基本使用法
python batch_analyzer.py <フォルダパス>

# 例: 過去問フォルダ全体を分析
python batch_analyzer.py "/path/to/過去問"

# 特定パターンのファイルのみ
python batch_analyzer.py "./texts" --pattern "25*.txt"

# 出力ファイル名を指定
python batch_analyzer.py "./texts" --output "results_2025.xlsx"
```

### コマンドラインオプション
```bash
# プラグイン一覧を表示
python3 main.py --list-plugins

# サポート学校一覧を表示
python3 main.py --list-schools

# データベースを検証
python3 main.py --validate-db

# サマリーレポートを出力
python3 main.py --export-summary
```

## システム構成

```
entrance_exam_analyzer/
├── core/                   # コアアプリケーション
│   ├── application.py     # メインアプリケーションロジック
│   └── cli.py            # CLIインターフェース
├── modules/               # 機能モジュール
│   ├── year_detector.py  # 年度検出
│   ├── school_detector.py # 学校名検出
│   ├── file_selector.py  # ファイル選択
│   ├── excel_manager.py  # Excel操作
│   └── text_analyzer.py  # テキスト分析
├── plugins/               # プラグインシステム
│   ├── base.py           # ベースクラス
│   ├── loader.py         # プラグインローダー
│   ├── musashi_plugin.py # 武蔵中学校用
│   ├── kaisei_plugin.py  # 開成中学校用
│   └── ouin_plugin.py    # 桜蔭中学校用
├── config/                # 設定
│   └── settings.py       # アプリケーション設定
├── models.py              # データモデル
├── exceptions.py          # カスタム例外
└── utils/                 # ユーティリティ
    ├── text_utils.py     # テキスト処理
    ├── file_utils.py     # ファイル操作
    └── display_utils.py  # 表示機能
```

## 分析機能

### 検出項目
- **学校名**: ファイル名やテキスト内容から自動検出
- **年度**: 西暦、令和、平成、2桁年度に対応
- **大問構造**: セクションマーカーを認識
- **設問タイプ**: 記述、選択、漢字・語句、抜き出し
- **出典情報**: 著者名、作品名、出版社
- **テーマ・ジャンル**: AIによる自動推定

### 対応学校（プラグイン）
- 武蔵中学校
- 開成中学校
- 桜蔭中学校
- 麻布中学校
- その他（汎用プラグイン）

## カスタムプラグインの作成

新しい学校に対応するプラグインを作成できます：

```python
# plugins/custom_school_plugin.py
from plugins.base import SchoolAnalyzerPlugin, PluginInfo

class CustomSchoolPlugin(SchoolAnalyzerPlugin):
    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="Custom School Analyzer",
            version="1.0.0",
            school_names=["カスタム中学校"],
            description="カスタム中学校用プラグイン"
        )
    
    # 必要なメソッドを実装
```

## データベース構造

分析結果はExcelファイルに保存されます：
- 1シート = 1学校
- 各シートには複数年度のデータを時系列で格納

### 保存される情報
- 年度
- 総文字数、総設問数、大問数
- 大問別の詳細（ジャンル、テーマ、著者、作品）
- 設問タイプ別の集計

## 開発

### 必要環境
- Python 3.8以上
- pandas
- openpyxl
- その他依存関係は`requirements.txt`参照

### テスト実行
```bash
pytest tests/
```

## ライセンス

MIT License

## 作成者

Entrance Exam Analyzer Team

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。