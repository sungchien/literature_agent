"""
scripts/fetch_openalex.py

OpenAlex 學術文獻檢索、審查與全文獲取追蹤管理工具
核心指令：
1. search:   向 OpenAlex 檢索文獻，自動生成流水號 candidate_papers_XX.md 與專屬追蹤檔案
2. list:     全域瀏覽目前所有 candidate_papers[00-99].md 的檢索條件、審查狀態與文獻獲取進度
3. review:   互動式文獻審查工具（禁止手動編輯），逐篇進行「採納納入 [+]」、「刪除排除 [-]」、「保留待定 [ ]」
4. download: 依據選定清單，自動下載標記為 [+] 的 OA PDF 原件，並分類記錄於專屬追蹤檔案中
5. track:    持續追蹤管理工具，自動偵測 raw_pdf/ 目錄中由研究者從圖書館補全的訂閱 PDF 並更新追蹤報告
"""

import os
import re
import sys
import json
import datetime
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# 設定 Windows 終端輸出編碼
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 工作區目錄常數
PAPERS_DIR = Path("01_papers")
RAW_PDF_DIR = Path("01_papers/raw_pdf")
METADATA_FILE = Path("01_papers/downloaded_metadata.json")
DEFAULT_CANDIDATE_MD = Path("01_papers/candidate_papers.md")
CANDIDATE_MD_FILE = DEFAULT_CANDIDATE_MD  # 保持相容性


def sanitize_filename(name: str) -> str:
    """清理檔名中的非法字元，替換為安全底線"""
    return re.sub(r'[\\/*?:"<>| ]', '_', name)


def reconstruct_abstract(inverted_index: Optional[dict]) -> str:
    """將 OpenAlex 倒排索引格式之摘要還原為完整自然段落"""
    if not inverted_index:
        return "（未提供摘要，請參閱原文 DOI 連結）"
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort(key=lambda x: x[0])
    return " ".join([word for _, word in word_positions])


def get_all_candidate_files() -> List[Path]:
    """取得 01_papers 目錄下所有 candidate_papers_XX.md 檔案，按流水號排序（排除 tracking 報告）"""
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    raw_files = list(PAPERS_DIR.glob("candidate_papers_*.md"))
    files = [p for p in raw_files if re.search(r"candidate_papers_\d+\.md$", p.name)]
    
    def sort_key(p: Path):
        m = re.search(r"candidate_papers_(\d+)\.md$", p.name)
        if m:
            return (1, int(m.group(1)))
        return (2, p.name)

    files.sort(key=sort_key)
    return files


def get_next_sequence_info() -> Tuple[str, Path]:
    """計算下一個檢索流水號（兩位數格式如 01, 02... 99）並回傳對應檔名路徑"""
    files = get_all_candidate_files()
    max_seq = 0
    for f in files:
        m = re.search(r"candidate_papers_(\d+)\.md$", f.name)
        if m:
            seq_num = int(m.group(1))
            if seq_num > max_seq:
                max_seq = seq_num
    
    next_seq = max_seq + 1
    seq_str = f"{next_seq:02d}"
    target_path = PAPERS_DIR / f"candidate_papers_{seq_str}.md"
    return seq_str, target_path


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """解析 Markdown 中的 YAML Frontmatter 與正文"""
    fm = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1].strip()
            body = parts[2]
            current_section = None
            for line in raw_yaml.split("\n"):
                line = line.rstrip()
                if not line or line.startswith("#"):
                    continue
                if line.endswith(":") and not line.startswith(" "):
                    current_section = line[:-1].strip()
                    fm[current_section] = {}
                elif ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if v.isdigit():
                        v = int(v)
                    if current_section:
                        fm[current_section][k] = v
                    else:
                        fm[k] = v
    return fm, body


def update_frontmatter_stats(file_path: Path) -> Dict[str, int]:
    """掃描 Markdown 正文中的 [+], [-], [ ] 標記，自動更新 YAML Frontmatter 統計"""
    if not file_path.exists():
        return {"total": 0, "included": 0, "excluded": 0, "pending": 0}

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    fm, body = parse_frontmatter(content)

    # 統計標記：支援 [+] (以及向下相容 [x]/[X])、[-]、[ ]
    headings = re.findall(r"^##\s+(\d+)\.\s*\[([\s\+\-xX])\]", body, re.MULTILINE)
    total = len(headings)
    included = 0
    excluded = 0
    pending = 0

    for idx, mark in headings:
        if mark in ['+', 'x', 'X']:
            included += 1
        elif mark == '-':
            excluded += 1
        else:
            pending += 1

    stats = {
        "total": total,
        "included": included,
        "excluded": excluded,
        "pending": pending
    }

    search_info = fm.get("search_info", {})
    seq_val = search_info.get("sequence_id")
    if not seq_val:
        m = re.search(r"candidate_papers_(\d+)\.md", file_path.name)
        seq_id = m.group(1) if m else "01"
    else:
        seq_id = f"{int(seq_val):02d}" if str(seq_val).isdigit() else str(seq_val)

    search_time = search_info.get("search_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    query = search_info.get("query", "Unknown Query")
    max_res = search_info.get("max_results", total)
    start_y = search_info.get("start_year", 2022)
    end_y = search_info.get("end_year", 2026)

    yaml_block = (
        "---\n"
        "search_info:\n"
        f"  sequence_id: \"{seq_id}\"\n"
        f"  search_time: \"{search_time}\"\n"
        f"  query: \"{query}\"\n"
        f"  max_results: {max_res}\n"
        f"  start_year: {start_y}\n"
        f"  end_year: {end_y}\n"
        "review_stats:\n"
        f"  total: {total}\n"
        f"  included: {included}\n"
        f"  excluded: {excluded}\n"
        f"  pending: {pending}\n"
        "---\n"
    )

    new_content = yaml_block + body.lstrip()
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return stats


def get_tracking_paths(seq_id: str) -> Tuple[Path, Path]:
    """依序號取得對應之 tracking JSON 與 Markdown 檔案路徑"""
    json_path = PAPERS_DIR / f"candidate_papers_{seq_id}_tracking.json"
    md_path = PAPERS_DIR / f"candidate_papers_{seq_id}_tracking.md"
    return json_path, md_path


def load_or_init_tracking(seq_id: str, candidate_file: Path) -> Dict[str, Any]:
    """載入或初始化特定 candidate_papers 批次之文獻獲取追蹤資料"""
    json_path, _ = get_tracking_paths(seq_id)
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    fm, _ = parse_frontmatter(candidate_file.read_text(encoding="utf-8")) if candidate_file.exists() else ({}, "")
    s_info = fm.get("search_info", {})
    query = s_info.get("query", "Unknown Query")

    return {
        "sequence_id": seq_id,
        "candidate_file": candidate_file.name,
        "query": query,
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_candidates": 0,
            "total_included": 0,
            "oa_downloaded": 0,
            "subscription_provided": 0,
            "subscription_pending": 0
        },
        "oa_downloaded_papers": [],
        "subscription_provided_papers": [],
        "subscription_pending_papers": []
    }


