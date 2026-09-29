"""
scripts/import_external_papers.py

外部自尋文獻匯入與學術元數據治理工具（雙引擎高精度探測版）
核心特色：
1. 雙重首頁文字與版面探測引擎：
   - 引擎 A (PyMuPDF)：首頁字體大小與視覺區塊啟發式分析（最高精度）
   - 引擎 B (pypdf/純文字串流)：啟發式內文標題與作者行語意解析（無外部編譯套件依賴備援）
2. 探測成果透明度：
   - 即時於終端機列印探測到的「論文題名」與「作者」，並註明所採用的解析引擎
3. 多源學術資料庫無縫檢索：
   - DOI 權威查詢：先查 CrossRef，失敗自動備援 DataCite（Zenodo/機構典藏）
   - 預印本查詢：自動辨識 arXiv ID 並連線 arXiv 官方 API
   - 題名反查：使用 PDF 探測到的真實論文題名向 CrossRef 及 OpenAlex 進行精準檢索
4. 規範化重構命名與入庫：
   - 去重檢驗、標準化命名（{年份}_{第一作者}_{短篇名}.pdf）、搬入 raw_pdf/ 並生成總目錄
"""

import os
import re
import sys
import json
import argparse
import urllib.request
import urllib.parse
import datetime
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# 設定 Windows 終端輸出編碼為 UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 目錄與檔案常數
PAPERS_DIR = Path("01_papers")
INBOX_DIR = Path("01_papers/inbox")
RAW_PDF_DIR = Path("01_papers/raw_pdf")
EXTERNAL_CATALOG_MD = Path("01_papers/external_papers_catalog.md")
EXTERNAL_METADATA_JSON = Path("01_papers/external_papers_metadata.json")

# 正則表達式
DOI_REGEX = re.compile(r'\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b', re.IGNORECASE)
ARXIV_REGEX = re.compile(r'\barXiv:\s*([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)\b', re.IGNORECASE)

USER_AGENT_STR = "ThesisLiteratureAgent/2.0 (mailto:academic-research@university.edu; Academic Research)"


