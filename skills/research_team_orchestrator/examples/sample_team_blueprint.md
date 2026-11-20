---
type: research_team_blueprint
blueprint_version: "1.0"
project_title: "導入 AI Agent 於碩士論文文獻探討之教學實踐研究：研究生認知轉變與研究歷程之行動探索"
topology_pattern: "Orchestrator-Worker + Sequential Pipeline + Adversarial Audit"
agent_count: 4
hitl_gates: 2
created_date: "2026-11-20"
---

# 學術研究多代理團隊設計藍圖：AI Agent 輔助碩士論文文獻探討研究團隊

## 1. 團隊總覽與協作拓撲選型 (Team Overview & Topology Selection)

- **設計目標與克服之單代理極限：** 本研究計畫書第二章需橫向綜整認知負荷理論（CLT）、自我調節學習（SRL）與科學研究多代理系統等跨領域文獻，並嚴格對接 `PROJECT.md (v0.4)` 之三大研究問題（RQ1–RQ3）。若由單一對話視窗從頭查資料、寫正文兼自我審查，極易因長文本上下文稀釋而漏引頁碼錨點，或出現「自寫自審放水」的確認偏誤。本團隊透過四代理角色隔離與工件交接，確保每一項論點皆可回溯至本機原文。
- **採行協作拓撲組合：** 採「**PI 主導之協調者派工（Orchestrator-Worker）為骨幹，單節寫作採順序流水線（Sequential Pipeline），事實核對採隔離對抗審查（Adversarial Audit）**」之混合拓撲；遇跨構面檢索時，可由協調總監平行分派檢索子代理分別查詢 RQ1–RQ3 證據。
- **前置依據檔案：**
  - 研究規格書：`PROJECT.md`
  - 文獻比較矩陣：`02_notes/literature_matrix.md`
  - 學術空白報告：`02_notes/research_gap_statement.md`
  - 本機向量索引：`01_papers/vector_index.json`

---

## 2. 角色名冊與最小權限邊界表 (Role Roster & Least-Privilege Boundaries)

> 注意：人類研究者（Human Principal Investigator，PI）為研究團隊總主持人，掌握選題方向、理論詮釋與最終修訂裁決權。

| 角色名稱 | 核心職責與任務邊界 | 授權工具與可讀目錄 | 允許寫入路徑 | 明確禁止事項（防越權紅線） |
| :--- | :--- | :--- | :--- | :--- |
| **協調與大綱總監**<br>(Orchestrator / Planner) | 讀取 `PROJECT.md`、矩陣與空白報告，拆解第二章各小節目標並追蹤交接狀態 | 唯讀 `PROJECT.md`、`02_notes/` | `03_drafts/_outline_plan.md` | 禁止直接撰寫正式章節段落；不得跳過 HITL 閘門派工 |
| **實證檢索員**<br>(Evidence Retriever) | 將中文構面需求轉譯為英文學術檢索詞，整合閱讀卡片與 RAG 段落為證據包 | `search_paper_chunks`、唯讀 `02_notes/cards/` | `03_drafts/_evidence_pack.md` | 禁止更動 `01_papers/`；禁止撰寫未附原文出處之推論 |
| **學術撰稿員**<br>(Academic Drafter) | 嚴格依大綱與證據包起草「概念中心」段落，遵循 APA 第七版格式與雙語標註 | 唯讀 `_outline_plan.md`、`_evidence_pack.md` | `03_drafts/02_literature_review_draft.md` | 禁止憑預訓練常識補寫證據包外之統計數據或年份 |
| **事實稽核與方法審稿人**<br>(Fact Auditor & Critic) | 於完全隔離的新脈絡中逐句核對草稿與原文，揪出無錨點主張與推論過度處 | `search_paper_chunks`、唯讀 `03_drafts/` 與 `02_notes/` | `03_drafts/_audit_report.md` | 禁止直接修改草稿正文；禁止讀取撰稿過程的對話辯護 |

---

## 3. 結構化交接契約與人類審查閘門 (Handoff Artifacts & HITL Gates)

### 3.1 交接工件規範（Shared Workspace Artifacts）
1. **大綱計畫書（`03_drafts/_outline_plan.md`）：** 針對每個小節明列「概念主題句」、「對應 RQ」、「共識／爭端／微差寫作軸線」與「待檢索英文查詢清單」。
2. **實證證據包（`03_drafts/_evidence_pack.md`）：** 採編號條目 `[EV-01]`、`[EV-02]` 紀錄，每筆必須包含 `作者 (年份)`、`對應檔案與頁碼/Chunk 標籤`、`英文原文關鍵句摘錄` 及 `繁體中文事實摘要`。
3. **章節草稿（`03_drafts/02_literature_review_draft.md`）：** 每個主張句尾必須標註引用來源與對應證據編號（如 `...[EV-03]`），嚴禁以作者人名報流水帳。
4. **事實稽核報告（`03_drafts/_audit_report.md`）：** 逐段產出四態判定表——`[通過]`（原文完全支持）、`[證據不足]`（需補充檢索）、`[疑似錯引]`（數據或作者與原文不符）、`[推論過度]`（將限制情境過度外推）。

### 3.2 強制人類暫停點（Human-in-the-Loop Gates）
- **HITL Gate 1（大綱與證據包核定閘門）：** 當 `03_drafts/_outline_plan.md` 與 `03_drafts/_evidence_pack.md` 產出後，主協調代理必須暫停並呈報 PI；確認核心論點與納入文獻無遺漏後，方可啟動撰稿員。
- **HITL Gate 2（稽核報告衝突裁決閘門）：** 當 `03_drafts/_audit_report.md` 完成後，主協調代理必須暫停並呈現所有 `[疑似錯引]` 與 `[推論過度]` 條目；由 PI 裁定修正方向後再行定稿。

---

## 4. Antigravity 2.0 派工與隔離驗證試跑計畫 (Orchestration & Pilot Protocol)

- **派工模式設定：** 採用 Antigravity 2.0 主對話視窗擔任「協調與大綱總監（Coordinator）」，分別呼叫隔離上下文的 Subagent 扮演「實證檢索員」、「學術撰稿員」與「事實稽核員」；並可搭配專案根目錄規則檔（如 `.agents/rules/team_governance.md`）固化「唯讀 `01_papers/`」與「強制標註頁碼錨點」紀律。
- **最小可行試跑範圍（Pilot Scope）：** 選取第二章第一小節「2.1 自主代理人在高階文獻探討中的認知負荷雙向效應」，先由檢索子代理產出 3 筆跨篇證據包至 `03_drafts/_evidence_pack.md`，再由隔離稽核子代理以 `search_paper_chunks` 獨立反查其中統計數值與研究限制是否精確無誤。
- **驗收與防禦指標：**
  1. 證據包中每一條 `[EV-XX]` 條目均能在 `01_papers/` 或 `02_notes/cards/` 中找到確切對應出處。
  2. 稽核子代理在未接觸檢索與撰稿對話紀錄的情況下，能獨立產出具備明確標籤與原文對照的 `03_drafts/_audit_report.md`。