def save_and_render_tracking(tracking_data: Dict[str, Any]):
    """將追蹤資料存入 JSON 並生成美觀專業之 Markdown 報告"""
    seq_id = tracking_data.get("sequence_id", "01")
    json_path, md_path = get_tracking_paths(seq_id)

    tracking_data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    oa_list = tracking_data.get("oa_downloaded_papers", [])
    prov_list = tracking_data.get("subscription_provided_papers", [])
    pend_list = tracking_data.get("subscription_pending_papers", [])

    tracking_data["summary"]["oa_downloaded"] = len(oa_list)
    tracking_data["summary"]["subscription_provided"] = len(prov_list)
    tracking_data["summary"]["subscription_pending"] = len(pend_list)
    total_included = len(oa_list) + len(prov_list) + len(pend_list)
    tracking_data["summary"]["total_included"] = total_included

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(tracking_data, jf, ensure_ascii=False, indent=2)

    tot_acquired = len(oa_list) + len(prov_list)
    rate = (tot_acquired / total_included * 100) if total_included > 0 else 0

    lines = [
        f"# 文獻獲取與訂閱追蹤紀錄報告：candidate_papers_{seq_id}\n",
        f"> **檢索主題**：`{tracking_data.get('query', 'N/A')}` | **最後更新時間**：`{tracking_data['last_updated']}`",
        ">",
        f"> **【獲取總結】**：採納文獻共 **{total_included}** 篇，已入庫 **{tot_acquired}** 篇（取得率：**{rate:.1f}%**）",
        f"> - 🟢 合法 Open Access 自動下載：**{len(oa_list)}** 篇",
        f"> - 🔵 封閉訂閱期刊（研究者已自圖書館補全）：**{len(prov_list)}** 篇",
        f"> - 🟡 封閉訂閱期刊（尚未提供 / 待向圖書館調閱）：**{len(pend_list)}** 篇\n",
        "---\n",
        "## 一、已經自動下載之合法 Open Access (OA) PDF\n"
    ]

    if oa_list:
        lines.append("| 編號 | 論文篇名 | 第一作者與年份 | 發表來源 (Source) | 檔案大小 | 本機 PDF 檔案 |")
        lines.append("| :---: | :--- | :---: | :--- | :---: | :--- |")
        for item in oa_list:
            t = item.get("title", "")
            ay = f"{item.get('first_author', '')} ({item.get('year', '')})"
            src = item.get("source", "")
            sz = f"{item.get('file_size_kb', 0):.1f} KB"
            fn = item.get("pdf_filename", "")
            lines.append(f"| {item.get('index', '')} | {t} | {ay} | `{src}` | {sz} | `01_papers/raw_pdf/{fn}` |")
        lines.append("")
    else:
        lines.append("*目前無自動下載之 Open Access 文獻。*\n")

    lines.append("---\n")
    lines.append("## 二、已經提供之訂閱文獻 PDF（研究者自圖書館取得）\n")
    if prov_list:
        lines.append("| 編號 | 論文篇名 | 第一作者與年份 | DOI / 調閱來源 | 提供入庫時間 | 本機 PDF 檔案 |")
        lines.append("| :---: | :--- | :---: | :--- | :---: | :--- |")
        for item in prov_list:
            t = item.get("title", "")
            ay = f"{item.get('first_author', '')} ({item.get('year', '')})"
            doi = item.get("doi", "")
            pt = item.get("provided_time", "")
            fn = item.get("pdf_filename", "")
            lines.append(f"| {item.get('index', '')} | {t} | {ay} | {doi} | {pt} | `01_papers/raw_pdf/{fn}` |")
        lines.append("")
    else:
        lines.append("*目前尚未有研究者自圖書館補全之訂閱文獻。*\n")

    lines.append("---\n")
    lines.append("## 三、尚未提供之訂閱文獻 PDF（待向校園圖書館調閱）\n")
    if pend_list:
        lines.append(f"> 💡 **【研究者調閱指引】**：請透過大學圖書館電子資料庫整合查詢或校園 VPN，依據下方 DOI 連結下載全文，並以**建議檔名**儲存至 `01_papers/raw_pdf/`。完成後執行 `python scripts/fetch_openalex.py track {seq_id}`，系統將自動感知並更新本追蹤表！\n")
        lines.append("| 編號 | 論文篇名 | 作者/年份 | 發表期刊 (Source) | DOI 調閱連結 | 建議存放檔名 |")
        lines.append("| :---: | :--- | :---: | :--- | :--- | :--- |")
        for item in pend_list:
            t = item.get("title", "")
            ay = f"{item.get('first_author', '')} ({item.get('year', '')})"
            src = item.get("source", "")
            doi = item.get("doi", "")
            doi_link = f"[{doi}]({doi})" if doi.startswith("http") else doi
            sug = item.get("suggested_filename", "")
            lines.append(f"| {item.get('index', '')} | {t} | {ay} | `{src}` | {doi_link} | `{sug}` |")
        lines.append("")
    else:
        lines.append("🎉 *所有採納之訂閱文獻皆已全數入庫，無待調閱項目！*\n")

    lines.append("---\n")
    lines.append("### 🛠️ 追蹤與管理指令速查")
    lines.append(f"- 重新偵測 `raw_pdf/` 並更新追蹤：`python scripts/fetch_openalex.py track {seq_id}`")
    lines.append(f"- 瀏覽所有候選批次進度：`python scripts/fetch_openalex.py list`")
    lines.append(f"- 再次進行互動審查：`python scripts/fetch_openalex.py review {seq_id}`\n")

    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write("\n".join(lines))


