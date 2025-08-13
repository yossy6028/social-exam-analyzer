# 社会科入試問題分析システム

中学入試の社会科問題を分析し、分野別・資料別・形式別に詳細な分析レポートを生成するシステムです。

## 主な機能

- **分野別分析**: 地理・歴史・公民の自動分類
- **テーマ抽出**: 問題文から主要テーマを自動抽出（95%の精度）
- **資料活用分析**: 地図、グラフ、年表などの資料使用状況を分析
- **時事問題検出**: SDGs、環境問題などの時事テーマを自動検出
- **Excel出力**: 詳細な分析レポートをExcel形式で出力

## 最新の改善（2025年1月）

- テーマ抽出精度を95%まで向上
- 社会科学習指導要領に準拠した分類体系
- 無効なテーマ（下線部、記号など）を100%除外

## 使用方法

```bash
python3 main.py
```

または

```bash
./analyze.command
```

## 必要な環境

- Python 3.8以上
- pandas
- openpyxl
- tkinter（GUI用）
- OCRライブラリ（Google Cloud Vision API推奨）

## 重要用語カタログ（Playwright 収集）

教材用語サイトを Playwright で巡回し、歴史/地理/公民ごとの重要用語カタログを作成できます。

- 対象:
  - 一般用語: https://study.005net.com/yogo/yogo.php
  - 地理用語: https://study.005net.com/chiriYogo/chiriYogo.php
  - 公民用語: https://study.005net.com/kominYogo/kominYogo.php

手順:
```
cd social_exam_analyzer
pip install playwright beautifulsoup4 lxml
playwright install
python3 tools/build_terms_catalog.py
```

出力:
- `data/terms_catalog/terms.json`（機械可読）
- `docs/terms_catalog.md`（人間可読）

備考:
- 用語カタログが存在する場合、抽出器は分野推定の補助に用います（任意）。
- サイト構造変更時は `tools/build_terms_catalog.py` 内の `select_terms()` の選択子を調整してください。

## テストの実行（軽量ランナー）

pytest が無い環境でも以下で test_*.py を一括実行できます。

```bash
python3 run_all_tests.py             # 通常（統合/外部依存テストを除外）
python3 run_all_tests.py --all       # すべての test_*.py を実行
python3 run_all_tests.py -k theme    # ファイル名に theme を含むものだけ
python3 run_all_tests.py --stop-on-fail  # 失敗時に中断
```

注意:
- デフォルトではネットワークや外部リソース依存の可能性があるテスト（ファイル名に `brave`/`web`/`real`/`pdf_analysis`/`real_pdf` を含む）を除外します。
- 一部のテストはテキスト出力に「❌」を含みます。ランナーは「❌」表示や終了コードをもとに失敗判定します。

pytest を利用する場合（環境にインストール済みであること）:

```bash
pytest -q social_exam_analyzer
```
