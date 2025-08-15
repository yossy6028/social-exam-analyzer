#!/bin/bash

# 社会科目入試問題分析システム（コマンドライン版）

# スクリプトのあるディレクトリに移動
cd "$(dirname "$0")"

# コマンドライン引数があれば直接実行（PDFファイルのドラッグ＆ドロップ対応）
if [ $# -gt 0 ]; then
    if [[ "$1" == *.pdf ]]; then
        echo -e "\033[0;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
        echo -e "\033[0;36m                     PDFファイル分析中...                      \033[0m"
        echo -e "\033[0;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
        echo ""
        
        # ファイル名から学校名と年度を推測
        FILENAME=$(basename "$1")
        SCHOOL=$(echo "$FILENAME" | sed 's/[0-9].*//;s/_.*//;s/\.pdf//')
        YEAR=$(echo "$FILENAME" | grep -o '[0-9]\{4\}' | head -1)
        
        echo "📚 ファイル: $FILENAME"
        echo "🏫 学校名: ${SCHOOL:-不明}"
        echo "📅 年度: ${YEAR:-2025}年"
        echo ""
        
        # Pythonコマンドの選択
        if [ -x "/Users/yoshiikatsuhiko/.pyenv/versions/3.11.9/bin/python3" ]; then
            PYTHON_CMD="/Users/yoshiikatsuhiko/.pyenv/versions/3.11.9/bin/python3"
        elif command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
        else
            echo "エラー: Python3が見つかりません"
            exit 1
        fi
        
        # Pythonスクリプトを直接実行（警告を抑制）
        $PYTHON_CMD main.py "$1" --school "$SCHOOL" --year "${YEAR:-2025}" 2>&1 | \
            grep -v "tkinter\|Warning:\|import _tkinter\|ModuleNotFoundError" | \
            grep -v "^$"  # 空行も削除
        
        echo ""
        echo -e "\033[0;32m✅ 分析完了！\033[0m"
        echo "📁 結果は /Users/yoshiikatsuhiko/Desktop/過去問_社会 に保存されました"
        echo ""
        echo "Enterキーを押して終了..."
        read -r
        exit 0
    else
        echo "エラー: PDFファイルを指定してください"
        exit 1
    fi
fi

# 引数がない場合は対話モード
echo -e "\033[0;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e "\033[0;36m                     社会科目入試問題分析システム                      \033[0m"
echo -e "\033[0;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo ""
echo "使い方："
echo "  1. このファイルにPDFをドラッグ＆ドロップ"
echo "  2. または、ターミナルで: ./analyze_cli.command PDFファイル"
echo ""
echo "分析機能："
echo "  📍 分野別分析（地理・歴史・公民）"
echo "  📝 テーマ一覧の生成"
echo "  📊 出題傾向の統計"
echo ""

# PDFファイルの選択を促す
echo "PDFファイルをドラッグ＆ドロップして、Enterキーを押してください："
read -r PDF_FILE

# 入力されたパスから引用符を除去
PDF_FILE=$(echo "$PDF_FILE" | sed 's/^['\''"]//;s/['\''"]$//' | sed 's/\\ / /g')

if [ -f "$PDF_FILE" ]; then
    # ファイル名から情報を抽出
    FILENAME=$(basename "$PDF_FILE")
    SCHOOL=$(echo "$FILENAME" | sed 's/[0-9].*//;s/_.*//;s/\.pdf//')
    YEAR=$(echo "$FILENAME" | grep -o '[0-9]\{4\}' | head -1)
    
    echo ""
    echo "学校名を入力（デフォルト: $SCHOOL）："
    read -r INPUT_SCHOOL
    [ -n "$INPUT_SCHOOL" ] && SCHOOL="$INPUT_SCHOOL"
    
    echo "年度を入力（デフォルト: ${YEAR:-2025}）："
    read -r INPUT_YEAR
    [ -n "$INPUT_YEAR" ] && YEAR="$INPUT_YEAR"
    
    echo ""
    echo "分析を開始します..."
    echo ""
    
    # Pythonコマンドの選択
    if [ -x "/Users/yoshiikatsuhiko/.pyenv/versions/3.11.9/bin/python3" ]; then
        PYTHON_CMD="/Users/yoshiikatsuhiko/.pyenv/versions/3.11.9/bin/python3"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo "エラー: Python3が見つかりません"
        exit 1
    fi
    
    # 分析実行
    $PYTHON_CMD main.py "$PDF_FILE" --school "$SCHOOL" --year "${YEAR:-2025}" 2>&1 | \
        grep -v "tkinter\|Warning:\|import _tkinter\|ModuleNotFoundError" | \
        grep -v "^$"
    
    echo ""
    echo -e "\033[0;32m✅ 分析完了！\033[0m"
    echo "📁 結果は /Users/yoshiikatsuhiko/Desktop/過去問_社会 に保存されました"
else
    echo "エラー: 指定されたファイルが見つかりません"
fi

echo ""
echo "Enterキーを押して終了..."
read -r