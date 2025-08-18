#!/usr/bin/env python3
"""
現在の分析結果の問題点を確認
"""
import re

def analyze_output():
    """出力結果から問題を分析"""
    
    # ユーザーが提供した出力結果
    output = """
  問1: 関東平野の特徴 [地理] | 主要語: 県内を流れるいくつかの河川、そくせい南北約60kmにわたる範囲に広がるこの平野、次の文章が説明している平野
  問2: 雨温図から気候の特徴を読み取る [地理]
  問3: 分析対象外 [総合]
  問4: 日本の近郊農業 [地理]
  問5: 分析対象外 [総合]
  問6: 地形図の読み取りと解釈 [地理]
  問7: 日本の近郊農業 [地理]
  問8: 分析対象外 [総合]
  問9: 循環型社会の仕組みと課題 [公民] | 主要語: リユース、ペットボトル
  問9: 幕末の開国と外国人との交渉 [歴史] | 主要語: リユース、ペットボトル
  問10: 明治時代の日本の領土と憲法 [歴史]
  問10: 江戸時代の武家社会の秩序と制度 [歴史]
  問11: 阪神・淡路大震災と防災・減災 [地理] | 主要語: 減災
  問11: 米騒動の原因と背景 [総合] | 主要語: 減災
  問1: 弥生時代の貯蔵施設 [歴史]
  問2: 平安時代の仏教文化の展開 [歴史]
  問3: 日宋貿易の輸入品 [歴史]
  問4: 鎌倉幕府の成立と北条氏の役割 [歴史] | 主要語: 尼将軍
  問5: 江戸時代の武家社会の秩序と制度 [歴史]
  問12: 米騒動の原因と背景、新聞記事の検閲 [歴史]
  問6: 江戸時代の勘合貿易と海賊 [地理]
  問7: 江戸時代の農業技術の発展 [地理]
  問8: 江戸時代の学問と教育 [歴史]
  問13: 日中戦争の開戦とその背景 [歴史]
  問1: 日本国憲法と内閣総理大臣の資格 [歴史]
  問2: 日本国憲法と内閣総理大臣の資格 [歴史] | 主要語: 第70条内閣総理大臣が欠けたとき
  問6: 日本の司法制度と裁判員制度 [歴史]
  問7: 憲法と裁判官の罷免 [公民] | 主要語: 衆議院、参議院、第78条裁判官は
  問3: 現行憲法下における天皇の役割 [公民] | 主要語: 衆議院、最高裁判所
  問8: 環太平洋パートナーシップ協定（TPP） [歴史] | 主要語: アジア、マレーシア、オーストラリア
  問4: 昭和戦後時代の特徴 [歴史]
  問5: 内閣の役割 [公民]
  問9: 経済の仕組み [公民]
  問10: 政治の仕組み [公民]
  問11: 国際協力 [公民] | 主要語: ウクライナ、ロシア
  問12: 社会保障制度 [歴史] | 主要語: プリンストン、ノーベル
  問13: 真鍋淑郎氏 [歴史] | 主要語: トランプ、ロシア、プリンストン、ノーベル
  問1: 社会保障制度 [公民] | 主要語: ワルシャワ
  問2: 基本的人権 [公民]
  問3: 国際平和と軍縮 [公民] | 主要語: この条約
  問4: 核兵器 下線部 [歴史] | 主要語: ーバイデン、アメリカ、ロシア、オバマオ、オバマウ
  問5: 公民総合問題 [公民]
    """
    
    print("=" * 60)
    print("現在の分析結果の問題点")
    print("=" * 60)
    
    # 1. OCRフラグメントのチェック
    print("\n1. OCRフラグメント:")
    ocr_fragments = []
    lines = output.strip().split('\n')
    for line in lines:
        if '核兵器 下線部' in line:
            ocr_fragments.append(line.strip())
    
    if ocr_fragments:
        print(f"   ❌ 残存フラグメント発見:")
        for frag in ocr_fragments:
            print(f"      {frag}")
    else:
        print("   ✅ フラグメントなし")
    
    # 2. 問題番号の重複チェック
    print("\n2. 問題番号の重複:")
    question_counts = {}
    current_major = 1
    
    for line in lines:
        if '大問' in line:
            major_match = re.search(r'大問\s*(\d+)', line)
            if major_match:
                current_major = int(major_match.group(1))
        elif re.match(r'\s*問\d+:', line):
            match = re.match(r'\s*問(\d+):', line)
            if match:
                q_num = int(match.group(1))
                key = f"大問{current_major}-問{q_num}"
                if key not in question_counts:
                    question_counts[key] = 0
                question_counts[key] += 1
    
    duplicates = [(k, v) for k, v in question_counts.items() if v > 1]
    if duplicates:
        print(f"   ❌ 重複発見:")
        for key, count in duplicates:
            print(f"      {key}: {count}回")
    else:
        print("   ✅ 重複なし")
    
    # 3. 主要語句の問題
    print("\n3. 主要語句の問題:")
    issues = []
    
    # 促成栽培が含まれていない
    if '促成' not in output and '促成栽培' not in output:
        issues.append("促成栽培が抽出されていない（大問1-問1）")
    
    # 「そくせい」という誤変換
    if 'そくせい' in output:
        issues.append("「そくせい」という誤変換がある（促成の誤り）")
    
    # オバマオ、オバマウという誤認識
    if 'オバマオ' in output or 'オバマウ' in output:
        issues.append("「オバマ」の誤認識（オバマオ、オバマウ）")
    
    if issues:
        print("   ❌ 問題発見:")
        for issue in issues:
            print(f"      - {issue}")
    else:
        print("   ✅ 問題なし")
    
    # 4. 分野判定の妥当性
    print("\n4. 分野判定の疑問点:")
    field_issues = []
    
    # 憲法関連が歴史になっている
    if '日本国憲法と内閣総理大臣の資格 [歴史]' in output:
        field_issues.append("日本国憲法関連が[歴史]になっている（[公民]が適切?）")
    
    # 司法制度が歴史になっている
    if '日本の司法制度と裁判員制度 [歴史]' in output:
        field_issues.append("司法制度が[歴史]になっている（[公民]が適切?）")
    
    if field_issues:
        print("   ⚠️  要検討:")
        for issue in field_issues:
            print(f"      - {issue}")
    else:
        print("   ✅ 問題なし")
    
    print("\n" + "=" * 60)
    print("改善が必要な項目:")
    print("1. 「核兵器 下線部」フラグメントの修正")
    print("2. 問題番号の重複解消（問9、問10、問11）")
    print("3. OCR誤認識の修正（そくせい→促成、オバマオ→オバマ）")
    print("4. 重要語句の抽出精度向上")
    print("=" * 60)

if __name__ == "__main__":
    analyze_output()