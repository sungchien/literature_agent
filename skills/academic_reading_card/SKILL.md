---
name: academic-reading-card

description: >
  當使用者需要對單篇已採納之學術論文（位於 01_papers/extracted_text/ 的 Markdown 檔案）進行深度批判精讀、
  解剖理論架構與方法學效度威脅、提取精準實證統計數據，並結構化提煉產出符合七維標準的
  原子學術閱讀卡片（儲存於 02_notes/cards/）時，請使用本 Skill。
  本 Skill 具備對抗性審稿人思維、嚴格事實錨定紀律，並能主動讀取 PROJECT.md 
  將論文發現精準映射至使用者的研究問題（RQ1-RQ3）。

version: "1.0"

author: "AI Agent 課程"

tags:
  - 學術精讀
  - 閱讀卡片
  - 批判性閱讀
  - 效度威脅
  - 結構化知識萃取
  - Zettelkasten
  - 提示詞工程

---

# 學術論文批判精讀與標準閱讀卡片 Skill (academic-reading-card)

## Skill 目的

本 Skill 旨在協助研究者將「非結構化、冗長龐雜的論文全文 Markdown」轉化為「高密度、模組化、可隨機重組的七維標準原子閱讀卡片」。
本 Skill 絕不產出空泛讚美或平鋪直敘的公關摘要，而是化身為**頂級同儕審查期刊的最嚴苛審稿人（Adversarial Reviewer）**，手持手術刀剖析論文的理論因果漏洞、方法學效度威脅與生態外推邊界，並將文獻精華深植於研究者個人的論文規格書（`PROJECT.md`）中。

---

## 支援資源與檔案結構

本 Skill 採用模組化組織架構（合併文獻與規範於 resources，不額外建立 assets），各子目錄分工如下：

```text
skills/academic_reading_card/
│
├── SKILL.md                          # 核心流程入口（SOP 規範、行為守則）
│
├── resources/                        # 靜態規範、空白範本、審核與管理面板（合併 references）
│   ├── card_template.md              # 七維標準卡片空白 Schema 範本
│   ├── review_criteria.md            # 對抗性審稿檢核表與經典方法學參考文獻
│   ├── card_curator.html             # 單篇卡片 Generative UI 人機審核面板
│   └── card_hub.html                 # 卡片庫維護、進度統計與再閱讀修訂中心 (Generative UI)
│
├── examples/                         # 少樣本學習（Few-shot）示範卡片
│   └── sample_reading_card.md        # 完整生產級文獻閱讀卡片範例（Chen, 2023）
│
└── scripts/                          # 本機自動化輔助工具
    ├── validate_card.py              # 卡片 Frontmatter 與七維結構自動驗證腳本
    └── manage_cards.py               # 卡片庫維護統計、雙向比對與動態儀表板生成腳本
```

---

## 何時應使用本 Skill？

當使用者提出下列需求時，Agent 應主動調用本 Skill：
- 「請幫我精讀這篇論文並做成閱讀卡片」
- 「將 `01_papers/extracted_text/` 中的論文提煉為標準閱讀卡片」
- 「產生 Generative UI 審核面板，協助我進行數據核對並親筆撰寫第 6 維度」
- 「查詢卡片庫維護進度與統計，列出已整理與待整理的文獻」
- 「再次閱讀並修改已存在的卡片」
- 「分析這篇論文的研究設計、效度威脅與對我論文的啟發」
- 「提取這篇論文的實證數據、效果量與限制，寫入 `02_notes/cards/`」
- 「以對抗性審稿人角度批判這篇文獻」

---

## 嚴格執行工作流程（SOP）

當 Agent 啟動本 Skill 後，必須按順序執行以下六個步驟：

