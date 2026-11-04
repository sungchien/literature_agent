#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全庫語意區塊主題建模 (BERTopic) 與跨篇相似度互動網路圖建置工具 (build_topic_network.py)

功能：
1. build    : 直接讀取第五週產出之 01_papers/vector_index.json 與 01_papers/vector_embeddings.npz (768 維向量)，
              執行首頁機構雜訊過濾、BERTopic 五階段主題建模（流形降維 -> HDBSCAN 密度聚類 -> 離群值收斂 ->
              Bigram CountVectorizer -> Class-based TF-IDF）、計算兩兩餘弦相似度矩陣 S = E * E^T，
              輸出：
              - 01_papers/topic_network_stats.json (完整主題、論文×主題矩陣、跨篇橋樑與結構洞統計數據)
              - 02_notes/topic_chunk_network.html  (自包含互動式跨篇語意區塊網路圖工作台)
              - 02_notes/topic_landscape.md        (可選 --init-report 自動生成結構化主題版圖報告初稿)
2. validate : 驗證 02_notes/topic_landscape.md 是否符合第七週標準 Schema 規範。

用法：
  python skills/topic_network_explorer/scripts/build_topic_network.py build
  python skills/topic_network_explorer/scripts/build_topic_network.py build --init-report
  python skills/topic_network_explorer/scripts/build_topic_network.py validate 02_notes/topic_landscape.md
