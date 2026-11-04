---
name: topic-network-explorer

description: >
  當使用者需要針對本機向量索引（01_papers/vector_index.json 與 vector_embeddings.npz）中的全庫論文區塊（Chunks），
  運用 BERTopic（UMAP + HDBSCAN + c-TF-IDF）進行無監督跨篇主題建模、計算「論文 × 主題權重分佈矩陣（Paper-Topic Distribution）」、
  計算區塊兩兩餘弦相似度以建構「跨篇語意區塊互動網路圖（02_notes/topic_chunk_network.html）」、
  識別跨篇共鳴樞紐區塊（Hub Chunks）與結構洞（Structural Holes），並產出結構化主題版圖報告（02_notes/topic_landscape.md）時，請使用本 Skill。

version: "1.0"

author: "AI Agent 課程"

tags:
  - BERTopic
  - 主題模型
  - 語意網路圖
  - 結構洞
  - 區塊相似度
  - UMAP
  - HDBSCAN
  - c-TF-IDF
---

# 基於 BERTopic 之跨篇主題建模與語意區塊互動網路 Skill (topic-network-explorer)

## Skill 目的

本 Skill 旨在協助研究者在「第五週全庫向量檢索」與「第六週單篇精讀卡片」之後，建立一座連結「微觀段落」與「宏觀文獻版圖」的計算文獻學橋樑。當工作區累積了數十篇論文、數百個結構化區塊（Chunks）時，研究者往往難以單憑人腦記憶看出全庫潛藏的理論群落（Latent Themes），也難以發現散落於不同論文深處卻高度共鳴的隱藏段落。

本 Skill 直接複用第五週已計算完畢的高維度稠密向量矩陣（`01_papers/vector_embeddings.npz`），零重算成本地執行兩大核心運算：
1. **區塊級 BERTopic 主題建模（Chunk-Level Topic Modeling）：** 結合 UMAP 流形降維、HDBSCAN 密度聚類、離群值收斂（Outlier Reduction）與雙詞組（Bigram）c-TF-IDF 演算法，由下而上（Bottom-Up）自動浮現全庫核心主題簇，並向上聚合計算每一篇論文的 **「跨主題混合分佈（Paper-Topic Mixture）」**。
2. **跨篇區塊相似度拓撲與互動網路圖（Cross-Paper Semantic Similarity Network）：** 計算全庫 Chunks 兩兩餘弦相似度矩陣 $S = E E^T$，過濾同篇自戀連線並採 Top-$K$ 最近鄰稀疏化，生成自包含的互動式網頁網路圖（`02_notes/topic_chunk_network.html`）與結構化主題版圖報告（`02_notes/topic_landscape.md`），協助研究者定位 **「跨篇共鳴橋樑（Cross-Paper Bridges）」** 與 **「結構洞（Structural Holes，Burt, 1992）」**，為第八週的概念中心矩陣與第九週的學術空白鎖定提供客觀數據支撐。

---

## 支援資源與檔案結構

本 Skill 採用模組化組織架構，各子目錄分工如下：

```text
skills/topic_network_explorer/
│
├── SKILL.md                          # 核心流程入口（六步 SOP 規範與圖論分析守則）
│
├── resources/                        # 靜態規範、版圖報告空白範本與計算文獻學規準
│   ├── topic_landscape_template.md   # 全庫主題版圖、論文×主題熱力矩陣與跨篇橋樑報告範本
│   └── bertopic_network_criteria.md  # BERTopic 參數調校、學術雜訊防禦與結構洞判讀規準
│
├── examples/                         # 少樣本學習（Few-shot）標準示範
│   └── sample_topic_landscape.md     # 全庫論文語意區塊之完整主題與網路分析典範
│
└── scripts/                          # 本機自動化建模、互動網路圖生成與驗證工具
    └── build_topic_network.py        # 一鍵執行 BERTopic、相似度網路生成與報告驗證腳本
```

---

## 何時應使用本 Skill？

當使用者提出下列需求時，Agent 應主動調用本 Skill：
- 「請針對我工作區的 `vector_embeddings.npz` 執行 BERTopic 主題建模並建立區塊互動網路圖」
- 「幫我分析全庫論文的區塊可以分成哪幾個主題簇，並生成 `02_notes/topic_landscape.md`」
- 「建立跨篇 Chunk 相似度的互動網路圖（`02_notes/topic_chunk_network.html`），找出不同論文間最相似的段落對」
- 「將 BERTopic 跑出來的統計關鍵字簇，結合我的 `PROJECT.md` 命名為高階學術概念構面」
- 「透過區塊網路圖的結構洞（Structural Holes）與主題分佈，推薦我優先補做哪幾篇論文的閱讀卡片」

---

## 嚴格執行工作流程（SOP）

當 Agent 啟動本 Skill 後，必須按順序執行以下六個步驟：

### 第一步：執行本機 BERTopic 與相似度網路建置腳本（Computational Pipeline Execution）
1. 確認工作區已存在 `01_papers/vector_index.json` 與 `01_papers/vector_embeddings.npz`。
2. 於終端機執行 `@Script(scripts/build_topic_network.py)` 的 `build` 子命令：
   ```bash
   python skills/topic_network_explorer/scripts/build_topic_network.py build
   ```
