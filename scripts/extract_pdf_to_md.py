"""
scripts/extract_pdf_to_md.py

學術文獻 PDF 轉譯與文字清洗工具
用途：依據指定的候選清單批次（candidate_papers_XX.md）精準轉譯採納之文獻 PDF，
      消除排版雜音與參考文獻清單，輸出純淨 Markdown 至 01_papers/extracted_text/，
      避免每次皆需全量掃描整個資料夾。
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# 設定 Windows 終端輸出編碼
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# 定義工作區目錄常數
PAPERS_DIR = Path("01_papers")
RAW_PDF_DIR = PAPERS_DIR / "raw_pdf"
EXTRACTED_TEXT_DIR = PAPERS_DIR / "extracted_text"


def sanitize_filename(name: str) -> str:
    """清理檔名中的特殊字元與標點符號，與 fetch_openalex 命名慣例一致"""
    s = re.sub(r'[\/:*?"<>|]', "_", name)
    s = re.sub(r'[\s_]+', "_", s)
    return s.strip("._")


def clean_academic_markdown(md_text: str) -> str:
    """
    清洗學術文字噪音：
    1. 移除 References / Bibliography 之後的龐大引用列表
    2. 消除多餘的頁碼與出版聲明行
    3. 合併連續過多空白行
    """
    lines = md_text.split("\n")
    cleaned_lines = []

    # 常見參考文獻標題樣式
    ref_pattern = re.compile(r"^#{1,3}\s*(references|bibliography|works cited|參考文獻)", re.IGNORECASE)
    # 常見頁碼與無效噪音樣式
    noise_pattern = re.compile(r"^(page \d+|\d+\s*/\s*\d+|downloaded from|https?://doi\.org/)", re.IGNORECASE)

    for line in lines:
        stripped = line.strip()

        # 截斷檢測：一旦讀到 References 章節標題，終止後續解析以節省空間
        if ref_pattern.match(stripped):
            cleaned_lines.append("\n\n---\n*（備註：系統已自動截斷後續 References 引用列表，以維護上下文純淨度）*")
            break

        # 噪音濾除：跳過純頁碼與常見版權行
        if noise_pattern.match(stripped):
            continue

        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines)
    # 正規化多重空行，最多保留兩個換行
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result


def convert_single_pdf(pdf_path: Path, target_md_path: Path) -> bool:
    """將單一 PDF 轉譯為乾淨 Markdown"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("[錯誤] 未檢測到 PyMuPDF 套件，請先執行：pip install PyMuPDF pymupdf4llm")
        return False

    try:
        # 優先嘗試 pymupdf4llm 進行結構化轉譯
        import pymupdf4llm
        raw_md = pymupdf4llm.to_markdown(str(pdf_path))
    except Exception:
        # 若無 pymupdf4llm，降級使用標準 PyMuPDF 解析
        try:
            doc = fitz.open(pdf_path)
            pages_text = []
            for page_num, page in enumerate(doc):
                pages_text.append(f"## Page {page_num + 1}\n\n" + page.get_text())
            raw_md = "\n\n".join(pages_text)
        except Exception as e:
            print(f"   [讀取錯誤] 無法開啟 PDF 檔案 {pdf_path.name}：{e}")
            return False

    # 執行學術文字工程清洗
    cleaned_md = clean_academic_markdown(raw_md)

    target_md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_md_path, "w", encoding="utf-8") as f:
        f.write(cleaned_md)

    return True


def get_candidate_files() -> List[Path]:
    """獲取 01_papers 下所有候選評估清單，依流水號由小至大排序"""
    if not PAPERS_DIR.exists():
        return []
    numbered = list(PAPERS_DIR.glob("candidate_papers_*.md"))
    # 排除 tracking 檔
    numbered = [f for f in numbered if not f.name.endswith("_tracking.md")]

    def sort_key(p: Path):
        m = re.search(r"candidate_papers_(\d+)\.md$", p.name)
        return int(m.group(1)) if m else 999

    numbered.sort(key=sort_key)
    if numbered:
        return numbered

    single = PAPERS_DIR / "candidate_papers.md"
    return [single] if single.exists() else []


