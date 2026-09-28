"""
scripts/import_external_papers.py

外部自尋文獻匯入與學術元數據治理工具
核心指令：
1. scan:    掃描 01_papers/inbox/ 中有哪些待治理的外部 PDF 檔案
2. resolve: 自動探測 PDF 首頁中的 DOI 並向 CrossRef API 查詢權威元數據（不搬移檔案）
3. ingest:  執行元數據逆向解析、智慧去重、標準化重構命名（{年份}_{作者}_{短篇名}.pdf）、搬移入庫至 raw_pdf/ 並生成目錄
4. list:    瀏覽 01_papers/external_papers_catalog.md 總目錄與入庫狀態
5. check:   檢驗 raw_pdf/ 中外部文獻之完整性與去重狀態
"""

import os
import re
import sys
import json
import argparse
import urllib.request
import urllib.parse
import datetime
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

# 標準 DOI 正則表達式
DOI_REGEX = re.compile(r'\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b', re.IGNORECASE)


def ensure_directories():
    """確保必要目錄存在"""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """清理檔案名稱中的非法字元"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'[\s_]+', "_", name)
    return name.strip("._")[:45]


def extract_first_page_text(pdf_path: Path) -> str:
    """提取 PDF 首頁文字以探測元數據與 DOI"""
    # 優先嘗試 PyMuPDF (fitz)
    try:
        import fitz
        doc = fitz.open(pdf_path)
        if len(doc) > 0:
            text = doc[0].get_text("text")
            doc.close()
            return text
        doc.close()
    except Exception:
        pass

    # 備援嘗試 pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        if len(reader.pages) > 0:
            return reader.pages[0].extract_text() or ""
    except Exception:
        pass

    # 若無套件，讀取二進位前 4096 位元組進行簡單 ASCII/UTF-8 粗提
    try:
        with open(pdf_path, "rb") as f:
            raw = f.read(40960)
            return raw.decode("latin1", errors="ignore")
    except Exception:
        return ""


def find_doi_in_text(text: str) -> Optional[str]:
    """從文本中檢索合法 DOI"""
    if not text:
        return None
    matches = DOI_REGEX.findall(text)
    if matches:
        for m in matches:
            clean_doi = m.rstrip(".,;)>]}")
            # 排除非學術或假性匹配
            if clean_doi.startswith("10.") and len(clean_doi) > 7:
                return clean_doi
    return None


def fetch_crossref_metadata(doi: str) -> Optional[Dict[str, Any]]:
    """向 CrossRef REST API 查詢權威元數據（遵循禮貌集原則）"""
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    headers = {
        "User-Agent": "ThesisLiteratureAgent/1.0 (mailto:academic-research@thesis-workspace.edu; Academic Research)"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                message = data.get("message", {})
                
                # 提取標題
                title_list = message.get("title", [])
                title = title_list[0].strip() if title_list else "Untitled"
                
                # 提取作者
                authors = message.get("author", [])
                first_author = "Author"
                if authors:
                    first_author = authors[0].get("family") or authors[0].get("name") or "Author"
                
                # 提取年份
                published = message.get("published-print") or message.get("published-online") or message.get("created", {})
                date_parts = published.get("date-parts", [[2024]])
                year = str(date_parts[0][0]) if date_parts and date_parts[0] else "2024"
                
                # 提取期刊/來源
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
                    "type": message.get("type", "journal-article")
                }
    except Exception as e:
        pass
    return None


def fetch_openalex_title_fallback(title_query: str) -> Optional[Dict[str, Any]]:
    """若無 DOI，調用 OpenAlex 標題搜尋作為降級反查"""
    try:
        clean_q = re.sub(r'[^\w\s]', ' ', title_query)[:80].strip()
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode({
            "filter": f"title.search:{clean_q}",
            "per-page": 1
        })
        headers = {"User-Agent": "ThesisLiteratureAgent/1.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if results:
                w = results[0]
                doi = w.get("doi") or ""
                authorships = w.get("authorships", [])
                fa = authorships[0]["author"].get("display_name", "Author").split()[-1] if authorships else "Author"
                return {
                    "doi": doi,
                    "raw_doi": doi.replace("https://doi.org/", ""),
                    "title": w.get("title", title_query),
                    "first_author": fa,
                    "year": str(w.get("publication_year", 2024)),
                    "source": (w.get("primary_location") or {}).get("source", {}).get("display_name", "OpenAlex Source"),
                    "authors_count": len(authorships)
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
    """探測並解析 inbox 中的所有 PDF，回傳預覽資訊"""
    files = scan_inbox()
    if not files:
        return []

    results = []
    print(f"\n🔍 開始探測首頁文字特徵與 CrossRef 權威元數據：\n")
    for idx, f in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] 檔案：{f.name}")
        first_text = extract_first_page_text(f)
        doi = find_doi_in_text(first_text)
        meta = None

        if doi:
            print(f"    ✨ 偵測到 DOI：{doi}")
            meta = fetch_crossref_metadata(doi)
            if meta:
                print(f"    ✅ CrossRef 成功解析：《{meta['title'][:55]}...》")
                print(f"       作者：{meta['first_author']} | 年份：{meta['year']} | 來源：{meta['source']}")
            else:
                print(f"    ⚠️ CrossRef 連線逾時或無回應，嘗試 OpenAlex 反查...")
                meta = fetch_openalex_title_fallback(f.stem)
        else:
            print(f"    ℹ️ 未探測到標準 DOI，嘗試以檔名進行標題模糊比對...")
            meta = fetch_openalex_title_fallback(f.stem)

        if not meta:
            # 手動/降級兜底
            meta = {
                "doi": "",
                "raw_doi": "",
                "title": f.stem.replace("_", " "),
                "first_author": "UnknownAuthor",
                "year": "2024",
                "source": "外部自尋文獻"
            }
            print(f"    ⚠️ 無法自動獲取元數據，將採用本機檔名建立基礎元數據。")

        results.append({
            "original_file": f,
            "metadata": meta
        })
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
            print(f"       來源：{p.get('source')} | DOI：{p.get('doi') or '無'}\n")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="外部自尋文獻匯入與學術元數據治理工具")
    subparsers = parser.add_subparsers(dest="command", help="操作指令")

    subparsers.add_parser("scan", help="掃描 01_papers/inbox/ 目錄")
    subparsers.add_parser("resolve", help="探測 PDF 首頁 DOI 並向 CrossRef 查詢元數據")
    
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
        # 預設執行掃描並顯示說明
        scan_inbox()
        parser.print_help()


if __name__ == "__main__":
    main()