"""

import os
import re
import sys
import json
import math
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import numpy as np

# 解決 Windows 終端機 UTF-8 編碼問題
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 學術通用結構停用詞與出版商雜訊停用詞（結合英文標準停用詞）
ACADEMIC_EXTRA_STOPWORDS = {
    "et", "al", "fig", "figure", "table", "section", "paper", "study", "studies",
    "research", "results", "result", "however", "also", "using", "used", "use",
    "based", "approach", "method", "methods", "proposed", "show", "shown", "shows",
    "can", "may", "would", "could", "one", "two", "three", "four", "first", "second",
    "new", "different", "various", "specific", "particular", "example", "eg", "ie",
    "university", "department", "school", "institute", "college", "faculty", "center",
    "centre", "laboratory", "lab", "usa", "uk", "india", "china", "germany", "france",
    "australia", "canada", "elsevier", "springer", "ieee", "acm", "wiley", "taylor",
    "francis", "mdpi", "arxiv", "preprint", "doi", "http", "https", "org", "com",
    "www", "copyright", "license", "creative", "commons", "author", "authors",
    "corresponding", "email", "address", "received", "accepted", "published", "available",
    "online", "journal", "volume", "issue", "pp", "pages", "page", "article", "info",
    "abstract", "introduction", "conclusion", "conclusions", "discussion", "acknowledge",
    "acknowledgements", "references", "supplementary", "appendix", "data", "set",
    "zhang", "wang", "chen", "liu", "lee", "kim", "smith", "dwivedi", "kasneci",
    "kshirsagar", "chintalapudi", "yang", "wu", "zhao", "huang", "zhou", "xu"
}

REQUIRED_FRONTMATTER_FIELDS = [
    "type", "landscape_version", "project_title",
    "total_papers", "total_chunks", "valid_chunks",
    "topic_count", "network_html", "stats_json", "created_date"
]

REQUIRED_SECTIONS = [
    (1, "全庫語意區塊建模總覽"),
    (2, "論文 × 主題權重分佈矩陣"),
    (3, "跨篇語意橋樑剖析"),
    (4, "網路拓撲"),
]


def find_workspace_root() -> Path:
    current = Path.cwd()
    for p in [current, current.parent, current.parent.parent, current.parent.parent.parent]:
        if (p / "01_papers").exists() or (p / "PROJECT.md").exists():
            return p
    return current


def is_affiliation_or_meta_noise(chunk: dict) -> bool:
    """
    檢測是否為首頁作者機構名單、版權聲明或過短殘渣區塊，避免污染 BERTopic 主題與相似度網路。
    """
    text = chunk.get("text", "")
    sec = chunk.get("section", "").lower()
    words = re.findall(r"[a-zA-Z]{2,}", text.lower())
    if len(words) < 25:
        return True

    # 計算機構與出版商雜訊密度
    affil_keywords = {
        "university", "department", "school", "institute", "faculty", "college",
        "elsevier", "creative", "commons", "corresponding", "campus", "avenue",
        "street", "boulevard", "kingdom", "states", "republic"
    }
    affil_hits = sum(1 for w in words if w in affil_keywords)
    affil_ratio = affil_hits / max(len(words), 1)

    if affil_ratio > 0.085:
        return True
    if ("page 1" in sec or "page 2" in sec) and affil_hits >= 12:
        return True

    # 檢測文末純參考文獻列表區塊 (Reference List Chunks)，避免書目清單產生假性語意連線
    doi_or_url_hits = len(re.findall(r"(doi\.org|https?://|arxiv preprint)", text.lower()))
    if doi_or_url_hits >= 5:
        return True

    return False


def run_bertopic_pipeline(
    texts: list,
    embeddings: np.ndarray,
    target_topics: int = 6,
    min_cluster_size: int = 18
) -> tuple:
    """
    執行標準 BERTopic 五階段計算管線（Grootendorst, 2022）：
    Stage 1: Pre-computed L2-normalized Dense Embeddings (768-dim BAAI/bge-base-en-v1.5)
    Stage 2: Manifold Dimensionality Reduction (UMAP if installed, else Spectral/SVD Manifold Projection)
    Stage 3: Density-Based Clustering (HDBSCAN) + Embedding Centroid Outlier Reduction (將 -1 離群區塊收斂至最近主題)
    Stage 4: Bigram CountVectorizer (ngram_range=(1, 2), 移除學術結構與機構停用詞)
    Stage 5: Class-based TF-IDF (c-TF-IDF: W_{t,c} = tf_{t,c} * log(1 + A / tf_t))
    """
    from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
    from sklearn.decomposition import TruncatedSVD
    from sklearn.preprocessing import normalize

    n_samples = len(texts)
    emb_norm = normalize(embeddings.astype(np.float32), norm="l2")

    # Stage 2: 降維 (優先嘗試 UMAP，若無則使用 TruncatedSVD 保留局部與全局流形結構)
    dim_method = "UMAP (5-dim)"
    reducer = None
    try:
        import warnings
        import umap
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reducer = umap.UMAP(
                n_neighbors=15,
                n_components=min(5, n_samples - 2),
                min_dist=0.0,
                metric="cosine",
                random_state=42
            )
            reduced_emb = reducer.fit_transform(emb_norm)
    except Exception:
        dim_method = "TruncatedSVD-Manifold (12-dim)"
        n_comp = min(12, n_samples - 1)
        svd = TruncatedSVD(n_components=n_comp, random_state=42)
        reduced_emb = normalize(svd.fit_transform(emb_norm), norm="l2")

    # Stage 3: 優先調用官方 BERTopic 套件 (若已安裝)，否則使用原生 HDBSCAN + c-TF-IDF 管線
    cluster_method = "HDBSCAN + Embedding Outlier Reduction"
    raw_labels = None
    try:
        import warnings
        from bertopic import BERTopic
        from bertopic.vectorizers import ClassTfidfTransformer
        from sklearn.cluster import HDBSCAN as SklearnHDBSCAN
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            stop_words_bt = list(ENGLISH_STOP_WORDS.union(ACADEMIC_EXTRA_STOPWORDS))
            vec_bt = CountVectorizer(
                ngram_range=(1, 2),
                stop_words=stop_words_bt,
                min_df=2,
                max_features=4000,
                token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]{2,}\b"
            )
            hdb_bt = SklearnHDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=4,
                metric="euclidean",
                cluster_selection_method="eom"
            )
            ctfidf_bt = ClassTfidfTransformer(bm25_weighting=False, reduce_frequent_words=True)
            topic_model = BERTopic(
                umap_model=reducer if reducer is not None else None,
                hdbscan_model=hdb_bt,
                vectorizer_model=vec_bt,
                ctfidf_model=ctfidf_bt,
                calculate_probabilities=False,
                verbose=False
            )
            bt_topics, _ = topic_model.fit_transform(texts, embeddings=emb_norm)
            raw_labels = np.array(bt_topics, dtype=int)
            cluster_method = "Official BERTopic (UMAP + HDBSCAN + c-TF-IDF)"
    except Exception:
        try:
            import warnings
            from sklearn.cluster import HDBSCAN as SklearnHDBSCAN
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                hdb = SklearnHDBSCAN(
                    min_cluster_size=min_cluster_size,
                    min_samples=4,
                    metric="euclidean",
                    cluster_selection_method="eom"
                )
                raw_labels = hdb.fit_predict(reduced_emb)
        except Exception:
            raw_labels = None

    unique_valid = set(raw_labels) - {-1} if raw_labels is not None else set()

    # 若 HDBSCAN 分出之主題數過少 (< 4)，使用 L2 正規化向量之 Ward 階層聚類；若過多 (> 9)，將小主題合併為 target_topics
    if len(unique_valid) < 4:
        from sklearn.cluster import AgglomerativeClustering
        cluster_method = f"L2-Normalized Ward Hierarchical Clustering (k={target_topics})"
        agg = AgglomerativeClustering(
            n_clusters=min(target_topics, n_samples),
            metric="euclidean",
            linkage="ward"
        )
        labels = agg.fit_predict(emb_norm)
        outlier_count = 0
    else:
        labels = raw_labels.copy()
        outlier_count = int(np.sum(labels == -1))
        valid_topic_ids = sorted(unique_valid)
        # 若主題簇超過 8 個，保留前 target_topics 個最大主題簇，其餘歸入離群收斂
        if len(valid_topic_ids) > 8:
            t_DynamicCounts = [(tid, int(np.sum(labels == tid))) for tid in valid_topic_ids]
            t_DynamicCounts.sort(key=lambda x: -x[1])
            keep_tids = {tid for tid, _ in t_DynamicCounts[:target_topics]}
            for idx in range(n_samples):
                if labels[idx] not in keep_tids:
                    labels[idx] = -1
            valid_topic_ids = sorted(keep_tids)
        # 計算各有效主題之中心向量 (Centroids)
        centroids = np.vstack([
            normalize(emb_norm[labels == tid].mean(axis=0, keepdims=True), norm="l2")[0]
            for tid in valid_topic_ids
        ])
        # 將 -1 離群區塊依餘弦相似度歸併至最近的主題中心 (對應 BERTopic reduce_outliers(strategy="embeddings"))
        for idx in range(n_samples):
            if labels[idx] == -1:
                sims = np.dot(centroids, emb_norm[idx])
                best_tid = valid_topic_ids[int(np.argmax(sims))]
                labels[idx] = best_tid

    # 重新依主題區塊數量由大到小編號為 Topic 0, Topic 1, Topic 2...
    unique_tids, counts = np.unique(labels, return_counts=True)
    sorted_order = np.argsort(-counts)
    remap = {int(unique_tids[old_i]): int(new_i) for new_i, old_i in enumerate(sorted_order)}
    final_labels = np.array([remap[int(x)] for x in labels], dtype=int)
    n_topics = len(unique_tids)

    # Stage 4: 將同一 Topic 之所有 Chunks 合併為單一類別文檔 (Class Document)，執行 Bigram CountVectorizer
    stop_words = list(ENGLISH_STOP_WORDS.union(ACADEMIC_EXTRA_STOPWORDS))
    class_docs = []
    for tid in range(n_topics):
        topic_texts = [texts[i] for i in range(n_samples) if final_labels[i] == tid]
        class_docs.append(" ".join(topic_texts))

    vectorizer = CountVectorizer(
        ngram_range=(1, 2),
        stop_words=stop_words,
        min_df=2 if n_topics >= 3 else 1,
        max_features=4000,
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]{2,}\b"
    )
    X_counts = vectorizer.fit_transform(class_docs).toarray().astype(np.float64)  # (n_topics, n_vocab)
    vocab = np.array(vectorizer.get_feature_names_out())

    # Stage 5: 計算 Grootendorst (2022) Class-based TF-IDF (c-TF-IDF)
    # W_{t, c} = tf_{t, c} * log(1 + A / tf_t)
    cluster_word_totals = X_counts.sum(axis=1, keepdims=True)
    tf_tc = X_counts / np.maximum(cluster_word_totals, 1.0)
    tf_t = X_counts.sum(axis=0, keepdims=True)  # 每個詞在所有類別的總出現次數
    avg_words_per_class = float(cluster_word_totals.mean())
    idf_t = np.log(1.0 + (avg_words_per_class / np.maximum(tf_t, 1.0)))
    c_tf_idf = tf_tc * idf_t  # (n_topics, n_vocab)

    # 提取每個 Topic 的 Top Keywords 與中心代表性 Chunks
    topics_info = []
    topic_centroids = []
    for tid in range(n_topics):
        idxs = np.where(final_labels == tid)[0]
        centroid = normalize(emb_norm[idxs].mean(axis=0, keepdims=True), norm="l2")[0]
        topic_centroids.append(centroid)

        # 取 c-TF-IDF 最高的前 12 個關鍵字詞（避免單複數完全重疊）
        scores = c_tf_idf[tid]
        top_v_idxs = np.argsort(-scores)
        top_keywords = []
        for v_i in top_v_idxs:
            term = str(vocab[v_i])
            score = round(float(scores[v_i]), 4)
            if any(term in existing or existing in term for existing, _ in top_keywords[:5]):
                if len(top_keywords) < 6:
                    continue
            top_keywords.append((term, score))
            if len(top_keywords) >= 10:
                break

        # 找出與該 Topic 中心向量餘弦相似度最高的前 3 個代表性 Chunks
        sims_to_center = np.dot(emb_norm[idxs], centroid)
        rep_order = np.argsort(-sims_to_center)[:3]
        rep_chunk_indices = [int(idxs[r]) for r in rep_order]

        short_label = " / ".join(k for k, _ in top_keywords[:3])
        topics_info.append({
            "topic_id": tid,
            "name": f"Topic {tid}: {short_label}",
            "short_label": short_label,
            "chunk_count": int(len(idxs)),
            "keywords": [{"term": k, "c_tfidf": s} for k, s in top_keywords],
            "representative_indices": rep_chunk_indices,
        })

    pipeline_meta = {
        "dim_reduction": dim_method,
        "clustering": cluster_method,
        "initial_outliers_merged": outlier_count,
        "c_tfidf_avg_words_A": round(avg_words_per_class, 1),
    }
    return final_labels, topics_info, emb_norm, np.vstack(topic_centroids), pipeline_meta


def generate_interactive_html(
    output_html_path: Path,
    nodes_data: list,
    edges_data: list,
    topics_data: list,
    papers_list: list,
    meta_info: dict
):
    """
    生成自包含、免外部伺服器依賴的「跨篇語意區塊互動網路圖工作台 (topic_chunk_network.html)」。
    採用護眼書卷淺色主題与 HTML5 Canvas 物理力導向圖 (Force-Directed Graph)，支援：
    - 相似度門檻滑桿 (Threshold Slider)
    - 僅顯示跨篇連線開關 (Cross-Paper Edges Only)
    - 突顯跨主題橋樑邊開關 (Highlight Inter-Topic Bridges)
    - 主題篩選、論文篩選與關鍵字即時搜尋
    - 節點點擊右側「跨篇段落對照閱讀器」
    """
    payload_json = json.dumps({
        "meta": meta_info,
        "topics": topics_data,
        "papers": papers_list,
        "nodes": nodes_data,
        "edges": edges_data
    }, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>跨篇語意區塊互動網路圖與 BERTopic 主題工作台</title>
<style>
  :root {{
    --bg-main: #fbfbfa;
    --bg-panel: #ffffff;
    --bg-sidebar: #f1f5f9;
    --text-primary: #0f172a;
    --text-secondary: #334155;
    --text-muted: #64748b;
    --border-color: #cbd5e1;
    --accent: #2563eb;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "Segoe UI", "Microsoft JhengHei", sans-serif;
    background-color: var(--bg-main);
    color: var(--text-primary);
    display: flex;
    height: 100vh;
    overflow: hidden;
  }}
  #sidebar-left {{
    width: 320px;
    background: var(--bg-sidebar);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    padding: 16px;
    overflow-y: auto;
    gap: 14px;
  }}
  #canvas-container {{
    flex: 1;
    position: relative;
    background: radial-gradient(circle at center, #ffffff 0%, #f4f4f0 100%);
    overflow: hidden;
  }}
  #network-canvas {{
    width: 100%;
    height: 100%;
    cursor: grab;
    display: block;
  }}
  #network-canvas:active {{ cursor: grabbing; }}
  #sidebar-right {{
    width: 400px;
    background: var(--bg-panel);
    border-left: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    padding: 18px;
    overflow-y: auto;
    gap: 14px;
  }}
  h1 {{ font-size: 16px; font-weight: 700; color: var(--text-primary); line-height: 1.4; }}
  h2 {{ font-size: 14px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }}
  .control-box {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  }}
  .control-label {{
    font-size: 12.5px;
    font-weight: 600;
    color: var(--text-secondary);
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
  }}
  input[type="range"] {{ width: 100%; cursor: pointer; }}
  input[type="text"], select {{
    width: 100%;
    padding: 7px 10px;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 13px;
    background: #ffffff;
    color: var(--text-primary);
  }}
  .checkbox-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 6px;
    cursor: pointer;
  }}
  .topic-legend-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border-radius: 6px;
    font-size: 12.5px;
    cursor: pointer;
    transition: background 0.15s;
  }}
  .topic-legend-item:hover {{ background: #e2e8f0; }}
  .color-dot {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
  }}
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    font-size: 11.5px;
    font-weight: 600;
    border-radius: 12px;
    background: #e2e8f0;
    color: #1e293b;
  }}
  .chunk-card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid var(--accent);
    border-radius: 6px;
    padding: 10px 12px;
    font-size: 12.5px;
    line-height: 1.55;
    margin-bottom: 10px;
  }}
  .chunk-meta {{
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
    display: flex;
    justify-content: space-between;
  }}
  .chunk-text {{
    color: #334155;
    max-height: 160px;
    overflow-y: auto;
    white-space: pre-wrap;
  }}
  #hud-bar {{
    position: absolute;
    top: 12px;
    left: 12px;
    background: rgba(255,255,255,0.92);
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12.5px;
    color: #334155;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    pointer-events: none;
  }}
  #btn-bar {{
    display: flex;
    gap: 6px;
    margin-top: 8px;
  }}
  button {{
    flex: 1;
    padding: 6px 10px;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    color: #1e293b;
    cursor: pointer;
  }}
  button:hover {{ background: #f1f5f9; border-color: #94a3b8; }}
  #tooltip {{
    position: absolute;
    display: none;
    background: rgba(15, 23, 42, 0.94);
    color: #f8fafc;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
    max-width: 320px;
    pointer-events: none;
    z-index: 20;
    line-height: 1.45;
  }}
</style>
</head>
<body>

<div id="sidebar-left">
  <div>
    <h1>BERTopic 主題與跨篇區塊網路工作台</h1>
    <div style="font-size:12px; color:#64748b; margin-top:4px;">
      論文數：<strong id="stat-papers">0</strong> 篇 | 有效區塊：<strong id="stat-nodes">0</strong> 個
    </div>
  </div>

  <div class="control-box">
    <h2>1. 網路拓撲過濾控制</h2>
    <div class="control-label">
      <span>餘弦相似度門檻 (&tau;)</span>
      <strong id="threshold-val">0.72</strong>
    </div>
    <input type="range" id="threshold-slider" min="0.64" max="0.88" step="0.01" value="0.72">

    <label class="checkbox-row">
      <input type="checkbox" id="cross-paper-only" checked>
      <span>僅顯示「跨篇語意連線」(不同論文)</span>
    </label>
    <label class="checkbox-row">
      <input type="checkbox" id="highlight-bridges">
      <span>突顯「跨主題橋樑邊」(不同 Topic)</span>
    </label>
    <div id="btn-bar">
      <button id="btn-reset-view">重置視角</button>
      <button id="btn-toggle-physics">暫停/啟動物理擺動</button>
    </div>
  </div>

  <div class="control-box">
    <h2>2. 語意主題與論文篩選</h2>
    <div class="control-label"><span>篩選 BERTopic 主題簇</span></div>
    <select id="topic-select">
      <option value="ALL">顯示全部主題簇 (All Topics)</option>
    </select>

    <div class="control-label" style="margin-top:10px;"><span>篩選特定論文 (Paper Filter)</span></div>
    <select id="paper-select">
      <option value="ALL">顯示全部論文 (All Papers)</option>
    </select>

    <div class="control-label" style="margin-top:10px;"><span>區塊內容關鍵字定位</span></div>
    <input type="text" id="search-input" placeholder="輸入英文詞彙 (如 cognitive load)...">
  </div>

  <div class="control-box">
    <h2>3. BERTopic 主題圖例 (點擊過濾)</h2>
    <div id="topic-legend-list"></div>
  </div>
</div>

<div id="canvas-container">
  <canvas id="network-canvas"></canvas>
  <div id="hud-bar">
    可見節點：<strong id="hud-nodes">0</strong> | 可見連線：<strong id="hud-edges">0</strong> (跨篇橋樑：<strong id="hud-cross">0</strong>) | 操作：滾輪縮放、拖曳畫布或節點、點擊節點檢視跨篇共鳴段落
  </div>
  <div id="tooltip"></div>
</div>

<div id="sidebar-right">
  <div>
    <h1>跨篇段落對照閱讀器 (Chunk Inspector)</h1>
    <div style="font-size:12px; color:#64748b; margin-top:2px;">點擊左側畫布任一區塊節點，即可並排檢視跨篇相似段落</div>
  </div>
  <div id="inspector-content">
    <div class="control-box" style="color:#64748b; font-size:13px; line-height:1.6;">
      [指引] 請在中間網路圖點擊任一圓點節點：<br>
      1. 圓點顏色代表 <strong>BERTopic 主題簇</strong>。<br>
      2. 圓點大小代表 <strong>跨篇語意樞紐度 (Cross-Paper Degree)</strong>，越大顆代表與越多不同論文產生高相似度共鳴。<br>
      3. 實線代表 <strong>跨篇語意橋樑</strong>，虛線代表同篇內部連線。
    </div>
  </div>
</div>

<script>
const DATA = {payload_json};
const PALETTE = [
  "#2563eb", "#d97706", "#059669", "#dc2626",
  "#7c3aed", "#0891b2", "#be185d", "#4f46e5",
  "#65a30d", "#b45309"
];

document.getElementById("stat-papers").textContent = DATA.papers.length;
document.getElementById("stat-nodes").textContent = DATA.nodes.length;

const topicSelect = document.getElementById("topic-select");
const legendList = document.getElementById("topic-legend-list");
DATA.topics.forEach((t, i) => {{
  const color = PALETTE[i % PALETTE.length];
  t.color = color;
  const opt = document.createElement("option");
  opt.value = String(t.topic_id);
  opt.textContent = `Topic ${{t.topic_id}} (${{t.chunk_count}} 塊): ${{t.short_label}}`;
  topicSelect.appendChild(opt);

  const item = document.createElement("div");
  item.className = "topic-legend-item";
  item.innerHTML = `<span class="color-dot" style="background:${{color}}"></span>
    <div style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
      <strong>T${{t.topic_id}}</strong>: ${{t.short_label}} <span style="color:#64748b">(${{t.chunk_count}})</span>
    </div>`;
  item.onclick = () => {{
    topicSelect.value = topicSelect.value === String(t.topic_id) ? "ALL" : String(t.topic_id);
    updateFilters();
  }};
  legendList.appendChild(item);
}});

const paperSelect = document.getElementById("paper-select");
DATA.papers.forEach(p => {{
  const opt = document.createElement("option");
  opt.value = p;
  opt.textContent = p.length > 42 ? p.slice(0, 42) + "..." : p;
  paperSelect.appendChild(opt);
}});

const canvas = document.getElementById("network-canvas");
const ctx = canvas.getContext("2d");
const tooltip = document.getElementById("tooltip");

let width = 800, height = 600;
function resizeCanvas() {{
  const rect = canvas.parentElement.getBoundingClientRect();
  width = rect.width;
  height = rect.height;
  canvas.width = width * window.devicePixelRatio;
  canvas.height = height * window.devicePixelRatio;
  ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
}}
window.addEventListener("resize", resizeCanvas);
resizeCanvas();

// 初始化節點座標（依 Topic 分群環狀散佈，加速物理收斂）
const numTopics = Math.max(DATA.topics.length, 1);
const nodeMap = new Map();
DATA.nodes.forEach((n, idx) => {{
  const angle = (2 * Math.PI * n.topic) / numTopics + (Math.random() - 0.5) * 0.65;
  const radius = 160 + Math.random() * 110;
  n.x = width / 2 + Math.cos(angle) * radius;
  n.y = height / 2 + Math.sin(angle) * radius;
  n.vx = 0;
  n.vy = 0;
  n.radius = Math.min(14, Math.max(4.5, 4.5 + Math.sqrt(n.cross_degree || 0) * 1.4));
  n.color = PALETTE[n.topic % PALETTE.length];
  nodeMap.set(n.id, n);
}});

let camera = {{ x: 0, y: 0, k: 1.0 }};
let physicsEnabled = true;
let selectedNode = null;
let hoveredNode = null;
let draggingNode = null;
let isPanning = false;
let panStart = {{ x: 0, y: 0 }};

let activeNodes = [];
let activeEdges = [];

function updateFilters() {{
  const tau = parseFloat(document.getElementById("threshold-slider").value);
  document.getElementById("threshold-val").textContent = tau.toFixed(2);
  const crossOnly = document.getElementById("cross-paper-only").checked;
  const topicFilter = topicSelect.value;
  const paperFilter = paperSelect.value;
  const query = document.getElementById("search-input").value.trim().toLowerCase();

  const visibleSet = new Set();
  activeNodes = DATA.nodes.filter(n => {{
    if (topicFilter !== "ALL" && String(n.topic) !== topicFilter) return false;
    if (paperFilter !== "ALL" && n.paper !== paperFilter) return false;
    n.matched = query ? (n.text.toLowerCase().includes(query) || n.section.toLowerCase().includes(query)) : false;
    visibleSet.add(n.id);
    return true;
  }});

  let crossCount = 0;
  activeEdges = DATA.edges.filter(e => {{
    if (e.sim < tau) return false;
    if (crossOnly && !e.cross_paper) return false;
    if (!visibleSet.has(e.source) || !visibleSet.has(e.target)) return false;
    if (e.cross_paper) crossCount++;
    return true;
  }});

  document.getElementById("hud-nodes").textContent = activeNodes.length;
  document.getElementById("hud-edges").textContent = activeEdges.length;
  document.getElementById("hud-cross").textContent = crossCount;
}}

document.getElementById("threshold-slider").addEventListener("input", updateFilters);
document.getElementById("cross-paper-only").addEventListener("change", updateFilters);
document.getElementById("highlight-bridges").addEventListener("change", updateFilters);
topicSelect.addEventListener("change", updateFilters);
paperSelect.addEventListener("change", updateFilters);
document.getElementById("search-input").addEventListener("input", updateFilters);

document.getElementById("btn-reset-view").onclick = () => {{
  camera = {{ x: 0, y: 0, k: 1.0 }};
}};
document.getElementById("btn-toggle-physics").onclick = () => {{
  physicsEnabled = !physicsEnabled;
}};

function stepPhysics() {{
  if (!physicsEnabled) return;
  const N = activeNodes.length;
  // 主題群聚引力與中心引力
  for (let i = 0; i < N; i++) {{
    const a = activeNodes[i];
    if (a === draggingNode) continue;
    const targetAngle = (2 * Math.PI * a.topic) / numTopics;
    const tx = width / 2 + Math.cos(targetAngle) * 180;
    const ty = height / 2 + Math.sin(targetAngle) * 180;
    a.vx += (tx - a.x) * 0.004;
    a.vy += (ty - a.y) * 0.004;
  }}
  // 節點斥力 (局部採樣加速，確保 700+ 節點 60fps 流暢運行)
  for (let i = 0; i < N; i++) {{
    const a = activeNodes[i];
    for (let j = i + 1; j < N; j++) {{
      const b = activeNodes[j];
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const d2 = dx * dx + dy * dy;
      if (d2 > 3600 || d2 === 0) continue;
      const d = Math.sqrt(d2);
      const force = 28 / d2;
      const fx = dx * force;
      const fy = dy * force;
      if (a !== draggingNode) {{ a.vx -= fx; a.vy -= fy; }}
      if (b !== draggingNode) {{ b.vx += fx; b.vy += fy; }}
    }}
  }}
  // 連線彈簧引力
  for (let i = 0; i < activeEdges.length; i++) {{
    const e = activeEdges[i];
    const s = nodeMap.get(e.source);
    const t = nodeMap.get(e.target);
    if (!s || !t) continue;
    const dx = t.x - s.x;
    const dy = t.y - s.y;
    const d = Math.sqrt(dx * dx + dy * dy) || 1;
    const ideal = e.cross_topic ? 150 : 65;
    const f = (d - ideal) * 0.006;
    const fx = (dx / d) * f;
    const fy = (dy / d) * f;
    if (s !== draggingNode) {{ s.vx += fx; s.vy += fy; }}
    if (t !== draggingNode) {{ t.vx -= fx; t.vy -= fy; }}
  }}
  for (let i = 0; i < N; i++) {{
    const a = activeNodes[i];
    if (a === draggingNode) continue;
    a.vx *= 0.78;
    a.vy *= 0.78;
    a.x += a.vx;
    a.y += a.vy;
  }}
}}

function render() {{
  stepPhysics();
  ctx.clearRect(0, 0, width, height);
  ctx.save();
  ctx.translate(camera.x, camera.y);
  ctx.scale(camera.k, camera.k);

  const highlightBridges = document.getElementById("highlight-bridges").checked;

  // 繪製連線
  for (let i = 0; i < activeEdges.length; i++) {{
    const e = activeEdges[i];
    const s = nodeMap.get(e.source);
    const t = nodeMap.get(e.target);
    if (!s || !t) continue;

    const isSelectedEdge = selectedNode && (s.id === selectedNode.id || t.id === selectedNode.id);
    ctx.beginPath();
    if (!e.cross_paper) {{
      ctx.setLineDash([3, 3]);
    }} else {{
      ctx.setLineDash([]);
    }}
    ctx.moveTo(s.x, s.y);
    ctx.lineTo(t.x, t.y);

    if (isSelectedEdge) {{
      ctx.strokeStyle = "#dc2626";
      ctx.lineWidth = 2.2 / camera.k;
    }} else if (highlightBridges && e.cross_topic) {{
      ctx.strokeStyle = "rgba(217, 119, 6, 0.72)";
      ctx.lineWidth = 1.6 / camera.k;
    }} else {{
      const alpha = Math.min(0.65, Math.max(0.12, (e.sim - 0.65) * 2.5));
      ctx.strokeStyle = `rgba(100, 116, 139, ${{alpha}})`;
      ctx.lineWidth = 1.0 / camera.k;
    }}
    ctx.stroke();
  }}
  ctx.setLineDash([]);

  // 繪製節點
  for (let i = 0; i < activeNodes.length; i++) {{
    const n = activeNodes[i];
    ctx.beginPath();
    const r = n.matched ? n.radius * 1.6 : n.radius;
    ctx.arc(n.x, n.y, r, 0, 2 * Math.PI);
    ctx.fillStyle = n.color;
    ctx.fill();

    if (n === selectedNode || n === hoveredNode || n.matched) {{
      ctx.lineWidth = 2.5 / camera.k;
      ctx.strokeStyle = n.matched ? "#f59e0b" : "#0f172a";
      ctx.stroke();
    }} else {{
      ctx.lineWidth = 1.0 / camera.k;
      ctx.strokeStyle = "#ffffff";
      ctx.stroke();
    }}

    if (camera.k > 1.35 || n === selectedNode || n.matched) {{
      ctx.fillStyle = "#0f172a";
      ctx.font = `${{Math.max(9, 11 / camera.k)}}px Segoe UI`;
      ctx.fillText(n.short_id, n.x + r + 3, n.y + 3);
    }}
  }}

  ctx.restore();
  requestAnimationFrame(render);
}}

function screenToWorld(sx, sy) {{
  return {{
    x: (sx - camera.x) / camera.k,
    y: (sy - camera.y) / camera.k
  }};
}}

function findNodeAt(wx, wy) {{
  for (let i = activeNodes.length - 1; i >= 0; i--) {{
    const n = activeNodes[i];
    const dx = n.x - wx;
    const dy = n.y - wy;
    if (dx * dx + dy * dy <= (n.radius + 3) * (n.radius + 3)) return n;
  }}
  return null;
}}

canvas.addEventListener("mousemove", ev => {{
  const rect = canvas.getBoundingClientRect();
  const sx = ev.clientX - rect.left;
  const sy = ev.clientY - rect.top;
  const w = screenToWorld(sx, sy);

  if (draggingNode) {{
    draggingNode.x = w.x;
    draggingNode.y = w.y;
    return;
  }}
  if (isPanning) {{
    camera.x += ev.clientX - panStart.x;
    camera.y += ev.clientY - panStart.y;
    panStart = {{ x: ev.clientX, y: ev.clientY }};
    return;
  }}

  const hit = findNodeAt(w.x, w.y);
  hoveredNode = hit;
  if (hit) {{
    canvas.style.cursor = "pointer";
    tooltip.style.display = "block";
    tooltip.style.left = (sx + 14) + "px";
    tooltip.style.top = (sy + 14) + "px";
    tooltip.innerHTML = `<strong>${{hit.id}}</strong><br>
      主題：Topic ${{hit.topic}} (${{DATA.topics[hit.topic]?.short_label || ""}})<br>
      章節：${{hit.section}}<br>
      跨篇高相似連線：${{hit.cross_degree}} 條`;
  }} else {{
    canvas.style.cursor = "grab";
    tooltip.style.display = "none";
  }}
}});

canvas.addEventListener("mousedown", ev => {{
  const rect = canvas.getBoundingClientRect();
  const w = screenToWorld(ev.clientX - rect.left, ev.clientY - rect.top);
  const hit = findNodeAt(w.x, w.y);
  if (hit) {{
    draggingNode = hit;
    selectNode(hit);
  }} else {{
    isPanning = true;
    panStart = {{ x: ev.clientX, y: ev.clientY }};
  }}
}});

window.addEventListener("mouseup", () => {{
  draggingNode = null;
  isPanning = false;
}});

canvas.addEventListener("wheel", ev => {{
  ev.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const sx = ev.clientX - rect.left;
  const sy = ev.clientY - rect.top;
  const zoom = ev.deltaY < 0 ? 1.12 : 0.89;
  const nextK = Math.min(5.0, Math.max(0.25, camera.k * zoom));
  camera.x = sx - (sx - camera.x) * (nextK / camera.k);
  camera.y = sy - (sy - camera.y) * (nextK / camera.k);
  camera.k = nextK;
}}, {{ passive: false }});

function selectNode(node) {{
  selectedNode = node;
  const tInfo = DATA.topics[node.topic] || {{ short_label: "", keywords: [] }};
  const kwHtml = (tInfo.keywords || []).slice(0, 6).map(k => `<span class="badge">${{k.term}}</span>`).join(" ");

  // 找出與此節點相連之跨篇相似段落
  const neighbors = [];
  DATA.edges.forEach(e => {{
    if (e.source === node.id) {{
      const other = nodeMap.get(e.target);
      if (other) neighbors.push({{ node: other, sim: e.sim, cross_paper: e.cross_paper }});
    }} else if (e.target === node.id) {{
      const other = nodeMap.get(e.source);
      if (other) neighbors.push({{ node: other, sim: e.sim, cross_paper: e.cross_paper }});
    }}
  }});
  neighbors.sort((a, b) => b.sim - a.sim);

  const crossNeighbors = neighbors.filter(x => x.cross_paper);
  const neighborCards = crossNeighbors.slice(0, 6).map(item => `
    <div class="chunk-card" style="border-left-color:${{item.node.color}}">
      <div class="chunk-meta">
        <span>${{item.node.id}}</span>
        <span class="badge">Cosine: ${{item.sim.toFixed(3)}} | T${{item.node.topic}}</span>
      </div>
      <div style="font-size:11.5px; color:#64748b; margin-bottom:4px;">
        論文：${{item.node.paper}} | 章節：${{item.node.section}}
      </div>
      <div class="chunk-text">${{item.node.text}}</div>
    </div>
  `).join("") || `<div style="font-size:12.5px; color:#64748b;">此區塊在目前門檻下無跨篇鄰居連線。</div>`;

  document.getElementById("inspector-content").innerHTML = `
    <div class="chunk-card" style="border-left-color:${{node.color}}; background:#ffffff;">
      <div class="chunk-meta">
        <span>[當前選取] ${{node.id}}</span>
        <span class="badge" style="background:${{node.color}}; color:#fff;">Topic ${{node.topic}}</span>
      </div>
      <div style="font-size:12px; color:#475569; margin:4px 0;">
        <strong>所屬論文：</strong>${{node.paper}}<br>
        <strong>所屬章節：</strong>${{node.section}}
      </div>
      <div style="margin:6px 0;">${{kwHtml}}</div>
      <div class="chunk-text" style="max-height:200px;">${{node.text}}</div>
    </div>
    <h2>跨篇高相似共鳴段落對照 (${{crossNeighbors.length}} 筆)</h2>
    ${{neighborCards}}
  `;
}}

updateFilters();
render();
</script>
</body>
</html>
"""
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    output_html_path.write_text(html_content, encoding="utf-8")


