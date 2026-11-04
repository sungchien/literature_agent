---
type: research_gap_statement
gap_version: 1.0
project_title: "導入 AI Agent 於碩士論文文獻探討之教學實踐研究：研究生認知轉變與研究歷程之行動探索"
source_matrix: "02_notes/literature_matrix.md"
gap_types:
  - Population_Context_Gap
  - Methodological_System_Gap
  - Theoretical_Tension_Gap
  - Ecological_Validity_Gap
target_project_version: "v0.4"
created_date: 2026-11-03
---

# 學術空白鎖定與開題立論防禦報告：AI Agent 輔助碩士論文文獻探討

## 1. 跨篇矩陣盲點審計與真偽空白診斷 (Matrix Blind-Spot Audit & Spurious Gap Diagnosis)

### 1.1 破除「偽空白（Spurious Gap）」之自我檢核
- **常見初學者偽空白陷阱：** 「過去國內較少針對台灣教育研究所碩士生使用 AI Agent 寫論文進行研究，因此本研究具有創新性。」（此說法僅置換受試者地區與系所，未觸及核心理論矛盾，極易遭口試委員質疑缺乏普適學術貢獻。）
- **本研究之結構性問題化（Problematization）轉化：** 依據 Sandberg & Alvesson (2011) 之問題化框架，本研究直接切入既有文獻的**雙重結構性矛盾**：第一，工程界科學代理人（如 Baek et al., 2025; Zheng et al., 2025）追求「端到端全自動代勞」，但教育心理實證（Wang et al., 2024）證實無約束自動化會引發「認知外包與批判退化」；第二，現有教育研究（Chen & Roberts, 2023）雖引入反思提示，卻停留於脫離本機文獻庫的雲端對話視窗，無法消解研究生的「虛假引用查證焦慮」與「工具中斷感」。本研究旨在解決「如何透過具備本機檔案感知與人機責任光譜之 Agent 鷹架，將減少的外在負荷實質轉化為高階批判綜整能力」之核心機制缺口。

### 1.2 四大經典學術空白型態定位表 (Four-Dimensional Gap Typology Mapping)

| 空白維度型態 (Gap Typology) | 既有文獻主流現象與矩陣證據 (Prior Literature Pattern) | 現有文獻之結構性缺口 (Unresolved Structural Gap) | 本研究之具體填補設計 (How This Thesis Bridges the Gap) |
| :--- | :--- | :--- | :--- |
| **1. 族群與場域脈絡空白**<br>(Population & Context Gap) | 既有實驗多以大學部學生進行單篇短文摘要或通用英語寫作測試（Wang et al., 2024）。 | 缺乏針對「非英語母語碩士研究生」面對高認知複雜度、高學術嚴謹度要求之「學位論文第二章文獻探討」的深度實證。 | 鎖定碩士班研究方法與論文寫作專題課程（$N=15$），聚焦跨語言檢索（中文提問、英文實證錨定）與學位論文開題實戰。 |
| **2. 方法學與工具系統空白**<br>(Methodological & System Gap) | 教育研究多使用無狀態之網頁版 ChatGPT（Wang et al., 2024）；工程研究則採用全自動黑箱生成系統（Baek et al., 2025）。 | 缺乏整合「本機檔案系統感知（Workspace）、PRISMA 追蹤、雙語 RAG 向量檢索與模組化 Skill 狀態機」之教學型 Agent 管線。 | 建構基於 Antigravity 2.0 Desktop 之漸進式工具鏈，結合 `PROJECT.md` 上下文工程與每階段強制驗證腳本。 |
| **3. 理論衝突與機制未解空白**<br>(Theoretical Tension Gap) | Chen & Roberts (2023) 發現 AI 降低外在負荷並提升品質，但 Wang et al. (2024) 卻發現批判提問顯著退化。 | 「AI 釋放出的工作記憶空間，究竟在何種約束條件下會轉化為深層相關認知負荷（Germane Load），而非淪為認知惰性？」機制未明。 | 提出並實證檢驗「三層級人機協同責任光譜（綠燈自動化、黃燈對抗覆核、藍燈親筆映射）」與「防硬填紀律」之調節機制。 |
| **4. 生態效度與長程歷程空白**<br>(Ecological Validity Gap) | 絕大多數研究為 2 小時單次實驗室施測（Wang et al., 2024）或僅依賴期末橫斷面問卷（Chen & Roberts, 2023）。 | 缺乏橫跨整學期（16–18 週）從「文獻檢索、PDF 清洗、卡片精讀、矩陣共構到空白鎖定」的動態認知轉變與障礙演化軌跡。 | 採用全學期教育行動研究，結合每週結構化反思日誌（`04_research_data/diaries/`）與文本產出物進行縱貫三角檢證。 |

