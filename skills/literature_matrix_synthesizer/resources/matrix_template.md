---
type: literature_matrix
matrix_version: 1.0
project_title: "{PROJECT.md 中的論文工作題目}"
card_count: {納入卡片總數}
included_cards: [{card_1檔名}, {card_2檔名}, {card_3檔名}]
rq_coverage:
  RQ1: {支援 RQ1 之篇數}
  RQ2: {支援 RQ2 之篇數}
  RQ3: {支援 RQ3 之篇數}
created_date: {YYYY-MM-DD}
---

# 跨篇文獻比較矩陣與概念導向綜整：{論文研究主題簡稱}

## 1. 卡片庫盤點與研究問題（RQs）映射分佈 (Card Inventory & RQ Mapping Overview)

- **納入分析卡片總數：** 共 {N} 篇核心文獻（源自 `02_notes/cards/`）
- **文類屬性分佈：** 實證研究 {X} 篇、系統性文獻回顧（SLR / Survey）{Y} 篇、概念立場或系統架構論文 {Z} 篇
- **對本研究 `PROJECT.md` 之支援矩陣：**

| 文獻標識 (Citation) | 來源卡片檔名 | 文獻文類 (Genre) | RQ1 (教學設計與鷹架) | RQ2 (認知歷程與負荷) | RQ3 (人機協作瓶頸) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **{Author (Year)}** | `{card_filename.md}` | {量化準實驗 / 混合實證 / SLR / 立場文 / 系統開發} | {核心借鑑 / 與本 RQ 無直接關聯} | {核心借鑑 / 與本 RQ 無直接關聯} | {核心借鑑 / 與本 RQ 無直接關聯} |

---

## 2. 第一層矩陣：跨篇方法學與實證特徵全覽矩陣 (Methodological & Empirical Overview Matrix)

本矩陣依循 Garrard (2020) 矩陣法，橫向展開各篇文獻之方法論細節與實證證據。針對非實驗文類（如 SLR、立場文、系統架構），嚴格恪守「防硬填紀律」，如實標註其文類特徵：

| 篇名與作者 (Citation & Genre) | 理論框架 (Theoretical Lens) | 研究對象與情境 (Sample & Context) | 核心機制 / 介入工具 (Intervention / System) | 評估指標與關鍵發現 (Instruments & Key Findings) | 方法學盲點與外推邊界 (Critical Limitations & Boundaries) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **{Author (Year)}**<br>[{文類標籤}] | {理論名稱；若無則填：無特定單一理論框架} | {受試樣本 N 與場域；綜述填納入文獻數；立場/系統文填不適用} | {自變項、AI 系統架構或探討焦點} | {量表/指標與具體統計數據 F/t/p/效果量或質性主題，附頁碼錨點} | {作者自陳限制 + 審查者獨立批判之效度威脅與邊界條件} |

---

## 3. 第二層矩陣：概念中心與研究問題對映矩陣 (Concept-Centric & RQ-Clustered Matrix)

本矩陣依循 Webster & Watson (2002)「由作者中心翻轉為概念中心」之典範，以本研究之核心概念與研究問題（RQ1–RQ3）為主軸，橫向檢視跨篇文獻的證據分佈與理論張力：

| 核心概念構面 (Core Thematic Construct) | 對應研究問題 | 主流實證共識與支持文獻 (Consensus & Supporting Evidence) | 跨篇爭端、反例或條件限制 (Tensions & Boundary Conditions) | 現有文獻之方法學或系統結構缺口 (Unresolved Structural Blind Spots) |
| :--- | :--- | :--- | :--- | :--- |
| **構面一：{概念名稱，如：結構化 AI 鷹架與人機協同流程}** | **RQ1** | {綜合支持此構面的文獻與核心結論，附引用錨點} | {不同研究間在介入時機或控制程度上的分歧} | {目前文獻尚未覆蓋的管線機制或教學場域} |
| **構面二：{概念名稱，如：外在認知負荷轉移與後設認知演變}** | **RQ2** | {綜合支持此構面的文獻與測量發現，附引用錨點} | {短期效率提升 vs. 長期批判思考弱化之矛盾} | {缺乏長週期動態日誌或延宕後測之實證追蹤} |
| **構面三：{概念名稱，如：學術幻覺防禦與工具中斷焦慮}** | **RQ3** | {綜合支持此構面的文獻與質性發現，附引用錨點} | {開放對話生成 vs. 本機事實錨定之信任落差} | {缺乏結合本機 RAG 與 PRISMA 驗證之實證研究} |

---

## 4. 跨篇對話三態綜整分析 (Tri-Modal Thematic Synthesis)

### 4.1 學術共識底座 (Scholarly Consensus: What We Collectively Know)
{以概念為段落主題句，整合多篇文獻共同證實的基礎命題，說明這些共識如何構成本研究設計的合法性底座。切忌一段講一篇論文，必須跨篇交織論證並附帶頁碼錨點。}

### 4.2 學術爭端與理論張力 (Contradiction & Theoretical Tension: Where Scholars Diverge)
{聚焦剖析矩陣中呈現矛盾或對立的實證發現（例如：為何 A 學者發現 AI 降低認知負荷，B 學者卻發現增加驗證焦慮與批判退化？），深入拆解背後的調節變項（Moderators）與方法學差異。}

### 4.3 情境脈絡與方法微差 (Contextual Nuance & Methodological Shifts)
{比較前人研究在「受試對象」、「任務時間尺度」與「AI 系統工程架構」上的邊界條件，說明為何既有結論無法直接外推至本研究的真實場域，從而自然鋪墊出第八週即將鎖定的學術空白（Research Gap）。}
