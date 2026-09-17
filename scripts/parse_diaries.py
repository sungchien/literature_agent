"""
scripts/parse_diaries.py

用途：批次解析 04_research_data/diaries/ 下的所有學生研究日記
演算法功能：
1. 自動提取 YAML Frontmatter 中的結構化量化指標（認知負荷、自我效能、里程碑）
2. 結構化提取各章節 Markdown 質性文本（提示詞記錄、瓶頸、反思、情感感受）
3. 支援將全班資料整合成單一 JSON 資料集或 CSV/Pandas DataFrame，供後續統計分析與 LLM 質性編碼。
"""

import os
import re
import sys
import json
import glob
from pathlib import Path
from typing import Dict, Any, List

# 確保 Windows 命令列輸出支援 UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


DIARIES_DIR = Path("04_research_data/diaries")
OUTPUT_SUMMARY_JSON = Path("04_research_data/diaries_summary.json")

def extract_checked_options(text: str) -> List[str]:
    """提取段落中被勾選的選項 [x] 或 [X]"""
    pattern = r"-\s*\[[xX]\]\s*(?:\*\*)?([^\n\*]+)"
    matches = re.findall(pattern, text)
    return [m.strip() for m in matches]

def parse_single_diary(file_path: Path) -> Dict[str, Any]:
    """解析單份研究日記（YAML Frontmatter + Markdown 階層分段）"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 提取 YAML Frontmatter
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not frontmatter_match:
        return {"file": file_path.name, "error": "無有效 YAML Frontmatter"}

    yaml_raw = frontmatter_match.group(1)
    body_markdown = frontmatter_match.group(2)

    # 簡易 YAML 解析器（優先嘗試 PyYAML，若無則以正則解析標準鍵值）
    data = {}
    try:
        import yaml
        data = yaml.safe_load(yaml_raw) or {}
    except ImportError:
        # 簡易純 Python 備用解析
        for line in yaml_raw.split("\n"):
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip().strip('"').strip("'")

    data["source_file"] = file_path.name

    # 2. 演算法結構化切分 Markdown 質性章節 (Regex Section Splitter)
    sections = {}
    pattern = r"##\s+(\d+\.[^\n]+)\n(.*?)(?=(?:##\s+\d+\.|\Z))"
    matches = re.findall(pattern, body_markdown, re.DOTALL)
    for title, text in matches:
        clean_title = title.strip()
        sections[clean_title] = text.strip()

    data["qualitative_sections"] = sections

    # 3. 自動解析核選項目（Checkboxes [x] 特徵提取）
    data["checkbox_features"] = {
        "interaction_outcomes": extract_checked_options(sections.get("1. 客觀歷程與工具操作日誌 (Objective Activity Logs)", "")),
        "bottlenecks": extract_checked_options(sections.get("2. 遭遇瓶頸與意外障礙 (Bottlenecks & Discrepancies - RQ3)", ""))
    }

    return data

def parse_all_diaries() -> List[Dict[str, Any]]:
    """掃描所有學生填寫的日記檔案（排除 TEMPLATE 檔案）"""
    diary_files = [
        f for f in DIARIES_DIR.glob("*.md")
        if not f.name.startswith("TEMPLATE")
    ]

    print(f"[掃描] 正在掃描 {DIARIES_DIR}，共發現 {len(diary_files)} 份學生研究日記...")
    results = []
    for f in diary_files:
        parsed = parse_single_diary(f)
        results.append(parsed)

    # 儲存結構化彙整 JSON
    if results:
        with open(OUTPUT_SUMMARY_JSON, "w", encoding="utf-8") as out:
            json.dump(results, out, ensure_ascii=False, indent=2)
        print(f"[成功] 解析完成！結構化數據已匯總輸出至：{OUTPUT_SUMMARY_JSON}")
    else:
        print("[提示] 目前尚未有學生上傳日記（僅有 TEMPLATE 檔案）。")

    return results

if __name__ == "__main__":
    parse_all_diaries()