---

## 2. CARS 四步修辭轉折學術空白陳述句 (CARS 4-Move Research Gap Statement)

### 2.1 四步結構化拆解 (Step-by-Step Rhetorical Anatomy)
- **第一步：肯定前人共識底座（Move 1: Consensus Grounding）**
  - 肯定近年生成式 AI 與科學研究代理人（Scientific Agents）在加速文獻檢索、降低初期資訊搜尋門檻以及提供寫作鷹架上的潛力（Kasneci et al., 2023; Chen & Roberts, 2023; Zheng et al., 2025）。
- **第二步：關鍵轉折與指出致命矛盾/局限（Move 2a: The Critical "However" Pivot）**
  - **然而（However）**，既有文獻在「認知成效」與「系統架構」上存在兩大未解斷層：一方面，無約束的開放式對話雖提升短期效率，卻極易誘發研究生的認知外包與批判性退化（Wang et al., 2024），而工程界追求的端到端全自動代理（Baek et al., 2025）更與碩士教育培養獨立研究者的目標背道而馳；另一方面，既有教育實證多侷限於短期實驗室任務與脫離本機文獻庫的網頁對話框，尚未探討具備「本機檔案感知、雙語 RAG 事實錨定與人機協同強制暫停點」之 Agent 鷹架在長程碩士論文寫作中的作用機制。
- **第三步：闡明未解問題的學術與實務代價（Move 2b: Cost of Inaction）**
  - **其結果是（Consequently）**，高等教育現場對於研究生在長達一學期的文獻探討歷程中，如何克服 AI 幻覺查證焦慮、並將釋放出的外在認知負荷轉化為實質的跨篇批判綜整能力，仍缺乏動態的理論解釋模型與可落地的教學工程規範。
- **第四步：確立本研究填補價值與引出 RQs（Move 3: Occupying the Niche & Introducing RQs）**
  - **為填補此一關鍵學術空白（To bridge this critical gap）**，本研究以碩士班論文文獻探討專題課程為田野場域，結合教育行動研究與每週研究日誌，建構並實證檢驗一套基於 Antigravity 2.0、MCP 工具鏈與「三層級人機責任光譜」之漸進式 AI Agent 教學鷹架，具體探究其教學管線設計（RQ1）、研究生認知負荷與動機之縱貫轉變（RQ2），以及人機協作過程中的核心瓶頸與防禦機制（RQ3）。

### 2.2 正式學術空白陳述段落（繁體中文定稿版 — 可直接嵌入第一章緒論與第二章結尾）
> 「儘管近年實證研究與系統性綜述已廣泛證實，生成式 AI 與自主代理人（AI Agents）在加速文獻篩選與輔助學術起草上具備顯著潛力（Kasneci et al., 2023; Chen & Roberts, 2023; Zheng et al., 2025），**然而（However）**，既有文獻體系在『認知轉化機制』與『工具生態效度』上仍存在深刻的結構性斷裂。首先，實證研究針對 AI 介入的認知後果呈現明顯分歧：部分研究發現反思型提示能降低外在認知負荷（Chen & Roberts, 2023），但另有實驗指出開放式 AI 對話雖提升 40% 任務速度，卻導致學習者產生『解釋深度錯覺』並顯著削弱批判提問深度（Wang et al., 2024）；同時，計算機領域所開發的端到端科學代理人（如 Baek et al., 2025）致力於以全自動代勞取代人類構思，若直接套用於研究生教育，將嚴重剝奪學位論文訓練核心的批判內化歷程。其次，既有教育實證多受限於單次短時實驗或孤立於瀏覽器視窗的聊天機器人，鮮少探討具備『本機工作區檔案感知、雙語 RAG 向量事實錨定與人機協同強制暫停點』之結構化 Agent 管線。**其結果是（Consequently）**，學界對於非英語母語碩士生在面對高壓、長週期的學位論文文獻探討時，如何透過精確的人機責任邊界設計克服幻覺查證焦慮，並將釋放出的工作記憶實質轉化為跨篇概念綜整與研究空白立論能力，仍缺乏長程的動態實證證據。**為填補此一關鍵學術空白（To bridge this critical gap）**，本研究採行全學期（16 至 18 週）之教育行動研究，於碩士班研究課程中導入結合上下文工程（`PROJECT.md`）、PRISMA 檢索追蹤、七維批判閱讀卡片與雙層次文獻矩陣之 AI Agent 漸進式鷹架，深入剖析該教學架構之設計原則（RQ1）、研究生認知負荷與自我效能之縱貫演變軌跡（RQ2），以及人機協同過程中的質性障礙與破局策略（RQ3）。」