def sync_tracking_from_candidate(seq_id: str, candidate_file: Path):
    """依據 candidate_papers 正文中的 [+] 標記，同步更新追蹤檔案的基礎結構"""
    tracking_data = load_or_init_tracking(seq_id, candidate_file)
    cache_file = PAPERS_DIR / f"candidates_cache_{seq_id}.json"
    cache_map = {}
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as cf:
                for it in json.load(cf):
                    cache_map[it["index"]] = it
        except Exception:
            pass

    content = candidate_file.read_text(encoding="utf-8")
    included_indices = [int(m.group(1)) for m in re.finditer(r"##\s+(\d+)\.\s*\[([\+xX])\]", content)]

    existing_oa = {it["index"]: it for it in tracking_data.get("oa_downloaded_papers", [])}
    existing_prov = {it["index"]: it for it in tracking_data.get("subscription_provided_papers", [])}
    existing_pend = {it["index"]: it for it in tracking_data.get("subscription_pending_papers", [])}

    new_oa = []
    new_prov = []
    new_pend = []

    for idx in included_indices:
        if idx in existing_oa:
            new_oa.append(existing_oa[idx])
        elif idx in existing_prov:
            new_prov.append(existing_prov[idx])
        elif idx in existing_pend:
            new_pend.append(existing_pend[idx])
        else:
            c_info = cache_map.get(idx, {})
            title = c_info.get("title", f"Paper #{idx}")
            yr = c_info.get("year", 2024)
            auth = c_info.get("first_author", "Author")
            src = c_info.get("source", "Unknown Source")
            doi = c_info.get("doi", "")
            is_oa = c_info.get("is_oa", False)
            short_t = sanitize_filename(title[:35].strip())
            safe_a = sanitize_filename(auth)
            sug_name = f"{yr}_{safe_a}_{short_t}.pdf"

            item_obj = {
                "index": idx,
                "title": title,
                "first_author": auth,
                "year": yr,
                "source": src,
                "doi": doi,
                "is_oa": is_oa,
                "suggested_filename": sug_name,
                "pdf_filename": sug_name,
                "status": "pending_download"
            }
            new_pend.append(item_obj)

    tracking_data["oa_downloaded_papers"] = new_oa
    tracking_data["subscription_provided_papers"] = new_prov
    tracking_data["subscription_pending_papers"] = new_pend

    save_and_render_tracking(tracking_data)


def select_candidate_file(file_arg: Optional[str] = None) -> Optional[Path]:
    """輔助函式：讓使用者選擇或解析欲操作的 candidate_papers 檔案"""
    files = get_all_candidate_files()
    if not files:
        print(f"[錯誤] 在 {PAPERS_DIR} 找不到任何 candidate_papers 檔案！請先執行 search 指令。")
        return None

    if file_arg:
        p = Path(file_arg)
        if p.exists():
            return p
        p2 = PAPERS_DIR / file_arg
        if p2.exists():
            return p2
        m_num = re.search(r"\d+", file_arg)
        if m_num:
            num = int(m_num.group())
            for f in files:
                m_f = re.search(r"candidate_papers_(\d+)\.md$", f.name)
                if m_f and int(m_f.group(1)) == num:
                    return f

    if len(files) == 1:
        return files[0]

    print("\n" + "="*70)
    print("發現多個候選文獻評估清單，請選擇欲操作的檔案：")
    for idx, f in enumerate(files, 1):
        fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        s_info = fm.get("search_info", {})
        r_stats = fm.get("review_stats", {})
        q = s_info.get("query", "無查詢詞")
        t = s_info.get("search_time", "未知時間")
        inc = r_stats.get("included", 0)
        exc = r_stats.get("excluded", 0)
        pen = r_stats.get("pending", 0)
        tot = r_stats.get("total", 0)
        print(f"  [{idx}] {f.name} (檢索: 『{q}』 | 時間: {t} | 採納: {inc}, 排除: {exc}, 保留: {pen} / 共 {tot} 篇)")

    latest_idx = len(files)
    choice = input(f"\n請輸入選單編號 (1~{latest_idx}，預設最新 [{latest_idx}]，或輸入 q 取消): ").strip()
    if choice.lower() in ['q', 'quit', 'exit']:
        return None
    if not choice:
        return files[-1]
    if choice.isdigit() and 1 <= int(choice) <= len(files):
        return files[int(choice) - 1]

    print("[警告] 輸入無效，預設選取最新檔案。")
    return files[-1]


