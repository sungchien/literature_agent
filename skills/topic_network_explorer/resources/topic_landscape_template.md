---
type: topic_landscape
landscape_version: 1.0
project_title: "{PROJECT.md 中的論文工作題目}"
total_papers: {全庫論文總數}
total_chunks: {全庫總區塊數}
valid_chunks: {過濾首頁雜訊後納入建模之有效區塊數}
topic_count: {聚類出之主題總數}
network_html: "02_notes/topic_chunk_network.html"
stats_json: "01_papers/topic_network_stats.json"
created_date: {YYYY-MM-DD}
---

# 全庫語意區塊主題版圖與跨篇網路拓撲報告：{論文研究主題簡稱}

## 1. 全庫語意區塊建模總覽与概念構面命名 (BERTopic Modeling Overview & Construct Naming)

- **底層嵌入模型與資料規模：** 基於 `BAAI/bge-base-en-v1.5`（768 維稠密向量），共掃描 {total_papers} 篇論文、{total_chunks} 個原始區塊；經排除首頁機構地址與行政宣告後，共納入 **{valid_chunks} 個有效學術語意區塊** 進行主題聚類與網路拓撲運算。
- **無監督主題聚類與高階概念構面對映表：**

| 主題編號 (Topic ID) | 區塊數量 (Chunk Count) | 涵蓋論文數 (Paper Coverage) | c-TF-IDF 核心雙詞組與關鍵詞 (Top Bigrams & Keywords) | LLM 升維命名之學術概念構面 (Academic Thematic Construct) | 對映 `PROJECT.md` 研究問題 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Topic 0** | {N_0} ({P_0}%) | {K_0} 篇 | `{kw_1}, {kw_2}, {kw_3}, ...` | **{具理論深度之中文概念構面名稱}** | {RQ1 / RQ2 / RQ3 / 方法背景} |
| **Topic 1** | {N_1} ({P_1}%) | {K_1} 篇 | `{kw_1}, {kw_2}, {kw_3}, ...` | **{具理論深度之中文概念構面名稱}** | {RQ1 / RQ2 / RQ3 / 方法背景} |

---

## 2. 論文 × 主題權重分佈矩陣與精讀選文雷達 (Paper-by-Topic Distribution & Hub Paper Radar)

本節將區塊級（Chunk-level）主題標籤向上聚合至「論文層級（Paper-level）」，揭示各篇核心文獻的跨主題組成結構，並結合跨篇語意連線度（Cross-Paper Centrality）標定全庫最具影響力的「樞紐論文（Hub Papers）」：

| 論文標識 (Paper Filename / Citation) | 總有效區塊數 | 主導主題 (Dominant Topic & Share) | 次要主題 (Secondary Topic & Share) | 跨篇高相似連線數 (Cross-Paper Edges) | 卡片庫狀態與精讀建議 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `{paper_filename.md}` | {n} | Topic {X} ({pct}%) | Topic {Y} ({pct}%) | {edges} 條 | {已建立卡片 / 建議優先補建卡片之高樞紐論文} |

---

## 3. 跨篇語意橋樑剖析：高相似度跨篇段落對 (Top Cross-Paper Semantic Bridges)

透過計算 $S = E E^T$ 餘弦相似度矩陣並過濾同篇自連（$\text{Paper}_i \neq \text{Paper}_j$），以下列出全庫最具跨篇對話價值的成對段落（可直接作為第八週跨篇文獻矩陣與概念綜整之核心引證）：

### 3.1 同主題跨篇共鳴橋樑 (Intra-Topic Cross-Paper Consensus Bridges)
1. **【橋樑對 #1】餘弦相似度：`{sim_score}` | 所屬主題：Topic {X}（{主題名稱}）**
   - **區塊 A：** `{chunk_id_A}`（章節：`{section_A}`）—— *"{原文關鍵摘錄 A}"*
   - **區塊 B：** `{chunk_id_B}`（章節：`{section_B}`）—— *"{原文關鍵摘錄 B}"*
   - **跨篇對話解析：** {闡明兩篇不同論文在此處如何共同支持同一實證結論或採用相同方法機制}

### 3.2 跨主題理論交織橋樑 (Inter-Topic Boundary-Spanning Bridges)
1. **【跨界對 #1】餘弦相似度：`{sim_score}` | 連結主題：Topic {X} $\longleftrightarrow$ Topic {Y}**
   - **區塊 A（Topic {X}）：** `{chunk_id_A}`（章節：`{section_A}`）—— *"{原文關鍵摘錄 A}"*
   - **區塊 B（Topic {Y}）：** `{chunk_id_B}`（章節：`{section_B}`）—— *"{原文關鍵摘錄 B}"*
   - **跨界整合啟發：** {說明此跨主題連線如何協助我們串聯兩個看似獨立的概念構面（例如將系統架構連結至學習者認知負荷）}

---

## 4. 網路拓撲「結構洞（Structural Holes）」診斷與下階段矩陣導航 (Structural Hole Diagnosis & Next-Step Navigation)

### 4.1 主題群集間連通密度與結構洞定位 (Inter-Topic Connectivity & Structural Holes)
- **高密度連通區（成熟研究領地）：** {指出哪兩個 Topic 之間跨篇連線最密集，代表學界已有大量結合探討}
- **稀疏斷裂區 / 結構洞（Structural Hole — 潛在學術空白）：** {依據 Burt (1992) 結構洞理論，指出哪兩個對本研究 `PROJECT.md` 皆極為重要的 Topic 群集，在網路圖上呈現明顯的連線斷層，預告此斷層將在第八週矩陣與第九週 Research Gap 中轉化為核心立論破口}

### 4.2 對第八週「第二層：概念中心矩陣」之構面建議 (Recommended Concept Matrix Axes)
- **建議構面一（對應 RQ1）：** 聚合 Topic {A} 與 Topic {B} 之高中心性段落與卡片。
- **建議構面二（對應 RQ2）：** 聚合 Topic {C} 之實證段落與卡片。
- **建議構面三（對應 RQ3）：** 聚合 Topic {D} 之風險與障礙段落與卡片。
