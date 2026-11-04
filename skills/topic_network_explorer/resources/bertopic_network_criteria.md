# BERTopic 區塊級主題建模與跨篇語意網路拓撲規準（Topic Modeling & Network Topology Criteria）

本文件收錄「區塊級 BERTopic 演算法管線規範」、「學術文本雜訊防禦準則」、「跨篇語意相似度網路稀疏化法則」與「Burt (1992) 結構洞理論判讀規準」，供 Agent 於執行 `topic-network-explorer` Skill 時動態查閱。

---

## 一、為什麼採用「區塊級（Chunk-Level）BERTopic」而非「單篇級」？

在個人學位論文或專題文獻庫中（通常收錄 20 至 50 篇核心論文），傳統以「整篇文獻（Document-level）」為單位的主題模型（如 LDA 或單篇 BERTopic）會遭遇兩大統計與語意瓶頸：
1. **樣本數過小導致聚類失效：** 密度聚類演算法（如 HDBSCAN）與流形降維（UMAP）在樣本數 $N < 50$ 時難以估計穩定的局部密度，極易將絕大多數文獻歸為 `-1` 離群值。將分析粒度降為第五週的 **結構感知段落區塊（Structure-Aware Chunks，$N \approx 500 \sim 2,000$）**，能直接進入非監督聚類的最佳統計甜蜜點。
2. **單篇論文的「多主題混合本質（Multi-Topic Mixture）」：** 一篇完整的實證論文必然同時包含「理論背景」、「研究方法與系統設計」、「統計結果」與「研究限制」。以區塊為單位建模後，再向上統計每篇論文旗下區塊的主題分佈比例：
   $$P(\text{Topic } k \mid \text{Paper } d) = \frac{\sum_{c \in d} \mathbb{I}(\text{topic}(c) = k)}{|d|}$$
   即可精確描繪出每篇論文的「跨主題指紋（Topic Fingerprint）」。

---

## 二、學術文本三道防噪與表徵優化紀律（Academic Text Sanitization & c-TF-IDF Tuning）

1. **首頁機構與出版聲明區塊過濾（Front-Matter Affiliation Filtering）：**
   - 學術論文首頁（Page 1 / Page 2）常包含數十位共同作者之大學系所、城市、郵遞區號與版權授權文字。若直接納入聚類，c-TF-IDF 會萃取出 `university_department_school_institute_uk_usa` 之假主題。
   - **強制過濾規則：** 在建模前，若區塊文字包含高密度機構詞彙（如連續出現多次 `University`, `Department of`, `School of`, `Corresponding author`, `Elsevier`, `Creative Commons`），腳本將自動標記為 `[META_NOISE]` 並排除於主題建模與網路連線之外。
2. **雙詞組（Bigram）與學術結構停用詞（Academic Stopwords）：**
   - 採用 `CountVectorizer(ngram_range=(1, 2))` 同時捕捉單字與雙詞組（如 `cognitive load`, `literature review`, `generative ai`, `language models`）。
   - 停用詞表除標準英文虛詞外，額外排除學術通用結構詞（如 `et al`, `fig`, `figure`, `table`, `section`, `paper`, `study`, `research`, `results`, `however`, `also`, `using`, `based`），確保提取出的 Top Keywords 100% 反映領域實質概念。
3. **離群區塊向量平滑歸併（Embedding-Based Outlier Reduction）：**
   - HDBSCAN 初始聚類後標記為 `-1` 的邊界區塊，透過計算其 768 維向量與各主題簇中心向量（Topic Centroids）之餘弦相似度，自動歸併至最接近之實質主題簇，實現全庫有效區塊 100% 主題覆蓋。

---

## 三、跨篇語意區塊互動網路圖（Interactive Chunk Network）之圖論建構法則

設全庫有效區塊之 L2 正規化嵌入矩陣為 $E \in \mathbb{R}^{N \times 768}$，則兩兩餘弦相似度矩陣為 $S = E E^T \in [-1, 1]^{N \times N}$。為避免「毛球效應（Hairball Effect）」與「同篇自戀效應（Intra-Paper Self-Clustering）」，網路圖之邊集 $\mathcal{E}$ 依下列法則建構：

1. **同篇與跨篇連線分離（Cross-Paper vs. Intra-Paper Separation）：**
   - **跨篇邊（Cross-Paper Edge）：** 連接兩篇不同論文之區塊（$\text{Paper}(i) \neq \text{Paper}(j)$），代表真正的跨文獻語意共鳴，於互動網路圖中以**高對比實線**優先呈現。
   - **同篇邊（Intra-Paper Edge）：** 連接同一篇論文內部之區塊（$\text{Paper}(i) = \text{Paper}(j)$），預設隱藏或僅於切換開關時以淡灰虛線顯示。
2. **每個節點 Top-$K$ 跨篇最近鄰稀疏化（Mutual / Top-$K$ Cross-Paper Sparsification）：**
   - 對每個區塊 $i$，僅在 $\text{Paper}(j) \neq \text{Paper}(i)$ 且 $S_{ij} \ge \tau_{\min}$ 的候選區塊中，保留相似度最高的前 $K$ 條邊（預設 $K=3, \tau_{\min}=0.70$），確保網路圖結構清晰、群落分明且瀏覽器 60 FPS 流暢互動。
3. **三大圖論拓撲角色判讀（Topological Roles for Literature Review）：**
   - **共鳴樞紐區塊（Hub Chunks — 高跨篇度數中心性 Cross-Paper Degree Centrality）：** 與最多不同論文產生高相似連結的區塊，代表該領域的核心共識命題或標準方法。
   - **跨界橋樑邊（Boundary-Spanning Edges — 連接不同 Topic 之高相似邊）：** 兩端節點分屬不同 BERTopic 主題（$\text{Topic}(i) \neq \text{Topic}(j)$）卻具備高語意相似度，是撰寫第八週「跨概念交織段落」的黃金線索。
   - **結構洞（Structural Holes，Burt, 1992）：** 兩個規模龐大且皆與 `PROJECT.md` 研究問題相關的主題群集之間，若跨群連線密度極低（Inter-Topic Density $\approx 0$），即構成圖論上的「結構洞」，為第九週鎖定 **「跨領域/跨機制學術空白（Research Gap）」** 提供最直觀的拓撲證據。

---

## 四、學理基礎與經典參考文獻（APA 7th）

- **Burt, R. S. (1992).** *Structural holes: The social structure of competition*. Harvard University Press.
- **Campello, R. J., Moulavi, D., & Sander, J. (2013).** Density-based clustering based on hierarchical density estimates. In *Advances in Knowledge Discovery and Data Mining (PAKDD 2013)* (pp. 160–172). Springer. https://doi.org/10.1007/978-3-642-37456-2_14
- **Grootendorst, M. (2022).** BERTopic: Neural topic modeling with a class-based TF-IDF procedure. *arXiv preprint arXiv:2203.05794*. https://doi.org/10.48550/arXiv.2203.05794
- **McInnes, L., Healy, J., & Melville, J. (2018).** UMAP: Uniform manifold approximation and projection for dimension reduction. *arXiv preprint arXiv:1802.03426*. https://doi.org/10.48550/arXiv.1802.03426
