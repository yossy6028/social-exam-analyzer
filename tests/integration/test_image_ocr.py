#!/usr/bin/env python3
"""
画像のOCR処理テスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_image_ocr():
    """画像のOCR処理テスト"""
    
    print("=== 画像のOCR処理テスト ===\n")
    
    # 画像ファイルの存在確認
    image_files = [
        "image1.png", "image2.png", "image3.png", "image4.png", "image5.png",
        "image1.jpg", "image2.jpg", "image3.jpg", "image4.jpg", "image5.jpg",
        "image1.jpeg", "image2.jpeg", "image3.jpeg", "image4.jpeg", "image5.jpeg"
    ]
    
    print("画像ファイルの確認:")
    for img_file in image_files:
        if os.path.exists(img_file):
            print(f"  ✅ {img_file} が見つかりました")
        else:
            print(f"  ❌ {img_file} が見つかりません")
    
    print("\n現在のディレクトリの内容:")
    current_files = os.listdir(".")
    image_files_found = [f for f in current_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    
    if image_files_found:
        print("画像ファイル:")
        for img_file in image_files_found:
            print(f"  📷 {img_file}")
    else:
        print("画像ファイルが見つかりません")
    
    print("\nOCR処理の準備:")
    try:
        import pytesseract
        print("  ✅ pytesseract が利用可能です")
    except ImportError:
        print("  ❌ pytesseract がインストールされていません")
        print("     pip install pytesseract でインストールしてください")
    
    try:
        from PIL import Image
        print("  ✅ PIL (Pillow) が利用可能です")
    except ImportError:
        print("  ❌ PIL (Pillow) がインストールされていません")
        print("     pip install Pillow でインストールしてください")
    
    # 画像ファイルが見つかった場合のOCR処理
    if image_files_found:
        print(f"\n画像ファイル {image_files_found[0]} のOCR処理を試行します...")
        try:
            from PIL import Image
            import pytesseract
            
            # 最初の画像ファイルでOCR処理
            img = Image.open(image_files_found[0])
            text = pytesseract.image_to_string(img, lang='jpn')
            
            print(f"\nOCR結果:")
            print("="*50)
            print(text)
            print("="*50)
            
            # テキストの分析
            lines = text.split('\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            
            print(f"\nテキスト分析:")
            print(f"  総行数: {len(lines)}")
            print(f"  非空行数: {len(non_empty_lines)}")
            print(f"  文字数: {len(text)}")
            
            # 問題番号の検出
            import re
            question_numbers = re.findall(r'問\s*(\d+)', text)
            major_numbers = re.findall(r'大問\s*(\d+)', text)
            
            print(f"\n検出された問題番号:")
            print(f"  大問: {major_numbers}")
            print(f"  小問: {question_numbers}")
            
        except Exception as e:
            print(f"OCR処理でエラーが発生しました: {e}")
    
    print("\n" + "="*50)
    print("次のステップ:")
    print("1. 画像ファイルが正しく添付されているか確認")
    print("2. 必要なライブラリのインストール")
    print("3. OCR処理の実行")
    print("4. 抽出されたテキストの分析")

if __name__ == "__main__":
    test_image_ocr()
