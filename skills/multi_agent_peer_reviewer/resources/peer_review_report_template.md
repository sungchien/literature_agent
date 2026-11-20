---
type: multi_agent_peer_review_report
report_version: "1.0"
project_title: "請填入 PROJECT.md 中之論文工作題目"
target_draft: "03_drafts/02_literature_review_draft.md"
review_rounds: 2
blocking_issues_remaining: 0
created_date: "YYYY-MM-DD"
---

# 多代理對抗式同儕審查報告：［請填入目標章節或小節名稱］

## 1. 審查範圍與輸入資產檢核 (Scope & Input Audit)

- **審查目標草稿：** `03_drafts/...`
- **對照依據藍圖：** `02_notes/research_team_blueprint.md`
- **對照證據與知識資產：** `03_drafts/_evidence_pack.md`、`02_notes/literature_matrix.md`、`02_notes/research_gap_statement.md`
- **引文與證據錨點初檢摘要：** ［填入 `draft_audit_tool.py scan-draft` 輸出統計結果。］

---

## 2. 三路對抗審查意見彙整表 (Three-Pronged Adversarial Review Matrix)

| 段落／主張位置 | 審查代理視角 | 診斷標籤 | 具體問題與原文比對依據 | 建議處置動作（修訂／補檢索／刪減） |
| :--- | :--- | :--- | :--- | :--- |
| 第 X 段 / `[EV-01]` | 事實稽核審稿人 | `[通過]` / `[疑似錯引]` | ［寫明與原文數據／年份／樣本是否一致］ | ［具體修正指示］ |
| 第 Y 段 / `[EV-02]` | 方法學審稿人 | `[推論過度]` | ［指出是否忽略原實驗限制或外推邊界］ | ［縮小論述範圍或補入限制說明］ |
| 第 Z 段 | 概念結構編輯 | `[流水帳風險]` / `[通過]` | ［檢視是否以概念為主題句並採群組引註］ | ［重構主題句並加強跨篇對比］ |

---

## 3. 跨回合修訂追蹤與分流處置 (Revision Loop & Stopping Check)

- **第一輪審查結果與分流：** ［記錄第一輪發現幾筆實質缺陷、退回檢索員補查項目與局部文字修正狀況。］
- **第二輪複核與收斂判定：** ［確認 `[疑似錯引]` 是否歸零、`[證據不足]` 是否已補證或移除，以及是否符合停止條件。］

---

## 4. 人類 PI 終局裁決紀錄 (HITL Final Sign-Off)

- **衝突意見裁決：** ［若三位審稿代理之間或代理與研究者立場不一致，記錄 PI 之最終取捨理由。］
- **PI 親筆定調與覆核確認：** ［記錄研究者親自潤飾的核心段落與抽驗之原始 PDF 頁碼清單。］
- **最終狀態判定：** `[核准定稿]` / `[退回重修]`（PI 簽署日期：`YYYY-MM-DD`）
