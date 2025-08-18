#!/bin/bash

# 社会科目入試問題分析システム起動スクリプト

# スクリプトのあるディレクトリに移動
cd "$(dirname "$0")"

# tkinter対応の仮想環境をアクティベート（存在する場合）
if [ -d "venv_gui" ]; then
    source venv_gui/bin/activate
    echo "GUI対応仮想環境をアクティベート"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo "標準仮想環境をアクティベート"
fi

# tkinter対応Pythonを検索
PYTHON_CMD=""

# 仮想環境がアクティブな場合は、そのpythonを優先
if [ -n "$VIRTUAL_ENV" ]; then
    if python3 -c "import tkinter" 2>/dev/null; then
        PYTHON_CMD="python3"
        echo "仮想環境のtkinter対応Python使用: $VIRTUAL_ENV"
    fi
fi

# 仮想環境で見つからない場合はシステムのPythonを検索
if [ -z "$PYTHON_CMD" ]; then
    for py in "/opt/homebrew/bin/python3" "/usr/local/bin/python3" "/usr/bin/python3" "python3"; do
        if $py -c "import tkinter" 2>/dev/null; then
            PYTHON_CMD=$py
            echo "tkinter対応Python発見: $py"
            break
        fi
    done
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "tkinter対応のPythonが見つかりません。"
    echo "Homebrew経由でPythonをインストールしてください: brew install python-tk"
    exit 1
fi

# Pythonバージョンの確認
echo "Pythonバージョン確認中..."
$PYTHON_CMD --version

# メインプログラムの起動
echo "社会科目入試問題分析システムを起動しています..."
$PYTHON_CMD main.py

# エラーが発生した場合のメッセージ
if [ $? -ne 0 ]; then
    echo ""
    echo "エラーが発生しました。"
    echo "ログファイル (logs/social_analyzer.log) を確認してください。"
    read -p "Enterキーを押して終了..."
fi