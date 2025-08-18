#!/usr/bin/env python3
"""
実際のPDFデータで修正されたテーマ抽出器をテスト
ログで問題があった実際のテキストを使用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.theme_extractor_v2 import ThemeExtractorV2

def test_real_data():
    """実際のデータでテーマ抽出をテスト"""
    extractor = ThemeExtractorV2()
    
    print("=== 実際のPDFデータでのテーマ抽出テスト ===\n")
    
    # ログで問題があった実際のテキスト
    real_test_cases = [
        # 空欄補充問題（ログで除外されていた）
        ("1. 次の資料を読んで、各設問に答えなさい。", "資料読み取り問題"),
        ("問1.空らん( ① )について、 空らんに入る適切な語句を、次のア~エの中 から一つ選び記号で答えなさい。", "空欄補充問題1"),
        ("エ.薬師寺 問2.空らん( ② )について、 空らんに入る適切な語句を、次のア~エの中 から一つ選び記号で答えなさい。", "空欄補充問題2"),
        ("ア.桓武天皇が平安京に遷都を行った。 イ. 朝廷によって墾田永年私財法が出された。 ウ. 大海人皇子と大友皇子の間で皇位継承をめぐり争いが起こった。 エ.白村江の戦いの後に新羅が朝鮮半島を統一した。", "選択肢問題1"),
        ("ア.栄西 イ. 道元 ウ. 日蓮 エ. 法然 問6. 下線⑥について、 この当時の中国の王朝として正しいものを、次のア~エの中から一つ選び記号で答えなさい。", "選択肢問題2"),
        ("ア.日露戦争の講和条約は、調停国であるアメリカで結ばれた。 イ. 日露戦争の結果、 日本は多額の賠償金を得た。", "選択肢問題3"),
        ("として正しいものを、次のア~エの中から一つ選び記号で答えなさい。 ア.韓国併合 イ.五・四運動 ウ.二十一か条の要求 エ.柳条湖事件", "選択肢問題4"),
        ("2.次の図と文章を読んで、各設問に答えなさい。", "図表問題1"),
        ("(い)淀 ウ. (あ) 千里 - (い) 大淀 エ. (あ)千里 (い)淀 問2.下線②について、 空らん (③)について、次の写真に見られる 災害を何といいますか。 空らんにあてはまるよう に答えなさい。", "複合問題1"),
        ("て、次の写真に見られる 災害を何といいますか。 空らんにあてはまるよう に答えなさい。 (出典:地理...", "写真問題"),
        ("465,902 88.6 (2020 年国勢調査より作成) 問6.下線⑥について、 関西地方の集落や", "統計問題"),
        ("ウ. (A) 高知 (C)山梨 エ.(A)山梨 (C) 徳島 問8. 下線⑧について、 空らん(⑧ )について、 空らんに", "複合問題2"),
        ("3.次の文章を読んで、各設問に答えなさい。", "文章問題"),
        ("大学に通勤している /月 26万円稼いでいる 38 歳/女性/主婦/千葉県松戸市在住/東京都武蔵野市", "現代社会問題"),
        ("ア.確定申告 イ.軽減税率 ウ. 源泉徴収 エ.累進課税 (3)表中の下線cについて、 デフリンピッ", "経済問題"),
        ("ア. 勤労権 イ. 団結権 ウ. 団体行動権 エ. 団体交渉権 -12- 25 中一社 (1) 問5", "公民問題"),
        ("エ.(X)誤・ (Y)誤 -13- 問7. 下線 ⑦について、次のグラフは日本の歳出の推移をしめした", "グラフ問題"),
        ("エ.(X)社会保障関係費 (Y) 防衛関係費 (Z)国債費 問8.空らん(⑧ )について、 空らんに", "複合問題3"),
    ]
    
    success_count = 0
    total_count = len(real_test_cases)
    
    for i, (text, description) in enumerate(real_test_cases, 1):
        print(f"テストケース {i}: {description}")
        print(f"テキスト: {text[:80]}...")
        
        try:
            result = extractor.extract(text)
            if result and result.theme:
                print(f"結果: ✓ テーマ抽出成功")
                print(f"  テーマ: {result.theme}")
                print(f"  カテゴリ: {result.category}")
                print(f"  信頼度: {result.confidence}")
                success_count += 1
            else:
                print(f"結果: ✗ テーマ抽出失敗")
                print(f"  テーマ: {result.theme if result else 'None'}")
                print(f"  カテゴリ: {result.category if result else 'None'}")
                print(f"  信頼度: {result.confidence if result else 'N/A'}")
        except Exception as e:
            print(f"結果: ✗ エラー発生: {e}")
        
        print("-" * 60)
    
    print(f"\n=== 結果サマリー ===")
    print(f"成功: {success_count}/{total_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 すべてのテストケースでテーマ抽出に成功しました！")
    elif success_count >= total_count * 0.8:
        print("✅ 大部分のテストケースでテーマ抽出に成功しました！")
    else:
        print("⚠️  テーマ抽出の改善が必要です。")

if __name__ == "__main__":
    test_real_data()
