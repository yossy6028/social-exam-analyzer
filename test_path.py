#!/usr/bin/env python3
"""
パス入力のテストスクリプト
"""

import os

def test_path_input():
    """パス入力テスト"""
    print("PDFファイルのパスを入力してください:")
    print("（Finderからドラッグ&ドロップするか、コピー&ペーストしてください）")
    print("")
    print("テスト用サンプルパス:")
    print("/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/東京電機大学中学校/2020年東京電機大学中学校問題_社会.pdf")
    print("")
    
    while True:
        file_path = input("ファイルパス: ").strip()
        
        if file_path.lower() == 'q':
            break
        
        # デバッグ情報
        print(f"\n入力された生データ: {repr(file_path)}")
        
        # クォートを除去
        file_path = file_path.strip('"').strip("'")
        print(f"クォート除去後: {repr(file_path)}")
        
        # エスケープ文字の処理（ターミナルからのコピペ用）
        if '\\' in file_path:
            print("エスケープ文字を検出しました")
            # バックスラッシュエスケープを解除
            file_path = file_path.replace('\\ ', ' ')
            file_path = file_path.replace('\\(', '(')
            file_path = file_path.replace('\\)', ')')
            print(f"エスケープ解除後: {repr(file_path)}")
        
        # ファイルの存在確認
        if os.path.exists(file_path):
            print(f"✅ ファイルが見つかりました!")
            print(f"   ファイル名: {os.path.basename(file_path)}")
            print(f"   サイズ: {os.path.getsize(file_path):,} bytes")
        else:
            print(f"❌ ファイルが見つかりません")
            
            # 代替パスを試す
            alt_path = file_path.replace('\\', '')
            if os.path.exists(alt_path):
                print(f"✅ 代替パスで見つかりました: {alt_path}")
            else:
                # よくある問題の診断
                parent_dir = os.path.dirname(file_path)
                if os.path.exists(parent_dir):
                    print(f"📁 親ディレクトリは存在します: {parent_dir}")
                    files = [f for f in os.listdir(parent_dir) if '.pdf' in f.lower()]
                    if files:
                        print(f"   このディレクトリのPDFファイル:")
                        for f in files[:5]:
                            print(f"   - {f}")
                else:
                    print(f"📁 親ディレクトリも見つかりません")
        
        print("")

if __name__ == "__main__":
    test_path_input()