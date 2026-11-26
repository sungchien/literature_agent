---
name: research-team-orchestrator

description: >
  當使用者需要跨越單一 AI 代理人的上下文稀釋與自寫自審偏誤，
  為碩士論文或學術研究工作區設計「Multi-Agent 多代理協作學術團隊」、
  定義角色名冊、最小權限邊界、結構化交接契約與人類審查閘門（HITL），
  或驗證 02_notes/research_team_blueprint.md 格式合規性時，請使用本 Skill。

version: "1.0"

author: "AI Agent 課程"

tags:
  - Multi-Agent
  - 多代理協作
  - 學術團隊設計
  - 上下文隔離
  - 人機協同
  - Subagent
---

# 多代理協作與學術研究團隊設計 Skill (research-team-orchestrator)

## Skill 目的

本 Skill 承接第九章已定錨的 `PROJECT.md`（v1.0）、`02_notes/literature_matrix.md` 與 `02_notes/research_gap_statement.md`，協助研究者從「單一對話視窗單兵作戰」升級為「人類總主持人（Principal Investigator，PI）主導的多代理研究團隊」。

透過強制性的**角色專責化（Role Specialization）**、**上下文隔離（Context Isolation）**、**最小權限工具綁定（Least-Privilege Tool Binding）**與**結構化工件交接契約（Structured Artifact Handoff）**，本 Skill 產出儲存於 `02_notes/research_team_blueprint.md` 的團隊設計藍圖，讓檢索、撰稿與事實稽核各自獨立運作並彼此制衡，為第十一章的「多代理對抗式同儕審查」與 `03_drafts/` 章節起草建立安全可控的協作基礎。

---

## 支援資源與檔案結構

```text
skills/research_team_orchestrator/
│
├── SKILL.md                               # 核心流程入口（六步 SOP 與治理守則）
├── resources/
│   ├── team_blueprint_template.md         # 團隊藍圖空白 Schema 範本
│   └── orchestration_criteria.md          # 拓撲選型、權限隔離與工作流決策規準
├── examples/
│   └── sample_team_blueprint.md           # 本專案四代理學術團隊示範藍圖
└── scripts/
    └── team_blueprint_tool.py             # 前置檢查、範本初始化與藍圖驗證腳本
```

---

## 何時應使用本 Skill？

當使用者提出下列需求時，Agent 應主動調用本 Skill：
- 「幫我設計一個針對我碩士論文第二章的多代理（Multi-Agent）學術團隊藍圖」
- 「根據 `PROJECT.md`，規劃檢索員、撰稿員與事實稽核員的權限邊界與交接流程」
- 「檢查我的 `02_notes/research_team_blueprint.md` 是否符合角色隔離與 HITL 規範」
- 「請依我的研究團隊藍圖，以隔離子代理（Subagent）試跑一次單一小節的檢索與稽核交接」

---

## 嚴格執行工作流程（SOP）

啟動本 Skill 後，請按順序執行以下六個步驟：

### 第一步：盤點前置研究資產（Input Readiness Audit）
1. 執行或參照 `@Script(scripts/team_blueprint_tool.py)` 的 `check-inputs` 子命令，確認工作區已具備 `PROJECT.md`、`02_notes/literature_matrix.md`、`02_notes/research_gap_statement.md` 與 `01_papers/vector_index.json`。
2. 讀取 `PROJECT.md` 中的研究問題（RQ1–RQ3）與工具調用規範，確認工作區採用的本機 MCP 工具（如 `search_paper_chunks`）。

### 第二步：協作拓撲選型（Topology Pattern Selection）
參照 `@Resource(resources/orchestration_criteria.md)`，依據任務性質為研究階段選擇最適拓撲：
1. **順序流水線（Sequential Pipeline）：** 適合有明確先後依賴的單節撰稿（大綱 $\rightarrow$ 檢索 $\rightarrow$ 起草 $\rightarrow$ 稽核）。
2. **協調者－工作者（Orchestrator-Worker）：** 適合由主對話動態拆解子任務並派工給獨立子代理。
3. **平行分片綜整（Parallel Fan-Out）：** 適合同時針對多個 RQ 或多個概念構面平行調用檢索代理。
4. **對抗辯論迴圈（Adversarial Debate）：** 適合撰稿代理與隔離上下文的審稿／稽核代理進行多輪質詢修正。

### 第三步：定義角色名冊與最小權限邊界（Role Roster & Least-Privilege Boundaries）
參照 `@Resource(resources/team_blueprint_template.md)` 與 `@Example(examples/sample_team_blueprint.md)`，設計「PI 主導之四核心角色」或依研究方法客製微調：
1. **協調與大綱總監（Orchestrator / Outline Planner）：** 讀取規格與筆記，拆解段落目標；禁止直接捏造引文細節。
2. **實證檢索員（Evidence Retriever）：** 僅綁定 `search_paper_chunks` 與 `02_notes/cards/` 讀取權限；輸出精確帶出處的證據包；禁止改寫正式草稿。
3. **學術撰稿員（Academic Drafter）：** 僅讀取大綱與證據包，寫入 `03_drafts/`；嚴禁補充證據包以外的未查證文獻。
4. **事實稽核與方法審稿人（Fact Auditor & Method Critic）：** 必須與撰稿員隔離對話上下文，直接比對 `03_drafts/` 與 `search_paper_chunks` 原文，輸出客觀稽核報告。

### 第四步：訂定結構化交接契約與人類審查閘門（Handoff Protocol & HITL Gates）
1. 禁止代理之間只以口頭長段落傳話；必須指定實體 Markdown 交接檔案（例如 `03_drafts/_outline_plan.md`、`03_drafts/_evidence_pack.md`、`03_drafts/_audit_report.md`）。
2. 至少設定兩道**強制人類暫停點（HITL Gates）**：大綱與證據包核定閘門、稽核衝突裁決閘門。在人類 PI 核可前，不得自動進入下一高風險階段。

### 第五步：寫入團隊設計藍圖（Persistence to `02_notes/research_team_blueprint.md`）
將完整的團隊拓撲選型、角色權限表、交接契約、HITL 閘門與雙代理最小可行試跑計畫，正式寫入 `02_notes/research_team_blueprint.md`。

### 第六步：執行藍圖驗證與最小可行雙代理試跑（Validation & Pilot Run）
1. 執行驗證腳本確認規格完整性：
   ```bash
   python skills/research_team_orchestrator/scripts/team_blueprint_tool.py validate
   ```
2. 驗證通過後，在對話中向人類 PI 簡報團隊設計，並詢問是否針對論文某一個小節，立即派出隔離上下文的檢索子代理與稽核子代理進行最小可行交接演練。

---

## 嚴格執行紀律（Governance Rules）

1. **強制上下文隔離（Mandatory Context Isolation）：** 稽核／審稿角色絕不可與撰稿角色共享同一段自我辯解的對話歷史，必須透過獨立子代理或獨立視窗僅讀取「草稿」與「原文證據」進行查核。
2. **禁止無邊界全自動寫作（No Unconstrained Autonomy）：** 本課程之多代理團隊定位為「PI 主導的研究協作與事實糾察隊」，所有跨階段推進必須尊重 HITL 暫停點。
3. **工具與目錄權限分離（Strict Read/Write Separation）：** 任何撰稿與稽核代理對 `01_papers/` 均維持唯讀權限，嚴禁修改原始文獻與索引資料。
