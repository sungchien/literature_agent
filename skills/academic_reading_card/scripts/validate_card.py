#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
學術閱讀卡片規格驗證腳本 (validate_card.py)
用途：自動化檢驗 02_notes/cards/*.md 是否符合七維標準 Schema 規範。
用法：python skills/academic_reading_card/scripts/validate_card.py 02_notes/cards/card_XXXX.md
"""

import sys
import os
import re

# 解決 Windows 主控台編碼問題
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REQUIRED_FRONTMATTER_FIELDS = [
    "type", "card_version", "bibtex_key", "title",
    "first_author", "year", "journal", "doi", "source_md", "tags"
]

REQUIRED_SECTIONS = [
    (1, "文獻元數據與引用標識"),
    (2, "核心研究問題與理論框架"),
    (3, "研究設計與實證方法論"),
    (4, "關鍵實證數據與核心發現"),
    (5, "批判性審視與方法學盲點"),
    (6, "對本研究 PROJECT.md 的直接啟發"),
    (7, "黃金引句與出處錨點"),
]

def validate_card(file_path: str) -> bool:
    if not os.path.exists(file_path):
        print(f"[ERROR] 找不到卡片檔案：{file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    errors = []
    warnings = []

    # 1. 檢查 Frontmatter
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

    # 2. 檢查七維標題
    for num, title in REQUIRED_SECTIONS:
        pattern = rf"^##\s*{num}\.\s*.*"
        if not re.search(pattern, content, re.MULTILINE):
            errors.append(f"缺少第 {num} 維度標題：## {num}. {title}")

    # 3. 檢查第 6 維度是否包含 RQ 映射
    if "## 6." in content:
        sec6_text = content.split("## 6.")[1].split("## 7.")[0] if "## 7." in content else content.split("## 6.")[1]
        if not re.search(r"RQ[1-3]", sec6_text):
            warnings.append("第 6 維度建議明確提及 RQ1、RQ2 或 RQ3 的對接啟發")

    # 4. 輸出檢驗結果
    print("\n==========================================")
    print(f"[CARD] 驗證卡片檔案：{os.path.basename(file_path)}")
    print("==========================================")

    if errors:
        print(f"[FAIL] 驗證失敗！發現 {len(errors)} 個格式錯誤：")
        for err in errors:
            print(f"   * {err}")
    else:
        print("[PASS] 格式合規！完全通過七維標準學術 Schema 檢驗！")

    if warnings:
        print(f"\n[WARN] 溫馨提示 ({len(warnings)} 項)：")
        for w in warnings:
            print(f"   * {w}")

    return len(errors) == 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方式: python validate_card.py <卡片檔案路徑>")
        sys.exit(1)
    
    target_path = sys.argv[1]
    success = validate_card(target_path)
    sys.exit(0 if success else 1)