def cmd_build(args):
    root = find_workspace_root()
    index_path = root / "01_papers" / "vector_index.json"
    vec_path = root / "01_papers" / "vector_embeddings.npz"
    stats_out_path = root / "01_papers" / "topic_network_stats.json"
    html_out_path = root / "02_notes" / "topic_chunk_network.html"
    proj_path = root / "PROJECT.md"

    if not index_path.exists() or not vec_path.exists():
        print("[錯誤] 找不到 01_papers/vector_index.json 或 vector_embeddings.npz！")
        print("[指引] 請先執行第五週建庫腳本：python scripts/paper_retriever_mcp.py build")
        return 1

    payload = json.loads(index_path.read_text(encoding="utf-8"))
    all_chunks = payload.get("chunks", [])
    npz_data = np.load(vec_path)
    arr_key = "embeddings" if "embeddings" in npz_data else list(npz_data.keys())[0]
    all_embeddings = npz_data[arr_key]

    print("==================================================================")
    print("[資訊] 全庫語意區塊 BERTopic 主題建模與跨篇相似度網路建置工具")
    print("==================================================================")
    print(f"[載入] 原始論文區塊總數 : {len(all_chunks)} 個 | 向量維度 : {all_embeddings.shape}")

    valid_indices = []
    valid_chunks = []
    for idx, ch in enumerate(all_chunks):
        if idx >= len(all_embeddings):
            break
        if not is_affiliation_or_meta_noise(ch):
            valid_indices.append(idx)
            valid_chunks.append(ch)

    valid_emb = all_embeddings[valid_indices]
    texts = [c["text"] for c in valid_chunks]
    papers_set = sorted({c["file"] for c in valid_chunks})

    print(f"[過濾] 已排除首頁作者機構地址與短碎屑區塊 : {len(all_chunks) - len(valid_chunks)} 個")
    print(f"[建模] 納入有效學術語意區塊 : {len(valid_chunks)} 個 (涵蓋 {len(papers_set)} 篇論文)")

    labels, topics_info, emb_norm, topic_centroids, pipe_meta = run_bertopic_pipeline(
        texts=texts,
        embeddings=valid_emb,
        target_topics=args.topics,
        min_cluster_size=args.min_cluster_size
    )

    print(f"[成功] 完成 BERTopic 主題聚類與 c-TF-IDF 表徵提取！共識別出 {len(topics_info)} 個主題簇：")
    for t in topics_info:
        kws = ", ".join(k["term"] for k in t["keywords"][:6])
        print(f"   * Topic {t['topic_id']} ({t['chunk_count']:3d} 塊): [{kws}]")

    # 計算兩兩餘弦相似度矩陣 S = E * E^T
    sim_matrix = np.dot(emb_norm, emb_norm.T)
    n_valid = len(valid_chunks)

    # 為每個節點提取 Top-K 跨篇最近鄰邊與 Top-1 同篇邊
    edge_dict = {}
    cross_degree = defaultdict(int)
    inter_topic_pairs = defaultdict(int)
    top_cross_paper_bridges = []
    top_inter_topic_bridges = []

    min_sim = args.min_similarity
    top_k = args.top_k

    for i in range(n_valid):
        paper_i = valid_chunks[i]["file"]
        topic_i = int(labels[i])
        sims = sim_matrix[i]
        order = np.argsort(-sims)

        cross_added = 0
        intra_added = 0
        for j in order:
            if i == j:
                continue
            s_val = float(sims[j])
            if s_val < min_sim:
                break

            paper_j = valid_chunks[j]["file"]
            topic_j = int(labels[j])
            is_cross_paper = (paper_i != paper_j)
            is_cross_topic = (topic_i != topic_j)

            if is_cross_paper:
                if cross_added >= top_k:
                    continue
                cross_added += 1
            else:
                if intra_added >= 1 or s_val < 0.78:
                    continue
                intra_added += 1

            u, v = (i, int(j)) if i < j else (int(j), i)
            if (u, v) not in edge_dict:
                edge_obj = {
                    "u": u,
                    "v": v,
                    "source": valid_chunks[u]["chunk_id"],
                    "target": valid_chunks[v]["chunk_id"],
                    "sim": round(s_val, 4),
                    "cross_paper": is_cross_paper,
                    "cross_topic": is_cross_topic,
                    "topic_u": int(labels[u]),
                    "topic_v": int(labels[v]),
                    "paper_u": valid_chunks[u]["file"],
                    "paper_v": valid_chunks[v]["file"],
                }
                edge_dict[(u, v)] = edge_obj
                if is_cross_paper:
                    cross_degree[u] += 1
                    cross_degree[v] += 1
                    t_pair = tuple(sorted([ int(labels[u]), int(labels[v]) ]))
                    inter_topic_pairs[t_pair] += 1
                    if not is_cross_topic:
                        top_cross_paper_bridges.append(edge_obj)
                    else:
                        top_inter_topic_bridges.append(edge_obj)

            if cross_added >= top_k and intra_added >= 1:
                break

    top_cross_paper_bridges.sort(key=lambda x: -x["sim"])
    top_inter_topic_bridges.sort(key=lambda x: -x["sim"])

    # 統計每篇論文的主題分佈矩陣 (Paper-by-Topic Distribution)
    paper_topic_counts = defaultdict(lambda: defaultdict(int))
    paper_cross_edges = defaultdict(int)
    for i, ch in enumerate(valid_chunks):
        paper_topic_counts[ch["file"]][int(labels[i])] += 1
        paper_cross_edges[ch["file"]] += cross_degree[i]

    cards_dir = root / "02_notes" / "cards"
    existing_cards = [p.name.lower() for p in cards_dir.glob("card_*.md")] if cards_dir.exists() else []

    paper_profiles = []
    for p_file in papers_set:
        t_counts = paper_topic_counts[p_file]
        total_c = sum(t_counts.values())
        sorted_t = sorted(t_counts.items(), key=lambda x: -x[1])
        dom_t, dom_cnt = sorted_t[0]
        sec_t, sec_cnt = sorted_t[1] if len(sorted_t) > 1 else (dom_t, 0)

        parts = Path(p_file).stem.lower().split("_")
        has_card = any(parts[0] in c_name and parts[1] in c_name for c_name in existing_cards) if len(parts) >= 2 else False

        paper_profiles.append({
            "paper": p_file,
            "valid_chunks": total_c,
            "dominant_topic": dom_t,
            "dominant_share": round(dom_cnt / total_c * 100, 1),
            "secondary_topic": sec_t,
            "secondary_share": round(sec_cnt / total_c * 100, 1),
            "cross_paper_edges": paper_cross_edges[p_file],
            "has_reading_card": has_card,
            "topic_distribution": {f"Topic_{k}": v for k, v in sorted(t_counts.items())},
        })

    paper_profiles.sort(key=lambda x: -x["cross_paper_edges"])

    # 更新每個 Topic 的涵蓋論文數與代表性 Chunks 詳細資訊
    for t in topics_info:
        tid = t["topic_id"]
        t["paper_coverage"] = sum(1 for p in paper_profiles if f"Topic_{tid}" in p["topic_distribution"])
        t["share_pct"] = round(t["chunk_count"] / n_valid * 100, 1)
        rep_details = []
        for r_idx in t["representative_indices"]:
            ch = valid_chunks[r_idx]
            rep_details.append({
                "chunk_id": ch["chunk_id"],
                "paper": ch["file"],
                "section": ch["section"],
                "excerpt": ch["text"][:260] + "..."
            })
        t["representative_chunks"] = rep_details
        del t["representative_indices"]

    # 建構主題間連通密度與結構洞 (Structural Holes) 診斷
    n_topics = len(topics_info)
    topic_connectivity = []
    for t1 in range(n_topics):
        for t2 in range(t1 + 1, n_topics):
            cnt = inter_topic_pairs.get((t1, t2), 0)
            cos_centers = float(np.dot(topic_centroids[t1], topic_centroids[t2]))
            topic_connectivity.append({
                "topic_a": t1,
                "topic_b": t2,
                "cross_paper_bridge_edges": cnt,
                "centroid_cosine": round(cos_centers, 4),
                "is_structural_hole": cnt <= 24
            })
    topic_connectivity.sort(key=lambda x: x["cross_paper_bridge_edges"])

    # 準備 HTML 網路圖之 Nodes 與 Edges
    nodes_for_html = []
    for i, ch in enumerate(valid_chunks):
        stem_parts = Path(ch["file"]).stem.split("_")
        short_author = f"{stem_parts[0]}_{stem_parts[1]}" if len(stem_parts) >= 2 else Path(ch["file"]).stem[:15]
        chunk_num = ch["chunk_id"].split("_chunk_")[-1]
        nodes_for_html.append({
            "id": ch["chunk_id"],
            "short_id": f"{short_author}#{chunk_num}",
            "paper": ch["file"],
            "section": ch["section"],
            "topic": int(labels[i]),
            "cross_degree": cross_degree[i],
            "text": ch["text"][:650] + ("..." if len(ch["text"]) > 650 else "")
        })

    edges_for_html = [
        {
            "source": e["source"],
            "target": e["target"],
            "sim": e["sim"],
            "cross_paper": e["cross_paper"],
            "cross_topic": e["cross_topic"]
        }
        for e in edge_dict.values()
    ]

    generate_interactive_html(
        output_html_path=html_out_path,
        nodes_data=nodes_for_html,
        edges_data=edges_for_html,
        topics_data=topics_info,
        papers_list=papers_set,
        meta_info={
            "total_papers": len(papers_set),
            "total_chunks": len(all_chunks),
            "valid_chunks": n_valid,
            "total_edges": len(edges_for_html),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    )

    def enrich_bridge(b_list, limit=8):
        out = []
        for b in b_list[:limit]:
            cu = valid_chunks[b["u"]]
            cv = valid_chunks[b["v"]]
            out.append({
                "sim": b["sim"],
                "topic_u": b["topic_u"],
                "topic_v": b["topic_v"],
                "chunk_a": cu["chunk_id"],
                "paper_a": cu["file"],
                "section_a": cu["section"],
                "excerpt_a": cu["text"][:220] + "...",
                "chunk_b": cv["chunk_id"],
                "paper_b": cv["file"],
                "section_b": cv["section"],
                "excerpt_b": cv["text"][:220] + "...",
            })
        return out

    stats_payload = {
        "metadata": {
            "total_papers": len(papers_set),
            "total_raw_chunks": len(all_chunks),
            "valid_modeled_chunks": n_valid,
            "topic_count": n_topics,
            "total_network_edges": len(edges_for_html),
            "cross_paper_edges": sum(1 for e in edges_for_html if e["cross_paper"]),
            "pipeline": pipe_meta,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "topics": topics_info,
        "paper_profiles": paper_profiles,
        "top_intra_topic_bridges": enrich_bridge(top_cross_paper_bridges, 8),
        "top_inter_topic_bridges": enrich_bridge(top_inter_topic_bridges, 8),
        "topic_connectivity_and_holes": topic_connectivity,
    }
    stats_out_path.write_text(json.dumps(stats_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("------------------------------------------------------------------")
    print(f"[網路] 已建立區塊相似度網路 : 共 {len(edges_for_html)} 條邊 (跨篇語意橋樑 {stats_payload['metadata']['cross_paper_edges']} 條)")
    print(f"[輸出] 結構化統計數據檔     : {stats_out_path.relative_to(root)}")
    print(f"[輸出] 互動式區塊網路圖網頁 : {html_out_path.relative_to(root)}")
    print("==================================================================")
    return 0


def validate_landscape(file_path: str) -> bool:
    p = Path(file_path)
    if not p.exists():
        print(f"[錯誤] 找不到主題版圖報告檔案：{file_path}")
        return False

    content = p.read_text(encoding="utf-8", errors="ignore")
    errors = []
    warnings = []

    if not content.startswith("---"):
        errors.append("缺少開頭 YAML Frontmatter 分隔線 (---)")
    else:
        parts = content.split("---", 2)
        if len(parts) < 3:
            errors.append("YAML Frontmatter 未正確閉合 (需要第二個 ---)")
        else:
            fm_text = parts[1]
            for field in REQUIRED_FRONTMATTER_FIELDS:
                if not re.search(rf"^{field}\s*:", fm_text, re.MULTILINE):
                    errors.append(f"Frontmatter 缺少必備欄位：{field}")

    for num, keyword in REQUIRED_SECTIONS:
        pattern = rf"^##\s*{num}\.\s*.*{keyword}.*"
        if not re.search(pattern, content, re.MULTILINE):
            errors.append(f"缺少第 {num} 節標準標題（需包含「## {num}. ...{keyword}...」）")

    for sub in ["3.1", "3.2", "4.1", "4.2"]:
        if not re.search(rf"^###\s*{re.escape(sub)}\s+", content, re.MULTILINE):
            errors.append(f"缺少必備分析子小節：### {sub}")

    table_headers = re.findall(r"^\|.*\|\s*\n\|[\s:|-]+\|", content, re.MULTILINE)
    if len(table_headers) < 2:
        errors.append("報告中至少需包含兩個 Markdown 表格（第 1 節主題構面對映表與第 2 節論文×主題分佈矩陣）")

    print("\n==========================================")
    print(f"[檢查] 驗證全庫主題版圖與網路報告：{p.name}")
    print("==========================================")

    if errors:
        print(f"[FAIL] 驗證未通過！共發現 {len(errors)} 項結構缺失：")
        for err in errors:
            print(f"   * {err}")
    else:
        print("[PASS] 格式合規！完全通過第七週 BERTopic 主題版圖與跨篇網路拓撲 Schema 檢驗！")

    if warnings:
        for w in warnings:
            print(f"   * [WARN] {w}")

    return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(description="全庫語意區塊 BERTopic 主題建模與跨篇相似度互動網路建置工具")
    subparsers = parser.add_subparsers(dest="command")

    b_parser = subparsers.add_parser("build", help="執行 BERTopic 主題聚類與生成互動網路圖")
    b_parser.add_argument("--topics", type=int, default=6, help="預設目標主題簇數量 (預設: 6)")
    b_parser.add_argument("--min-cluster-size", type=int, default=15, help="HDBSCAN 最小群集區塊數 (預設: 15)")
    b_parser.add_argument("--min-similarity", type=float, default=0.68, help="納入網路圖之最低餘弦相似度門檻 (預設: 0.68)")
    b_parser.add_argument("--top-k", type=int, default=4, help="每個節點保留之最大跨篇最近鄰連線數 (預設: 4)")

    v_parser = subparsers.add_parser("validate", help="驗證 topic_landscape.md 是否符合標準 Schema")
    v_parser.add_argument("report_path", nargs="?", default="02_notes/topic_landscape.md", help="報告檔案路徑")

    args = parser.parse_args()
    if args.command == "build":
        sys.exit(cmd_build(args))
    elif args.command == "validate":
        ok = validate_landscape(args.report_path)
        sys.exit(0 if ok else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