def select_candidate_batch(batch_arg: Optional[str] = None) -> Optional[Path]:
    """解析使用者指定的批次流水號或清單檔案，支援互動式選擇與最新批次預設"""
    files = get_candidate_files()
    if not files:
        print(f"[錯誤] 在 {PAPERS_DIR} 中未找到任何 candidate_papers 清單檔案！請先執行檢索。")
        return None

    if batch_arg:
        arg_str = str(batch_arg).strip()
        # 1. 直接路徑或檔名比對
        p = Path(arg_str)
        if p.exists():
            return p
        p_sub = PAPERS_DIR / arg_str
        if p_sub.exists():
            return p_sub

        # 2. 流水號比對（例如 '01', '1'）
        m_num = re.search(r"\d+", arg_str)
        if m_num:
            num = int(m_num.group())
            for f in files:
                m_f = re.search(r"candidate_papers_(\d+)\.md$", f.name)
                if m_f and int(m_f.group(1)) == num:
                    return f

        print(f"[警告] 找不到與 '{arg_str}' 相符的候選清單檔案。")

    if len(files) == 1:
        return files[0]

    # 非互動環境（如 Agent 調用或管線串接）預設使用最新批次
    if not sys.stdin.isatty():
        return files[-1]

    # 終端機互動式挑選
    print("\n" + "=" * 76)
    print("📚 發現多個候選文獻評估清單，請選擇欲轉譯的檢索批次：")
    print("=" * 76)
    for idx, f in enumerate(files, 1):
        content = f.read_text(encoding="utf-8")
        q_m = re.search(r'query:\s*["\']?(.*?)["\']?\s*\n', content)
        if not q_m:
            q_m = re.search(r"\*\*檢索主題\*\*：`([^`]+)`", content)
        q = q_m.group(1).strip() if q_m else "未標記主題"

        inc_count = len(re.findall(r"##\s+\d+\.\s*\[[\+xX]\]", content))
        total_count = len(re.findall(r"##\s+\d+\.\s*\[", content))
        print(f"  [{idx}] {f.name:<24} | 主題: {q[:25]:<25} | 採納: {inc_count}/{total_count} 篇")

    print("-" * 76)
    latest_idx = len(files)
    choice = input(f"請輸入選單編號 (1~{latest_idx}，直接按 Enter 預設最新 [{latest_idx}]，或輸入 q 取消): ").strip()
    if choice.lower() in ['q', 'quit', 'exit']:
        return None
    if not choice:
        return files[-1]
    try:
        c_num = int(choice)
        if 1 <= c_num <= len(files):
            return files[c_num - 1]
    except ValueError:
        pass

    print("[提示] 輸入無效，自動選取最新批次。")
    return files[-1]