def ensure_directories():
    """確保必要目錄存在"""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """清理檔案名稱中的非法字元"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'[\s_]+', "_", name)
    return name.strip("._")[:45]


def extract_title_and_author_from_raw_text(raw_text: str) -> Tuple[str, str]:
    """
    當 PyMuPDF 視覺版面不可用時，從純文字首頁啟發式提取論文題名與作者
    （專為 pypdf 與二進位串流設計之備援演算法）
    """
    if not raw_text:
        return "", ""

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return "", ""

    # 尋找 Abstract / Summary 所在行
    abs_line_idx = -1
    for i, line in enumerate(lines[:35]):
        if re.search(r'^\s*(abstract|summary|executive summary)\b', line, re.IGNORECASE):
            abs_line_idx = i
            break

    header_limit = abs_line_idx if abs_line_idx != -1 else min(16, len(lines))

    # 排除常見出版商頁首雜訊
    cand_lines = []
    for i in range(header_limit):
        line = lines[i]
        if re.search(r'^(proceedings of|volume|issue|published|received|copyright|arxiv:|http|doi:|issn|\d{4}\b)', line, re.IGNORECASE):
            continue
        cand_lines.append(line)

    if not cand_lines:
        return "", ""

    title_parts = []
    author_parts = []
    found_authors = False

    for line in cand_lines:
        is_affil_or_email = bool(re.search(
            r'(@|department|university|laboratory|institute|school|center|college|national|\bave\b|\busa\b|\bbrazil\b|\bitaly\b|\bchina\b|\bspain\b|\buk\b|\bgerma\b)',
            line, re.IGNORECASE
        ))
        if is_affil_or_email:
            found_authors = True
            continue

        # 作者行特徵：含有 and、逗號分割姓名、或數字上標，且不含常見論文題目名詞
        is_author_line = bool(
            re.search(r'(\band\b|,\s*|\bby\s+|[A-Z][a-z]+\s+[A-Z][a-z]+\s*\d*)', line) and
            not re.search(r'(:|-|Topic|Model|Language|Approach|Study|Survey|Analysis|Learning|Framework)', line)
        )

        if not found_authors:
            if is_author_line and len(title_parts) >= 1:
                found_authors = True
                author_parts.append(line)
            else:
                title_parts.append(line)
        else:
            if not is_affil_or_email and len(author_parts) < 2:
                author_parts.append(line)

    title = " ".join(title_parts).strip()
    title = re.sub(r'[\*\dagger\ddagger\d]+$', '', title).strip()

    raw_author = " ".join(author_parts).strip()
    clean_author = re.sub(r'[\*\d†‡]+', ' ', raw_author)
    clean_author = re.sub(r'\s+', ' ', clean_author).strip()

    return title, clean_author


def extract_pdf_features(pdf_path: Path) -> Dict[str, Any]:
    """
    從 PDF 首頁提取文字、DOI、arXiv ID 以及推斷真實題名與作者
    優先級：
    1. 內嵌 Document Info（PDF Metadata）
    2. 首頁視覺版面分析（PyMuPDF Font-size & Layout Heuristics）
    3. 純文字首頁結構化啟發式解析（pypdf / Byte-stream Text Heuristics）
    """
    raw_text = ""
    extracted_title = ""
    extracted_author = ""
    engine_used = "None"

    # 1. 嘗試透過 PyMuPDF (fitz) 分析版面區塊
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz

        doc = fitz.open(pdf_path)
        engine_used = "PyMuPDF (視覺版面)"
        meta = doc.metadata or {}
        meta_title = (meta.get("title") or "").strip()
        meta_author = (meta.get("author") or "").strip()

        # 檢驗內建 metadata 是否為有效題名與作者
        invalid_titles = ["untitled", "title", "microsoft word", "latex", ".pdf", "document", "arxiv"]
        if meta_title and len(meta_title) > 8 and not any(meta_title.lower() == inv or meta_title.lower().startswith(inv) for inv in invalid_titles):
            extracted_title = meta_title

        if meta_author and len(meta_author) > 2 and meta_author.lower() not in ["author", "unknown", "admin", "user"]:
            extracted_author = meta_author

        if len(doc) > 0:
            first_page = doc[0]
            raw_text = first_page.get_text("text") or ""
            dict_data = first_page.get_text("dict")
            blocks = dict_data.get("blocks", [])

            text_blocks = []
            for b in blocks:
                if b.get("type") == 0 and "lines" in b:  # 文字區塊
                    block_lines = []
                    max_size = 0
                    for l in b["lines"]:
                        line_text = "".join(s.get("text", "") for s in l["spans"]).strip()
                        if line_text:
                            block_lines.append(line_text)
                            for s in l["spans"]:
                                sz = s.get("size", 0)
                                if sz > max_size and len(s.get("text", "").strip()) > 1:
                                    max_size = sz
                    full_block_text = " ".join(block_lines).strip()
                    if full_block_text:
                        text_blocks.append({
                            "text": full_block_text,
                            "max_size": max_size,
                            "bbox": b.get("bbox", [0, 0, 0, 0])
                        })

            # 尋找 Abstract/Summary 所在的區塊位置
            abs_idx = -1
            for i, tb in enumerate(text_blocks):
                if re.search(r'^\s*(abstract|summary|executive summary)\b', tb["text"], re.IGNORECASE):
                    abs_idx = i
                    break

            limit_idx = abs_idx if abs_idx != -1 else min(7, len(text_blocks))

            # 找出最大字體的區塊（標題候選）
            max_font = 0
            title_idx = -1
            for i in range(limit_idx):
                tb = text_blocks[i]
                if re.search(r'^(proceedings of|volume|issue|published|received|copyright|arxiv:|http|doi:|issn|\d{4})', tb["text"], re.IGNORECASE):
                    continue
                if tb["max_size"] > max_font:
                    max_font = tb["max_size"]
                    title_idx = i

            # 若未在內嵌 metadata 找到標題，由版面分析組裝
            if not extracted_title and title_idx != -1:
                title_parts = [text_blocks[title_idx]["text"]]
                curr = title_idx + 1
                while curr < limit_idx:
                    tb = text_blocks[curr]
                    if abs(tb["max_size"] - max_font) <= 1.8:
                        if not re.search(r'^(abstract|by\s|author|university|laboratory|department|school|institute)', tb["text"], re.IGNORECASE):
                            title_parts.append(tb["text"])
                            curr += 1
                        else:
                            break
                    else:
                        break
                cand_title = " ".join(title_parts).strip()
                cand_title = re.sub(r'[\*\dagger\ddagger\d]+$', '', cand_title).strip()
                if len(cand_title) > 6:
                    extracted_title = cand_title
            else:
                curr = title_idx + 1 if title_idx != -1 else 0

            # 若未在內嵌 metadata 找到作者，由標題後方區塊推算
            if not extracted_author and title_idx != -1:
                author_blocks = []
                for i in range(curr, limit_idx):
                    tb = text_blocks[i]
                    txt = tb["text"]
                    if re.search(r'(@|department|university|laboratory|institute|school|center|college|national|\bave\b|\busa\b|\bchina\b|\bspain\b|\buk\b)', txt, re.IGNORECASE):
                        continue
                    if not re.search(r'^(abstract|keywords|a preprint|introduction)', txt, re.IGNORECASE):
                        if len(txt) > 3 and not re.match(r'^\d+$', txt):
                            author_blocks.append(txt)

                if author_blocks:
                    raw_a = " ".join(author_blocks[:2])
                    clean_a = re.sub(r'[\*\d†‡]+', ' ', raw_a)
                    clean_a = re.sub(r'\s+', ' ', clean_a).strip()
                    extracted_author = clean_a

        doc.close()
    except Exception:
        pass

    # 2. 備援嘗試 pypdf 提取純文字並進行結構化分析
    if not raw_text or not extracted_title:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(pdf_path))
            if len(reader.pages) > 0:
                pypdf_text = reader.pages[0].extract_text() or ""
                if not raw_text:
                    raw_text = pypdf_text
                    engine_used = "pypdf (純文字備援)"

                # 若尚未取得標題或作者，調用純文字結構化提取器
                if not extracted_title or not extracted_author:
                    t_text, a_text = extract_title_and_author_from_raw_text(pypdf_text)
                    if not extracted_title and t_text:
                        extracted_title = t_text
                    if not extracted_author and a_text:
                        extracted_author = a_text

                # 檢查 pypdf 的 metadata
                if not extracted_title and reader.metadata and reader.metadata.title:
                    mt = reader.metadata.title.strip()
                    if len(mt) > 8 and not mt.lower().startswith("untitled"):
                        extracted_title = mt
                if not extracted_author and reader.metadata and reader.metadata.author:
                    ma = reader.metadata.author.strip()
                    if len(ma) > 2 and ma.lower() not in ["author", "unknown"]:
                        extracted_author = ma
        except Exception:
            pass

    # 3. 備援位元組串流粗讀
    if not raw_text or not extracted_title:
        try:
            with open(pdf_path, "rb") as f:
                raw = f.read(40960)
                byte_text = raw.decode("latin1", errors="ignore")
                if not raw_text:
                    raw_text = byte_text
                    engine_used = "ByteStream (底層粗讀)"
                if not extracted_title:
                    t_byte, a_byte = extract_title_and_author_from_raw_text(byte_text)
                    if t_byte:
                        extracted_title = t_byte
                    if a_byte and not extracted_author:
                        extracted_author = a_byte
        except Exception:
            pass

    # 4. 探測 DOI
    doi = None
    if raw_text:
        matches = DOI_REGEX.findall(raw_text)
        if matches:
            for m in matches:
                clean_doi = m.rstrip(".,;)>]}")
                if clean_doi.startswith("10.") and len(clean_doi) > 7:
                    doi = clean_doi
                    break

    # 5. 探測 arXiv ID
    arxiv_id = None
    if raw_text:
        m_ax = ARXIV_REGEX.search(raw_text)
        if m_ax:
            arxiv_id = m_ax.group(1)

    return {
        "raw_text": raw_text,
        "extracted_title": extracted_title,
        "extracted_author": extracted_author,
        "doi": doi,
        "arxiv_id": arxiv_id,
        "engine_used": engine_used
    }


def fetch_crossref_metadata(doi: str) -> Optional[Dict[str, Any]]:
    """向 CrossRef REST API 查詢權威元數據（遵循禮貌集原則）"""
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    headers = {"User-Agent": USER_AGENT_STR}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                message = data.get("message", {})

                title_list = message.get("title", [])
                title = title_list[0].strip() if title_list else "Untitled"

                authors = message.get("author", [])
                first_author = "Author"
                if authors:
                    first_author = authors[0].get("family") or authors[0].get("name") or "Author"

                published = message.get("published-print") or message.get("published-online") or message.get("created", {})
                date_parts = published.get("date-parts", [[2024]])
                year = str(date_parts[0][0]) if date_parts and date_parts[0] else "2024"

                containers = message.get("container-title", [])
                source = containers[0].strip() if containers else (message.get("publisher") or "Academic Source")

                return {
                    "doi": f"https://doi.org/{doi}",
                    "raw_doi": doi,
                    "title": title,
                    "first_author": first_author,
                    "year": year,
                    "source": source,
                    "authors_count": len(authors),
                    "publisher": message.get("publisher", ""),
                    "type": message.get("type", "journal-article"),
                    "service": "CrossRef"
                }
    except Exception:
        pass
    return None


def fetch_datacite_metadata(doi: str) -> Optional[Dict[str, Any]]:
    """向 DataCite REST API 查詢元數據（Zenodo、機構典藏、開放科學平台備援）"""
    url = f"https://api.datacite.org/dois/{urllib.parse.quote(doi)}"
    headers = {"User-Agent": USER_AGENT_STR}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                attrs = data.get("data", {}).get("attributes", {})
                titles = attrs.get("titles", [])
                title = titles[0].get("title", "").strip() if titles else "Untitled"

                creators = attrs.get("creators", [])
                first_author = "Author"
                if creators:
                    first_author = creators[0].get("familyName") or creators[0].get("name", "Author").split()[-1]

                year = str(attrs.get("publicationYear") or 2024)
                source = attrs.get("publisher", "DataCite Source")

                return {
                    "doi": f"https://doi.org/{doi}",
                    "raw_doi": doi,
                    "title": title,
                    "first_author": first_author,
                    "year": year,
                    "source": source,
                    "authors_count": len(creators),
                    "publisher": source,
                    "type": attrs.get("types", {}).get("resourceTypeGeneral", "Preprint/Dataset"),
                    "service": "DataCite"
                }
    except Exception:
        pass
    return None


def fetch_arxiv_metadata(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """向 arXiv 官方 API 查詢預印本文獻元數據"""
    clean_id = re.sub(r'v\d+$', '', arxiv_id)
    url = f"http://export.arxiv.org/api/query?id_list={urllib.parse.quote(clean_id)}&max_results=1"
    headers = {"User-Agent": USER_AGENT_STR}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            root = ET.fromstring(resp.read().decode("utf-8"))
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entry = root.find("atom:entry", ns)
            if entry is not None:
                title_elem = entry.find("atom:title", ns)
                title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else "arXiv Paper"

                author_elem = entry.find("atom:author/atom:name", ns)
                first_author = "Author"
                if author_elem is not None and author_elem.text:
                    first_author = author_elem.text.strip().split()[-1]

                published_elem = entry.find("atom:published", ns)
                year = published_elem.text[:4] if published_elem is not None and published_elem.text else "2024"

                return {
                    "doi": f"https://arxiv.org/abs/{arxiv_id}",
                    "raw_doi": f"arXiv:{arxiv_id}",
                    "title": title,
                    "first_author": first_author,
                    "year": year,
                    "source": f"arXiv Preprint ({clean_id})",
                    "authors_count": len(entry.findall("atom:author", ns)),
                    "publisher": "arXiv",
                    "type": "preprint",
                    "service": "arXiv"
                }
    except Exception:
        pass
    return None


def fetch_crossref_title_search(title: str, author_hint: str = "") -> Optional[Dict[str, Any]]:
    """向 CrossRef 標題端點搜尋論文元數據"""
    clean_title = re.sub(r'[^\w\s]', ' ', title)[:120].strip()
    if len(clean_title) < 5:
        return None
    url = f"https://api.crossref.org/works?" + urllib.parse.urlencode({
        "query.title": clean_title,
        "rows": 1
    })
    headers = {"User-Agent": USER_AGENT_STR}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("message", {}).get("items", [])
            if items:
                it = items[0]
                t_list = it.get("title", [])
                res_title = t_list[0].strip() if t_list else title
                authors = it.get("author", [])
                fa = "Author"
                if authors:
                    fa = authors[0].get("family") or authors[0].get("name") or "Author"

                published = it.get("published-print") or it.get("published-online") or it.get("created", {})
                date_parts = published.get("date-parts", [[2024]])
                year = str(date_parts[0][0]) if date_parts and date_parts[0] else "2024"
                containers = it.get("container-title", [])
                source = containers[0].strip() if containers else (it.get("publisher") or "Academic Source")
                doi_str = it.get("DOI", "")

                return {
                    "doi": f"https://doi.org/{doi_str}" if doi_str else "",
                    "raw_doi": doi_str,
                    "title": res_title,
                    "first_author": fa,
                    "year": year,
                    "source": source,
                    "authors_count": len(authors),
                    "publisher": it.get("publisher", ""),
                    "service": "CrossRef Title Search"
                }
    except Exception:
        pass
    return None


def fetch_openalex_title_fallback(title_query: str, author_hint: str = "") -> Optional[Dict[str, Any]]:
    """調用 OpenAlex 檢索端點進行標題與作者反查"""
    try:
        clean_q = re.sub(r'[^\w\s]', ' ', title_query)[:120].strip()
        if not clean_q or len(clean_q) < 5:
            return None

        url = "https://api.openalex.org/works?" + urllib.parse.urlencode({
            "search": clean_q,
            "per-page": 3
        })
        headers = {"User-Agent": USER_AGENT_STR}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if results:
                target_w = results[0]
                if author_hint:
                    clean_ah = author_hint.lower()
                    for w in results:
                        authors = [a["author"].get("display_name", "").lower() for a in w.get("authorships", [])]
                        if any(clean_ah in a_name or a_name in clean_ah for a_name in authors):
                            target_w = w
                            break

                doi = target_w.get("doi") or ""
                authorships = target_w.get("authorships", [])
                fa = authorships[0]["author"].get("display_name", "Author").split()[-1] if authorships else "Author"
                source_name = (target_w.get("primary_location") or {}).get("source", {}).get("display_name") or "OpenAlex Source"
                return {
                    "doi": doi,
                    "raw_doi": doi.replace("https://doi.org/", "") if doi else "",
                    "title": target_w.get("title", title_query),
                    "first_author": fa,
                    "year": str(target_w.get("publication_year", 2024)),
                    "source": source_name,
                    "authors_count": len(authorships),
                    "service": "OpenAlex"
                }
    except Exception:
        pass
    return None


def load_external_metadata() -> Dict[str, Any]:
    """載入自尋文獻元數據資料庫"""
    if EXTERNAL_METADATA_JSON.exists():
        try:
            with open(EXTERNAL_METADATA_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_ingested": 0,
        "papers": []
    }


def save_external_metadata(data: Dict[str, Any]):
    """儲存自尋文獻元數據資料庫並刷新 Markdown 目錄"""
    ensure_directories()
    data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["total_ingested"] = len(data.get("papers", []))

    with open(EXTERNAL_METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    render_external_catalog_md(data)


def render_external_catalog_md(data: Dict[str, Any]):
    """渲染生成 external_papers_catalog.md"""
    papers = data.get("papers", [])
    lines = [
        "# 外部自尋文獻治理總目錄 (External Papers Catalog)\n",
        f"> **最後更新時間**：`{data.get('last_updated', 'N/A')}` | **自尋入庫總篇數**：`{len(papers)} 篇`",
        "> **目錄定位**：記錄未經 API 檢索、由指導教授交辦、研究者自尋或從博碩士論文網/預印本下載並經由元數據治理規範化入庫之文獻。\n",
        "---\n",
        "## 一、已入庫外部文獻清單\n"
    ]

    if papers:
        lines.append("| 編號 | 規範化檔名 | 發表年份 | 第一作者 | 發表期刊 / 研討會 / 出版出處 | 調閱與 DOI 連結 | 來源標籤 |")
        lines.append("| :---: | :--- | :---: | :---: | :--- | :--- | :---: |")
        for idx, p in enumerate(papers, 1):
            doi = p.get("doi", "")
            doi_link = f"[{doi}]({doi})" if doi.startswith("http") else (doi or "無 DOI")
            fn = p.get("filename", "")
            yr = p.get("year", "")
            fa = p.get("first_author", "")
            src = p.get("source", "外部文獻")
            tag = p.get("source_tag", "外部自尋")
            lines.append(f"| EXT-{idx:02d} | `{fn}` | {yr} | {fa} | `{src}` | {doi_link} | `{tag}` |")
        lines.append("")
    else:
        lines.append("*目前尚未有任何外部自尋文獻入庫。請將檔案放入 `01_papers/inbox/` 後執行 `ingest` 指令。*\n")

    lines.append("---\n")
    lines.append("## 二、標準引用條目（APA 7th Format）\n")
    if papers:
        for idx, p in enumerate(papers, 1):
            fa = p.get("first_author", "Author")
            yr = p.get("year", "2024")
            title = p.get("title", "Untitled")
            src = p.get("source", "Journal")
            doi = p.get("doi", "")
            doi_suffix = f" {doi}" if doi.startswith("http") else ""
            lines.append(f"{idx}. {fa} ({yr}). {title}. *{src}*.{doi_suffix}")
        lines.append("")
    else:
        lines.append("*暫無引用項目。*\n")

    lines.append("---\n")
    lines.append("### 🛠️ 外部文獻管理指令速查")
    lines.append("- 掃描收件箱：`python scripts/import_external_papers.py scan`")
    lines.append("- 預覽元數據解析：`python scripts/import_external_papers.py resolve`")
    lines.append("- 正式入庫治理：`python scripts/import_external_papers.py ingest`\n")

    with open(EXTERNAL_CATALOG_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def scan_inbox() -> List[Path]:
    """掃描 inbox 中的 PDF 檔案清單"""
    ensure_directories()
    files = sorted(list(INBOX_DIR.glob("*.pdf")))
    print("\n" + "="*70)
    print(f"📥 外部文獻收件箱掃描 (01_papers/inbox/): 共發現 {len(files)} 個檔案")
    print("="*70)
    for idx, f in enumerate(files, 1):
        sz = round(f.stat().st_size / 1024, 1)
        print(f"  [{idx}] {f.name} ({sz} KB)")
    if not files:
        print("  💡 收件箱目前為空。請將自尋文獻 PDF 檔案放入 01_papers/inbox/ 中。")
    print("="*70 + "\n")
    return files


def resolve_inbox_papers() -> List[Dict[str, Any]]:
    """探測並解析 inbox 中的所有 PDF，具備多層學術註冊庫備援與 PDF 內文題名反查"""
    files = scan_inbox()
    if not files:
        return []

    results = []
    print(f"\n🔍 開始探測 PDF 內文特徵與多源學術權威元數據：\n")
    for idx, f in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] 檔案：{f.name}")
        features = extract_pdf_features(f)
        doi = features.get("doi")
        arxiv_id = features.get("arxiv_id")
        extracted_title = features.get("extracted_title") or ""
        extracted_author = features.get("extracted_author") or ""
        engine = features.get("engine_used", "Auto")
        meta = None

        # 【核心改進】：明確列印出從 PDF 內文探測到的題名與作者
        print(f"    📖 PDF 首頁特徵探測成果（解析引擎：{engine}）：")
        if extracted_title:
            print(f"       ├─ 探測題名：《{extracted_title}》")
        else:
            print(f"       ├─ 探測題名：（未能辨識出高信心標題，將由檔名備援）")

        if extracted_author:
            print(f"       └─ 探測作者：{extracted_author}")
        else:
            print(f"       └─ 探測作者：（未能辨識出作者）")

        # 1. 優先嘗試 DOI 逆向查詢（先 CrossRef，失敗轉 DataCite）
        if doi:
            print(f"    ✨ 偵測到 DOI：{doi}")
            meta = fetch_crossref_metadata(doi)
            if meta:
                print(f"    ✅ CrossRef DOI 解析成功：《{meta['title'][:55]}...》")
                print(f"       作者：{meta['first_author']} | 年份：{meta['year']} | 來源：{meta['source']}")
            else:
                print(f"    ⚠️ CrossRef 連線逾時或查無此 DOI，轉向 DataCite 查詢...")
                meta = fetch_datacite_metadata(doi)
                if meta:
                    print(f"    ✅ DataCite DOI 解析成功：《{meta['title'][:55]}...》")
                    print(f"       作者：{meta['first_author']} | 年份：{meta['year']} | 來源：{meta['source']}")
                else:
                    print(f"    ⚠️ DataCite 亦無此 DOI 記錄。")

        # 2. 次選嘗試 arXiv ID 查詢
        if not meta and arxiv_id:
            print(f"    ✨ 偵測到 arXiv ID：{arxiv_id}，調用 arXiv 官方 API...")
            meta = fetch_arxiv_metadata(arxiv_id)
            if meta:
                print(f"    ✅ arXiv API 解析成功：《{meta['title'][:55]}...》")
                print(f"       作者：{meta['first_author']} | 年份：{meta['year']} | 來源：{meta['source']}")

        # 3. 三選嘗試：以探測到的真實論文題名向學術資料庫（CrossRef & OpenAlex）查詢
        if not meta and extracted_title:
            print(f"    🚀 正在使用探測到的論文題名向學術資料庫進行檢索...")
            print(f"       檢索關鍵題名：《{extracted_title[:65]}...》")
            if extracted_author:
                print(f"       搭配作者驗證：{extracted_author}")

            # 3.1 優先調用 CrossRef 標題端點（穩定無 IP 限制）
            meta = fetch_crossref_title_search(extracted_title, author_hint=extracted_author)
            if meta:
                print(f"    ✅ CrossRef 題名檢索成功命中！")
                print(f"       正式篇名：《{meta['title'][:55]}...》")
                print(f"       第一作者：{meta['first_author']} | 出版年份：{meta['year']} | 來源：{meta['source']}")
                if meta.get("doi"):
                    print(f"       官方 DOI：{meta['doi']}")
            else:
                # 3.2 備援調用 OpenAlex 標題端點
                meta = fetch_openalex_title_fallback(extracted_title, author_hint=extracted_author)
                if meta:
                    print(f"    ✅ OpenAlex 題名檢索成功命中！")
                    print(f"       正式篇名：《{meta['title'][:55]}...》")
                    print(f"       第一作者：{meta['first_author']} | 出版年份：{meta['year']} | 來源：{meta['source']}")
                    if meta.get("doi"):
                        print(f"       官方 DOI：{meta['doi']}")

        # 4. 四選降級：以本機檔名嘗試查詢
        if not meta:
            clean_stem = f.stem.replace("_", " ").strip()
            if len(clean_stem) > 6 and not re.search(r'^(download|1-s2\.0|paper|document)', clean_stem, re.IGNORECASE):
                print(f"    ℹ️ 嘗試以檔名向學術資料庫發送降級檢索：《{clean_stem[:45]}》...")
                meta = fetch_crossref_title_search(clean_stem) or fetch_openalex_title_fallback(clean_stem)
                if meta:
                    print(f"    ✅ 檔名檢索命中成功：《{meta['title'][:55]}...》")

        # 5. 兜底方案：採用探測到的題名與作者建立基礎元數據
        if not meta:
            final_title = extracted_title if extracted_title else f.stem.replace("_", " ")
            final_author = extracted_author.split(",")[0].split(";")[0].split()[-1] if extracted_author else "Author"
            meta = {
                "doi": f"https://doi.org/{doi}" if doi else "",
                "raw_doi": doi or (f"arXiv:{arxiv_id}" if arxiv_id else ""),
                "title": final_title,
                "first_author": final_author,
                "year": "2024",
                "source": "外部自尋文獻",
                "service": "LocalPDFExtraction"
            }
            print(f"    ⚠️ 資料庫查無更完整記錄，直接採用 PDF 首頁探測成果建立基礎元數據。")
            print(f"       題名：《{final_title[:50]}》 | 作者：{final_author}")

        results.append({
            "original_file": f,
            "metadata": meta
        })
        print("-" * 70)
    return results


def ingest_inbox_papers(source_tag: str = "外部自尋"):
    """正式治理：去重比對、重新命名、搬移至 raw_pdf/、更新總目錄"""
    ensure_directories()
    resolved = resolve_inbox_papers()
    if not resolved:
        return

    db = load_external_metadata()
    existing_dois = {p.get("raw_doi") for p in db.get("papers", []) if p.get("raw_doi")}
    existing_titles = {p.get("title", "").strip().lower() for p in db.get("papers", [])}

    print("\n" + "="*70)
    print(f"🚀 開始執行標準化入庫作業（目標目錄：01_papers/raw_pdf/）")
    print("="*70)

    ingested_count = 0
    for item in resolved:
        orig_file = item["original_file"]
        meta = item["metadata"]
        raw_doi = meta.get("raw_doi")
        title = meta.get("title", "Untitled")
        title_lower = title.strip().lower()

        # 去重比對
        if raw_doi and raw_doi in existing_dois:
            print(f"  [略過重複] DOI 已在庫中：{raw_doi}（{orig_file.name}）")
            continue
        if title_lower in existing_titles:
            print(f"  [略過重複] 篇名已在庫中：《{title[:40]}...》（{orig_file.name}）")
            continue

        year = meta.get("year", "2024")
        author = sanitize_filename(meta.get("first_author", "Author"))
        short_title = sanitize_filename(title[:35].strip())
        new_filename = f"{year}_{author}_{short_title}.pdf"
        target_path = RAW_PDF_DIR / new_filename

        # 若目標檔案已存在
        if target_path.exists():
            counter = 1
            while target_path.exists():
                new_filename = f"{year}_{author}_{short_title}_{counter}.pdf"
                target_path = RAW_PDF_DIR / new_filename
                counter += 1

        try:
            orig_file.rename(target_path)
            print(f"  [入庫成功] {orig_file.name}")
            print(f"            --> 01_papers/raw_pdf/{new_filename}")

            record = {
                "id": f"EXT-{len(db.get('papers', [])) + 1:02d}",
                "filename": new_filename,
                "filepath": str(target_path),
                "title": title,
                "first_author": meta.get("first_author", "Author"),
                "year": year,
                "source": meta.get("source", "外部文獻"),
                "doi": meta.get("doi", ""),
                "raw_doi": raw_doi,
                "source_tag": source_tag,
                "service": meta.get("service", "Unknown"),
                "file_size_kb": round(target_path.stat().st_size / 1024, 1),
                "ingested_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            db["papers"].append(record)
            if raw_doi:
                existing_dois.add(raw_doi)
            existing_titles.add(title_lower)
            ingested_count += 1
        except Exception as e:
            print(f"  [搬移失敗] {orig_file.name}: {e}")

    save_external_metadata(db)
    print("="*70)
    print(f"✨ 外部文獻治理入庫完成！本次成功入庫：{ingested_count} 篇")
    print(f"📋 總目錄已刷新：01_papers/external_papers_catalog.md")
    print(f"📦 結構化數據：01_papers/external_papers_metadata.json")
    print("="*70 + "\n")


def list_external_papers():
    """在終端機打印已入庫之外部文獻目錄"""
    db = load_external_metadata()
    papers = db.get("papers", [])
    print("\n" + "="*80)
    print(f"📚 外部自尋文獻庫存總覽 (共 {len(papers)} 篇)")
    print("="*80)
    if not papers:
        print("  目前尚無外部文獻記錄。")
    else:
        for p in papers:
            print(f"[{p.get('id', 'EXT')}] 《{p.get('title', '')}》")
            print(f"       檔名：{p.get('filename')} | 出版：{p.get('year')} | 標籤：{p.get('source_tag')}")
            print(f"       來源：{p.get('source')} | 查詢服務：{p.get('service', 'N/A')} | DOI：{p.get('doi') or '無'}\n")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="外部自尋文獻匯入與學術元數據治理工具（高精度探測版）")
    subparsers = parser.add_subparsers(dest="command", help="操作指令")

    subparsers.add_parser("scan", help="掃描 01_papers/inbox/ 目錄")
    subparsers.add_parser("resolve", help="探測 PDF 內文題名與多源學術資料庫元數據")

    ingest_parser = subparsers.add_parser("ingest", help="正式治理入庫（重命名、搬移至 raw_pdf/、更新總目錄）")
    ingest_parser.add_argument("-t", "--tag", default="外部自尋", help="來源標籤（例：教授推薦、碩博論文、自尋文獻）")

    subparsers.add_parser("list", help="檢視已入庫外部文獻清單")
    subparsers.add_parser("check", help="檢查收件箱與文獻庫健康狀態")

    args = parser.parse_args()

    if args.command == "scan":
        scan_inbox()
    elif args.command == "resolve":
        resolve_inbox_papers()
    elif args.command == "ingest":
        ingest_inbox_papers(source_tag=args.tag)
    elif args.command == "list":
        list_external_papers()
    elif args.command == "check":
        scan_inbox()
        list_external_papers()
    else:
        scan_inbox()
        parser.print_help()


if __name__ == "__main__":
    main()