def search_candidate_papers(
    query: str,
    max_candidates: int = 10,
    start_year: int = 2022,
    end_year: int = 2026,
    target_file: Optional[Path] = None
) -> Optional[Path]:
    """
    功能 1 (search)：向 OpenAlex API 檢索候選文獻，生成帶流水號之 candidate_papers_XX.md 與追蹤檔
    """
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)

    if target_file is None:
        seq_str, target_path = get_next_sequence_info()
    else:
        target_path = target_file
        m = re.search(r"candidate_papers_(\d+)\.md$", target_path.name)
        seq_str = f"{int(m.group(1)):02d}" if m else "01"

    cache_path = PAPERS_DIR / f"candidates_cache_{seq_str}.json"

    print(f"\n[查詢] 正在向 OpenAlex 檢索候選學術文獻：『{query}』...")
    print(f"[條件] 年份區間：{start_year} - {end_year} 年 | 候選評估篇數：{max_candidates} 篇")
    print(f"[目標] 輸出流水號檔案：{target_path.name}")

    params = {
        "search": query,
        "filter": f"publication_year:{start_year}-{end_year}",
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
        return None

    results = data.get("results", [])
    if not results:
        print("[警告] 未找到符合條件之文獻，請調整檢索關鍵字或放寬年份限制。")
        return None

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    frontmatter_lines = [
        "---",
        "search_info:",
        f"  sequence_id: \"{seq_str}\"",
        f"  search_time: \"{now_str}\"",
        f"  query: \"{query}\"",
        f"  max_results: {len(results)}",
        f"  start_year: {start_year}",
        f"  end_year: {end_year}",
        "review_stats:",
        f"  total: {len(results)}",
        "  included: 0",
        "  excluded: 0",
        f"  pending: {len(results)}",
        "---",
        ""
    ]

    header_lines = [
        f"# 候選文獻評估與品質篩選清單：{target_path.name}\n",
        f"> **檢索主題**：`{query}` | **檢索年份**：{start_year}-{end_year} | **檢索總數**：{len(results)} 篇",
        ">",
        "> ⚠️ **【系統自動化管理提示（請勿手動編輯）】**：",
        "> 本檔案由系統腳本自動維護，**請勿直接手動編輯此 Markdown 檔案**，以防格式錯位破壞資料完整性！",
        "> 所有候選文獻的納入、排除與審查決策，請一律透過終端機執行專屬審查工具：",
        f"> 👉 `python scripts/fetch_openalex.py review {seq_str}`",
        ">",
        "> **【文獻審查三種狀態說明】**：",
        "> - `[+]` **採納納入**：確認與論文主題高度相關、具備學術品質，後續將自動獲取全文。",
        "> - `[-]` **刪除排除**：主題偏離、方法不符或品質不足，明確予以剔除。",
        "> - `[ ]` **保留待定**：暫時不表意見，留待後續進一步評估。",
        ">",
        "> **【下一步工作指引】**：",
        f"> 1. 審查決策：`python scripts/fetch_openalex.py review {seq_str}`",
        f"> 2. 全文下載：`python scripts/fetch_openalex.py download {seq_str}`",
        f"> 3. 持續追蹤：`python scripts/fetch_openalex.py track {seq_str}`\n",
        "---\n"
    ]

    candidates = []
    paper_blocks = []

    for idx, item in enumerate(results, 1):
        title = item.get("title") or "Untitled"
        pub_year = item.get("publication_year") or "UnknownYear"
        cited_count = item.get("cited_by_count", 0)
        doi = item.get("doi") or "無 DOI"

        primary_loc = item.get("primary_location") or {}
        source_obj = primary_loc.get("source") or {}
        source_name = source_obj.get("display_name") or "未列明期刊/研討會"

        authorships = item.get("authorships", [])
        if authorships and "author" in authorships[0]:
            first_author = authorships[0]["author"].get("display_name", "Author").split()[-1]
        else:
            first_author = "Author"

        is_oa = item.get("open_access", {}).get("is_oa", False)
        best_oa = item.get("best_oa_location") or {}
        pdf_url = best_oa.get("pdf_url") or item.get("open_access", {}).get("oa_url")
        oa_status_text = "[開放取用] Open Access 直連" if (is_oa and pdf_url and pdf_url.startswith("http")) else "[封閉訂閱] 非直接 OA（需校園圖書館授權）"

        abstract_text = reconstruct_abstract(item.get("abstract_inverted_index"))

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
            "abstract": abstract_text,
            "status": "pending"
        }
        candidates.append(record)

        block = [
            f"## {idx}. [ ] {title}\n",
            f"- **發表來源 (Source)**：`{source_name}`",
            f"- **作者與年份**：{first_author} ({pub_year}) | **被引用數**：{cited_count} 次",
            f"- **審查狀態**：`[ ]` 保留待定 (Pending)",
            f"- **全文狀態**：{oa_status_text}",
            f"- **DOI 直連**：{doi}",
            "- **摘要 (Abstract)**：",
            f"  > {abstract_text}\n",
            "---\n"
        ]
        paper_blocks.append("\n".join(block))

    full_content = "\n".join(frontmatter_lines) + "\n".join(header_lines) + "\n".join(paper_blocks)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(full_content)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    with open(DEFAULT_CANDIDATE_MD, "w", encoding="utf-8") as f:
        f.write(full_content)

    initial_tracking = {
        "sequence_id": seq_str,
        "candidate_file": target_path.name,
        "query": query,
        "last_updated": now_str,
        "summary": {
            "total_candidates": len(candidates),
            "total_included": 0,
            "oa_downloaded": 0,
            "subscription_provided": 0,
            "subscription_pending": 0
        },
        "oa_downloaded_papers": [],
        "subscription_provided_papers": [],
        "subscription_pending_papers": []
    }
    save_and_render_tracking(initial_tracking)

    print(f"\n[成功] 候選書目清單已輸出至：{target_path}")
    print(f"[成功] 專屬獲取追蹤檔案已建立：candidate_papers_{seq_str}_tracking.md")
    print(f"[統計] 序號：{seq_str} | 共整理 {len(candidates)} 篇文獻。")
    print(f"\n[下一步操作指南]：")
    print(f"  • 啟動審查：python scripts/fetch_openalex.py review {seq_str}")
    print(f"  • 瀏覽清單：python scripts/fetch_openalex.py list")

    return target_path


def list_candidate_papers():
    """
    功能 2 (list)：瀏覽目前所有 candidate_papers[00-99].md 的檢索資訊、審核狀態與全文追蹤進度
    """
    files = get_all_candidate_files()
    if not files:
        print(f"\n[提示] 目前在 {PAPERS_DIR} 中尚未找到任何候選文獻清單。請先執行 search 指令進行檢索！")
        return

    print("\n" + "="*112)
    print("📚 碩士論文候選文獻庫總覽 (Master Thesis Candidate Papers Catalog)")
    print("="*112)
    header = f"{'序號':<4} {'檔案名稱':<24} {'檢索時間':<17} {'篇數':<5} {'採納[+]':<7} {'排除[-]':<7} {'待定[ ]':<7} {'OA下載':<7} {'已補訂閱':<8} {'待調閱':<6} {'檢索關鍵字'}"
    print(header)
    print("-" * 112)

    total_candidates_all = 0
    total_included_all = 0
    total_excluded_all = 0
    total_pending_all = 0
    total_oa_all = 0
    total_sub_prov_all = 0
    total_sub_pend_all = 0

    for f in files:
        fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        s_info = fm.get("search_info", {})
        r_stats = fm.get("review_stats", {})

        m = re.search(r"candidate_papers_(\d+)\.md$", f.name)
        seq_str = m.group(1) if m else "01"
        seq_fmt = f"{int(seq_str):02d}" if seq_str.isdigit() else seq_str

        q = s_info.get("query", "無查詢詞")
        t = s_info.get("search_time", "未知時間")[:16]
        tot = r_stats.get("total", 0)
        inc = r_stats.get("included", 0)
        exc = r_stats.get("excluded", 0)
        pen = r_stats.get("pending", 0)

        track_json, _ = get_tracking_paths(seq_fmt)
        oa_cnt = 0
        prov_cnt = 0
        pend_cnt = 0
        if track_json.exists():
            try:
                with open(track_json, "r", encoding="utf-8") as tj:
                    t_data = json.load(tj)
                    t_sum = t_data.get("summary", {})
                    oa_cnt = t_sum.get("oa_downloaded", 0)
                    prov_cnt = t_sum.get("subscription_provided", 0)
                    pend_cnt = t_sum.get("subscription_pending", 0)
            except Exception:
                pass

        total_candidates_all += tot
        total_included_all += inc
        total_excluded_all += exc
        total_pending_all += pen
        total_oa_all += oa_cnt
        total_sub_prov_all += prov_cnt
        total_sub_pend_all += pend_cnt

        q_display = q[:24] + "..." if len(q) > 24 else q
        row = f"{seq_fmt:<4} {f.name:<24} {t:<17} {tot:<5} {inc:<7} {exc:<7} {pen:<7} {oa_cnt:<7} {prov_cnt:<8} {pend_cnt:<6} {q_display}"
        print(row)

    print("-" * 112)
    summary_row = f"{'總計':<4} {f'共 {len(files)} 批候選清單':<24} {'-':<17} {total_candidates_all:<5} {total_included_all:<7} {total_excluded_all:<7} {total_pending_all:<7} {total_oa_all:<7} {total_sub_prov_all:<8} {total_sub_pend_all:<6} 全專案文獻池"
    print(summary_row)
    print("=" * 112)
    print("\n💡 常用操作指引：")
    print("  • 審查特定清單：python scripts/fetch_openalex.py review <序號>")
    print("  • 下載採納全文：python scripts/fetch_openalex.py download <序號>")
    print("  • 追蹤調閱進度：python scripts/fetch_openalex.py track <序號>\n")


