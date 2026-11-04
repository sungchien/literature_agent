---
name: literature-matrix-synthesizer

description: >
  當使用者需要將 02_notes/cards/ 目錄下的多張單篇原子閱讀卡片（card_*.md），
  橫向整合為結構化的跨篇文獻比較矩陣（儲存於 02_notes/literature_matrix.md），
  並從「作者中心流水帳」轉化為「概念中心綜整（Concept-Centric Synthesis）」時，請使用本 Skill。
  本 Skill 嚴格遵循 Garrard (2020) 矩陣回顧法與 Webster & Watson (2002) 概念矩陣規範，
  具備異質文類（實證研究、系統性綜述 SLR、概念立場文、技術架構開發）欄位適配能力，
  並能針對 PROJECT.md 的核心研究問題（RQ1-RQ3）提煉跨篇共識、爭端與情境微差。

version: "1.0"

author: "AI Agent 課程"

tags:
  - 文獻矩陣
  - 概念綜整
  - 跨篇比較
  - Matrix Method
  - Concept-Centric
  - 文獻探討
---

# 跨篇文獻矩陣共構與概念導向綜整 Skill (literature-matrix-synthesizer)

## Skill 目的

本 Skill 旨在協助研究者跨越「單篇卡片孤島」與「報流水帳（Annotated Bibliography）」的寫作陷阱，將散落於 `02_notes/cards/` 的多張七維標準閱讀卡片，系統化重組為儲存在 `02_notes/literature_matrix.md` 的**雙層次跨篇文獻比較矩陣**與**概念導向綜整分析（Thematic Synthesis）**。

本 Skill 絕不將不同文類的論文削足適履硬塞入單一死板表格，而是承接第七週「BERTopic 全庫主題建模與跨篇區塊相似度網路（`02_notes/topic_landscape.md`）」的宏觀結構指引，結合 **Garrard (2020) 矩陣式文獻檢閱法（The Matrix Method）** 與 **Webster & Watson (2002) 概念中心矩陣（Concept-Centric Matrix）**，引導研究者扮演「學術圓桌會議主席」，精確梳理前人文獻在各個核心研究問題（RQs）上的**學術共識（Consensus）**、**實證爭端與張力（Contradiction & Tension）**以及**情境脈絡微差（Nuance & Boundary Conditions）**，為第九週的學術空白（Research Gap）鎖定提供堅實的客觀地基。

---

## 支援資源與檔案結構

本 Skill 採用模組化組織架構，各子目錄分工如下：

```text
skills/literature_matrix_synthesizer/
│
├── SKILL.md                          # 核心流程入口（六步 SOP 規範與防硬填紀律）
│
├── resources/                        # 靜態規範、矩陣空白範本與綜整檢核規準
│   ├── matrix_template.md            # 雙層次跨篇矩陣與三態綜整分析 Schema 範本
│   └── synthesis_criteria.md         # 概念中心轉換規準、異質文類適配與學術轉承語料庫
│
├── examples/                         # 少樣本學習（Few-shot）標準示範
│   └── sample_literature_matrix.md   # 完整生產級跨篇文獻矩陣與概念綜整範例
│
└── scripts/                          # 本機自動化輔助與驗證工具
    └── matrix_synthesizer.py         # 卡片庫批次掃描、RQ 映射統計與矩陣合規驗證腳本
```

---

## 何時應使用本 Skill？

當使用者提出下列需求時，Agent 應主動調用本 Skill：
- 「請讀取 `02_notes/cards/` 下的所有卡片，幫我建立跨篇文獻比較矩陣」
- 「將我的單篇閱讀卡片轉化為概念中心的文獻矩陣並存入 `02_notes/literature_matrix.md`」
- 「分析現有卡片在 RQ1、RQ2、RQ3 上的覆蓋率與跨篇共識、矛盾」
- 「幫我把作者中心的摘要清單改寫為概念導向的文獻綜整（Synthesis）」
- 「檢驗我的 `literature_matrix.md` 是否符合雙層次矩陣與防硬填規範」

---

## 嚴格執行工作流程（SOP）

當 Agent 啟動本 Skill 後，必須按順序執行以下六個步驟：

### 第一步：批次盤點卡片庫與讀取專案規格（Card Inventory & PROJECT.md Alignment）
1. 執行或參照 `@Script(scripts/matrix_synthesizer.py)` 之 `scan` 功能，遍歷 `02_notes/cards/card_*.md` 的所有原子閱讀卡片。
2. 讀取根目錄下的 `PROJECT.md`，掌握研究者定義的核心研究問題（RQ1、RQ2、RQ3）與研究範疇。
3. 盤點每張卡片的 YAML Frontmatter、文獻文類屬性（實證研究、系統性綜述 SLR、概念立場文、技術架構開發）以及【第六維度】對各 RQ 的實質映射狀態（區分「有具體啟發」與「與本 RQ 無直接關聯」）。

