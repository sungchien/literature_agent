---
name: research-gap-challenger

description: >
  當使用者需要從跨篇文獻比較矩陣（02_notes/literature_matrix.md）與閱讀卡片中，
  鎖定具備學術合法性的「研究空白（Research Gap）」、破除「過去沒人做過」的偽空白陷阱、
  運用 Swales (1990, 2004) CARS 模型撰寫四步修辭轉折陳述句（Gap Statement）、
  進行模擬學位口試委員的對抗性壓力測試（Adversarial Oral Defense），
  並最終迭代收斂根目錄 PROJECT.md 的研究問題（升級至 v0.4 開題定錨版）時，請使用本 Skill。

version: "1.0"

author: "AI Agent 課程"

tags:
  - 學術空白
  - Research Gap
  - CARS模型
  - 口試防禦
  - 對抗性壓力測試
  - 研究問題收斂
  - PROJECT.md
---

# 學術空白鎖定、開題立論防禦與規格收斂 Skill (research-gap-challenger)

## Skill 目的

本 Skill 旨在協助研究者完成從「文獻綜整（Literature Synthesis）」邁向「開題立論（Problem Formulation & Niche Establishment）」的關鍵一躍。許多研究生在完成文獻矩陣後，仍習慣以「過去很少有人研究 X 對 Y 的影響」這種極易被口試委員擊潰的「偽空白（Spurious Gap）」作為研究動機。

本 Skill 深度融合 **Swales (1990, 2004) CARS 模型（Create a Research Space）**、**Sandberg & Alvesson (2011) 缺口鎖定與問題化理論（Gap-Spotting & Problematization）** 以及 **Robinson et al. (2011) 系統性研究缺口分類框架**，引導研究者從 `02_notes/literature_matrix.md` 的結構性矛盾中提煉真正的學術空白，撰寫符合國際期刊規範的 **四步修辭轉折陳述句（Gap Statement）**，接著由 Agent 化身最嚴厲的學位口試委員結合本機 RAG（`search_paper_chunks`）發動三路極限壓力測試，最終將淬鍊成熟的立論與研究問題（RQ1–RQ3）正式回寫收斂至根目錄 `PROJECT.md (v0.4 開題定錨版)`。

---

## 支援資源與檔案結構

本 Skill 採用模組化組織架構，各子目錄分工如下：

```text
skills/research_gap_challenger/
│
├── SKILL.md                          # 核心流程入口（六步 SOP 規範、人機對抗暫停點與治理守則）
│
├── resources/                        # 靜態規範、立論空白範本與口試防禦規準
│   ├── gap_statement_template.md     # 學術空白診斷、CARS 四步陳述、口試答辯與 RQ 收斂範本
│   └── defense_rubric.md             # 真偽空白判準、CARS 修辭架構與口試委員殺手級提問規準
│
├── examples/                         # 少樣本學習（Few-shot）標準示範
│   └── sample_gap_statement.md       # 完整生產級學術空白陳述與口試對抗防禦範例
│
└── scripts/                          # 本機自動化輔助、版本歸檔與驗證工具
    └── gap_defense_tool.py           # 矩陣盲點審計、Gap 報告合規檢驗與 PROJECT.md 版本歸檔腳本
```

---

## 何時應使用本 Skill？

當使用者提出下列需求時，Agent 應主動調用本 Skill：
- 「請根據我的 `02_notes/literature_matrix.md` 幫我診斷並鎖定研究空白（Research Gap）」
- 「幫我用 CARS 四步修辭轉折公式起草碩士論文的 Gap Statement」
- 「請扮演嚴厲的學位口試委員，對我的研究空白陳述進行極限壓力測試」
- 「檢驗我的 Research Gap 是否屬於偽空白，並查核本機文獻庫是否已有論文解答過」
- 「將定稿的學術空白與收斂後的 RQ1–RQ3 更新回 `PROJECT.md`，並將舊版歸檔至 `05_project_history/`」

---

## 嚴格執行工作流程（SOP）

當 Agent 啟動本 Skill 後，必須按順序執行以下六個步驟：

### 第一步：審計跨篇矩陣盲點與卡片啟發（Matrix Blind-Spot Audit）
1. 讀取 `02_notes/literature_matrix.md`（特別聚焦於第二層概念矩陣的「跨篇爭端」與「未解結構缺口」欄，以及第 4.2、4.3 節綜整分析），並檢視 `02_notes/cards/card_*.md` 的第 5、6 維度。
2. 執行或參照 `@Script(scripts/gap_defense_tool.py)` 的 `audit` 子命令，盤點目前各個探索性研究問題（RQ1–RQ3）背後的文獻限制與矛盾焦點。

### 第二步：真偽空白鑑定與四大空白型態定位（Gap Authentication & Typology Mapping）
參照 `@Resource(resources/defense_rubric.md)`，協助研究者剔除毫無理論價值的「單純未做型偽空白（Mere Neglect / Spurious Gap）」，並將研究缺口精確定位至四大經典學術空白型態（可單一或複合定位）：
1. **型態一：族群與高壓場域脈絡空白（Population & Ecological Context Gap）**
2. **型態二：方法學與工具系統架構空白（Methodological & System Architecture Gap）**
3. **型態三：理論衝突與中介機制未解空白（Theoretical Tension & Unresolved Mechanism Gap）**
4. **型態四：生態效度與長程歷程轉化空白（Ecological Validity & Longitudinal Process Gap）**