### 2.3 國際期刊投稿級英文陳述段落（Academic English Version）
> *"While burgeoning empirical studies and systematic reviews have broadly confirmed the potential of generative AI and autonomous agents to accelerate literature screening and scaffold academic drafting (Kasneci et al., 2023; Chen & Roberts, 2023; Zheng et al., 2025), **however**, profound structural disconnects persist regarding both their cognitive internalization mechanisms and ecological validity. First, empirical evidence remains sharply divided on the cognitive consequences of AI intervention: whereas structured prompting can alleviate extraneous cognitive load (Chen & Roberts, 2023), unconstrained conversational AI often induces an 'illusion of explanatory depth' and significantly diminishes critical questioning despite faster task completion (Wang et al., 2024). Concurrently, end-to-end scientific agents in computer science (e.g., Baek et al., 2025) prioritize full automation over human agency, which risks inducing severe cognitive offloading if directly transplanted into graduate thesis training. Second, prior educational interventions predominantly rely on short-term laboratory tasks and browser-isolated chatbots detached from local file systems, leaving workspace-aware agents equipped with bilingual RAG fact-grounding and human-in-the-loop pause points largely unexplored. **Consequently**, the field lacks longitudinal empirical evidence on how L2 master's students navigate hallucination verification anxiety and channel freed cognitive resources into rigorous cross-paper synthesis during authentic thesis writing. **To bridge this critical gap**, this study conducts a semester-long (16–18 weeks) educational action research to investigate a progressive AI Agent scaffolding framework—integrating Context Engineering (`PROJECT.md`), PRISMA tracking, atomic reading cards, and concept-centric matrices—specifically examining its pedagogical architecture (RQ1), students' longitudinal cognitive load and motivational trajectories (RQ2), and human-AI collaboration bottlenecks (RQ3)."*

---

## 3. 對抗性口試委員極限壓力測試與答辯實錄 (Adversarial Oral Defense Simulation)

### 3.1 第一回合：真偽性與「那又怎樣（So What?）」挑戰
- **嚴苛口試委員質詢：** 「同學，你宣稱過去教育研究用的是網頁版 ChatGPT，而你用的是具備本機檔案感知與 MCP 工具鏈的 Antigravity 2.0。這聽起來只是一項『軟體工具升級』！如果三年後軟體又換了一代，你的研究還有什麼學術價值？這難道不是典型的工具應用型偽空白嗎？」
- **研究者實證與理論答辯：** 「感謝委員一針見血的提問。本研究的核心貢獻絕非替特定軟體背書，而是透過這套管線實證檢驗認知負荷理論（CLT）與人機協同認知中的核心理論命題：**『物理環境耦合（Workspace Grounding）與強制人機責任邊界（Human-AI Responsibility Spectrum）如何調節外在負荷向相關認知負荷的轉化』**。無論未來軟體介面如何更迭，『全自動黑箱代勞導致認知退化』與『孤島式對話引發查證焦慮』的認知心理學矛盾永遠存在。本研究提出的『三層級人機協同責任光譜（綠燈機械自動化、黃燈對抗性覆核、藍燈研究者親筆主導）』與『防硬填紀律』，是一套超越特定軟體版本的教學設計原理（Design Principles），能為高等教育導入任何新世代 AI Agent 提供可遷移的理論模型。」

### 3.2 第二回合：既有文獻反擊（Prior Art Counter-Attack）
- **嚴苛口試委員質詢：** 「請打開你的 `02_notes/literature_matrix.md`。Chen & Roberts (2023) 已經針對 64 名台灣碩士生進行了 10 週的 AI Agent 反思鷹架實驗，也使用了 Paas 心理努力量表證明外在認知負荷降低（$p < .001$）。你的 RQ1 與 RQ2 跟 Chen & Roberts (2023) 到底有什麼本質區別？為什麼學界還需要你再做一次？」
- **研究者實證與理論答辯：** 「委員好，根據我們在第六週卡片與第七週矩陣對 Chen & Roberts (2023) 的深度方法學解剖，該研究存在三個關鍵限制，正是本研究往前推進的起點：第一，Chen & Roberts (2023) 的 Agent 僅為對話框內的反思提示器，未連結本機向量檢索與原文頁碼錨定，因此他們在第五維度限制中未能解決學生面對『跨篇數據張冠李戴與假引用』的核心瓶頸（這正是本研究的 RQ3）；第二，該研究僅將文獻探討視為單一籠統任務，未拆解出『檢索篩選 $\rightarrow$ 單篇七維卡片 $\rightarrow$ 雙層次矩陣 $\rightarrow$ CARS 空白鎖定』的細粒度知識工程狀態機（本研究之 RQ1）；第三，本研究透過每週研究日誌（`04_research_data/diaries/`）捕捉學生在 16–18 週內經歷『工具蜜月期、幻覺幻滅期到主導權重建期』的非線性縱貫轉折（本研究之 RQ2），填補了前人僅看前後測量表均值的黑盒子。」

