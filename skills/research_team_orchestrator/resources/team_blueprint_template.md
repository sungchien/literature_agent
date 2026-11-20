---
type: research_team_blueprint
blueprint_version: "1.0"
project_title: "請填入 PROJECT.md 中之論文工作題目"
topology_pattern: "Orchestrator-Worker + Sequential Pipeline + Adversarial Audit"
agent_count: 4
hitl_gates: 2
created_date: "YYYY-MM-DD"
---

# 學術研究多代理團隊設計藍圖：［請填入研究主題簡稱］

## 1. 團隊總覽與協作拓撲選型 (Team Overview & Topology Selection)

- **設計目標與克服之單代理極限：** ［說明本團隊主要解決哪些單代理瓶頸，例如避免長文寫作時遺忘事實錨點、消除自寫自審偏誤。］
- **採行協作拓撲組合：** ［說明本團隊採用的模式，例如：以 Coordinator-Worker 派工為主幹，撰稿採順序流水線，審查採隔離對抗迴圈。］
- **前置依據檔案：**
  - 研究規格書：`PROJECT.md`
  - 文獻比較矩陣：`02_notes/literature_matrix.md`
  - 學術空白報告：`02_notes/research_gap_statement.md`
  - 本機向量索引：`01_papers/vector_index.json`

---

## 2. 角色名冊與最小權限邊界表 (Role Roster & Least-Privilege Boundaries)

> 注意：Human Principal Investigator（人類研究者 / PI）為團隊最高決策者，不計入 AI 代理數量，但握有所有階段之最終裁決權。

| 角色名稱 | 核心職責與任務邊界 | 授權工具與可讀目錄 | 允許寫入路徑 | 明確禁止事項（防越權紅線） |
| :--- | :--- | :--- | :--- | :--- |
| **協調與大綱總監**<br>(Orchestrator / Planner) | 解析 `PROJECT.md` 與矩陣，拆解章節寫作目標並指派子任務 | 唯讀 `PROJECT.md`、`02_notes/` | `03_drafts/_outline_plan.md` | 禁止自行撰寫正文或未經檢索編造引文 |
| **實證檢索員**<br>(Evidence Retriever) | 執行中轉英查詢，自本機文獻庫提取帶出處與頁碼的實證段落 | `search_paper_chunks`、唯讀 `02_notes/cards/` | `03_drafts/_evidence_pack.md` | 禁止改寫正式草稿或夾帶未經檢索之評論 |
| **學術撰稿員**<br>(Academic Drafter) | 嚴格依據大綱與證據包撰寫概念中心段落與 APA 引註 | 唯讀 `_outline_plan.md`、`_evidence_pack.md` | `03_drafts/02_literature_review_draft.md` | 禁止憑預訓練記憶補寫證據包外之統計數據 |
| **事實稽核與方法審稿人**<br>(Fact Auditor & Critic) | 於隔離視窗比對草稿與原文，標記無錨點句與推論過度處 | `search_paper_chunks`、唯讀 `03_drafts/` 與 `02_notes/` | `03_drafts/_audit_report.md` | 禁止直接覆寫撰稿員正文；不可沿用撰稿對話脈絡 |

---

## 3. 結構化交接契約與人類審查閘門 (Handoff Artifacts & HITL Gates)

### 3.1 交接工件規範（Shared Workspace Artifacts）
1. **大綱計畫書（`03_drafts/_outline_plan.md`）：** 須包含小節主題句、對應之 RQ 編號、預計調用之核心文獻清單。
2. **實證證據包（`03_drafts/_evidence_pack.md`）：** 每條證據須含 `作者 (年份)`、`檔案名稱`、`章節或頁碼錨點`、`英文原文關鍵句` 與 `繁中摘要`。
3. **章節草稿（`03_drafts/02_literature_review_draft.md`）：** 每段須以概念為中心，所有數據與主張皆須標註對應證據編號。
4. **事實稽核報告（`03_drafts/_audit_report.md`）：** 逐條列出 `[通過]`、`[證據不足]`、`[疑似錯引]` 與 `[推論過度]` 清單及具體修正建議。

### 3.2 強制人類暫停點（Human-in-the-Loop Gates）
- **HITL Gate 1（大綱與證據包核定閘門）：** 完成大綱與實證檢索後必須暫停，由人類 PI 確認論證主軸與文獻覆蓋度無誤，始得進入撰稿階段。
- **HITL Gate 2（稽核報告衝突裁決閘門）：** 稽核員提出修正清單後必須暫停，由人類 PI 裁決採納修正、補充檢索或保留研究者個人詮釋。

---

## 4. Antigravity 2.0 派工與隔離驗證試跑計畫 (Orchestration & Pilot Protocol)

- **派工模式設定：** ［填寫採用「主代理派工獨立 Subagent」或「分開對話視窗手動接力」，並說明是否搭配 `.agents/rules/` 規則檔。］
- **最小可行試跑範圍（Pilot Scope）：** ［選定第二章中的一個小節，例如「2.1 自主代理人的認知負荷雙向效應」，測試檢索員產出證據包後交由隔離稽核員核驗之流程。］
- **驗收與防禦指標：**
  1. 證據包內所有引文是否 100% 附有可查證的檔案與段落錨點？
  2. 稽核員是否在隔離視窗中成功揪出至少一項潛在推論過度或缺失細節？
