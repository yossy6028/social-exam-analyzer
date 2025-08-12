#!/bin/bash

# 社会科目入試問題分析システム起動スクリプト

# スクリプトのあるディレクトリに移動
cd "$(dirname "$0")"

# Python仮想環境のアクティベート（存在する場合）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Pythonバージョンの確認
echo "Pythonバージョン確認中..."
python3 --version

# 必要なパッケージのインストール確認
echo "必要なパッケージを確認中..."
python3 -c "import tkinter" 2>/dev/null || {
    echo "tkinterがインストールされていません。"
    exit 1
}

# メインプログラムの起動
echo "社会科目入試問題分析システムを起動しています..."
python3 main.py

# エラーが発生した場合のメッセージ
if [ $? -ne 0 ]; then
    echo ""
    echo "エラーが発生しました。"
    echo "ログファイル (logs/social_analyzer.log) を確認してください。"
    read -p "Enterキーを押して終了..."
fi