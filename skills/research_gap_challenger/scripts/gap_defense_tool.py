#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
學術空白鎖定、口試防禦檢驗與專案規格升級工具 (gap_defense_tool.py)
用途：
1. audit           : 讀取 02_notes/literature_matrix.md 與 PROJECT.md，自動審計跨篇限制與 RQ 缺口線索。
2. validate        : 自動檢驗 02_notes/research_gap_statement.md 是否符合 CARS 四步結構、四大空白型態與三回合口試答辯規範。
3. archive-project : 將根目錄現有的 PROJECT.md 安全備份歸檔至 05_project_history/PROJECT_{version}.md，確保規格演進有跡可循。

用法：
  python skills/research_gap_challenger/scripts/gap_defense_tool.py audit
  python skills/research_gap_challenger/scripts/gap_defense_tool.py validate 02_notes/research_gap_statement.md
  python skills/research_gap_challenger/scripts/gap_defense_tool.py archive-project --version v0.3
"""

import os
import re
import sys
import shutil
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
    "type", "gap_version", "project_title",
    "source_matrix", "gap_types", "target_project_version", "created_date"
]

REQUIRED_SECTIONS = [
    (1, "跨篇矩陣盲點審計與真偽空白診斷"),
    (2, "CARS 四步修辭轉折學術空白陳述句"),
    (3, "對抗性口試委員極限壓力測試與答辯實錄"),
    (4, "研究問題"),
]


def find_workspace_root() -> Path:
    current = Path.cwd()
    for p in [current, current.parent, current.parent.parent, current.parent.parent.parent]:
        if (p / "PROJECT.md").exists() or (p / "02_notes").exists():
            return p
    return current


def cmd_audit(args):
    root = find_workspace_root()
    matrix_path = root / "02_notes" / "literature_matrix.md"
    cards_dir = root / "02_notes" / "cards"
    proj_path = root / "PROJECT.md"

    print("==================================================================")
    print("[資訊] 學術空白 (Research Gap) 前導審計工具 (Gap Defense Auditor)")
    print("==================================================================")
    print(f"[路徑] 工作區根目錄 : {root}")

    if proj_path.exists():
        proj_txt = proj_path.read_text(encoding="utf-8", errors="ignore")
        rqs = re.findall(r"-\s*\*\*(RQ\d+[^*]*)\*\*\s*(.+)", proj_txt)
        print(f"[專案] 已載入 PROJECT.md，偵測到 {len(rqs)} 項探索性研究問題：")
        for rq_label, rq_desc in rqs:
            print(f"   * {rq_label} {rq_desc[:55]}...")
    else:
        print("[警告] 根目錄找不到 PROJECT.md！")

    print("------------------------------------------------------------------")
    if matrix_path.exists():
        m_txt = matrix_path.read_text(encoding="utf-8", errors="ignore")
        print(f"[成功] 已找到跨篇文獻矩陣 : {matrix_path.relative_to(root)} ({len(m_txt)} 字元)")
        has_tension = "4.2" in m_txt or "爭端" in m_txt or "矛盾" in m_txt
        has_nuance = "4.3" in m_txt or "微差" in m_txt or "邊界" in m_txt
        print(f"   * 跨篇爭端與張力段落檢核 : {'[已具備]' if has_tension else '[待補充]'}")
        print(f"   * 情境脈絡與邊界段落檢核 : {'[已具備]' if has_nuance else '[待補充]'}")
    else:
        print("[警告] 尚未找到 02_notes/literature_matrix.md！")
        print("[指引] 請先執行第七週 literature-matrix-synthesizer Skill 建立跨篇比較矩陣。")

    card_gaps = []
    if cards_dir.exists():
        for c_path in sorted(cards_dir.glob("card_*.md")):
            c_txt = c_path.read_text(encoding="utf-8", errors="ignore")
            m_gap = re.search(r"本研究可推進的空間[^：:\n]*[：:]\**\s*(.+)", c_txt)
            if m_gap:
                card_gaps.append((c_path.name, m_gap.group(1).strip()))

    print("------------------------------------------------------------------")
    print(f"[統計] 從單篇閱讀卡片第 6 維度提取之潛在推進線索 ({len(card_gaps)} 筆)：")
    if not card_gaps:
        print("   (目前卡片庫中尚無已填寫之 Research Gap 線索)")
    else:
        for c_name, g_str in card_gaps:
            print(f"   * [{c_name}] -> {g_str[:65]}...")
    print("==================================================================")
    return 0


def cmd_archive_project(args):
    root = find_workspace_root()
    proj_path = root / "PROJECT.md"
    hist_dir = root / "05_project_history"
    hist_dir.mkdir(parents=True, exist_ok=True)

    if not proj_path.exists():
        print(f"[錯誤] 根目錄找不到 PROJECT.md：{proj_path}")
        return 1

    ver = args.version.strip()
    if not ver.startswith("v"):
        ver = "v" + ver

    target_file = hist_dir / f"PROJECT_{ver}.md"
    shutil.copy2(proj_path, target_file)
    print("==================================================================")
    print("[成功] 專案規格書歷史版本歸檔完成！")
    print(f"   * 來源檔案 : {proj_path.relative_to(root)}")
    print(f"   * 歸檔路徑 : {target_file.relative_to(root)}")
    print("[指引] 現在可安全將收斂後之 Research Gap 與定錨版 RQ1-RQ3 寫入根目錄 PROJECT.md (v0.4)。")
    print("==================================================================")
    return 0


def validate_gap_statement(file_path: str) -> bool:
    p = Path(file_path)
    if not p.exists():
        print(f"[錯誤] 找不到學術空白防禦報告檔案：{file_path}")
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

    # 2. 檢查四大主章節
    for num, keyword in REQUIRED_SECTIONS:
        pattern = rf"^##\s*{num}\.\s*.*{keyword}.*"
        if not re.search(pattern, content, re.MULTILINE):
            errors.append(f"缺少第 {num} 節標準標題（需包含「## {num}. ...{keyword}...」）")

    # 3. 檢查 CARS 四步修辭關鍵元素
    cars_keywords = ["第一步", "第二步", "第三步", "第四步"]
    for kw in cars_keywords:
        if kw not in content:
            errors.append(f"第 2 節缺少 CARS 四步修辭轉折結構標記：{kw}")

    # 4. 檢查三回合對抗性口試答辯 (3.1, 3.2, 3.3)
    for sub in ["3.1", "3.2", "3.3"]:
        if not re.search(rf"^###\s*{re.escape(sub)}\s+", content, re.MULTILINE):
            errors.append(f"第 3 節缺少口試對抗壓力測試回合：### {sub}")

    # 5. 檢查 RQ1-RQ3 收斂映射
    for rq in ["RQ1", "RQ2", "RQ3"]:
        if rq not in content:
            warnings.append(f"報告中未明確提及 {rq} 的收斂映射，請確認第 4 節是否完整對接 PROJECT.md")

    print("\n==========================================")
    print(f"[檢查] 驗證學術空白與口試防禦報告：{p.name}")
    print("==========================================")

    if errors:
        print(f"[FAIL] 驗證未通過！共發現 {len(errors)} 項結構缺失：")
        for err in errors:
            print(f"   * {err}")
    else:
        print("[PASS] 格式合規！完全通過 CARS 四步學術空白陳述與三回合口試防禦 Schema 檢驗！")

    if warnings:
        print(f"\n[WARN] 提醒事項 ({len(warnings)} 項)：")
        for w in warnings:
            print(f"   * {w}")

    return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(description="學術空白鎖定、口試防禦檢驗與專案規格升級工具")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("audit", help="審計 literature_matrix.md 與 PROJECT.md 之研究空白線索")

    arch_parser = subparsers.add_parser("archive-project", help="將現有 PROJECT.md 備份歸檔至 05_project_history/")
    arch_parser.add_argument("--version", default="v0.3", help="欲歸檔之舊版版本號 (預設: v0.3)")

    val_parser = subparsers.add_parser("validate", help="驗證 research_gap_statement.md 是否符合標準 Schema")
    val_parser.add_argument("report_path", nargs="?", default="02_notes/research_gap_statement.md", help="報告檔案路徑")

    args = parser.parse_args()
    if args.command == "audit":
        sys.exit(cmd_audit(args))
    elif args.command == "archive-project":
        sys.exit(cmd_archive_project(args))
    elif args.command == "validate":
        ok = validate_gap_statement(args.report_path)
        sys.exit(0 if ok else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
