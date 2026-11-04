#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨篇文獻比較矩陣合成與合規驗證工具 (matrix_synthesizer.py)
用途：
1. scan     : 掃描 02_notes/cards/ 下的所有標準閱讀卡片，解析 YAML Frontmatter 與七大維度（含 RQ1-RQ3 映射分佈），
              自動輸出卡片庫跨篇盤點摘要，並可選擇生成預填版矩陣骨架草稿。
2. validate : 自動檢驗 02_notes/literature_matrix.md 是否符合雙層次矩陣與三態綜整 Schema 規範。

用法：
  python skills/literature_matrix_synthesizer/scripts/matrix_synthesizer.py scan
  python skills/literature_matrix_synthesizer/scripts/matrix_synthesizer.py scan --init-draft
  python skills/literature_matrix_synthesizer/scripts/matrix_synthesizer.py validate 02_notes/literature_matrix.md
"""

import os
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 解決 Windows 終端機編碼問題
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REQUIRED_FRONTMATTER_FIELDS = [
    "type", "matrix_version", "project_title",
    "card_count", "included_cards", "rq_coverage", "created_date"
]

REQUIRED_SECTIONS = [
    (1, "卡片庫盤點與研究問題"),
    (2, "第一層矩陣"),
    (3, "第二層矩陣"),
    (4, "跨篇對話三態綜整分析"),
]

REQUIRED_SYNTHESIS_SUBSECTIONS = [
    "4.1",
    "4.2",
    "4.3",
]


def find_workspace_root() -> Path:
    current = Path.cwd()
    for p in [current, current.parent, current.parent.parent, current.parent.parent.parent]:
        if (p / "PROJECT.md").exists() or (p / "02_notes").exists():
            return p
    return current


def parse_single_card(card_path: Path) -> dict:
    content = card_path.read_text(encoding="utf-8", errors="ignore")
    info = {
        "filename": card_path.name,
        "bibtex_key": "",
        "title": card_path.stem,
        "first_author": "Unknown",
        "year": "N/A",
        "journal": "",
        "source_md": "",
        "tags": [],
        "rq1_status": "未標註",
        "rq2_status": "未標註",
        "rq3_status": "未標註",
        "theory_snippet": "",
        "method_snippet": "",
        "limit_snippet": "",
    }

    fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k == "tags":
                    info["tags"] = re.findall(r"[\w-]+", v)
                elif k in info:
                    info[k] = v

    def get_sec(num: int) -> str:
        m = re.search(rf"##\s*{num}\.\s*[^\n]+\n(.*?)(?=\n##\s*\d+\.|\Z)", content, re.DOTALL)
        return m.group(1).strip() if m else ""

    sec2 = get_sec(2)
    sec3 = get_sec(3)
    sec5 = get_sec(5)
    sec6 = get_sec(6)

    info["theory_snippet"] = sec2.splitlines()[0][:60] if sec2 else "未提取"
    info["method_snippet"] = sec3.splitlines()[0][:60] if sec3 else "未提取"
    info["limit_snippet"] = sec5.splitlines()[0][:60] if sec5 else "未提取"

    for rq_idx in [1, 2, 3]:
        rq_m = re.search(rf"RQ{rq_idx}[^：:\n]*[：:]\**\s*(.*?)(?=\n-\s*\*\*對\s*RQ|\n-\s*\*\*本研究|\Z)", sec6, re.DOTALL)
        if rq_m:
            rq_txt = rq_m.group(1).strip()
            if "無直接關聯" in rq_txt or rq_txt.startswith("無關"):
                info[f"rq{rq_idx}_status"] = "無直接關聯"
            else:
                first_line = rq_txt.replace("\n", " ").strip()
                info[f"rq{rq_idx}_status"] = "有啟發 (" + first_line[:28] + "...)"

    return info


def cmd_scan(args):
    root = find_workspace_root()
    cards_dir = root / "02_notes" / "cards"
    project_file = root / "PROJECT.md"

    project_title = "未定研究主題"
    if project_file.exists():
        proj_txt = project_file.read_text(encoding="utf-8", errors="ignore")
        m_title = re.search(r"工作題目[：:]\**\s*(.+)", proj_txt)
        if m_title:
            project_title = m_title.group(1).strip()

    cards = []
    if cards_dir.exists():
        for p in sorted(cards_dir.glob("card_*.md")):
            cards.append(parse_single_card(p))

    print("==================================================================")
    print("[資訊] 跨篇文獻矩陣掃描與 RQ 映射盤點工具 (Matrix Synthesizer)")
    print("==================================================================")
    print(f"[路徑] 工作區根目錄 : {root}")
    print(f"[專案] 當前研究題目 : {project_title}")
    print(f"[統計] 已收錄卡片數 : {len(cards)} 張 (目錄: 02_notes/cards/)")
    print("------------------------------------------------------------------")

    rq_counts = {"RQ1": 0, "RQ2": 0, "RQ3": 0}
    if not cards:
        print("[警告] 目前 02_notes/cards/ 目錄下尚無 card_*.md 檔案。")
        print("[指引] 請先使用第六週 academic-reading-card Skill 產出單篇閱讀卡片。")
        return 0

    for idx, c in enumerate(cards, 1):
        print(f"  {idx}. [{c['filename']}] {c['first_author']} ({c['year']})")
        print(f"     - RQ1 映射: {c['rq1_status']}")
        print(f"     - RQ2 映射: {c['rq2_status']}")
        print(f"     - RQ3 映射: {c['rq3_status']}")
        for r_i in [1, 2, 3]:
            if c[f"rq{r_i}_status"].startswith("有啟發"):
                rq_counts[f"RQ{r_i}"] += 1

    print("------------------------------------------------------------------")
    print("[統計] 核心研究問題 (RQs) 卡片支撐覆蓋度：")
    print(f"  - RQ1 支撐卡片數 : {rq_counts['RQ1']} / {len(cards)} 篇")
    print(f"  - RQ2 支撐卡片數 : {rq_counts['RQ2']} / {len(cards)} 篇")
    print(f"  - RQ3 支撐卡片數 : {rq_counts['RQ3']} / {len(cards)} 篇")
    print("==================================================================")

    if args.init_draft:
        out_path = root / "02_notes" / "literature_matrix.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        card_list_str = "\n".join(f"  - {c['filename']}" for c in cards)
        rows_rq = "\n".join(
            f"| **{c['first_author']} ({c['year']})** | `{c['filename']}` | 待填文類 | {c['rq1_status']} | {c['rq2_status']} | {c['rq3_status']} |"
            for c in cards
        )
        draft_md = f"""---
