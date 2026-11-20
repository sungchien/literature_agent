---
type: ai_collaboration_disclosure
disclosure_version: "1.0"
project_title: "請填入 PROJECT.md 中之論文工作題目"
target_manuscript: "03_drafts/02_literature_review_draft.md"
human_author: "請填入研究生／研究者姓名"
human_verification_rate: "100%"
created_date: "YYYY-MM-DD"
---

# 學術研究 AI 協作與多代理使用揭露聲明 (AI Collaboration & Audit Disclosure)

## 1. 協作工具與系統環境清單 (Tools & Model Environment)

- **研究協調環境：** Antigravity 2.0 Desktop（搭配本機工作區與 `PROJECT.md` 上下文規格）
- **本機檢索與驗證工具：** `literature-workflow` MCP（`search_paper_chunks`，基於 `BAAI/bge-base-en-v1.5` 本機向量索引）與專案驗證腳本
- **代理輔助範圍聲明：** 所有 AI 代理僅作為「文獻檢索輔助、結構化筆記整理、文字起草鷹架與對抗式同儕模擬審查」工具，**不具作者資格（Non-Authorship）**。

---

## 2. 多代理角色分工與權限邊界紀錄 (Multi-Agent Role & Governance Log)

| 協作階段 | 負責角色／工具 | 實際執行任務範圍 | 嚴格限制與隔離機制 |
| :--- | :--- | :--- | :--- |
| 前期規劃與大綱 | 協調大綱總監 + 人類 PI | 依 `literature_matrix.md` 拆解章節結構 | 大綱經 PI 於 HITL Gate 1 核定後始得進行 |
| 實證段落萃取 | 實證檢索員 (`search_paper_chunks`) | 檢索英文原文段落並組裝 `_evidence_pack.md` | 禁止更動 `01_papers/`；每筆證據須附檔案與頁碼 |
| 初稿架構起草 | 學術撰稿員 | 依證據包編寫段落草稿並標註 `[EV-XX]` | 嚴禁編造證據包以外之文獻數據或統計檢定 |
| 對抗同儕審查 | 事實稽核＋方法審查＋結構編輯 | 於隔離上下文反查原文並產出 `_peer_review_report.md` | 隔離撰稿對話脈絡；發現 `[疑似錯引]` 一律退回 |

---

## 3. 人類研究者實質控制權與核實紀錄 (Human-in-the-Loop Verification Record)

- **100% 原始文獻覆核確認：** 本稿件所保留之所有學術引註、統計數據（如 $N, F, t, p$ 值）與研究限制，均已由人類研究者本人核對 `01_papers/raw_pdf/` 或官方出版原件。
- **人類親筆修訂紀錄（Authorial Voice & Final Control）：**
  1. ［寫明研究者親自決定或改寫之理論詮釋／立論關鍵段 1］
  2. ［寫明研究者親自修正或刪除 AI 過度推論之處 2］

---

## 4. 可直接附於論文之標準揭露聲明段落 (Standard Disclosure Statements)

### 4.1 繁體中文聲明（適用碩士學位論文研究方法或附錄）
> 「本研究於文獻梳理與初稿籌備階段，採用基於本機檔案系統與檢索增強生成（RAG）之多代理 AI 協作工作流作為輔助研究工具，分別執行跨語言原文檢索、閱讀卡片結構化、段落初稿鷹架建構與模擬同儕對抗審查。所有研究問題設定、理論觀點詮釋、文獻取捨裁決及最終文字定稿，均由研究者本人（Principal Investigator）主導完成；稿件內引用之每一筆書目元數據、實證數據與原文論點，皆已由研究者親自比對原始出版文獻確認無誤，並由研究者對本研究之學術內容與研究誠信負完全責任。」

### 4.2 英文標準聲明（Academic English Disclosure for Journal Submissions）
> *"During the preparation of this manuscript, the author utilized a workspace-grounded, human-in-the-loop multi-agent AI workflow (equipped with local RAG retrieval and isolated adversarial peer-review checks) solely to assist with cross-lingual evidence extraction, structural outlining, initial drafting scaffolding, and citation consistency auditing. All research questions, theoretical interpretations, methodological decisions, and final textual revisions were directed and executed by the human author. Every cited reference, statistical figure, and empirical claim in the final manuscript has been independently verified against the original source publications by the human author, who takes full responsibility for the integrity and accuracy of the published work."*

---

## 5. 研究者終局簽署 (PI Final Sign-Off)

- **核實人員（Human PI）：** ［請填入姓名］
- **核實確認日期：** `YYYY-MM-DD`
- **狀態：** `[已核實並承擔全責]`
