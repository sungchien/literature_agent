---
name: multi-agent-peer-reviewer

description: >
  當使用者已完成第十章的多代理團隊藍圖（02_notes/research_team_blueprint.md），
  需要針對 03_drafts/ 的緒論或文獻探討初稿進行「三路對抗式同儕審查（事實稽核、
  方法學效度、概念結構修辭）」、執行審查—修訂收斂迴圈、合成跨章節初稿，
  並產出符合學術誠信的「AI 協作使用揭露聲明」時，請使用本 Skill。

version: "1.0"

author: "AI Agent 課程"

tags:
  - 同儕審查
  - Peer Review
  - 初稿合成
  - 事實稽核
  - 學術誠信
  - AI使用揭露
---

# 多代理對抗式同儕審查與研究初稿合成 Skill (multi-agent-peer-reviewer)

## Skill 目的

本 Skill 承接第十章 `research-team-orchestrator` 所建立的四代理組織設計（`02_notes/research_team_blueprint.md`）與交接工件（`03_drafts/_outline_plan.md`、`03_drafts/_evidence_pack.md`），專責執行**執行期與驗收期（Runtime & Audit-time）**之多代理對抗式審查與初稿合成治理。

透過將審查拆分為三個彼此隔離上下文的對抗視角——**事實稽核審稿人（Fact Auditor）**、**方法學審稿人（Methodological Reviewer）**與**概念結構編輯（Synthesis & Rhetorical Editor）**——並結合明確的回合收斂停止條件（Stopping Criteria）、人類總主持人（PI）終局裁決（HITL Final Sign-Off）以及標準化 **AI 協作使用揭露聲明**，確保 `03_drafts/` 初稿兼具嚴謹實證錨定與學術誠信透明度。

---

## 支援資源與檔案結構

```text
skills/multi_agent_peer_reviewer/
│
├── SKILL.md                                    # 核心六步 SOP 與治理守則
├── resources/
│   ├── peer_review_rubric.md                   # 三路審查規準、停止條件與防偏誤守則
│   ├── peer_review_report_template.md          # 同儕審查報告空白 Schema 範本
│   └── ai_disclosure_template.md               # 中英雙語 AI 協作使用揭露聲明範本
├── examples/
│   └── sample_peer_review_and_disclosure.md    # 單節審查報告與揭露聲明示範範例
└── scripts/
    └── draft_audit_tool.py                     # 草稿引文掃描、揭露初始化與合規驗證腳本
```

---

## 何時應使用本 Skill？

當使用者提出下列需求時，Agent 應主動調用本 Skill：
- 「依據團隊藍圖，幫我把 `02_notes/` 的矩陣與空白報告合成為 `03_drafts/` 初稿」
- 「請派出隔離上下文的三路對抗式審稿代理，審查我的 `03_drafts/` 初稿」
- 「幫我執行草稿引文與 `[EV-XX]` 證據錨點掃描，檢查是否有無根據的數據」
- 「依本學期多代理協作過程，產出一份可供論文附錄使用的 AI 使用揭露聲明」

---

## 嚴格執行工作流程（SOP）

啟動本 Skill 後，請按順序執行以下六個步驟：

### 第一步：盤點前置藍圖、證據包與待審草稿（Pre-Review & Synthesis Check）
1. 確認第十章產出之 `02_notes/research_team_blueprint.md` 與 `03_drafts/_evidence_pack.md` 已就位；若尚未建立正式草稿，先依 `PROJECT.md (v1.0)`、`02_notes/literature_matrix.md` 與 `02_notes/research_gap_statement.md` 執行「證據包驅動合成」，產出 `03_drafts/01_introduction_draft.md` 或 `03_drafts/02_literature_review_draft.md`（每項實證主張須附帶 `[EV-XX]` 與 APA 引註）。
2. 執行 `@Script(scripts/draft_audit_tool.py)` 掃描待審草稿的引註與證據標記覆蓋狀況：
   ```bash
   python skills/multi_agent_peer_reviewer/scripts/draft_audit_tool.py scan-draft 03_drafts/02_literature_review_draft.md
   ```