def find_batch_paper_pdfs(candidate_file: Path) -> Dict[str, Any]:
    """
    從 candidate_papers_XX.md 中剖析出標記採納 [+] 的文獻資訊，
    並結合 tracking 與檔案系統搜尋 01_papers/raw_pdf/ 中對應的 PDF 檔案。
    """
    content = candidate_file.read_text(encoding="utf-8")

    # 擷取批次流水號
    m_seq = re.search(r"candidate_papers_(\d+)\.md$", candidate_file.name)
    seq_str = f"{int(m_seq.group(1)):02d}" if m_seq else ""
    if not seq_str:
        m_fm = re.search(r'sequence_id:\s*["\']?(\d+)["\']?', content)
        if m_fm:
            seq_str = f"{int(m_fm.group(1)):02d}"

    # 讀取查詢詞
    q_m = re.search(r'query:\s*["\']?(.*?)["\']?\s*\n', content)
    if not q_m:
        q_m = re.search(r"\*\*檢索主題\*\*：`([^`]+)`", content)
    query_text = q_m.group(1).strip() if q_m else "未標記主題"

    # 嘗試讀取 tracking json 作為精確對照
    tracking_map: Dict[int, Dict[str, Any]] = {}
    if seq_str:
        tracking_json_path = PAPERS_DIR / f"candidate_papers_{seq_str}_tracking.json"
        if tracking_json_path.exists():
            try:
                tdata = json.loads(tracking_json_path.read_text(encoding="utf-8"))
                for p in tdata.get("oa_downloaded_papers", []):
                    tracking_map[p.get("index")] = p
                for p in tdata.get("subscription_provided_papers", []):
                    tracking_map[p.get("index")] = p
                for p in tdata.get("subscription_pending_papers", []):
                    if p.get("index") not in tracking_map:
                        tracking_map[p.get("index")] = p
            except Exception:
                pass

    # 剖析 candidate_papers 中的論文區塊
    sections = re.split(r'\n(?=##\s+\d+\.)', content)
    papers = []

    for sec in sections:
        header_m = re.match(r'##\s+(\d+)\.\s*\[([+\-xX\s])\]\s+(.*)', sec.strip())
        if not header_m:
            continue

        idx = int(header_m.group(1))
        status = header_m.group(2).strip()
        title = header_m.group(3).strip()

        # 只挑選採納 [+] / [x] / [X] 的論文
        is_included = status in ['+', 'x', 'X']

        auth_yr_m = re.search(r'\*\*作者與年份\*\*：([^\s(]+)\s*\((\d{4})\)', sec)
        if not auth_yr_m:
            auth_yr_m = re.search(r'\*\*作者與年份\*\*：([^(]+)\((\d{4})\)', sec)

        author = auth_yr_m.group(1).strip() if auth_yr_m else "Author"
        year = auth_yr_m.group(2).strip() if auth_yr_m else "2024"

        src_m = re.search(r'\*\*發表來源 \(Source\)\*\*：`([^`]+)`', sec)
        source = src_m.group(1).strip() if src_m else "Journal"

        doi_m = re.search(r'\*\*DOI 直連\*\*：([^\n\r]+)', sec)
        doi = doi_m.group(1).strip() if doi_m else ""

        # 計算標準產生之預期檔名
        short_title = sanitize_filename(title[:35].strip())
        safe_author = sanitize_filename(author)
        default_filename = f"{year}_{safe_author}_{short_title}.pdf"

        # 若 tracking 有記錄特定檔名
        tracked_item = tracking_map.get(idx, {})
        recorded_filename = tracked_item.get("pdf_filename") or tracked_item.get("suggested_filename") or default_filename

        papers.append({
            "index": idx,
            "included": is_included,
            "status": status,
            "title": title,
            "first_author": author,
            "year": year,
            "source": source,
            "doi": doi,
            "expected_filename": default_filename,
            "recorded_filename": recorded_filename
        })

    # 針對採納的論文比對 raw_pdf 目錄中的檔案
    all_raw_pdfs = list(RAW_PDF_DIR.glob("*.pdf")) if RAW_PDF_DIR.exists() else []

    found_papers = []
    missing_papers = []

    included_papers = [p for p in papers if p["included"]]

    for p in included_papers:
        matched_file = None

        # 1. 精確比對 recorded_filename
        candidate_path1 = RAW_PDF_DIR / p["recorded_filename"]
        if candidate_path1.exists():
            matched_file = candidate_path1

        # 2. 精確比對 expected_filename
        if not matched_file:
            candidate_path2 = RAW_PDF_DIR / p["expected_filename"]
            if candidate_path2.exists():
                matched_file = candidate_path2

        # 3. 容錯比對：年份與第一作者前綴符合者
        if not matched_file:
            prefix = f"{p['year']}_{sanitize_filename(p['first_author'])}".lower()
            for rf in all_raw_pdfs:
                if rf.name.lower().startswith(prefix):
                    matched_file = rf
                    break

        # 4. 容錯比對：短篇名前綴符合者
        if not matched_file:
            stem_core = sanitize_filename(p["title"][:20]).lower()
            for rf in all_raw_pdfs:
                if stem_core in rf.name.lower():
                    matched_file = rf
                    break

        if matched_file:
            p_copy = dict(p)
            p_copy["pdf_path"] = matched_file
            found_papers.append(p_copy)
        else:
            missing_papers.append(p)

    return {
        "candidate_file": candidate_file,
        "sequence_id": seq_str,
        "query": query_text,
        "total_papers": len(papers),
        "included_papers": included_papers,
        "found_papers": found_papers,
        "missing_papers": missing_papers
    }


