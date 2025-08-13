## mcp-chrome を用いた重要用語HTMLの取得手順

目的: 以下の3ページを mcp-chrome で巡回し、HTML を保存してオフライン取り込みに使う。

- 一般用語: https://study.005net.com/yogo/yogo.php → history.html
- 地理用語: https://study.005net.com/chiriYogo/chiriYogo.php → geography.html
- 公民用語: https://study.005net.com/kominYogo/kominYogo.php → civics.html

### 1. 保存先の用意

```
cd /Users/yoshiikatsuhiko/social_exam_analyzer
mkdir -p data/terms_catalog/html
```

### 2. mcp-chrome での操作（例）

クライアント（Serena/Claude等）から mcp-chrome のツールを使い、以下の操作を順番に行います。

1) ブラウズ開始 / 新規タブを開く
2) URL へ移動（goTo / navigate）
   - https://study.005net.com/yogo/yogo.php
3) ページの HTML を取得（getContent / getHTML / pageContent など）
4) 取得した HTML をファイルへ保存
   - `/Users/yoshiikatsuhiko/social_exam_analyzer/data/terms_catalog/html/history.html`

同様に以下も保存:

- https://study.005net.com/chiriYogo/chiriYogo.php → geography.html
- https://study.005net.com/kominYogo/kominYogo.php → civics.html

注意:
- mcp-chrome の具体的なツール名は環境により異なります（例: open, goto, content, save 等）。
- 文字コードは UTF-8 で保存してください。

### 3. 取り込み（オフラインモード）

```
cd /Users/yoshiikatsuhiko/social_exam_analyzer
pip install beautifulsoup4 lxml
python3 tools/build_terms_catalog.py --offline-dir data/terms_catalog/html
```

出力:

- data/terms_catalog/terms.json
- docs/terms_catalog.md

### 4. 抽出器での活用（自動）

`terms.json` が存在する場合、テーマ抽出器（ThemeExtractorV2）が用語カタログを補助的に利用し、
未検出テーマの削減や分野推定の精度向上に寄与します。

### 備考

- サイト構造が変更された場合、抽出が弱くなる可能性があります。必要に応じて `tools/build_terms_catalog.py` の `select_terms()` を調整してください。
- 定期更新したい場合は、mcp-chrome ワークフロー（巡回→HTML保存）を定期的に実行し、上記の取り込みを再実行してください。