### 第三步：CARS 四步修辭轉折陳述句起草（CARS 4-Move Gap Statement Drafting）
依據 **Swales (1990, 2004) CARS 模型**，為研究者起草中英雙語對照、邏輯張力飽滿的「四步修辭轉折公式」初稿：
- **第一步：肯定前人共識底座（Move 1: Consensus Grounding）** —— 引用矩陣中之核心共識文獻，確立研究領域的重要性。
- **第二步：關鍵轉折與指出結構性盲點（Move 2a: The Critical "However" Pivot）** —— 精準點出前人研究在方法、系統架構或理論機制上的結構性局限與矛盾。
- **第三步：闡明未解問題的學術與實務代價（Move 2b: Cost of Inaction）** —— 論證若不填補此缺口，將對學界理論建構或教育/實務現場造成何種具體阻礙。
- **第四步：確立本研究填補價值與引出 RQs（Move 3: Occupying the Niche & RQs）** —— 順理成章宣告本研究的介入架構、研究方法與具體解答之 RQ1、RQ2、RQ3。

### 第四步：啟動「對抗性口試委員壓力測試」與人機暫停點（Adversarial Oral Defense & HITL Pause）
1. **轉換嚴苛人設並調用 RAG 反查：** Agent 必須暫時卸下溫和顧問角色，化身 **「國際頂級期刊副主編兼最嚴厲的學位口試委員」**，並主動調用本機 `search_paper_chunks` 檢索工具，嘗試從 `01_papers/` 現有論文中尋找能夠推翻或削弱該 Gap 的反證段落。
2. **提出三路尖銳質詢（Three-Pronged Interrogation）：**
   - **質詢一（真偽性與 So What 挑戰）：** 質疑該 Gap 是否只是「把 A 工具換成 B 對象」的瑣碎填補？若不做這項研究，學術界真的有損失嗎？
   - **質詢二（文獻反擊 Prior Art Counter-Attack）：** 點名 `02_notes/literature_matrix.md` 中的具體文獻，質疑前人是否早已部分解答該問題？本研究宣稱的創新點是否言過其實？
   - **質詢三（方法可操作性與內外部效度挑戰）：** 在一學期的時間與樣本規模（如 $N=15$）限制下，研究設計如何排除混淆變項並真正回答所宣稱的 Gap？
3. **【強制人機協同暫停點（Human-in-the-Loop Pause）】：**
   - Agent 列出三大質詢後，**必須主動在對話中暫停**，邀請研究者以自然語言針對質詢提出辯護或修正想法，或者由研究者審閱並微調防禦策略後，再共同淬鍊出「終極防禦版 Gap Statement」。

### 第五步：產出結構化立論防禦報告（Persistence to `02_notes/research_gap_statement.md`）
遵循 `@Resource(resources/gap_statement_template.md)` 與 `@Example(examples/sample_gap_statement.md)` 規範，將完整的空白型態診斷表、CARS 四步陳述句（初稿與終極修訂版）、三問三答口試防禦實錄、以及從「探索性 RQ」演進至「定錨版 RQ」的對照表，寫入 `02_notes/research_gap_statement.md`。

### 第六步：專案規格書歸檔與升級（`PROJECT.md` v0.4 Convergence & Validation）
1. 執行 `@Script(scripts/gap_defense_tool.py)` 的 `archive-project` 子命令，將根目錄現有的 `PROJECT.md (v0.3)` 安全備份至 `05_project_history/PROJECT_v0.3.md`：
   ```bash
   python skills/research_gap_challenger/scripts/gap_defense_tool.py archive-project --version v0.3
   ```
2. 將根目錄的 `PROJECT.md` 升級為 **`v0.4 學術空白鎖定與開題定錨版`**，新增或更新「核心學術空白陳述（Research Gap Statement）」與「收斂定錨後之研究問題（Refined RQs）」。
3. 執行 `validate` 子命令驗證 `02_notes/research_gap_statement.md` 格式合規性：
   ```bash
   python skills/research_gap_challenger/scripts/gap_defense_tool.py validate 02_notes/research_gap_statement.md
   ```

---

## 嚴格執行紀律（Governance Rules）

1. **嚴禁捏造無根據之空白（Evidence-Backed Gap Only）：** 所有的 Research Gap 宣告，必須 100% 對應至 `02_notes/literature_matrix.md` 中真實存在的文獻限制或跨篇矛盾，嚴禁脫離工作區文獻庫憑空吹噓「全球首創」。
2. **拒絕溫吞放水之壓力測試（Uncompromising Adversarial Rigor）：** 在第四步扮演口試委員時，必須引用工作區具體文獻作者與方法細節進行刁鑽質詢，不得提出空泛客套的假問題。
3. **嚴守歷史規格歸檔紀律（Clean Root & Version Archiving）：** 在修改根目錄 `PROJECT.md` 前，務必先將舊版歸檔至 `05_project_history/`，確保根目錄永遠只保留唯一權威的最新規格，同時完整留存研究問題聚焦演進的客觀軌跡。
