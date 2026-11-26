---
trigger: model_decision
description: 當進行多代理學術團隊協作、初稿合成（03_drafts/）、證據包交接或對抗式同儕審查時載入的團隊隔離與收斂治理規範。
---

# 多代理學術協作與對抗式審查治理規範

## 1. 證據包驅動合成（Evidence-Pack Grounding）
- 撰寫 `03_drafts/` 正式論文草稿時，所有實證主張、樣本數與統計數據必須能在 `03_drafts/_evidence_pack.md` 找到對應之 `[EV-XX]` 證據錨點，並同時保留 APA 第七版文內引註與 `[EV-XX]` 編號以供程式稽核。

## 2. 上下文隔離與最小權限（Context Isolation & Least Privilege）
- 事實稽核（`fact-auditor`）與對抗式同儕審查（`methodological-reviewer`、`synthesis-editor`）必須透過隔離上下文的 Subagent（`.agents/agents/*.md` 或 `invoke_subagent`）執行，**嚴禁於撰稿原視窗自寫自審**。
- 審查代理僅具唯讀與檢索權限，嚴禁未經人類總主持人（PI）裁決即直接修改 `03_drafts/` 草稿正文。

## 3. 有界收斂與 PI 終局裁決（Bounded Convergence & HITL）
- 三路對抗審查與問題分流修訂迴圈**上限為 2 至 3 輪**；以 `[疑似錯引]` 歸零及 `[證據不足]` 補證或刪除為停損條件。
- 審查意見須彙整至 `03_drafts/_peer_review_report.md` 並暫停，交由人類研究者（PI）裁決定調。