type: literature_matrix
matrix_version: 1.0
project_title: "{project_title}"
card_count: {len(cards)}
included_cards:
{card_list_str}
rq_coverage:
  RQ1: {rq_counts['RQ1']}
  RQ2: {rq_counts['RQ2']}
  RQ3: {rq_counts['RQ3']}
created_date: {datetime.now().strftime('%Y-%m-%d')}
---

# 跨篇文獻比較矩陣與概念導向綜整：{project_title}

## 1. 卡片庫盤點與研究問題（RQs）映射分佈 (Card Inventory & RQ Mapping Overview)

| 文獻標識 (Citation) | 來源卡片檔名 | 文獻文類 (Genre) | RQ1 | RQ2 | RQ3 |
| :--- | :--- | :--- | :--- | :--- | :--- |
{rows_rq}

## 2. 第一層矩陣：跨篇方法學與實證特徵全覽矩陣 (Methodological & Empirical Overview Matrix)

| 篇名與作者 (Citation & Genre) | 理論框架 | 研究對象與情境 | 核心機制 / 介入工具 | 評估指標與關鍵發現 | 方法學盲點與外推邊界 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 待 Agent 依卡片填寫 | 待填寫 | 待填寫 | 待填寫 | 待填寫 | 待填寫 |

## 3. 第二層矩陣：概念中心與研究問題對映矩陣 (Concept-Centric & RQ-Clustered Matrix)