def review_candidate_papers(file_arg: Optional[str] = None):
    """
    功能 3 (review): 互動式審查工具（全面禁止手動編輯），逐篇判定 [+] 採納、[-] 排除、[ ] 保留
    """
    target_file = select_candidate_file(file_arg)
    if not target_file:
        return

    m = re.search(r"candidate_papers_(\d+)\.md$", target_file.name)
    seq_str = f"{int(m.group(1)):02d}" if m else "01"

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    fm, body = parse_frontmatter(content)
    s_info = fm.get("search_info", {})
    query = s_info.get("query", "未知主題")

    pattern = r"(##\s+(\d+)\.\s*\[([\s\+\-xX])\]\s+([^\n]+))"
    matches = list(re.finditer(pattern, body))

    if not matches:
        print(f"[錯誤] 在 {target_file.name} 中找不到任何論文條目。")
        return

    print("\n" + "="*80)
    print(f"📋 啟動互動式文獻審查工具：{target_file.name}")
    print(f"🔍 檢索主題：『{query}』 | 候選文獻總數：{len(matches)} 篇")
    print("決策選項說明：")
    print("  [+] 或 [y] 採納納入 (Include) -> 標記為 [+]，後續自動抓取全文")
    print("  [-] 或 [n] 刪除排除 (Exclude) -> 標記為 [-]，方法或主題不符予以剔除")
    print("  [k] 或 [空白] 保留待定 (Pending) -> 標記為 [ ]，暫時不表意見")
    print("  [Enter]    維持目前審核狀態，跳至下一篇")
    print("  [b]        返回上一篇文獻重新評估")
    print("  [q]        完成儲存並退出審查系統")
    print("="*80)

    paper_sections = []
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i + 1 < len(matches) else len(body)
        sec_text = body[start:end]
        raw_mark = matches[i].group(3)
        std_mark = '+' if raw_mark in ['+', 'x', 'X'] else ('-' if raw_mark == '-' else ' ')
        paper_sections.append({
            "idx": int(matches[i].group(2)),
            "mark": std_mark,
            "title": matches[i].group(4).strip(),
            "text": sec_text
        })

    idx_cursor = 0
    modified = False

    while idx_cursor < len(paper_sections):
        item = paper_sections[idx_cursor]
        current_mark = item["mark"]
        status_desc = "採納納入 [+]" if current_mark == '+' else ("刪除排除 [-]" if current_mark == '-' else "保留待定 [ ]")

        src_m = re.search(r"- \*\*發表來源 \(Source\)\*\*：`([^`]+)`", item["text"])
        year_m = re.search(r"- \*\*作者與年份\*\*：([^\n]+)", item["text"])
        oa_m = re.search(r"- \*\*全文狀態\*\*：([^\n]+)", item["text"])
        doi_m = re.search(r"- \*\*DOI 直連\*\*：([^\n]+)", item["text"])
        abs_m = re.search(r"- \*\*摘要 \(Abstract\)\*\*：\s*\n\s*>\s*([^\n]+)", item["text"])

        src = src_m.group(1) if src_m else "未知來源"
        yr = year_m.group(1) if year_m else ""
        oa_st = oa_m.group(1) if oa_m else ""
        doi = doi_m.group(1) if doi_m else ""
        ab = abs_m.group(1) if abs_m else "無摘要"

        print(f"\n[{idx_cursor + 1}/{len(paper_sections)}] 目前審查狀態：【{status_desc}】")
        print(f"📖 篇名：{item['title']}")
        print(f"🏛️ 來源：{src} | {yr} | 全文：{oa_st}")
        print(f"🔗 DOI ：{doi}")
        print(f"📝 摘要：{ab[:220]}..." if len(ab) > 220 else f"📝 摘要：{ab}")

        prompt = f"👉 請輸入審查決策 [+/y:採納, -/n:排除, k/空白:保留, b:上一篇, Enter:跳過, q:儲存離開]: "
        try:
            user_choice = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n[中斷] 正在儲存審查成果並更新追蹤檔...")
            break

        if user_choice == 'q':
            print("\n[退出] 正在儲存審查成果並更新追蹤檔...")
            break
        elif user_choice == 'b':
            if idx_cursor > 0:
                idx_cursor -= 1
            else:
                print("已在第一篇文獻！")
            continue
        elif user_choice in ['+', 'y', '1']:
            new_mark = '+'
            new_status_line = "- **審查狀態**：`[+]` 採納納入 (Included)"
        elif user_choice in ['-', 'n', '2']:
            new_mark = '-'
            new_status_line = "- **審查狀態**：`[-]` 刪除排除 (Excluded)"
        elif user_choice in ['k', '3', ' ']:
            new_mark = ' '
            new_status_line = "- **審查狀態**：`[ ]` 保留待定 (Pending)"
        else:
            idx_cursor += 1
            continue

        if new_mark != current_mark:
            old_header_re = rf"##\s+{item['idx']}\.\s*\[[\s\+\-xX]\]"
            new_header = f"## {item['idx']}. [{new_mark}]"
            updated_text = re.sub(old_header_re, new_header, item["text"], count=1)
            updated_text = re.sub(r"- \*\*審查狀態\*\*：[^\n]+", new_status_line, updated_text)

            item["mark"] = new_mark
            item["text"] = updated_text
            modified = True

        idx_cursor += 1

    header_part = body[:matches[0].start()]
    new_body = header_part + "".join([p["text"] for p in paper_sections])

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content.split("---", 2)[0] + "---" + content.split("---", 2)[1] + "---\n" + new_body.lstrip())

    stats = update_frontmatter_stats(target_file)
    sync_tracking_from_candidate(seq_str, target_file)

    print("\n" + "="*75)
    print(f"✨ 審查紀錄已完整保存至：{target_file.name}")
    print(f"📊 最新統計：總數 {stats['total']} 篇 | 採納[+]: {stats['included']} 篇 | 排除[-]: {stats['excluded']} 篇 | 待定[ ]: {stats['pending']} 篇")
    print(f"📋 專屬追蹤檔已同步刷新：candidate_papers_{seq_str}_tracking.md")
    print(f"📥 下一步全文下載指引：python scripts/fetch_openalex.py download {seq_str}")
    print("="*75)


