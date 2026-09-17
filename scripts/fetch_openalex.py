"""
scripts/fetch_openalex.py

OpenAlex 學術文獻人機協同檢索與全文獲取工具
核心流程：
1. 階段一 (search)：向 OpenAlex 檢索候選文獻，生成包含來源、摘要與品質指標之 01_papers/candidate_papers.md
2. 階段二 (人機協同品質判讀)：研究者人工審閱 candidate_papers.md，將欲納入之文獻勾選為 [x]
3. 階段三 (download)：Agent 依據勾選清單自動下載 OA PDF，無法自動取得者提示圖書館人工取得指引
"""

import os
import re
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path

# 設定 Windows 終端輸出編碼
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 定義工作區目錄常數
RAW_PDF_DIR = Path("01_papers/raw_pdf")
CANDIDATE_MD_FILE = Path("01_papers/candidate_papers.md")
CANDIDATE_CACHE_FILE = Path("01_papers/candidates_cache.json")
METADATA_FILE = Path("01_papers/downloaded_metadata.json")

def sanitize_filename(name: str) -> str:
    """清理檔名中的非法字元，替換為安全底線"""
    return re.sub(r'[\\/*?:"<>| ]', '_', name)

def reconstruct_abstract(inverted_index: dict) -> str:
    """將 OpenAlex 倒排索引格式之摘要還原為完整自然段落"""
    if not inverted_index:
        return "（未提供摘要，請參閱原文 DOI 連結）"
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort(key=lambda x: x[0])
    return " ".join([word for _, word in word_positions])

