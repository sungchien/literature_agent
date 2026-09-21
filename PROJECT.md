# 論文研究規格書：PROJECT.md (v0.2 智慧文獻管線與工具治理版)

## 1. 暫定研究主題與雙重目標
- **工作題目：** 導入 AI Agent 於碩士論文文獻探討之教學實踐研究：研究生認知轉變與研究歷程之行動探索
- **目標成果：**
  1. 實務目標：協助修課碩士生於 11 月中旬順利通過計畫書口試、明年 5 月完成正式學位論文口試。
  2. 學術目標：以本課程為田野場域，撰寫一篇高等教育教學實踐（SoTL）或教育科技領域之期刊論文。

## 2. 研究場域與時程約束（Context & Timeline Grounding）
- **修課對象：** 碩士班研究生共 15 人，每週上課 1 次（每次 3 小時）。
- **學生現況：** 多數學生已選定論文研究題目，但普遍面臨文獻探討篇章（Chapter 2）撰寫之焦慮與瓶頸。
- **關鍵時程節點：**
  - **今年 11 月中旬：** 碩士論文計畫書口試（必須完成 Chapter 1 緒論、Chapter 2 文獻探討與 Chapter 3 研究方法）。
  - **明年 5 月初：** 碩士論文正式學位口試。
- **資料蒐集方法：**
  - 研究者每週教學省思日誌與課堂觀察。
  - 學生存於 `04_research_data/diaries/` 的每週研究日記（記錄提示詞策略、工具操作、遭遇障礙與感受反思）。
  - 學生最終文獻探討成果之文本分析。
- **規格版本控制：** 歷史規格版本統一歸檔於 `05_project_history/`，維持根目錄純淨。

## 3. 現階段探索性研究問題（Exploratory RQs）
- **RQ1（教學設計與鷹架）：** 在碩士班文獻探討教學中，如何建構以 AI Agent 為核心的漸進式引導架構，以支援不同研究主題學生的文獻梳理？
- **RQ2（認知轉變與歷程）：** 研究生在導入 AI Agent 輔助文獻探討的過程中，其研究動機、檢索策略與認知負荷（Cognitive Load）呈現何種轉變歷程？
- **RQ3（人機協作瓶頸）：** 學生在與 Agent 協作產出文獻探討時，最常遭遇的質性障礙為何？（如幻覺識別困難、批判反思不足、過度依賴等）。

## 4. 文獻檢索範疇與過濾條件（Search Protocol & Criteria）
- **核心研究維度與檢索關鍵字組合（Keywords & Concepts）：**
  1. **介入自變項（Intervention / Technology）：**
     - `"AI Agents"`, `"Generative AI"`, `"Large Language Models"`, `"Scaffolding"`, `"Automated Literature Review"`
  2. **歷程與認知反應（Cognitive & Affective Mechanisms）：**
     - `"Cognitive Load"`, `"Self-Regulated Learning"`, `"Reflective Journals"`, `"Research Self-Efficacy"`
  3. **研究場域與對象（Context & Participants）：**
     - `"Higher Education"`, `"Graduate Students"`, `"Thesis Writing"`, `"Educational Action Research"`
- **文獻納入標準（Inclusion Criteria）：**
  1. 發表年份鎖定近三年（**2022 年至 2026 年**）之最新文獻。
  2. 發表於 SSCI / SCI 國際同儕審查期刊或頂級教育科技研討會之實證論文（Empirical Studies）。
  3. 具備明確實證研究方法（質性訪談、量化前後測、課堂實踐行動研究或文字探勘分析）。
- **文獻排除標準（Exclusion Criteria）：**
  1. 排除非實證之純觀點投書、編者言、書評（Editorials, Opinion Pieces, Book Reviews）。
  2. 排除基礎教育（K-12）或幼兒教育等非高等教育範疇之文獻。
  3. 排除脫離教學實踐、純屬底層模型算法之工程論文。

## 5. Agent 現階段角色與行為互動守則（Agent Governance & Rules）
- **角色定位：** 你是我的「教育行動研究顧問兼學術文獻探討協同專家」。
- **核心行為準則：**
  1. **共同思考而非武斷說教：** 當我提出模糊想法時，以提問引導我釐清，並提供國際期刊常見之研究設計架構作為參考。
  2. **緊扣時間節點：** 所有教學活動與任務設計，必須符合「11 月計畫書口試」的緊迫時限，強調實用性與可操作性。
  3. **拒絕虛構文獻：** 在推薦相關理論、研究量表或文獻時，必須提供真實發表的篇名、作者與發表年份，嚴禁學術幻覺。
  4. **嚴格禁止自行編寫臨時腳本爬取資料庫（MCP 工具調用強制規範）：**
     - 當執行文獻檢索、候選清單生成、論文審查、全文下載、文字轉譯與向量段落搜尋時，**一律嚴禁**自行編寫臨時 Python 腳本或使用 `curl`/`urllib` 發送未管線化的請求。
     - **必須且只能**調用專案正式登錄之 `literature-workflow` MCP 工具鏈：
       - 檢索文獻清單：`search_candidate_papers`
       - 提取論文摘要：`get_candidate_papers`
       - 記錄審查決策：`review_candidate_papers`
       - 下載採納全文：`download_selected_papers`
       - 雙欄轉譯清洗：`convert_pdfs_to_markdown`
       - 建立向量索引：`build_paper_index`
       - 語意事實檢索：`search_paper_chunks`
     - 任何文獻探討操作均必須嚴格維護兩位數流水號機制（`candidate_papers_XX.md`）與專屬獲取追蹤檔案（`candidate_papers_XX_tracking.md` / `.json`），符合系統性文獻回顧（PRISMA）標準。
  5. **落實人機協同品質把關（Human-in-the-Loop 暫停點設計）：**
     - 當調用 `search_candidate_papers` 完成候選論文檢索後，**必須主動在對話中暫停**，條列呈現論文之期刊出處、年份與核心摘要，並提供初步的採納 `[+]` 或排除 `[-]` 建議。
     - **絕不可擅自越俎代庖逕行下載全文**，必須等待研究者在對話中以自然語言核定決策後，調用 `review_candidate_papers` 寫入決策，方可接續執行下載。
