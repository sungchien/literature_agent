#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多代理對抗式審查、草稿引文掃描與 AI 使用揭露驗證工具 (draft_audit_tool.py)

用途：
1. scan-draft          : 掃描 03_drafts/ 草稿之段落數、文內引註、證據編號 [EV-XX] 與無錨點風險句。
2. init-disclosure     : 建立 03_drafts/ai_collaboration_disclosure.md 標準揭露聲明範本。
3. validate-review     : 驗證 03_drafts/_peer_review_report.md 是否符合三路審查與 PI 裁決 Schema。
4. validate-disclosure : 驗證 03_drafts/ai_collaboration_disclosure.md 是否完整具備雙語聲明與人類簽署。

用法：
  python skills/multi_agent_peer_reviewer/scripts/draft_audit_tool.py scan-draft 03_drafts/02_literature_review_draft.md
  python skills/multi_agent_peer_reviewer/scripts/draft_audit_tool.py init-disclosure
  python skills/multi_agent_peer_reviewer/scripts/draft_audit_tool.py validate-review 03_drafts/_peer_review_report.md
  python skills/multi_agent_peer_reviewer/scripts/draft_audit_tool.py validate-disclosure 03_drafts/ai_collaboration_disclosure.md
"""

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import List

# 解決 Windows 終端機 UTF-8 編碼輸出問題
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REVIEW_FRONTMATTER_FIELDS = [
    "type",
    "report_version",
    "project_title",
    "target_draft",
    "review_rounds",
    "blocking_issues_remaining",
    "created_date",
]

REVIEW_SECTIONS = [
    (1, "審查範圍與輸入資產檢核"),
    (2, "三路對抗審查意見彙整表"),
    (3, "跨回合修訂追蹤與分流處置"),
    (4, "人類 PI 終局裁決紀錄"),
]

DISCLOSURE_FRONTMATTER_FIELDS = [
    "type",
    "disclosure_version",
    "project_title",
    "target_manuscript",
    "human_author",
    "human_verification_rate",
    "created_date",
]

DISCLOSURE_SECTIONS = [
    (1, "協作工具與系統環境清單"),
    (2, "多代理角色分工與權限邊界紀錄"),
    (3, "人類研究者實質控制權與核實紀錄"),
    (4, "標準揭露聲明段落"),
    (5, "研究者終局簽署"),
]


def find_workspace_root() -> Path:
    current = Path.cwd()
    for p in [current, current.parent, current.parent.parent, current.parent.parent.parent]:
        if (p / "PROJECT.md").exists() or (p / "03_drafts").exists():
            return p
    return current


def check_frontmatter(content: str, required_fields: List[str]) -> List[str]:
    errors = []
    if not content.startswith("---"):
        errors.append("缺少開頭 YAML Frontmatter 分隔線 (---)")
        return errors
    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append("YAML Frontmatter 未正確閉合 (需要第二個 ---)")
        return errors
    fm_text = parts[1]
    for field in required_fields:
        if not re.search(rf"^{field}\s*:", fm_text, re.MULTILINE):
            errors.append(f"Frontmatter 缺少必備欄位：{field}")
    return errors


def cmd_scan_draft(args) -> int:
    root = find_workspace_root()
    draft_path = Path(args.draft_path)
    if not draft_path.is_absolute():
        draft_path = root / draft_path

    if not draft_path.exists():
        print(f"[錯誤] 找不到待掃描草稿檔案：{draft_path}")
        return 1

    text = draft_path.read_text(encoding="utf-8", errors="ignore")
    ev_pack_path = root / "03_drafts" / "_evidence_pack.md"
    defined_evs = set()
    if ev_pack_path.exists():
        ev_txt = ev_pack_path.read_text(encoding="utf-8", errors="ignore")
        defined_evs = set(re.findall(r"\[(EV-\d+)\]", ev_txt))

    paragraphs = [
        p.strip()
        for p in re.split(r"\n\s*\n", text)
        if p.strip() and not p.strip().startswith("#") and not p.strip().startswith("---")
    ]

    cite_pattern = re.compile(r"\([A-Z][A-Za-z\-&\s]+,\s*\d{4}[a-z]?\)|[A-Z][A-Za-z\-]+\s*\(\d{4}\)")
    ev_pattern = re.compile(r"\[(EV-\d+)\]")
    stat_pattern = re.compile(r"(\d+%|\bp\s*[<>=]\s*\.?\d+|\bN\s*=\s*\d+|\bF\s*\()")

    total_cites = 0
    total_evs = []
    unanchored_risks = []

    for idx, para in enumerate(paragraphs, 1):
        cites = cite_pattern.findall(para)
        evs = ev_pattern.findall(para)
        total_cites += len(cites)
        total_evs.extend(evs)
        if (cites or stat_pattern.search(para)) and not evs:
            unanchored_risks.append((idx, para[:55].replace("\n", " ")))

    used_ev_set = set(total_evs)
    orphan_evs = sorted(used_ev_set - defined_evs) if defined_evs else []

    print("==================================================================")
    print(f"[資訊] 草稿事實錨點與引文預掃描：{draft_path.name}")
    print("==================================================================")
    print(f"   * 實質論述段落數           : {len(paragraphs)} 段")
    print(f"   * 偵測 APA 文內引註次數    : {total_cites} 次")
    print(f"   * 偵測證據編號標記 [EV-XX] : {len(total_evs)} 處（涵蓋 {len(used_ev_set)} 筆獨立證據）")
    if ev_pack_path.exists():
        print(f"   * 證據包已登錄條目數       : {len(defined_evs)} 筆")
        if orphan_evs:
            print(f"[警告] 草稿出現未在 _evidence_pack.md 登錄之編號：{', '.join(orphan_evs)}")
    else:
        print("[警告] 尚未找到 03_drafts/_evidence_pack.md，無法比對證據包登錄編號。")

    print("------------------------------------------------------------------")
    if unanchored_risks:
        print(f"[警告] 發現 {len(unanchored_risks)} 個包含引文或數據但缺乏 [EV-XX] 錨點之段落：")
        for p_idx, preview in unanchored_risks:
            print(f"   * 第 {p_idx} 段 : {preview}...")
        print("[指引] 建議交由事實稽核審稿代理於隔離視窗逐一反查原文出處。")
    else:
        print("[成功] 所有包含引文或統計數據之段落均已標註 [EV-XX] 證據編號。")
    print("==================================================================")
    return 0


def cmd_init_disclosure(args) -> int:
    root = find_workspace_root()
    template_path = (
        Path(__file__).resolve().parent.parent / "resources" / "ai_disclosure_template.md"
    )
    target_path = root / "03_drafts" / "ai_collaboration_disclosure.md"

    if not template_path.exists():
        print(f"[錯誤] 找不到揭露聲明範本：{template_path}")
        return 1

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists() and not args.force:
        print(f"[警告] 目標檔案已存在：{target_path.relative_to(root)}")
        print("[指引] 若需覆蓋重建，請加上 --force 參數。")
        return 1

    shutil.copy2(template_path, target_path)
    print("==================================================================")
    print("[成功] 已初始化 AI 協作使用揭露聲明範本！")
    print(f"   * 輸出路徑 : {target_path.relative_to(root)}")
    print("[指引] 請填寫個人查證紀錄與簽署日期後，執行 validate-disclosure 檢驗。")
    print("==================================================================")
    return 0


def cmd_validate_review(args) -> int:
    p = Path(args.report_path)
    if not p.exists():
        print(f"[錯誤] 找不到同儕審查報告：{args.report_path}")
        return 1

    content = p.read_text(encoding="utf-8", errors="ignore")
    errors = check_frontmatter(content, REVIEW_FRONTMATTER_FIELDS)
    warnings = []

    for num, keyword in REVIEW_SECTIONS:
        pattern = rf"^##\s*{num}\.\s*.*{keyword}.*"
        if not re.search(pattern, content, re.MULTILINE):
            errors.append(f"缺少第 {num} 節標準標題（需包含「## {num}. ...{keyword}...」）")

    for role in ["事實稽核", "方法學審稿", "結構編輯"]:
        if role not in content:
            errors.append(f"審查彙整表缺少三路審查角色之一：「{role}」")

    if "請填入" in content:
        warnings.append("偵測到範本佔位文字「請填入」，請確認所有欄位均已實際填寫。")

    print("\n==========================================")
    print(f"[檢查] 驗證多代理同儕審查報告：{p.name}")
    print("==========================================")
    if errors:
        print(f"[FAIL] 驗證未通過！共發現 {len(errors)} 項結構缺失：")
        for e in errors:
            print(f"   * {e}")
    else:
        print("[PASS] 格式合規！完全通過三路對抗同儕審查報告 Schema 檢驗！")
    if warnings:
        print(f"\n[WARN] 提醒事項 ({len(warnings)} 項)：")
        for w in warnings:
            print(f"   * {w}")
    return 0 if not errors else 1


def cmd_validate_disclosure(args) -> int:
    p = Path(args.disclosure_path)
    if not p.exists():
        print(f"[錯誤] 找不到 AI 使用揭露聲明檔案：{args.disclosure_path}")
        return 1

    content = p.read_text(encoding="utf-8", errors="ignore")
    errors = check_frontmatter(content, DISCLOSURE_FRONTMATTER_FIELDS)
    warnings = []

    for num, keyword in DISCLOSURE_SECTIONS:
        pattern = rf"^##\s*{num}\.\s*.*{keyword}.*"
        if not re.search(pattern, content, re.MULTILINE):
            errors.append(f"缺少第 {num} 節標準標題（需包含「## {num}. ...{keyword}...」）")

    if "100%" not in content and "核實" not in content:
        errors.append("缺少人類研究者原始文獻覆核確認紀錄")

    if "Principal Investigator" not in content and "author" not in content:
        warnings.append("請確認已包含中英雙語揭露聲明段落。")

    if "請填入" in content:
        warnings.append("偵測到範本佔位文字「請填入」，請確認已填妥作者姓名與簽署日期。")

    print("\n==========================================")
    print(f"[檢查] 驗證 AI 協作使用揭露聲明：{p.name}")
    print("==========================================")
    if errors:
        print(f"[FAIL] 驗證未通過！共發現 {len(errors)} 項結構缺失：")
        for e in errors:
            print(f"   * {e}")
    else:
        print("[PASS] 格式合規！完全通過學術誠信與 AI 協作揭露聲明 Schema 檢驗！")
    if warnings:
        print(f"\n[WARN] 提醒事項 ({len(warnings)} 項)：")
        for w in warnings:
            print(f"   * {w}")
    return 0 if not errors else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="多代理對抗式審查、草稿引文掃描與 AI 使用揭露驗證工具"
    )
    subparsers = parser.add_subparsers(dest="command")

    scan_p = subparsers.add_parser("scan-draft", help="掃描草稿段落引文與 [EV-XX] 證據錨點")
    scan_p.add_argument(
        "draft_path",
        nargs="?",
        default="03_drafts/02_literature_review_draft.md",
        help="草稿檔案路徑",
    )

    init_p = subparsers.add_parser("init-disclosure", help="初始化 AI 協作使用揭露聲明")
    init_p.add_argument("--force", action="store_true", help="若檔案已存在則強制覆蓋")

    rev_p = subparsers.add_parser("validate-review", help="驗證多代理同儕審查報告 Schema")
    rev_p.add_argument(
        "report_path",
        nargs="?",
        default="03_drafts/_peer_review_report.md",
        help="審查報告檔案路徑",
    )

    dis_p = subparsers.add_parser("validate-disclosure", help="驗證 AI 協作使用揭露聲明 Schema")
    dis_p.add_argument(
        "disclosure_path",
        nargs="?",
        default="03_drafts/ai_collaboration_disclosure.md",
        help="揭露聲明檔案路徑",
    )

    args = parser.parse_args()
    if args.command == "scan-draft":
        return cmd_scan_draft(args)
    if args.command == "init-disclosure":
        return cmd_init_disclosure(args)
    if args.command == "validate-review":
        return cmd_validate_review(args)
    if args.command == "validate-disclosure":
        return cmd_validate_disclosure(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