### 第二步：異質文類識別與欄位防硬填適配（Genre-Adaptive Field Alignment）
延續第六週建立的「學術誠實與防硬填紀律」，在橫向對齊多篇文獻時，嚴禁為了填滿矩陣格子而無中生有：
1. **實證研究論文（Empirical Studies）：** 完整提取理論框架、受試樣本數（$N$）與場域、介入工具/自變項、測量量表/因變項、具體統計檢定結果（$F, t, p, \eta_p^2$）與效度威脅。
2. **系統性文獻回顧與綜述（SLR / Survey）：** 理論欄如實標註「無單一理論框架（系統性綜述）」；樣本欄標註「納入文獻數 $N = \text{XX}$ 篇（無人類受試者）」；測量工具標註「PRISMA 篩選與編碼架構」。
3. **概念立場文與系統架構論文（Position / System Architecture Papers）：** 樣本與情境欄標註「不適用（概念立場論述 / 系統工程架構）」；評估指標標註「專家論證 / 系統基準測試集（Benchmark）」，統計欄標註「無初級推論統計」。

### 第三步：建構「雙層次跨篇文獻矩陣」（Dual-Layer Matrix Construction）
參照 `@Resource(resources/matrix_template.md)`，依序建立兩個互補的結構化矩陣：
1. **第一層：跨篇方法學與實證特徵全覽矩陣（Methodological & Empirical Overview Matrix）**
   - 以「文獻（Citation & Genre）」為列，橫向對齊七大核心欄位：文類與領域定位、支撐理論框架、研究對象/樣本與場域、核心機制/介入工具、評估指標與關鍵發現（含頁碼錨點）、核心方法學盲點與外推邊界。
2. **第二層：概念中心與研究問題對映矩陣（Concept-Centric & RQ-Clustered Matrix）**
   - 依據 **Webster & Watson (2002)** 典範，將視角由「作者」翻轉為「核心概念主題與研究問題（RQ1–RQ3）」。
   - 以「核心概念構面 / 對應 RQ」為列，橫向比較：核心理論主張、支持文獻群（標註 `[+]` 實證支持或 `[~]` 概念倡議）、反方/條件限制文獻群、跨篇方法學落差，藉此一眼看穿哪個 RQ 證據充足、哪個 RQ 存在結構性爭端。

### 第四步：提煉「跨篇對話三態綜整分析」（Tri-Modal Thematic Synthesis）
參照 `@Resource(resources/synthesis_criteria.md)`，在矩陣下方撰寫有血有肉、拒絕報流水帳的「跨篇概念綜整分析」：
1. **模式一：學術共識底座（Scholarly Consensus）：** 歸納多篇文獻跨越不同方法或場域共同支持的核心結論，作為本研究設計的穩定基石。
2. **模式二：學術爭端與理論張力（Contradiction & Theoretical Tension）：** 精確指認哪兩派（或兩類）文獻在實證結果、認知機制或工具介入成效上出現矛盾，並深入剖析造成分歧的潛在調節變項（如介入時長、是否有強制反思鷹架、是否具備本地檔案事實錨定）。
3. **模式三：情境脈絡與方法微差（Contextual Nuance & Methodological Shifts）：** 梳理前人理論在轉換研究對象（如歐美資工大學生 vs. 非英語母語碩士生）、轉換任務型態（單次短文實驗 vs. 長週期學位論文）或轉換技術架構（網頁版 Chatbot vs. 本機 RAG + MCP Agent）時的邊界衰減效應。

### 第五步：持久化儲存與出處錨定核驗（Persistence & Citation Grounding）
1. 將產出的雙層次矩陣與三態綜整分析完整寫入工作區指定路徑：`02_notes/literature_matrix.md`。
2. 確認矩陣與綜整段落中引用的每一項數據與論點，均保留對應卡片的作者年份與原文頁碼/章節錨點（如 `[Chen, 2023, p. 4]` 或 `[Kasneci et al., 2023, Sec. 3]`）。

### 第六步：執行自動化格式與品質檢驗（Automated Matrix Validation）
1. 於終端機執行 `@Script(scripts/matrix_synthesizer.py)` 的 `validate` 子命令：
   ```bash
   python skills/literature_matrix_synthesizer/scripts/matrix_synthesizer.py validate 02_notes/literature_matrix.md
   ```
2. 確認 YAML Frontmatter、雙層次矩陣結構、RQ1–RQ3 映射完整性與三態綜整段落全部通過合規驗證，並在對話中向研究者呈報跨篇分析摘要。

---

## 嚴格執行紀律（Governance Rules）

1. **嚴禁退回報流水帳（Anti-Annotated Bibliography）：** 在撰寫綜整分析時，嚴禁以「首先 A (2023) 做了……接著 B (2024) 做了……」作為段落主軸；每個段落必須以「核心概念、理論張力或方法演進」作為主題句（Topic Sentence），將多位學者編織於同一論證脈絡中。
2. **嚴格防硬填與文類誠實（Genre Integrity in Matrix）：** 矩陣中的非實驗文類（SLR、立場文、系統開發）必須如實標註其文類特徵，絕對不可為了讓表格看起來整齊而捏造受試者人數 $N$ 或 $p$ 值。
3. **忠於卡片與原文錨點（Strict Card & Source Grounding）：** 矩陣中的所有數值與結論必須 100% 源自 `02_notes/cards/*.md` 與 `01_papers/extracted_text/*.md`，若卡片第 6 維度已標註「與本 RQ 無直接關聯」，在概念對映矩陣中即應如實反映其分工，不可強行勾連。
4. **職責邊界清晰（Focus on Synthesis, Prepare for Gap）：** 本 Skill 的核心任務是「把前人研究版圖畫清楚（What & How of Prior Art）」，指出共識、爭端與盲點位置；至於正式的 CARS 四步學術空白命題與口試對抗防禦，則交由第八週的 `research-gap-challenger` Skill 接棒執行。