| 核心概念構面 | 對應研究問題 | 主流實證共識與支持文獻 | 跨篇爭端、反例或條件限制 | 現有文獻之方法學或系統結構缺口 |
| :--- | :--- | :--- | :--- | :--- |
| 構面一 | RQ1 | 待填寫 | 待填寫 | 待填寫 |
| 構面二 | RQ2 | 待填寫 | 待填寫 | 待填寫 |
| 構面三 | RQ3 | 待填寫 | 待填寫 | 待填寫 |

## 4. 跨篇對話三態綜整分析 (Tri-Modal Thematic Synthesis)

### 4.1 學術共識底座 (Scholarly Consensus)
待 Agent 依卡片綜整撰寫。

### 4.2 學術爭端與理論張力 (Contradiction & Theoretical Tension)
待 Agent 依卡片綜整撰寫。

### 4.3 情境脈絡與方法微差 (Contextual Nuance & Methodological Shifts)
待 Agent 依卡片綜整撰寫。
"""
        out_path.write_text(draft_md, encoding="utf-8")
        print(f"[成功] 已生成跨篇文獻矩陣骨架草稿：{out_path}")

    return 0


def validate_matrix(file_path: str) -> bool:
    p = Path(file_path)
    if not p.exists():
        print(f"[錯誤] 找不到矩陣檔案：{file_path}")
        return False

    content = p.read_text(encoding="utf-8", errors="ignore")
    errors = []
    warnings = []

    # 1. 檢查 YAML Frontmatter
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

    # 2. 檢查四大主章節標題
    for num, keyword in REQUIRED_SECTIONS:
        pattern = rf"^##\s*{num}\.\s*.*{keyword}.*"
        if not re.search(pattern, content, re.MULTILINE):
            errors.append(f"缺少第 {num} 節標準標題（需包含「## {num}. ...{keyword}...」）")

    # 3. 檢查第 4 節三態綜整子標題 (4.1, 4.2, 4.3)
    for sub in REQUIRED_SYNTHESIS_SUBSECTIONS:
        if not re.search(rf"^###\s*{re.escape(sub)}\s+", content, re.MULTILINE):
            errors.append(f"缺少跨篇對話三態綜整子小節：### {sub}")

    # 4. 檢查是否包含至少兩個 Markdown 表格
    table_headers = re.findall(r"^\|.*\|\s*\n\|[\s:|-]+\|", content, re.MULTILINE)
    if len(table_headers) < 2:
        errors.append("檔案中至少需包含兩個結構化 Markdown 矩陣表格（第一層方法學全覽矩陣與第二層概念中心對映矩陣）")

    # 5. 檢查是否提及 RQ1-RQ3
    for rq in ["RQ1", "RQ2", "RQ3"]:
        if rq not in content:
            warnings.append(f"矩陣內容未明確標註 {rq}，建議確認與 PROJECT.md 的研究問題對齊")

    print("\n==========================================")
    print(f"[檢查] 驗證跨篇文獻矩陣：{p.name}")
    print("==========================================")

    if errors:
        print(f"[FAIL] 驗證未通過！共發現 {len(errors)} 項結構缺失：")
        for err in errors:
            print(f"   * {err}")
    else:
        print("[PASS] 格式合規！完全通過雙層次跨篇文獻矩陣與三態綜整 Schema 檢驗！")

    if warnings:
        print(f"\n[WARN] 提醒事項 ({len(warnings)} 項)：")
        for w in warnings:
            print(f"   * {w}")

    return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(description="跨篇文獻比較矩陣合成與合規驗證工具")
    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan", help="掃描 02_notes/cards/ 並統計 RQ 映射覆蓋率")
    scan_parser.add_argument("--init-draft", action="store_true", help="於 02_notes/literature_matrix.md 生成預填骨架草稿")

    val_parser = subparsers.add_parser("validate", help="驗證 literature_matrix.md 是否符合標準 Schema")
    val_parser.add_argument("matrix_path", nargs="?", default="02_notes/literature_matrix.md", help="矩陣檔案路徑")

    args = parser.parse_args()
    if args.command == "scan":
        sys.exit(cmd_scan(args))
    elif args.command == "validate":
        ok = validate_matrix(args.matrix_path)
        sys.exit(0 if ok else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