def get_candidate_papers_summary(file_arg: Optional[str] = None) -> Dict[str, Any]:
    """
    程式化讀取候選論文清單與詳細欄位（供 MCP 伺服器與 Agent 於對話中調用）
    """
    target_file = select_candidate_file(file_arg)
    if not target_file or not target_file.exists():
        return {"error": f"找不到候選論文檔案：{file_arg or '最新清單'}"}

    m = re.search(r"candidate_papers_(\d+)\.md$", target_file.name)
    seq_str = f"{int(m.group(1)):02d}" if m else "01"

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    fm, body = parse_frontmatter(content)
    pattern = r"(##\s+(\d+)\.\s*\[([\s\+\-xX])\]\s+([^\n]+))"
    matches = list(re.finditer(pattern, body))

    papers = []
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i + 1 < len(matches) else len(body)
        sec_text = body[start:end]
        raw_mark = matches[i].group(3)
        std_mark = '+' if raw_mark in ['+', 'x', 'X'] else ('-' if raw_mark == '-' else ' ')
        idx = int(matches[i].group(2))
        title = matches[i].group(4).strip()

        src_m = re.search(r"- \*\*發表來源 \(Source\)\*\*：`([^`]+)`", sec_text)
        year_m = re.search(r"- \*\*作者與年份\*\*：([^\n]+)", sec_text)
        oa_m = re.search(r"- \*\*全文狀態\*\*：([^\n]+)", sec_text)
        doi_m = re.search(r"- \*\*DOI 直連\*\*：([^\n]+)", sec_text)
        abs_m = re.search(r"- \*\*摘要 \(Abstract\)\*\*：\s*\n\s*>\s*([^\n]+)", sec_text)

        status_desc = "採納 [+]" if std_mark == '+' else ("排除 [-]" if std_mark == '-' else "待定 [ ]")

        papers.append({
            "index": idx,
            "mark": std_mark,
            "status": status_desc,
            "title": title,
            "source": src_m.group(1) if src_m else "未知來源",
            "authors_year": year_m.group(1).strip() if year_m else "",
            "oa_status": oa_m.group(1).strip() if oa_m else "",
            "doi": doi_m.group(1).strip() if doi_m else "",
            "abstract": abs_m.group(1).strip() if abs_m else ""
        })

    return {
        "file": target_file.name,
        "sequence": seq_str,
        "query": fm.get("search_info", {}).get("query", ""),
        "stats": fm.get("stats", {}),
        "total": len(papers),
        "papers": papers
    }


def apply_review_decisions(file_arg: Optional[str] = None, decisions: Optional[Dict[Any, str]] = None) -> Dict[str, Any]:
    """
    程式化批次更新候選論文審查狀態（支援 Agent 於對話中經由 MCP 提交研究者的審查決策）
    decisions: 鍵為論文序號（如 "1" 或 1），值為 "+", "-", " "（或 "include", "exclude", "pending"）
    """
    if not decisions:
        return {"error": "未提供任何審查決策 (decisions 為空)"}

    target_file = select_candidate_file(file_arg)
    if not target_file or not target_file.exists():
        return {"error": f"找不到候選論文檔案：{file_arg or '最新清單'}"}

    m = re.search(r"candidate_papers_(\d+)\.md$", target_file.name)
    seq_str = f"{int(m.group(1)):02d}" if m else "01"

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    fm, body = parse_frontmatter(content)
    pattern = r"(##\s+(\d+)\.\s*\[([\s\+\-xX])\]\s+([^\n]+))"
    matches = list(re.finditer(pattern, body))

    if not matches:
        return {"error": f"在 {target_file.name} 中找不到任何論文條目。"}

    norm_decisions = {}
    for k, v in decisions.items():
        v_str = str(v).strip().lower()
        if v_str in ['+', 'y', 'include', 'included', 'yes', '1']:
            std_val = '+'
        elif v_str in ['-', 'n', 'exclude', 'excluded', 'no', '2']:
            std_val = '-'
        elif v_str in [' ', 'k', 'pending', 'hold', '3']:
            std_val = ' '
        else:
            continue
        norm_decisions[str(k).strip()] = std_val

    paper_sections = []
    updated_count = 0
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i + 1 < len(matches) else len(body)
        sec_text = body[start:end]
        raw_mark = matches[i].group(3)
        std_mark = '+' if raw_mark in ['+', 'x', 'X'] else ('-' if raw_mark == '-' else ' ')
        idx_str = str(matches[i].group(2))

        if idx_str in norm_decisions:
            new_mark = norm_decisions[idx_str]
            if new_mark != std_mark:
                old_header_re = rf"##\s+{idx_str}\.\s*\[[\s\+\-xX]\]"
                new_header = f"## {idx_str}. [{new_mark}]"
                sec_text = re.sub(old_header_re, new_header, sec_text, count=1)

                if new_mark == '+':
                    new_status_line = "- **審查狀態**：`[+]` 採納納入 (Included)"
                elif new_mark == '-':
                    new_status_line = "- **審查狀態**：`[-]` 刪除排除 (Excluded)"
                else:
                    new_status_line = "- **審查狀態**：`[ ]` 保留待定 (Pending)"
                sec_text = re.sub(r"- \*\*審查狀態\*\*：[^\n]+", new_status_line, sec_text)
                std_mark = new_mark
                updated_count += 1

        paper_sections.append(sec_text)

    header_part = body[:matches[0].start()]
    new_body = header_part + "".join(paper_sections)

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content.split("---", 2)[0] + "---" + content.split("---", 2)[1] + "---\n" + new_body.lstrip())

    stats = update_frontmatter_stats(target_file)
    sync_tracking_from_candidate(seq_str, target_file)

    return {
        "success": True,
        "file": target_file.name,
        "sequence": seq_str,
        "updated_count": updated_count,
        "stats": stats,
        "message": f"已成功更新 {target_file.name} 的審查狀態（更新 {updated_count} 篇）：採納[+] {stats['included']} 篇，排除[-] {stats['excluded']} 篇，待定[ ] {stats['pending']} 篇。追蹤檔 candidate_papers_{seq_str}_tracking.md 已同步刷新。"
    }