def convert_batch_pdfs(batch_arg: Optional[str] = None) -> int:
    """指定檢索批次進行 PDF to Markdown 轉換"""
    candidate_file = select_candidate_batch(batch_arg)
    if not candidate_file:
        return 0

    batch_info = find_batch_paper_pdfs(candidate_file)
    c_name = candidate_file.name
    seq = batch_info["sequence_id"] or "--"
    q = batch_info["query"]
    included = batch_info["included_papers"]
    found = batch_info["found_papers"]
    missing = batch_info["missing_papers"]

    print("\n" + "=" * 80)
    print(f"📄 執行文獻轉譯：批次 [{seq}] {c_name}")
    print(f"🔍 檢索主題：『{q}』")
    print(f"📊 審查採納：{len(included)} 篇 | 在庫 PDF：{len(found)} 篇 | 待補文獻：{len(missing)} 篇")
    print("=" * 80)

    if not included:
        print(f"\n[提示] 在 {c_name} 中未檢測到標記為 [+] 採納的文獻。")
        print(f"👉 請先執行審查篩選：python scripts/fetch_openalex.py review {seq}")
        return 0

    if not found:
        print(f"\n[警告] 在 {RAW_PDF_DIR} 中尚未找到本批次採納文獻之 PDF 原件！")
        if missing:
            print("尚未入庫文獻：")
            for m in missing:
                print(f"  • [{m['index']}] {m['title'][:55]}...")
                print(f"    預期檔名：{m['expected_filename']}")
            print(f"\n👉 請先執行下載：python scripts/fetch_openalex.py download {seq}")
            print(f"   （若為校園訂閱文獻，請由圖書館調閱後存放至 {RAW_PDF_DIR}）")
        return 0

    EXTRACTED_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    converted_count = 0

    print(f"\n[進度] 開始轉譯本批次之 {len(found)} 篇文獻...\n")
    for idx, item in enumerate(found, 1):
        pdf_path = item["pdf_path"]
        target_md = EXTRACTED_TEXT_DIR / f"{pdf_path.stem}.md"
        print(f"[{idx}/{len(found)}] 正在解析：{pdf_path.name}")

        ok = convert_single_pdf(pdf_path, target_md)
        if ok:
            converted_count += 1
            sz_kb = target_md.stat().st_size / 1024
            print(f"   [成功] 轉譯完成！輸出至：{target_md.name} ({sz_kb:.1f} KB)")
        else:
            print(f"   [失敗] 無法解析此檔案：{pdf_path.name}")

    if missing:
        print(f"\n⚠️ 注意：本批次尚有 {len(missing)} 篇採納論文未在 raw_pdf/ 中找到 PDF 原件：")
        for m in missing:
            print(f"  • [{m['index']}] {m['first_author']} ({m['year']}) - {m['title'][:50]}...")
            print(f"    建議手動存放檔名：01_papers/raw_pdf/{m['expected_filename']}")

    print(f"\n[完成] 批次 [{seq}] 轉譯作業結束！成功轉譯 {converted_count} 篇純淨 Markdown。")
    print(f"📁 儲存路徑：{EXTRACTED_TEXT_DIR}\n")
    return converted_count


