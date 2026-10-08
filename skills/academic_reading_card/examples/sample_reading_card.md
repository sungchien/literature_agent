---
type: literature_card
card_version: 1.0
bibtex_key: chen2023scaffolding
title: "Scaffolding Complex Academic Writing with Generative AI Agents: An Empirical Study in Graduate Education"
first_author: "Chen, Mei-Ling"
year: 2023
journal: "Computers & Education"
doi: "10.1016/j.compedu.2023.104800"
source_md: "01_papers/extracted_text/2023_Chen_Scaffolding_GenAI_in_Higher_Ed.md"
tags: [AI_Agents, Scaffolding, Cognitive_Load, Graduate_Writing, Higher_Ed]
created_date: 2026-09-28
---

# 文獻卡片：Chen (2023) - AI 代理人鷹架輔助研究生學術寫作實證研究

## 1. 文獻元數據與引用標識 (Metadata)
- **標準引用 (APA 7th)：** Chen, M.-L., & Roberts, D. (2023). Scaffolding complex academic writing with generative AI agents: An empirical study in graduate education. *Computers & Education*, 198, 104800. https://doi.org/10.1016/j.compedu.2023.104800
- **研究領域：** 教育科技 / 人工智慧教育應用 / 高等教育教學實踐 (SoTL)
- **原始文件路徑：** `01_papers/extracted_text/2023_Chen_Scaffolding_GenAI_in_Higher_Ed.md`

## 2. 核心研究問題與理論框架 (RQs & Theoretical Lens)
- **核心研究問題：**
  1. 導入具備反思機制的 AI Agent 鷹架，對碩士生在撰寫文獻探討時的外在認知負荷（Extraneous Cognitive Load）有何影響？
  2. 學生在人機協作過程中的自我調節學習（SRL）策略如何演變？
- **支撐理論框架：**
  - Sweller 的認知負荷理論（Cognitive Load Theory, CLT）：特別聚焦於如何降低「外在認知負荷」，釋放資源以進行「相關認知負荷（Germane Load）」。
  - Zimmerman 的自我調節學習模型（Self-Regulated Learning, SRL）。

## 3. 研究設計與實證方法論 (Methodology & Context)
- **研究方法：** 混合研究設計（混合準實驗與質性反思日誌分析）。
- **研究樣本與情境：**
  - 台灣某國立大學碩士班研究生共 64 名（教育與社會科學領域），進行為期 10 週的教學介入。
  - **實驗組 (N=32)：** 使用結構化 AI Agent 輔助文獻檢索與架構梳理。
  - **對照組 (N=32)：** 使用一般商用搜尋引擎與未受提示約束的 ChatGPT 進行文獻收集。
- **測量工具：**
  - Paas & Van Merriënboer (1994) 9 點心理努力量表（施測於每週作業提交後）。
  - 文獻探討成果盲審評分規準（Rubric，滿分 50 分，由兩位資深審稿人盲審，Kappa = .86）。

## 4. 關鍵實證數據與核心發現 (Empirical Findings)
- **量化統計結論：**
  - **外在認知負荷顯著降低：** 實驗組的外在認知負荷平均得分 ($M = 3.42, SD = 0.81$) 顯著低於對照組 ($M = 5.86, SD = 1.05$)，單因子共變數分析顯示達極顯著水準：$F(1, 61) = 14.82, p < .001, \eta_p^2 = .195$（達大效果量）。
  - **文獻綜整品質顯著提升：** 實驗組在「概念批判與整合」維度的評分顯著高於對照組 ($t(62) = 3.45, p = .001$)。
- **質性發現：**
  - 對照組學生在反思日記中頻繁表達「被海量文獻淹沒」與「無法驗證 AI 假引用」的高度焦慮感；實驗組則將焦點轉移至「如何向 Agent 提出更尖銳的提問」。

## 5. 批判性審視與方法學盲點 (Critical Limitations)
- **作者承認之限制：** 介入時間僅 10 週，且樣本僅限於單一人文社科院所，缺乏跨理工學科的外推驗證。
- **審查者獨立批判（對抗性審稿視角）：**
  1. **忽視長期依賴性：** 該研究未設計「撤除 AI 鷹架後的延宕後測（Delayed Post-test）」，無法證明學生的批判思考能力是真正內化，抑或只是對該 Agent 產生了認知依賴。
  2. **實驗組額外指導偏差：** 實驗組在介入前接受了 2 小時的提示詞培訓，而對照組未獲得同等時數的常規寫作指導，可能存在指導時間不等造成的內部效度威脅。

## 6. 對本研究 PROJECT.md 的直接啟發 (Actionable Insights)
- **對 RQ1（教學設計與鷹架）的啟發：**
  - 可直接借鑑 Chen (2023) 的 10 週進度節奏，將文獻探討拆分為「概念發散、篩選驗證、批判矩陣」三階段，並將此流程寫入我們課程的課堂引導講義中。
- **對 RQ2（認知負荷與日誌分析）的啟發：**
  - Chen 使用的 Paas 心理努力量表設計簡短（僅單一題目），非常適合放入我們工作區的 `04_research_data/diaries/` 每週反思問卷中，不造成學生額外填寫負擔。
- **本研究可推進的空間（Research Gap）：**
  - Chen 的研究未探討「本機 RAG 向量檢索」與「MCP 工具鏈」的具體工程架構。我們的研究可在此基礎上，進一步論證「具備本地檔案感知與 PRISMA 追蹤機制的 Agent」如何進一步降低學生的工具中斷焦慮！

## 7. 黃金引句與出處錨點 (Golden Quotes)
1. *"The primary bottleneck in graduate literature reviews is not the acquisition of information, but the cognitive exhaustion caused by unstructured information processing."*
   — Section 1. Introduction, p. 2.
2. *"When AI scaffolding transitions from open-ended chat to constraint-based task execution, students shift from passive consumers of generated text to active evaluators of synthesized evidence."*
   — Section 5. Discussion, p. 9.
