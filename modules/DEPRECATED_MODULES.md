# 廃止予定モジュール一覧

## 即座に削除可能（未使用）
- improved_content_extractor.py
- enhanced_content_extractor.py
- final_content_extractor.py
- improved_question_extractor_v2.py
- improved_question_extractor_v3.py
- text_analyzer_backup.py

## 統合予定（使用中だが重複）
- social_analyzer_fixed.py → social_analyzer.pyに統合
- social_analyzer_improved.py → social_analyzer.pyに統合
- gemini_analyzer.py → gemini_bridge.pyに統合
- gemini_theme_analyzer.py → analyze_with_gemini_detailed.pyに統合

## リファクタリング対象
- theme_extractor_v2.py → improved_theme_extractor.pyに統合
- improved_question_analyzer.py → improved_question_extractor.pyに統合