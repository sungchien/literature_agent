---
trigger: model_decision
description: 當執行學術文獻檢索、候選清單審查、全文下載、外部 PDF 收件匯入、PDF 轉譯 Markdown 或本機向量索引建置時載入的工具治理與 PRISMA 規範。
---

# 學術文獻管線與 MCP 工具強制治理規範

## 1. 嚴格禁止工具漂移（嚴禁臨時腳本與外部替代工具）
執行文獻檢索、審查、下載、外部論文入庫、PDF 轉譯與向量檢索時，**一律嚴禁**自行編寫臨時 Python 爬蟲腳本（如 `requests` / `urllib` / `curl`），**亦嚴禁**調用外部 Plugin 之通用 Skill（如 `literature-search-openalex`）替代本專案管線。必須依運算性質嚴格區分以下兩條正式路徑：

- **在線動態人機協同（`literature-workflow` MCP 工具鏈）：**
  - 檢索候選文獻清單：`search_candidate_papers`
  - 提取候選論文摘要：`get_candidate_papers`
  - 寫入審查採納決策：`review_candidate_papers`
  - 下載採納文獻全文：`download_selected_papers`
  - 掃描外部論文收件匣：`scan_inbox_papers`
  - 外部文獻元數據治理入庫：`ingest_external_papers`
  - 語意事實精華檢索：`search_paper_chunks`
- **離線批次重型計算（本機終端機腳本執行，非 MCP 工具）：**
  - PDF 雙欄版面轉譯清洗：`python scripts/extract_pdf_to_md.py`
  - 雙檔解耦向量索引建置：`python scripts/paper_retriever_mcp.py build [--force]`（採用 `BAAI/bge-base-en-v1.5` 768 維模型，具增量快取與 TQDM 進度條）

## 2. PRISMA 規範化追蹤機制
- 所有文獻檢索操作皆必須嚴格維護兩位數流水號機制（`01_papers/candidate_papers_XX.md`）與專屬獲取追蹤檔案（`candidate_papers_XX_tracking.md` / `.json`），確保符合系統性文獻回顧（PRISMA）可稽核標準。

## 3. 人機協同品質把關（Human-in-the-Loop 強制暫停點）
- 調用 `search_candidate_papers` 完成候選論文檢索後，**必須主動在對話中暫停**，條列呈現論文之期刊出處、年份與核心摘要，並依 `PROJECT.md` 納入／排除標準提出初步採納 `[+]` 或排除 `[-]` 建議。
- **絕不可擅自越俎代庖逕行下載全文**，必須等待研究者在對話中以自然語言核定決策後，調用 `review_candidate_papers` 寫入決策，方可接續執行 `download_selected_papers`。
