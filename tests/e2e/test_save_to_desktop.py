#!/usr/bin/env python3
"""
保存先ディレクトリの動作テスト
"""

import sys
from pathlib import Path
from datetime import datetime

def test_save_directory():
    """保存先ディレクトリのテスト"""
    
    # 保存先ディレクトリを固定
    save_dir = Path("/Users/yoshiikatsuhiko/Desktop/過去問_社会")
    
    print(f"保存先ディレクトリ: {save_dir}")
    print(f"ディレクトリ存在確認: {save_dir.exists()}")
    
    # ディレクトリが存在しない場合は作成
    try:
        save_dir.mkdir(parents=True, exist_ok=True)
        print("✅ ディレクトリ作成成功（または既存）")
    except Exception as e:
        print(f"❌ ディレクトリ作成エラー: {e}")
        return False
    
    # テストファイルの作成
    school_name = "テスト学校"
    year = "2025"
    filename = f"{school_name}_{year}_テーマ一覧_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    file_path = save_dir / filename
    
    print(f"テストファイル名: {filename}")
    print(f"フルパス: {file_path}")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("テスト: 社会科入試問題分析 - テーマ一覧\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"学校名: {school_name}\n")
            f.write(f"年度: {year}年\n")
            f.write(f"分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
            f.write("\n【テスト内容】\n")
            f.write("このファイルは保存先ディレクトリのテスト用です。\n")
            f.write("正常に保存されれば、機能は正しく動作しています。\n")
        
        print(f"✅ ファイル作成成功: {file_path}")
        
        # ファイルの存在確認
        if file_path.exists():
            print(f"✅ ファイル存在確認: OK")
            print(f"ファイルサイズ: {file_path.stat().st_size} bytes")
            
            # ファイル内容の確認
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"ファイル内容の先頭100文字:\n{content[:100]}...")
            
            return True
        else:
            print("❌ ファイル存在確認: NG")
            return False
            
    except Exception as e:
        print(f"❌ ファイル作成エラー: {e}")
        return False

if __name__ == "__main__":
    print("保存先ディレクトリ機能のテスト開始\n")
    result = test_save_directory()
    
    if result:
        print("\n✅ テスト成功: 保存先ディレクトリ機能は正常に動作しています")
        sys.exit(0)
    else:
        print("\n❌ テスト失敗: エラーを確認してください")
        sys.exit(1)