def convert_all_pdfs() -> int:
    """批次將 raw_pdf 下的所有 PDF 轉換為乾淨 Markdown（全量轉譯模式）"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("[錯誤] 未檢測到 PyMuPDF 套件，請先執行：pip install PyMuPDF pymupdf4llm")
        return 0

    EXTRACTED_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_files = list(RAW_PDF_DIR.glob("*.pdf")) if RAW_PDF_DIR.exists() else []

    if not pdf_files:
        print(f"[警告] 在 {RAW_PDF_DIR} 找不到任何 PDF 檔案，請先執行下載腳本。")
        return 0

    print(f"[全量] 開始批次轉譯 raw_pdf/ 下所有學術文獻（共 {len(pdf_files)} 篇）...\n")

    success_count = 0
    for idx, pdf_path in enumerate(pdf_files, 1):
        target_md_path = EXTRACTED_TEXT_DIR / f"{pdf_path.stem}.md"
        print(f"[{idx}/{len(pdf_files)}] 正在解析：{pdf_path.name}")
        ok = convert_single_pdf(pdf_path, target_md_path)
        if ok:
            success_count += 1
            sz_kb = target_md_path.stat().st_size / 1024
            print(f"   [成功] 轉譯成功！輸出檔案：{target_md_path.name} ({sz_kb:.1f} KB)")
        else:
            print(f"   [失敗] 解析失敗：{pdf_path.name}")

    print(f"\n[完成] 全量轉譯完成！共成功產出 {success_count} 篇 Markdown。存放於：{EXTRACTED_TEXT_DIR}\n")
    return success_count


def convert_batch_or_all(batch_arg: Optional[str] = None) -> int:
    """統一呼叫入口（供 MCP 或程式化調用）"""
    if batch_arg and str(batch_arg).strip().lower() == "all":
        return convert_all_pdfs()
    else:
        return convert_batch_pdfs(batch_arg)


def list_batches_status():
    """列出所有檢索批次的文獻採納與轉譯狀態"""
    files = get_candidate_files()
    if not files:
        print(f"[提示] 目前在 {PAPERS_DIR} 中尚未找到任何 candidate_papers 清單。")
        return

    print("\n" + "=" * 92)
    print("📚 碩士論文檢索批次 PDF 轉譯狀態總覽")
    print("=" * 92)
    print(f"{'序號':<4} {'候選清單檔案':<24} {'檢索主題':<28} {'採納':<6} {'在庫PDF':<8} {'已轉Markdown':<10}")
    print("-" * 92)

    for f in files:
        info = find_batch_paper_pdfs(f)
        seq = info["sequence_id"] or "--"
        q = info["query"]
        q_display = q[:26] + ".." if len(q) > 26 else q
        inc_cnt = len(info["included_papers"])
        found_cnt = len(info["found_papers"])

        md_cnt = 0
        for p in info["found_papers"]:
            target_md = EXTRACTED_TEXT_DIR / f"{p['pdf_path'].stem}.md"
            if target_md.exists():
                md_cnt += 1

        print(f"{seq:<4} {f.name:<24} {q_display:<28} {inc_cnt:<6} {found_cnt:<8} {md_cnt:<10}")

    print("=" * 92)
    print("💡 常用操作指引：")
    print("  • 轉譯指定批次：python scripts/extract_pdf_to_md.py <序號>")
    print("  • 轉譯最新批次：python scripts/extract_pdf_to_md.py")
    print("  • 全量重新轉譯：python scripts/extract_pdf_to_md.py --all\n")


def main():
    parser = argparse.ArgumentParser(
        description="學術文獻 PDF 轉譯與文字清洗工具（支援指定檢索批次 candidate_papers_XX.md，精準轉譯避免全量耗時）"
    )
    parser.add_argument(
        "batch",
        nargs="?",
        default=None,
        help="指定檢索批次流水號（例如 '01'、'02'）或候選檔名（例如 candidate_papers_01.md）。未指定時挑選或預設最新批次。"
    )
    parser.add_argument(
        "-b", "--batch",
        dest="batch_flag",
        default=None,
        help="指定檢索批次流水號（例如 '01'、'02'）"
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="全量轉譯：處理 raw_pdf/ 目錄下的所有 PDF 檔案"
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="列出所有檢索批次的文獻採納與 PDF/Markdown 轉譯狀態"
    )

    args = parser.parse_args()

    if args.list:
        list_batches_status()
        return

    if args.all:
        convert_all_pdfs()
        return

    target_batch = args.batch_flag or args.batch
    convert_batch_pdfs(target_batch)


if __name__ == "__main__":
    main()
