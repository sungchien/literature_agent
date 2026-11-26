---
trigger: always_on
description: 本機 RAG 向量檢索之中英雙語中介協定與嚴格事實錨定紀律（常駐生效）。
---

# 雙語學術檢索與事實錨定規範

## 1. 跨語言學術檢索與雙語中介協定（Bilingual Scaffolding）
- **輸入轉譯（Chinese-to-English Query Formulation）：** 研究者得以繁體中文進行所有學術對話、討論與提問。當調用 `search_paper_chunks` 進行本機論文向量檢索時，因底層索引模型（`BAAI/bge-base-en-v1.5`）與論文全文皆為英文，**必須自動將研究者的中文提問意圖提煉轉譯為精確的「英文學術關鍵詞組」（Academic English Keywords / Query）**（例如：將「請檢索各篇論文對認知負荷的量表測量構面與研究限制」轉化為 `query="cognitive load measurement scale instrument dimensions limitations"`），**嚴禁直接以原始中文語句傳入檢索工具**。
- **輸出統整（English-to-Chinese Fact Synthesis）：** 當檢索工具回傳英文原文精華段落後，必須以嚴謹的學術繁體中文進行綜合論述與事實錨定，並完整保留英文文獻出處、作者與章節標籤（如 `[2024_Wang.md, 2.3 Instruments]`）。

## 2. 嚴格事實錨定紀律（Strict Fact Grounding & Anti-Hallucination）
- **百分百錨定實證段落：** 回答實證文獻問題時，所有數據、樣本數、統計檢定值與結論必須完全依據工作區檢索出的原文段落，嚴禁推論或補齊未被提及的統計結果。
- **客觀承認檢索空白：** 若檢索段落中未包含回答所需資訊，必須客觀坦誠指出：「本機現有檢索段落中未包含此項資訊，建議擴大文獻庫或調整檢索關鍵詞」，切勿利用預訓練常識進行腦補。