def download_selected_papers(file_arg: Optional[str] = None):
    """
    功能 4 (download)：讀取候選清單中標記為 [+] 的論文，自動下載 OA PDF，分類記錄至專屬追蹤檔
    """
    target_file = select_candidate_file(file_arg)
    if not target_file:
        return

    update_frontmatter_stats(target_file)

    m = re.search(r"candidate_papers_(\d+)\.md$", target_file.name)
    seq_str = f"{int(m.group(1)):02d}" if m else "01"

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    cache_file = PAPERS_DIR / f"candidates_cache_{seq_str}.json"
    candidates_map = {}
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as cf:
            for item in json.load(cf):
                candidates_map[item["index"]] = item

    checked_indices = []
    pattern = r"##\s+(\d+)\.\s*\[([\+xX])\]"
    for m in re.finditer(pattern, content):
        checked_indices.append(int(m.group(1)))

    if not checked_indices:
        print(f"\n[警告] 在 {target_file.name} 中未檢測到任何已採納納入 [+] 的論文！")
        print(f"[指引] 請先執行互動式審查：python scripts/fetch_openalex.py review {seq_str}")
        return

    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[啟動] 針對 {target_file.name}，開始處理 {len(checked_indices)} 篇採納文獻之全文獲取：\n")

    tracking_data = load_or_init_tracking(seq_str, target_file)

    oa_downloaded_papers = []
    subscription_provided_papers = []
    subscription_pending_papers = []

    for idx in checked_indices:
        item = candidates_map.get(idx)
        if not item:
            sec_match = re.search(rf"##\s+{idx}\.\s*\[[\+xX]\]\s+([^\n]+)([\s\S]*?)(?=##\s+\d+\.|\Z)", content)
            if sec_match:
                title = sec_match.group(1).strip()
                block_txt = sec_match.group(2)
                src_m = re.search(r"- \*\*發表來源 \(Source\)\*\*：`([^`]+)`", block_txt)
                yr_m = re.search(r"- \*\*作者與年份\*\*：([^\s]+)\s*\((\d+)\)", block_txt)
                doi_m = re.search(r"- \*\*DOI 直連\*\*：([^\n]+)", block_txt)
                item = {
                    "index": idx,
                    "title": title,
                    "first_author": yr_m.group(1) if yr_m else "Author",
                    "year": yr_m.group(2) if yr_m else "2024",
                    "source": src_m.group(1) if src_m else "Journal",
                    "doi": doi_m.group(1) if doi_m else "",
                    "is_oa": "[開放取用]" in block_txt,
                    "pdf_url": None
                }
            else:
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

        print(f"[{idx}] 處理文獻：{title[:55]}...")
        print(f"    來源：{source} | 年份：{year}")

        if item.get("is_oa") and pdf_url and pdf_url.startswith("http"):
            if target_path.exists() and target_path.stat().st_size > 1000:
                print(f"    [略過] PDF 原件已存在：{target_path}（{target_path.stat().st_size / 1024:.1f} KB）")
                oa_downloaded_papers.append({
                    "index": idx,
                    "title": title,
                    "first_author": author,
                    "year": year,
                    "source": source,
                    "doi": doi,
                    "pdf_filename": filename,
                    "pdf_path": str(target_path),
                    "file_size_kb": round(target_path.stat().st_size / 1024, 1),
                    "download_time": datetime.datetime.fromtimestamp(target_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                print(f"    [下載] 偵測到合法 OA 直連，正在自動抓取...")
                try:
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    req = urllib.request.Request(pdf_url, headers=headers)
                    with urllib.request.urlopen(req, timeout=25) as resp:
                        content_type = resp.headers.get("Content-Type", "")
                        content_data = resp.read()

                        if len(content_data) > 1000 and (content_data.startswith(b"%PDF") or "pdf" in content_type.lower() or pdf_url.lower().endswith(".pdf")):
                            with open(target_path, "wb") as pf:
                                pf.write(content_data)
                            sz = round(len(content_data) / 1024, 1)
                            print(f"    [成功] 下載完成！已儲存至：{target_path}（{sz} KB）")
                            oa_downloaded_papers.append({
                                "index": idx,
                                "title": title,
                                "first_author": author,
                                "year": year,
                                "source": source,
                                "doi": doi,
                                "pdf_filename": filename,
                                "pdf_path": str(target_path),
                                "file_size_kb": sz,
                                "download_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                        else:
                            print(f"    [轉移] 遠端受防爬蟲限制，歸入封閉待調閱項目。")
                            subscription_pending_papers.append({
                                "index": idx,
                                "title": title,
                                "first_author": author,
                                "year": year,
                                "source": source,
                                "doi": doi,
                                "suggested_filename": filename
                            })
                except Exception as err:
                    print(f"    [連線失敗] {err}，歸入封閉待調閱項目。")
                    subscription_pending_papers.append({
                        "index": idx,
                        "title": title,
                        "first_author": author,
                        "year": year,
                        "source": source,
                        "doi": doi,
                        "suggested_filename": filename
                    })
        else:
            if target_path.exists() and target_path.stat().st_size > 1000:
                print(f"    [已提供] 偵測到研究者已自圖書館調閱入庫：{filename}")
                subscription_provided_papers.append({
                    "index": idx,
                    "title": title,
                    "first_author": author,
                    "year": year,
                    "source": source,
                    "doi": doi,
                    "pdf_filename": filename,
                    "pdf_path": str(target_path),
                    "file_size_kb": round(target_path.stat().st_size / 1024, 1),
                    "provided_time": datetime.datetime.fromtimestamp(target_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                print(f"    [待調閱] 封閉訂閱文獻，需自校園圖書館下載取得。")
                subscription_pending_papers.append({
                    "index": idx,
                    "title": title,
                    "first_author": author,
                    "year": year,
                    "source": source,
                    "doi": doi,
                    "suggested_filename": filename
                })

    tracking_data["oa_downloaded_papers"] = oa_downloaded_papers
    tracking_data["subscription_provided_papers"] = subscription_provided_papers
    tracking_data["subscription_pending_papers"] = subscription_pending_papers
    save_and_render_tracking(tracking_data)

    print("\n" + "="*75)
    print(f"[總結] 全文獲取與分類追蹤完成（批次：{seq_str}）：")
    print(f"  🟢 自動下載合法 OA PDF：{len(oa_downloaded_papers)} 篇")
    print(f"  🔵 已提供圖書館訂閱 PDF：{len(subscription_provided_papers)} 篇")
    print(f"  🟡 尚未提供圖書館訂閱 PDF：{len(subscription_pending_papers)} 篇")
    print(f"  📄 專屬追蹤報表已刷新：candidate_papers_{seq_str}_tracking.md")
    print("="*75)

    if subscription_pending_papers:
        print(f"\n💡 【尚未提供之訂閱文獻調閱清單】：")
        for p_item in subscription_pending_papers:
            print(f"  • [{p_item['index']}] {p_item['title']}")
            print(f"    DOI ：{p_item['doi']}")
            print(f"    請下載並命名為：01_papers/raw_pdf/{p_item['suggested_filename']}\n")
        print(f"放入檔案後，請執行持續追蹤指令：python scripts/fetch_openalex.py track {seq_str}")


def track_candidate_papers(file_arg: Optional[str] = None):
    """
    功能 5 (track)：持續追蹤管理工具，自動偵測 raw_pdf/ 中新補全的訂閱 PDF，無縫更新追蹤檔案
    """
    target_file = select_candidate_file(file_arg)
    if not target_file:
        return

    m = re.search(r"candidate_papers_(\d+)\.md$", target_file.name)
    seq_str = f"{int(m.group(1)):02d}" if m else "01"

    print(f"\n[掃描] 正在為 candidate_papers_{seq_str} 檢測 raw_pdf/ 目錄之文獻補全狀況...")
    tracking_data = load_or_init_tracking(seq_str, target_file)

    pending_list = tracking_data.get("subscription_pending_papers", [])
    provided_list = tracking_data.get("subscription_provided_papers", [])

    if not pending_list:
        print(f"[恭喜] 批次 {seq_str} 目前沒有任何「尚未提供」的訂閱文獻！所有採納論文皆已完整入庫。")
        save_and_render_tracking(tracking_data)
        return

    remaining_pending = []
    newly_detected = []

    for item in pending_list:
        sug_filename = item.get("suggested_filename", "")
        target_path = RAW_PDF_DIR / sug_filename

        found_path = None
        if target_path.exists() and target_path.stat().st_size > 1000:
            found_path = target_path
        else:
            auth = sanitize_filename(item.get("first_author", ""))
            yr = str(item.get("year", ""))
            for f in RAW_PDF_DIR.glob("*.pdf"):
                if auth.lower() in f.name.lower() and yr in f.name:
                    found_path = f
                    break

        if found_path:
            sz = round(found_path.stat().st_size / 1024, 1)
            now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            prov_item = {
                "index": item["index"],
                "title": item["title"],
                "first_author": item["first_author"],
                "year": item["year"],
                "source": item.get("source", ""),
                "doi": item.get("doi", ""),
                "pdf_filename": found_path.name,
                "pdf_path": str(found_path),
                "file_size_kb": sz,
                "provided_time": now_time
            }
            provided_list.append(prov_item)
            newly_detected.append(prov_item)
        else:
            remaining_pending.append(item)

    tracking_data["subscription_provided_papers"] = provided_list
    tracking_data["subscription_pending_papers"] = remaining_pending
    save_and_render_tracking(tracking_data)

    print("\n" + "="*75)
    print(f"📊 追蹤掃描完成（批次：{seq_str}）：")
    if newly_detected:
        print(f"🎉 成功感知並入庫 {len(newly_detected)} 篇新提供之訂閱 PDF！")
        for nd in newly_detected:
            print(f"  • [{nd['index']}] {nd['title'][:55]} -> {nd['pdf_filename']} ({nd['file_size_kb']} KB)")
    else:
        print("ℹ️ 本次未檢測到新放入 raw_pdf/ 的訂閱檔案。")

    print(f"\n目前進度概況：")
    print(f"  🟢 合法 OA 已下載：{len(tracking_data.get('oa_downloaded_papers', []))} 篇")
    print(f"  🔵 圖書館訂閱已補全：{len(provided_list)} 篇")
    print(f"  🟡 圖書館訂閱仍待調閱：{len(remaining_pending)} 篇")
    print(f"📄 追蹤報表已更新：candidate_papers_{seq_str}_tracking.md")
    print("="*75)

    if remaining_pending:
        print(f"\n仍待調閱之論文（共 {len(remaining_pending)} 篇）：")
        for rp in remaining_pending:
            print(f"  • DOI: {rp['doi']} -> 請存為: {rp['suggested_filename']}")


def main():
    parser = argparse.ArgumentParser(
        description="OpenAlex 學術文獻檢索、審查與追蹤管理工具 (fetch_openalex.py)",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="欲執行的指令")

    # 1. search 指令
    p_search = subparsers.add_parser("search", help="檢索文獻並生成流水號 candidate_papers_XX.md 與追蹤檔")
    p_search.add_argument("query", nargs="*", help="檢索關鍵字詞（例：AI Agents in Higher Education）")
    p_search.add_argument("-m", "--max", type=int, default=10, help="最大檢索候選筆數（預設：10）")
    p_search.add_argument("-s", "--start-year", type=int, default=2022, help="發表起始年份（預設：2022）")
    p_search.add_argument("-e", "--end-year", type=int, default=2026, help="發表結束年份（預設：2026）")

    # 2. list 指令
    subparsers.add_parser("list", help="全域瀏覽所有 candidate_papers[00-99].md 之檢索條件、審查與追蹤狀態")

    # 3. review 指令
    p_review = subparsers.add_parser("review", help="啟動互動式審查工具（[+] 採納, [-] 排除, [ ] 保留）")
    p_review.add_argument("file", nargs="?", default=None, help="欲審查的候選檔案名稱或流水號（例：01）")

    # 4. download 指令
    p_download = subparsers.add_parser("download", help="下載選定清單中標記為 [+] 的 OA 全文並更新追蹤檔")
    p_download.add_argument("file", nargs="?", default=None, help="欲下載的候選檔案名稱或流水號（例：01）")

    # 5. track 指令
    p_track = subparsers.add_parser("track", help="持續追蹤 raw_pdf/ 中補全的訂閱文獻並更新追蹤報告")
    p_track.add_argument("file", nargs="?", default=None, help="欲追蹤的候選檔案名稱或流水號（例：01）")

    args = parser.parse_args()

    if not args.command:
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            q = " ".join(sys.argv[1:])
            search_candidate_papers(q, max_candidates=10, start_year=2022, end_year=2026)
            return
        parser.print_help()
        return

    if args.command == "search":
        q = " ".join(args.query) if args.query else "AI Agents in Higher Education scaffolding"
        search_candidate_papers(q, max_candidates=args.max, start_year=args.start_year, end_year=args.end_year)

    elif args.command == "list":
        list_candidate_papers()

    elif args.command == "review":
        review_candidate_papers(args.file)

    elif args.command == "download":
        download_selected_papers(args.file)

    elif args.command == "track":
        track_candidate_papers(args.file)


if __name__ == "__main__":
    main()
