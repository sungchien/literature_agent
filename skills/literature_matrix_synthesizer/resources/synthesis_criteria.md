# 跨篇文獻矩陣共構與概念導向綜整規準（Synthesis Criteria & Methodological Foundations）

本文件收錄「作者中心轉概念中心矩陣規範」、「異質文類橫向對齊準則」、「跨篇對話三態檢核表」與「國際期刊綜整轉承語料庫」，供 Agent 於執行 `literature-matrix-synthesizer` Skill 時動態查閱。

---

## 一、從「作者中心（Author-Centric）」到「概念中心（Concept-Centric）」的轉換法則

根據資訊系統與社會科學文獻回顧的經典方法論（**Webster & Watson, 2002**; **Garrard, 2020**），文獻探討的品質取決於組織知識的維度：

1. **作者中心模式（Author-Centric Approach，嚴格禁止）：**
   - **特徵：** 每個段落或小節以單一作者為主角（例如：「Chen (2023) 探討了……；Wang (2024) 則研究了……；Kasneci et al. (2023) 提出了……」）。
   - **致命缺陷：** 讀者只能看到零散的實驗清單（Annotated Bibliography），無法看出文獻之間的因果演進、共同盲點與方法學優劣。
2. **概念中心模式（Concept-Centric Approach，強制採用）：**
   - **特徵：** 以「理論構念（Constructs）」、「自變項與因變項關係」或「方法學爭端」作為矩陣的主軸與段落標題。多位學者的研究被拆解後，依據概念重新編織在同一段落內相互對話與對質。
   - **轉換操作三步驟：**
     1. **縱向拆解（Deconstruction）：** 先在第一層矩陣將每張卡片拆解為標準欄位（理論、樣本、機制、發現、限制）。
     2. **橫向聚類（Clustering by Concept & RQ）：** 在第二層矩陣中，將相同概念或支援同一個 RQ 的文獻歸入同一列，標記一致處與衝突處。
     3. **辯證編織（Dialectical Weaving）：** 以「共識 $\rightarrow$ 爭端 $\rightarrow$ 微差」的三態結構撰寫綜整段落。

---

## 二、異質文類橫向對齊與防硬填規準（Cross-Genre Matrix Alignment Rules）

真實論文工作區中的文獻往往橫跨多種文類（Genre）。在建構跨篇矩陣時，必須遵循以下對齊規範，嚴禁削足適履：

| 矩陣欄位 | 量化/混合實證研究 (Empirical) | 系統性文獻回顧 (SLR / Survey) | 概念立場論文 (Position Paper) | 系統架構與工程論文 (System / Tool) |
| :--- | :--- | :--- | :--- | :--- |
| **理論框架** | 具體心理/教育理論（如 CLT, SRL, TAM） | 標註「無單一理論框架（依分類學 Taxonomy 歸納）」 | 標註「無單一實證理論（專家觀點倡議藍圖）」 | 標註「無行為理論（基於 Multi-Agent / RAG 架構設計）」 |
| **樣本與場域** | 受試者人數 $N$、學科背景、介入週數 | 納入分析之文獻篇數（如 $N = 85$ 篇論文） | 標註「不適用（全領域宏觀論述，無受試者）」 | 標註「不適用（採用基準測試集 Benchmark 評測）」 |
| **核心機制/工具** | 實驗組介入鷹架 vs. 對照組常規工具 | 文獻檢索策略、PRISMA 篩選與編碼維度 | 概念性機會與風險框架（Opportunities & Challenges） | 系統管線模組（如 Planner, Reviewer, MCP 工具鏈） |
| **評估與關鍵發現** | 量表信效度、統計檢定值（$F, t, p, \eta_p^2$） | 領域發表趨勢、主流方法分佈比例與研究缺口盤點 | 核心前瞻命題與政策/教學建議（無初級統計數值） | 任務成功率、準確率、成本與消融實驗（Ablation Study） |
| **方法學盲點** | 內部效度威脅、樣本偏差、缺乏延宕後測 | 資料庫涵蓋偏誤、未評估納入文獻之實驗品質 | 缺乏實證數據支撐、因果推導存在黑盒子、忽視群體邊界 | 缺乏真實人類學習者實證、基準集過於理想化、認知影響未知 |

---

## 三、跨篇綜整學術英文與中文轉承語料庫（Academic Phrasebank for Synthesis）

在撰寫第四節「跨篇對話三態綜整分析」時，建議採用以下高張力學術句型：

### 1. 表達跨篇學術共識（Establishing Consensus）
- **中文範式：** 「綜觀近年實證研究與系統性回顧，學界已廣泛證實……（Author A, Year; Author B, Year）。無論是在……場域（Author A, Year, p. X）抑或採用……架構（Author C, Year, p. Y），研究結果皆一致指出……」
- **英文範式：** *"Across diverse empirical contexts and system architectures, a robust scholarly consensus has emerged that... (Author A, Year; Author B, Year). Converging evidence from both quasi-experimental studies (Author A, Year) and systematic reviews (Author C, Year) demonstrates that..."*

### 2. 揭示跨篇爭端與方法學張力（Highlighting Contradictions & Tensions）
- **中文範式：** 「然而，針對……的深層認知機制，既有文獻卻呈現顯著的實證分歧。儘管 Author A (Year) 發現……能顯著降低外在認知負荷（$p < .001$），Author B (Year) 在……情境下卻觀察到相反的退化效應。深入比對兩者之研究設計可發現，此一矛盾源於……」
- **英文範式：** *"Substantial divergence emerges, however, regarding the cognitive consequences of... While Author A (Year) reported a significant reduction in extraneous load, Author B (Year) observed heightened verification anxiety and superficial engagement. A granular comparison via the literature matrix reveals that this tension stems from..."*

### 3. 點出情境微差與外推邊界（Articulating Nuance & Boundary Conditions）
- **中文範式：** 「此外，既有研究在技術介入形態與生態脈絡上存在明確的邊界條件。雖然多代理人自動化管線在工程基準測試中展現極高效率（Author D, Year; Author E, Year），但此類全自動代勞模式若直接套用至強調批判內化的碩士論文訓練中，將面臨……」
- **英文範式：** *"Furthermore, critical boundary conditions govern the generalizability of prior findings. Whereas end-to-end autonomous frameworks excel in computational benchmarks (Author D, Year), directly transplanting such fully automated pipelines into graduate thesis education overlooks..."*

---

## 四、學理基礎與經典參考文獻（APA 7th）

- **Garrard, J. (2020).** *Health sciences literature review made easy: The matrix method* (6th ed.). Jones & Bartlett Learning.
- **Klopper, R., Lubbe, S., & Rugbeer, H. (2007).** The matrix method of literature review. *Alternation*, *14*(1), 262–276.
- **Torraco, R. J. (2005).** Writing integrative literature reviews: Guidelines and examples. *Human Resource Development Review*, *4*(3), 356–367. https://doi.org/10.1177/1534484305278283
- **Webster, J., & Watson, R. T. (2002).** Analyzing the past to prepare for the future: Writing a literature review. *MIS Quarterly*, *26*(2), xiii–xxiii.