### 第一步：定位目標論文與讀取全文
1. 確認目標論文 Markdown 檔案路徑（通常位於 `01_papers/extracted_text/`，例如 `01_papers/extracted_text/2023_Kasneci_ChatGPT_for_good__On_opportunities.md`）。
2. 完整閱讀論文內容，掌握其研究問題、理論模型、研究方法、主要數據與結論。
3. 若遇長篇論文或需要核對特定章節（如 Methodology, Findings），可調用向量檢索工具 `search_paper_chunks` 進行多維度事實交叉檢驗。

### 第二步：讀取專案規格（PROJECT.md）
1. 主動讀取根目錄下的 `PROJECT.md`，釐清研究者目前的：
   - 核心研究題目與目標領域
   - 探索性研究問題（RQ1, RQ2, RQ3）
   - 時程約束與文獻納入/排除範疇
2. 判定文獻與各 RQ 之實質關聯度：
   - 此步驟是產出【第六維度：對本研究的直接啟發】的核心前置作業。
   - **【嚴格防硬填紀律】：** 許多文獻在學術範疇上高度聚焦，**可能只與其中一個 RQ 有關，甚至與目前設定的個別具體 RQ 完全沒有直接關聯**。Agent 必須進行真實性判定：**若目標文獻與某個 RQ 無實質關聯，嚴禁為了湊字數而強行生造一段牽強附會的文字，必須直接誠實標註「與本 RQ 無直接關聯」或「無關」！**

### 第三步：啟動「對抗性審稿人（Adversarial Reviewer）」思維
參照 `@Resource(resources/review_criteria.md)` 之檢核清單，從「批判解剖的三大核心構面」切入審查，拒絕全盤接收作者結論：
1. **構面一：理論依據與因果邏輯（Theoretical Coherence）**
   - 檢視理論是否真正支撐假設？因果傳導路徑是否存在未控制的混淆變項？
2. **構面二：方法學嚴謹度與效度威脅（Methodological Rigor & Threats to Validity）**
   - 檢查內部效度（是否有霍桑效應、指導時間偏差？）、構念效度（量表信效度、EFA/CFA 指標）、統計結論效度（樣本量 N、檢定力 Power、效果量 Effect Size）。
3. **構面三：生態效度與外推邊界（Ecological Validity & Boundary Conditions）**
   - 檢驗研究情境在其他學科、文化或實務脈絡下是否依然適用？找出作者刻意淡化或避談的邊界條件。

### 第四步：事實與數據精確錨定（Anti-Hallucination & Fit-to-Context Grounding）
1. **每個萃取細項強制標註出處（Per-Item Citation & Page Anchoring）：**
   - 為了杜絕大型語言模型的憑空捏造（Hallucination），**在各維度（尤其是第 1 至第 5 維度）提取的每個實證細項、研究問題、理論基礎、方法設計、統計數據與限制後方，必須強制附上原文具體出處標記**（例如：`[出處：Page 2, Background]` 或 `[出處：Page 4, Table 1]`）。
   - 若論文為方法學綜述或立場論文且未提供初級統計數據，必須明確標註出處並據實說明：`[出處：全文檢驗，原文未提供初級統計數值]`，嚴禁虛構數值。
2. **各維度子項目文類精確適配（拒絕硬套標籤）：**
   - **支撐理論框架：** 若為系統性文獻回顧（SLR）、技術工具開發、實務報告或前瞻立場論文且原文未採用特定理論模型，**嚴禁硬套心理學理論，直接誠實標註「無特定單一理論框架（本文為系統性文獻回顧 / 立場論述 / 技術工具開發）」或「無」**。
   - **樣本與情境：** 文獻綜述之樣本為文獻（如「文獻樣本量：共篩選納入 N = XX 篇論文，無人類受試者」），情境標註「不適用（桌面文獻回顧，無實體介入）」；純立場論述或系統架構無受試樣本則標註「不適用」。
   - **測量工具：** 若未使用心理或教育量表，如實標註「無量表測量工具（採用質性編碼表 / 基準測試集 / 系統日誌）」或「不適用」，嚴禁憑空生造量表。
   - **量化統計結論：** 純質性研究、概念立場文或未做元分析之文獻綜述，標註「無量化統計檢定（本篇為純質性研究 / 概念架構文，原文未提供初級統計數值）」，嚴禁虛構數值！