### 3.3 第三回合：方法學可操作性與效度威脅挑戰（Feasibility & Validity Defense）
- **嚴苛口試委員質詢：** 「你的研究場域是單一碩士班課程（$N=15$），且由授課教師兼任研究者進行教育行動研究。沒有隨機分派對照組，樣本又只有 15 人，你要如何說服審稿人你的發現不是因為『學生為了拿高分而在反思日誌裡討好老師（社會期許偏誤與霍桑效應）』？」
- **研究者實證與理論答辯：** 「委員點出了行動研究最關鍵的內部效度挑戰。為嚴格控制社會期許偏誤，本研究不單憑學生的主觀感受日誌下結論，而是建立 **『三源客觀文本與行為三角檢證（Triangulation）』**：第一，檢視學生在 `02_notes/cards/` 與 `02_notes/literature_matrix.md` 中實際留存的『審查者獨立批判深度』與『防硬填誠實標註率』（客觀工作區製品分析）；第二，比對學生在版本控制庫 `05_project_history/` 中從 v0.1 到 v0.4 的研究問題收斂品質（客觀文本演進證據）；第三，在每週日誌中明確設計『AI 失敗案例與提示詞除錯紀錄』計分鼓勵機制——學生記錄越真實的 AI 幻覺與卡關挫敗，越能獲得實作肯定，從制度上消除報喜不報憂的誘因。」

---

## 4. 研究問題（RQs）收斂定錨與 `PROJECT.md (v0.4)` 升級映射 (RQ Convergence & Specification Upgrade)

| 研究問題編號 | 原探索版研究問題 (`PROJECT.md` v0.1–v0.3) | 經學術空白與矩陣定錨後之收斂版研究問題 (`PROJECT.md` v0.4) | 對應之空白型態與實證資料來源 (`04_research_data/`) |
| :--- | :--- | :--- | :--- |
| **RQ1** | 在碩士班文獻探討教學中，如何建構以 AI Agent 為核心的漸進式引導架構，以支援不同研究主題學生的文獻梳理？ | **RQ1（教學鷹架與人機責任邊界設計）：** 在碩士班學位論文文獻探討教學中，如何建構整合「上下文工程（`PROJECT.md`）、本機 RAG 事實錨定與三層級人機責任光譜」之模組化 AI Agent 漸進式鷹架，以兼顧機械性減負與高階批判主體性？ | **方法與系統空白**；教師每週教學省思日誌、Skill 管線迭代紀錄、學生卡片與矩陣製品合規率分析 |
| **RQ2** | 研究生在導入 AI Agent 輔助文獻探討的過程中，其研究動機、檢索策略與認知負荷呈現何種轉變歷程？ | **RQ2（認知負荷轉化與縱貫發展軌跡）：** 碩士生在經歷「文獻檢索、七維卡片精讀、跨篇矩陣共構至學術空白鎖定」的 16–18 週行動歷程中，其外在認知負荷如何轉化為相關認知負荷？其研究自我效能感經歷何種階段性轉折？ | **理論衝突與長程空白**；`04_research_data/diaries/` 每週研究日誌質性編碼、Paas 心理努力量表縱貫趨勢、`05_project_history/` 規格演進分析 |
| **RQ3** | 學生在與 Agent 協作產出文獻探討時，最常遭遇的質性障礙為何？（如幻覺識別困難、批判反思不足、過度依賴等）。 | **RQ3（人機協作瓶頸與防禦機制）：** 非英語母語碩士生在與具備本機感知之 AI Agent 協作時，於「跨語言語意檢索、幻覺查證、防硬填抗拒及主導權協商」上面臨哪些核心瓶頸？「對抗性審稿與口試壓力測試機制」如何協助其突破過度依賴？ | **族群場域與理論機制空白**；學生提示詞操作日誌、卡片/矩陣驗證錯誤紀錄、期末半結構式深度訪談 |