def search_candidate_papers(query: str, max_candidates: int = 10, start_year: int = 2022):
    """
    步驟 1：檢索候選書目與摘要，輸出至 01_papers/candidate_papers.md
    """
    CANDIDATE_MD_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n[查詢] 正在向 OpenAlex 檢索候選學術文獻：『{query}』...")
    print(f"[條件] 限制年份：{start_year} 年至今 | 候選評估篇數：{max_candidates} 篇")

    params = {
        "search": query,
        "filter": f"publication_year:{start_year}-2026",
        "sort": "cited_by_count:desc",
        "per-page": max_candidates
    }
    api_url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    headers = {
        "User-Agent": "ThesisLiteratureAgent/2.0 (mailto:student@university.edu)"
    }

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[錯誤] OpenAlex API 請求失敗：{e}")
        return

    results = data.get("results", [])
    if not results:
        print("[警告] 未找到符合條件之文獻，請調整檢索關鍵字。")
        return

    candidates = []
    md_lines = [
        "# 候選文獻評估與品質篩選清單：candidate_papers.md\n",
        f"> **檢索主題**：`{query}` | **檢索年份**：{start_year}-2026 | **檢索總數**：{len(results)} 篇",
        ">",
        "> **【研究者人機協同判讀說明】**：",
        "> 1. **文獻品質評估**：請務必檢視各篇論文的 **發表來源 (Source)**、**題名 (Title)** 與 **摘要 (Abstract)**，排除掠奪性期刊或品質可疑之巨型期刊，確保文獻符合碩士論文核心研究問題。",
        "> 2. **決策標記**：欲納入研究並取得全文之文獻，請將標題旁的 `[ ]` 改為 `[x]`；暫不採用者維持 `[ ]`。",
        "> 3. **全文獲取**：完成勾選並儲存本檔案後，在終端機執行：`python scripts/fetch_openalex.py download`。",
        ">    - 若為開放取用 (OA)，系統將自動下載 PDF 至 `01_papers/raw_pdf/`。",
        ">    - 若為封閉訂閱文獻，系統將列出指引，提示您透過學校圖書館整合查詢系統人工取得。\n",
        "---\n"
    ]

    for idx, item in enumerate(results, 1):
        title = item.get("title") or "Untitled"
        pub_year = item.get("publication_year") or "UnknownYear"
        cited_count = item.get("cited_by_count", 0)
        doi = item.get("doi") or "無 DOI"

        # 取得發表載體 (Journal / Conference Source)
        primary_loc = item.get("primary_location") or {}
        source_obj = primary_loc.get("source") or {}
        source_name = source_obj.get("display_name") or "未列明期刊/研討會（需留心來源品質）"

        # 取得第一作者
        authorships = item.get("authorships", [])
        if authorships and "author" in authorships[0]:
            first_author = authorships[0]["author"].get("display_name", "Author").split()[-1]
        else:
            first_author = "Author"

        # 取得全文 OA 狀態與直連 PDF
        is_oa = item.get("open_access", {}).get("is_oa", False)
        best_oa = item.get("best_oa_location") or {}
        pdf_url = best_oa.get("pdf_url") or item.get("open_access", {}).get("oa_url")
        oa_status_text = "[開放取用] Open Access 直連" if (is_oa and pdf_url and pdf_url.startswith("http")) else "[封閉訂閱] 非直接 OA（需校園圖書館授權）"

        # 還原摘要
        abstract_text = reconstruct_abstract(item.get("abstract_inverted_index"))

        # 暫存候選物件
        record = {
            "index": idx,
            "title": title,
            "first_author": first_author,
            "year": pub_year,
            "source": source_name,
            "doi": doi,
            "cited_by_count": cited_count,
            "is_oa": bool(is_oa and pdf_url),
            "pdf_url": pdf_url,
            "openalex_id": item.get("id"),
            "abstract": abstract_text
        }
        candidates.append(record)

        # 格式化輸出 Markdown
        md_lines.append(f"## {idx}. [ ] {title}\n")
        md_lines.append(f"- **發表來源 (Source)**：`{source_name}`")
        md_lines.append(f"- **作者與年份**：{first_author} ({pub_year}) | **被引用數**：{cited_count} 次")
        md_lines.append(f"- **全文狀態**：{oa_status_text}")
        md_lines.append(f"- **DOI 直連**：{doi}")
        md_lines.append("- **摘要 (Abstract)**：")
        md_lines.append(f"  > {abstract_text}\n")
        md_lines.append("- **研究者品質判讀筆記（選填）**：")
        md_lines.append("  - \n")
        md_lines.append("---\n")

    # 寫入候選文件與快取檔
    with open(CANDIDATE_MD_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    with open(CANDIDATE_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print(f"[成功] 候選書目清單已成功輸出至：{CANDIDATE_MD_FILE}")
    print(f"[統計] 共整理 {len(candidates)} 篇文獻。")
    print(f"\n[下一步操作]：")
    print(f"   1. 請在編輯器開啟 {CANDIDATE_MD_FILE}。")
    print(f"   2. 閱讀各篇來源期刊與摘要，將欲納入之論文標題旁的 [ ] 改為 [x]。")
    print(f"   3. 存檔後於終端機執行：python scripts/fetch_openalex.py download")

def download_selected_papers():
    """
    步驟 3：閱讀 candidate_papers.md 勾選結果，自動下載 OA PDF，提示人工取得封閉文獻
    """
    if not CANDIDATE_MD_FILE.exists() or not CANDIDATE_CACHE_FILE.exists():
        print("[錯誤] 找不到候選清單，請先執行：python scripts/fetch_openalex.py search \"關鍵字\"")
        return

    # 讀取快取
    with open(CANDIDATE_CACHE_FILE, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    # 讀取 MD 判定勾選狀態
    with open(CANDIDATE_MD_FILE, "r", encoding="utf-8") as f:
        md_content = f.read()

    # 比對哪些編號被勾選 [x] 或 [X]
    checked_indices = set()
    pattern = r"##\s+(\d+)\.\s*\[[xX]\]"
    for m in re.finditer(pattern, md_content):
        checked_indices.add(int(m.group(1)))

    if not checked_indices:
        print(f"[警告] 在 {CANDIDATE_MD_FILE} 中未檢測到任何已勾選 [x] 的論文！")
        print("[提示] 請在欲下載的論文標題前方將 [ ] 改為 [x]，儲存後再次執行本指令。")
        return

    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[啟動] 檢測到研究者共選取 {len(checked_indices)} 篇論文進行全文獲取：\n")

    oa_success = 0
    manual_required = []
    final_records = []

    for item in candidates:
        idx = item["index"]
        if idx not in checked_indices:
            continue

        title = item["title"]
        year = item["year"]
        author = item["first_author"]
        pdf_url = item.get("pdf_url")
        doi = item.get("doi")
        source = item.get("source")

        short_title = sanitize_filename(title[:35].strip())
        safe_author = sanitize_filename(author)
        filename = f"{year}_{safe_author}_{short_title}.pdf"
        target_path = RAW_PDF_DIR / filename

        print(f"[{idx}] 處理文獻：{title[:60]}...")
        print(f"    來源：{source} | 年份：{year}")

        # 情況 A：具備直接 OA PDF 連結
        if item["is_oa"] and pdf_url and pdf_url.startswith("http"):
            print(f"    [下載] 偵測到合法 OA 直連，正在自動下載原件...")
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                req = urllib.request.Request(pdf_url, headers=headers)
                with urllib.request.urlopen(req, timeout=25) as resp:
                    content_type = resp.headers.get("Content-Type", "")
                    content_data = resp.read()

                    # 基本驗證是否為 PDF 或非空檔案
                    if len(content_data) > 1000 and (content_data.startswith(b"%PDF") or "pdf" in content_type.lower() or pdf_url.lower().endswith(".pdf")):
                        with open(target_path, "wb") as pf:
                            pf.write(content_data)
                        print(f"    [成功] 下載成功！已儲存至：{target_path}")
                        oa_success += 1
                        item["download_status"] = "downloaded_oa"
                        item["local_file"] = str(target_path)
                    else:
                        print(f"    [警告] 遠端下載內容非標準 PDF（可能受出版商反爬蟲限制），列為人工取得。")
                        manual_required.append(item)
                        item["download_status"] = "manual_required"
            except Exception as err:
                print(f"    [錯誤] 下載連線失敗（{err}），列為人工取得。")
                manual_required.append(item)
                item["download_status"] = "manual_required"
        else:
            # 情況 B：無直接 OA（封閉授權 / 付費期刊）
            print(f"    [封閉] 本篇為封閉訂閱文獻（非直接開放取用），需透過學校圖書館授權取得。")
            manual_required.append(item)
            item["download_status"] = "manual_required"

        final_records.append(item)

    # 保存元數據
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(final_records, f, ensure_ascii=False, indent=2)

    # 輸出彙整報告
    print(f"\n" + "="*70)
    print(f"[總結] 全文獲取歷程總結：")
    print(f"  • 自動下載成功 (Open Access)：{oa_success} 篇")
    print(f"  • 需人工取得文獻 (圖書館/VPN)：{len(manual_required)} 篇")
    print(f"  • 元數據已更新至：{METADATA_FILE}")
    print("="*70)

    if manual_required:
        print(f"\n[指引] 【需人工自學校圖書館取得之高品質文獻指引】：")
        print(f"請利用學校圖書館電子資源整合查詢或校園 VPN，依 DOI/篇名下載後，以標準檔名存放至 01_papers/raw_pdf/：\n")
        for m_item in manual_required:
            short_t = sanitize_filename(m_item['title'][:35].strip())
            safe_a = sanitize_filename(m_item['first_author'])
            suggested_name = f"{m_item['year']}_{safe_a}_{short_t}.pdf"
            print(f"  • 篇名：{m_item['title']}")
            print(f"    來源：{m_item['source']}")
            print(f"    DOI ：{m_item['doi']}")
            print(f"    建議檔名：{suggested_name}")
            print(f"    目標路徑：01_papers/raw_pdf/{suggested_name}\n")

def main():
    if len(sys.argv) < 2:
        print("使用方式：")
        print("  1. 檢索候選文獻並生成評估清單：")
        print("     python scripts/fetch_openalex.py search \"AI Agents higher education\"")
        print("  2. 依 candidate_papers.md 勾選結果自動下載 OA / 提示手動下載：")
        print("     python scripts/fetch_openalex.py download")
        return

    cmd = sys.argv[1].lower()
    if cmd == "search":
        topic = "AI Agents in Higher Education scaffolding"
        if len(sys.argv) > 2:
            topic = " ".join(sys.argv[2:])
        search_candidate_papers(topic, max_candidates=10, start_year=2022)
    elif cmd == "download":
        download_selected_papers()
    else:
        # 相容原本直接傳關鍵字的用法，預設執行 search
        search_candidate_papers(" ".join(sys.argv[1:]), max_candidates=10, start_year=2022)

if __name__ == "__main__":
    main()