### 第二步：啟動三路隔離對抗審查委員會（Three-Pronged Isolated Peer Review）
參照 `@Resource(resources/peer_review_rubric.md)`，必須在**隔離撰稿對話脈絡**的獨立子代理或新對話中，依序或平行執行三路審查：
1. **事實稽核審稿人（Fact Auditor）：** 僅讀取草稿與 `search_paper_chunks`／`_evidence_pack.md`，逐段核對統計數字、樣本數、年份與研究對象，標註 `[通過]`、`[證據不足]`、`[疑似錯引]` 或 `[推論過度]`。
2. **方法學審稿人（Methodological Reviewer）：** 對照 `02_notes/literature_matrix.md` 與 `02_notes/research_gap_statement.md`，檢查是否將短時實驗結果過度外推為長程效應，或忽略異質文類限制。
3. **概念結構編輯（Synthesis & Rhetorical Editor）：** 檢核段落是否退化為「作者中心流水帳」、主題句是否清楚呈現共識／爭端／微差，並確認符合 CARS 四步轉折與 APA 第七版規範。

### 第三步：審查分流與收斂迴圈（Triage & Bounded Revision Loop）
1. 將三路意見依嚴重度分流為「局部文字修訂（交由撰稿員修正）」與「實質證據缺口（退回檢索員呼叫 `search_paper_chunks` 補證）」。
2. **嚴格停止條件（Stopping Criteria）：** 單一小節或章節之自動審查修訂迴圈**上限為 2 至 3 輪**；達標條件為所有 `[疑似錯引]` 歸零且重大 `[推論過度]` 均獲處置，禁止無止盡反覆重寫。

### 第四步：人類 PI 終局裁決與親筆定調（HITL Final Sign-Off）
1. 彙整審查衝突與未決意見至 `03_drafts/_peer_review_report.md` 後，**必須強制暫停**。
2. 由人類 PI 決定理論取捨、刪改或保留特定主張，並親筆潤飾核心立論段以確立個人學術聲腔（Authorial Voice）。

### 第五步：產出標準化 AI 協作使用揭露聲明（AI Collaboration Disclosure）
參照 `@Resource(resources/ai_disclosure_template.md)` 與 `@Example(examples/sample_peer_review_and_disclosure.md)`，執行初始化或協助撰寫 `03_drafts/ai_collaboration_disclosure.md`，如實登錄使用之工具與模型、多代理角色分工邊界、人類覆核與事實驗證機制。

### 第六步：執行自動化合規檢驗（Automated Audit & Validation）
執行腳本驗證審查報告與 AI 揭露聲明是否符合專案規範：
```bash
python skills/multi_agent_peer_reviewer/scripts/draft_audit_tool.py validate-review 03_drafts/_peer_review_report.md
python skills/multi_agent_peer_reviewer/scripts/draft_audit_tool.py validate-disclosure 03_drafts/ai_collaboration_disclosure.md
```

---

## 嚴格執行紀律（Governance Rules）

1. **禁止未經證據包之「憑空補寫」（Zero Unanchored Synthesis）：** 撰稿與修訂過程中若發現證據不足，必須退回檢索員調用 `search_paper_chunks`，嚴禁撰稿代理靠預訓練常識補齊文獻數據。
2. **防範錯誤級聯與迴音室偏誤：** 三位審稿代理必須彼此隔離且隔離於撰稿代理之自我辯護脈絡；所有退回修改必須可回溯至具體段落與原文錨點。
3. **誠實揭露與人類全權負責：** AI 多代理系統僅為輔助工具，不可列為作者；最終提交之每項引用與數據均須經人類 PI 核實並承擔完全學術責任。
