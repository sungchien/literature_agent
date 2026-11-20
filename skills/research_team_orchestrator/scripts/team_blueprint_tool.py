#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多代理學術團隊藍圖盤點、初始化與合規驗證工具 (team_blueprint_tool.py)

用途：
1. check-inputs : 盤點工作區前置資產（PROJECT.md、文獻矩陣、空白報告、向量索引）是否齊備。
2. init         : 依據標準範本建立個人化 02_notes/research_team_blueprint.md 起始草稿。
3. validate     : 檢驗團隊藍圖是否完整具備 YAML Frontmatter、四大核心章節、角色權限邊界與 HITL 閘門。

用法：
  python skills/research_team_orchestrator/scripts/team_blueprint_tool.py check-inputs
  python skills/research_team_orchestrator/scripts/team_blueprint_tool.py init
  python skills/research_team_orchestrator/scripts/team_blueprint_tool.py validate 02_notes/research_team_blueprint.md
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

# 解決 Windows 終端機 UTF-8 編碼輸出問題
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REQUIRED_FRONTMATTER_FIELDS = [
    "type",
    "blueprint_version",
    "project_title",
    "topology_pattern",
    "agent_count",
    "hitl_gates",
    "created_date",
]

REQUIRED_SECTIONS = [
    (1, "團隊總覽與協作拓撲選型"),
    (2, "角色名冊與最小權限邊界表"),
    (3, "結構化交接契約與人類審查閘門"),
    (4, "派工與隔離驗證試跑計畫"),
]


def find_workspace_root() -> Path:
    current = Path.cwd()
    for p in [current, current.parent, current.parent.parent, current.parent.parent.parent]:
        if (p / "PROJECT.md").exists() or (p / "02_notes").exists():
            return p
    return current


def cmd_check_inputs(args) -> int:
    root = find_workspace_root()
    checks = [
        ("PROJECT.md", root / "PROJECT.md", True),
        ("02_notes/literature_matrix.md", root / "02_notes" / "literature_matrix.md", True),
        ("02_notes/research_gap_statement.md", root / "02_notes" / "research_gap_statement.md", True),
        ("01_papers/vector_index.json", root / "01_papers" / "vector_index.json", True),
        ("02_notes/cards/", root / "02_notes" / "cards", False),
        ("03_drafts/", root / "03_drafts", False),
    ]

    print("==================================================================")
    print("[資訊] 多代理學術團隊前置資產盤點 (Team Input Readiness Check)")
    print("==================================================================")
    print(f"[路徑] 工作區根目錄 : {root}")

    missing_required = 0
    for label, path, required in checks:
        exists = path.exists()
        if exists and path.is_dir():
            count = len(list(path.glob("*.md")))
            status = f"[就緒] ({count} 份 Markdown 檔案)"
        elif exists:
            size_kb = path.stat().st_size / 1024.0
            status = f"[就緒] ({size_kb:.1f} KB)"
        else:
            status = "[缺失]" if required else "[尚未建立]"
            if required:
                missing_required += 1
        print(f"   * {label:<36} : {status}")

    print("------------------------------------------------------------------")
    if missing_required == 0:
        print("[成功] 核心前置資產皆已就緒，可開始設計多代理研究團隊藍圖。")
    else:
        print(f"[警告] 尚有 {missing_required} 項建議前置檔案缺失，建議先完成前序章節產出。")
    print("==================================================================")
    return 0


def cmd_init(args) -> int:
    root = find_workspace_root()
    template_path = (
        Path(__file__).resolve().parent.parent / "resources" / "team_blueprint_template.md"
    )
    target_path = root / "02_notes" / "research_team_blueprint.md"

    if not template_path.exists():
        print(f"[錯誤] 找不到藍圖範本檔案：{template_path}")
        return 1

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists() and not args.force:
        print(f"[警告] 目標檔案已存在：{target_path.relative_to(root)}")
        print("[指引] 若需覆蓋重建，請加上 --force 參數。")
        return 1

    shutil.copy2(template_path, target_path)
    print("==================================================================")
    print("[成功] 已初始化個人化多代理研究團隊藍圖草稿！")
    print(f"   * 輸出路徑 : {target_path.relative_to(root)}")
    print("[指引] 請依研究主題填寫各欄位後，執行 validate 指令檢驗合規性。")
    print("==================================================================")
    return 0


def validate_blueprint(file_path: str) -> bool:
    p = Path(file_path)
    if not p.exists():
        print(f"[錯誤] 找不到研究團隊藍圖檔案：{file_path}")
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

    # 3. 檢查角色與最小權限關鍵要素
    for kw in ["禁止", "唯讀", "HITL"]:
        if kw not in content:
            errors.append(f"藍圖缺少關鍵治理規範標記：「{kw}」（須明確定義角色禁區與人類審查閘門）")

    # 4. 檢查是否保留未填寫之佔位符提示
    if "請填入" in content:
        warnings.append("偵測到範本佔位文字「請填入」，請確認所有欄位皆已替換為實際研究設計。")

    # 5. 檢查上下文隔離設計
    if "隔離" not in content:
        warnings.append("建議於第 2 節或第 4 節明確說明稽核／審稿角色的上下文隔離機制。")

    print("\n==========================================")
    print(f"[檢查] 驗證研究團隊藍圖：{p.name}")
    print("==========================================")

    if errors:
        print(f"[FAIL] 驗證未通過！共發現 {len(errors)} 項結構缺失：")
        for err in errors:
            print(f"   * {err}")
    else:
        print("[PASS] 格式合規！完全通過多代理團隊藍圖角色權限、交接契約與 HITL 檢驗！")

    if warnings:
        print(f"\n[WARN] 提醒事項 ({len(warnings)} 項)：")
        for w in warnings:
            print(f"   * {w}")

    return len(errors) == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="多代理學術團隊藍圖盤點、初始化與合規驗證工具"
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("check-inputs", help="盤點工作區前置研究資產是否齊備")

    init_parser = subparsers.add_parser("init", help="建立 02_notes/research_team_blueprint.md 起始範本")
    init_parser.add_argument("--force", action="store_true", help="若檔案已存在則強制覆蓋")

    val_parser = subparsers.add_parser("validate", help="驗證研究團隊藍圖是否符合標準 Schema")
    val_parser.add_argument(
        "blueprint_path",
        nargs="?",
        default="02_notes/research_team_blueprint.md",
        help="藍圖檔案路徑（預設：02_notes/research_team_blueprint.md）",
    )

    args = parser.parse_args()
    if args.command == "check-inputs":
        return cmd_check_inputs(args)
    if args.command == "init":
        return cmd_init(args)
    if args.command == "validate":
        return 0 if validate_blueprint(args.blueprint_path) else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