3. 該腳本會自動完成：
   - **學術首頁與機構雜訊過濾：** 自動排除僅含大學機構地址、版權聲明或過短的雜訊區塊。
   - **BERTopic 主題聚類與離群收斂：** 對有效區塊執行降維、聚類、離群值歸併與 Bigram c-TF-IDF 關鍵詞提取。
   - **兩兩餘弦相似度與跨篇橋樑提取：** 計算 $S = E E^T$，提取全庫最強的「跨篇同題共鳴邊（Intra-Topic Cross-Paper Bridges）」與「跨篇跨題橋樑邊（Inter-Topic Cross-Paper Bridges）」，以及各主題間的跨群連通密度矩陣（Inter-Topic Connectivity Matrix）。
   - **產出雙模態交付物：** 自動生成互動式網路圖網頁 `02_notes/topic_chunk_network.html` 與底層統計數據檔 `01_papers/topic_network_stats.json`。

### 第二步：讀取統計結果與對齊 `PROJECT.md`（Data Grounding & RQ Alignment）
1. 讀取腳本輸出的 `01_papers/topic_network_stats.json` 與根目錄的 `PROJECT.md`（掌握研究者的 RQ1–RQ3）。
2. 同時檢查 `02_notes/cards/` 目錄，比對全庫論文中哪些已經建立單篇閱讀卡片、哪些高樞紐度（High Centrality）論文尚未建立卡片。

### 第三步：執行「從統計詞袋到學術概念構面」之語意升維命名（LLM Concept Naming）
參照 `@Resource(resources/bertopic_network_criteria.md)`：
1. 演算法（c-TF-IDF）原始產出的是統計詞組（如 `ai_agents_research_scientific_automated` 或 `cognitive_load_students_learning_writing`）。
2. Agent 必須閱讀每個 Topic 的 Top-10 c-TF-IDF 關鍵詞與最具代表性的 3 個原文 Chunks，將每個 Topic 升維命名為符合國際期刊水準的 **「學術概念構面名稱（Academic Thematic Construct）」**，並標註其主要對映至 `PROJECT.md` 的哪一個研究問題（RQ1、RQ2、RQ3 或背景方法脈絡）。

### 第四步：剖析「論文 × 主題分佈矩陣」與「跨篇語意橋樑」（Paper-Topic Mixture & Bridge Analysis）
1. 整理全庫代表性論文在各大主題上的區塊佔比（Paper-Topic Distribution），指出哪些論文屬於「單一主題深耕型」，哪些屬於「跨主題綜合型」。
2. 挑選相似度最高且最具理論對話價值的 Top 跨篇段落對（Cross-Paper Chunk Pairs，$\text{Paper}_i \neq \text{Paper}_j$），明確展示 A 論文的哪個章節段落與 B 論文的哪個章節段落產生高度共鳴或方法交鋒，作為第八週撰寫文獻綜整（Synthesis）的直接彈藥。

### 第五步：診斷網路「結構洞（Structural Holes）」與產出 `02_notes/topic_landscape.md`
1. 依據 **Burt (1992) 結構洞理論（Structural Holes Theory）**，檢視主題間的跨群連通密度（Inter-Topic Edge Density）：找出哪兩個與本研究密切相關的主題群集之間連線最為稀疏（例如「工程界自主代理系統群集」與「教育界學習者認知與日誌反思群集」之間缺乏直接實證連線），將其標定為視覺化的潛在研究缺口。
2. 遵循 `@Resource(resources/topic_landscape_template.md)` 與 `@Example(examples/sample_topic_landscape.md)`，將完整分析寫入 `02_notes/topic_landscape.md`。

### 第六步：執行報告合規檢驗與指引互動視覺化探索（Validation & Interactive Guidance）
1. 執行驗證子命令確認 `02_notes/topic_landscape.md` 結構完整：
   ```bash
   python skills/topic_network_explorer/scripts/build_topic_network.py validate 02_notes/topic_landscape.md
   ```
2. 引導研究者在瀏覽器開啟 `02_notes/topic_chunk_network.html`，利用相似度滑桿、跨篇連線開關與右側段落對照器進行視覺化探索。

---

## 嚴格執行紀律（Governance Rules）

1. **百分百錨定真實聚類數據（Strict Algorithmic Grounding）：** `02_notes/topic_landscape.md` 中列出的主題編號、區塊數量、c-TF-IDF 關鍵詞、跨篇相似度分數（Cosine Similarity）與 `chunk_id`，必須 100% 源自 `01_papers/topic_network_stats.json` 的真實計算結果，嚴禁憑空捏造統計數值。
2. **區分「同篇相鄰相似」與「跨篇語意共鳴」（Cross-Paper Priority）：** 在分析區塊網路時，必須聚焦於不同論文之間（$\text{Paper}_A \neq \text{Paper}_B$）的跨篇連線，切勿拿同一篇論文內部的前後段相似性充當跨篇學術對話。
3. **演算法輔助而非取代精讀（Complement, Not Replace Reading Cards）：** 明確提醒研究者：BERTopic 與網路圖是宏觀的「衛星導航雷達」，能幫助發掘主題結構與挑選高價值核心論文；針對網路圖抓出的關鍵樞紐論文（Hub Papers），仍應搭配第六週的 `academic-reading-card` 進行深度方法學效度解剖。