3. 提取原文中的具體統計數據（如 $F$ 值、$t$ 值、$p$ 值、$\eta_p^2$、Cohen's $d$ 等），嚴禁只寫「效果顯著」等空泛形容詞。
4. 挑選 2 至 3 句具備高度學術代表性、最適合未來直接引用於研究計畫第二章的核心英文原文引述，並精確標記出處章節與頁碼。

### 第五步：遵循「七維標準 Schema」生成卡片內容
載入並遵循 `@Resource(resources/card_template.md)` 之結構規範，並參照 `@Example(examples/sample_reading_card.md)` 之寫作深度與標籤水準產出卡片，保證 YAML Frontmatter 與 Markdown 層級完整，並落實「無關 RQ 標註無關、不適用子項如實標註不適用」之紀律。

### 第六步：生成 Generative UI 審核面板與人機協同落盤
1. **生成互動式審核面板（Generative UI Artifact）：**
   - 調用 `write_to_file` 於對話 Artifact 目錄中建立專屬審核面板 `card_curator_{年份}_{第一作者}.html`（以 `@Resource(resources/card_curator.html)` 為範本，預先填入該論文的初稿數據與分析）。
   - 在對話中以 `<agent-embed>` 嵌入或呈現該 Artifact，供研究者進行：
     - **🟢 第一層級 掃描：** 快速核對 BibTeX、DOI。
     - **🟡 第二層級 審核：** 勾選確認無數據幻覺，把關文類適配，並補充審查者的獨立批判觀點。
     - **🔵 第三層級 主筆：** 透過 RQ1–RQ3 鷹架引導晶片，親筆撰寫對自身的論文啟發與 Research Gap 推進；無關之 RQ 果斷標註無關。
2. **持久化儲存卡片檔案：**
   - 將初稿或審核後的標準卡片存入工作區指定位置：
     ```text
     02_notes/cards/card_{發表年份}_{第一作者英文姓氏}_{核心概念縮寫}.md
     ```
3. **格式合規檢驗與回報：**
   - 可於終端機執行 `@Script(scripts/validate_card.py)` 自動驗證卡片格式合規性：
     ```bash
     python skills/academic_reading_card/scripts/validate_card.py 02_notes/cards/card_{檔名}.md
     ```
   - 在對話中清晰回報卡片路徑、Generative UI 審核面板連結，並特別標註待研究者實質審核與親筆撰寫的重點。

---

## 嚴格執行紀律（Governance Rules）

1. **零幻覺數據（Strict Grounding）：** 第 4 維度的統計數據必須 100% 來自 Markdown 文本。若文本中未揭露具體效果量或檢定值，必須誠實標註「原文未提供具體數值」，嚴禁揣測編造。
2. **拒絕平庸讚美（Adversarial Discipline）：** 第 5 維度必須至少列出 2 點犀利的方法學或生態效度批判，不得僅抄寫作者客套的研究限制。
3. **真實對接與拒絕強行硬填（Fit-to-Context & Anti-Forced Filling）：** 第 6 維度嚴禁對無關 RQ 強行生造牽強附會的字句！若經研讀判定文獻與特定 RQ 無實質關聯，直接誠實標明「與本 RQ 無直接關聯」或「無關」；整張卡片僅針對真正有啟發的 RQ 進行深度論述。
4. **命名與路徑規格：** 檔案名稱必須保持小寫開頭標準格式：`card_{年份}_{第一作者}_{概念簡寫}.md`，統一儲存於 `02_notes/cards/`。
5. **子項目文類適配（Genre Integrity）：** 各維度子項目必須嚴格遵循文獻真實屬性。文獻綜述等非實驗論文不得硬套理論框架、不得捏造受試樣本、量表與量化檢定值，客觀不具備之子項目必須如實標註「無特定單一理論框架」、「不適用」或「無量化統計檢定」。
