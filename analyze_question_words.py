#!/usr/bin/env python3
"""
小問のワード分析とsubject_index.md照合のプロセス
"""

import re
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.terms_repository import TermsRepository
from modules.improved_question_extractor import ImprovedQuestionExtractor

def analyze_question_words():
    """小問のワード分析とsubject_index.md照合のプロセス"""
    
    print("=== 小問のワード分析とsubject_index.md照合のプロセス ===\n")
    
    # 必要なモジュールを初期化
    extractor = ImprovedQuestionExtractor()
    terms_repo = TermsRepository()
    
    # 実際のOCRテキストファイルを読み込み
    ocr_file = "logs/ocr_2023_日工大駒場_社会.txt"
    
    try:
        with open(ocr_file, 'r', encoding='utf-8') as f:
            ocr_text = f.read()
    except FileNotFoundError:
        print(f"❌ OCRファイルが見つかりません: {ocr_file}")
        return
    
    print(f"📁 OCRファイル: {ocr_file}")
    
    # 大問セクションを抽出
    major_sections = extractor._find_major_sections(ocr_text)
    
    if not major_sections:
        print("❌ 大問セクションが見つかりません")
        return
    
    print(f"✅ 検出された大問数: {len(major_sections)}")
    
    # 各小問を詳細分析
    for major_num, section_text in major_sections:
        print(f"\n{'='*60}")
        print(f"大問{major_num}の詳細分析")
        print(f"{'='*60}")
        
        # 小問を抽出
        minor_questions = extractor._extract_minor_questions(section_text)
        
        print(f"抽出された小問数: {len(minor_questions)}")
        
        # 各小問を詳細分析
        for i, (q_num, q_text) in enumerate(minor_questions[:5]):  # 最初の5問のみ
            print(f"\n--- 小問{q_num} ---")
            print(f"テキスト: {q_text[:100]}...")
            
            # ステップ1: ワード分割
            words = extract_keywords_from_question(q_text)
            print(f"抽出されたキーワード: {words}")
            
            # ステップ2: subject_index.mdとの照合
            matched_terms = find_matching_terms(words, terms_repo)
            print(f"照合結果: {matched_terms}")
            
            # ステップ3: 主題の決定
            main_theme = determine_main_theme(matched_terms, q_text)
            print(f"決定された主題: {main_theme}")
            
            print("-" * 40)

def extract_keywords_from_question(question_text: str) -> list:
    """小問からキーワードを抽出"""
    # 基本的な前処理
    text = question_text.strip()
    
    # 不要な文字を除去
    text = re.sub(r'[【】「」『』()（）\[\]{}]', '', text)
    
    # 句読点で分割
    sentences = re.split(r'[。、，．]', text)
    
    keywords = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 3:
            continue
        
        # 重要なキーワードを抽出
        # 1. 専門用語（漢字の連続）
        kanji_terms = re.findall(r'[一-龯]{2,}', sentence)
        keywords.extend(kanji_terms)
        
        # 2. 地名・人名
        location_names = re.findall(r'[東南西北]京|[東南西北]海道|[都道府県]|[市町村]', sentence)
        keywords.extend(location_names)
        
        # 3. 年代・世紀
        time_periods = re.findall(r'\d+世紀|\d+年代|\d+年', sentence)
        keywords.extend(time_periods)
        
        # 4. 制度・政策名
        policy_terms = re.findall(r'[制政策法憲条約]', sentence)
        keywords.extend(policy_terms)
    
    # 重複を除去
    unique_keywords = list(set(keywords))
    
    # 短すぎるキーワードを除外
    filtered_keywords = [kw for kw in unique_keywords if len(kw) >= 2]
    
    return filtered_keywords

def find_matching_terms(keywords: list, terms_repo: TermsRepository) -> list:
    """キーワードとsubject_index.mdの用語を照合"""
    matched_terms = []
    
    for keyword in keywords:
        # TermsRepositoryで用語を検索
        found_terms = terms_repo.find_terms_in_text(keyword)
        
        if found_terms:
            for field, term in found_terms:
                matched_terms.append({
                    'keyword': keyword,
                    'term': term,
                    'field': field,
                    'confidence': calculate_confidence(keyword, term)
                })
    
    # 信頼度でソート
    matched_terms.sort(key=lambda x: x['confidence'], reverse=True)
    
    return matched_terms

def calculate_confidence(keyword: str, term: str) -> float:
    """キーワードと用語の一致度を計算"""
    if keyword == term:
        return 1.0
    elif keyword in term or term in keyword:
        return 0.8
    elif len(set(keyword) & set(term)) / len(set(keyword) | set(term)) > 0.5:
        return 0.6
    else:
        return 0.3

def determine_main_theme(matched_terms: list, question_text: str) -> str:
    """照合結果から主題を決定"""
    if not matched_terms:
        return "主題不明"
    
    # 最も信頼度の高い用語を選択
    best_match = matched_terms[0]
    
    # 分野別の重み付け
    field_weights = {
        'geography': 1.0,
        'history': 1.0,
        'civics': 1.0
    }
    
    # 信頼度と分野の重みを考慮して最終スコアを計算
    final_score = best_match['confidence'] * field_weights.get(best_match['field'], 1.0)
    
    # 主題を決定
    if final_score >= 0.8:
        theme = f"{best_match['term']}について"
    elif final_score >= 0.6:
        theme = f"{best_match['term']}に関する問題"
    else:
        theme = f"{best_match['keyword']}について"
    
    return theme

if __name__ == "__main__":
    analyze_question_words()
