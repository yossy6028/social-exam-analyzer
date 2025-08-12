# ファイル選択機能の改善完了

## 解決した問題
BunkoOCRのファイルダイアログでPDFファイルを自動選択できない問題を解決。

## 実装した解決策

### 1. フルパス直接指定方式（推奨）
- **Cmd+Shift+G**でパス入力ダイアログを開く
- フルパスをペーストして直接ファイルに移動
- 最も確実で高速な方法

```python
pyperclip.copy(full_path)
pyautogui.hotkey('cmd', 'shift', 'g')
time.sleep(1)
pyautogui.hotkey('cmd', 'v')
time.sleep(0.5)
pyautogui.press('return')
time.sleep(1.5)
pyautogui.press('return')
```

### 2. デスクトップエイリアス方式（オプション）
- デスクトップの「過去問」エイリアスを使用
- フォルダを段階的にナビゲート
- より柔軟だが時間がかかる

## 技術的なポイント

### 問題の原因
- macOSのファイルダイアログは通常のウィンドウと異なる扱い
- キーボード入力のフォーカスが適切に移らない
- 検索ウィンドウの位置やアクセス方法が特殊

### 解決のキー
- **Cmd+Shift+G**（Go to Folder）機能の活用
- フルパスを使用することで確実にファイルを特定
- pyperclipでクリップボード経由でパスを渡す

## 今後の拡張案

1. **設定ファイルでの選択**
   ```json
   {
     "file_selection_method": "fullpath",  // or "alias"
     "alias_location": "~/Desktop/過去問"
   }
   ```

2. **複数の方法を試すフォールバック機構**
   - フルパス方式 → エイリアス方式 → 手動選択

3. **学校・年度別のショートカット設定**
   - よく使う組み合わせを事前定義

## 使用方法

現在の実装では自動的にフルパス方式でファイルを開きます：

```bash
python3 entrance_exam_app_cli.py
# または
python3 run_app.py
```

## 注意事項
- macOSのアクセシビリティ設定でPythonに権限を付与する必要がある
- BunkoOCRが起動している必要がある
- pyautoguiとpyperclipのインストールが必要