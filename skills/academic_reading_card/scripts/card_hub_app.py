#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
學術文獻閱讀卡片庫維護與統計中心 (Streamlit Web App)
Academic Reading Card Hub & Multi-Field Editor
啟動方式：
    streamlit run skills/academic_reading_card/scripts/card_hub_app.py
"""

import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime

# 將 scripts 目錄加入 sys.path，以利調用 extract_pdf_to_md 與 paper_retriever_mcp
_CURRENT_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _CURRENT_DIR.parent.parent.parent  # skills -> academic_reading_card -> scripts -> root
_SCRIPTS_DIR = _WORKSPACE_ROOT / "scripts"
if _SCRIPTS_DIR.exists() and str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

try:
    import extract_pdf_to_md
except Exception:
    extract_pdf_to_md = None

try:
    import paper_retriever_mcp
except Exception:
    paper_retriever_mcp = None

try:
    import streamlit as st
except ImportError:
    print("請先安裝 streamlit 套件：pip install streamlit")
    sys.exit(1)

# 設定頁面配置
st.set_page_config(
    page_title="學術閱讀卡片維護中心 | Academic Card Hub",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入護眼書卷淺色樣式 (Warm Paper & Deep Slate Palette)
st.markdown("""
<style>
    /* 全域溫潤書卷背景與深色文字 */
    .stApp {
        background-color: #fbfbfa !important;
        color: #1e293b !important;
    }
    header { background-color: transparent !important; }
    
    /* 側邊欄樣式 */
    section[data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #1e293b !important;
    }
    
    /* 標題與副標題文字 */
    h1, h2, h3, h4, h5, h6 {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    p, span, label {
        color: #334155 !important;
    }

    /* 表單文字框與輸入區：白底深字、清晰易讀 */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 1px #2563eb !important;
    }

    /* 指標卡片樣式 */
    div[data-testid="metric-container"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        padding: 14px 18px !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }
    div[data-testid="metric-container"] label {
        color: #64748b !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* 按鈕樣式 */
    .stButton > button {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        border-color: #94a3b8 !important;
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }

    /* 頁籤標籤 */
    div[data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 2px solid #e2e8f0 !important;
        gap: 12px !important;
    }
    div[data-baseweb="tab"] {
        color: #64748b !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
    }
    div[aria-selected="true"] {
        color: #2563eb !important;
        border-bottom-color: #2563eb !important;
    }

    /* 折疊面板卡片 */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stExpander"] details summary {
        color: #0f172a !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    .field-hint {
        font-size: 12px;
        color: #64748b;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)


def find_workspace_root():
    """自動偵測專案工作區路徑"""
    current = Path.cwd()
    for p in [current, current.parent, current / "my_thesis_workspace", current.parent / "my_thesis_workspace"]:
        if (p / "01_papers").exists() or (p / "PROJECT.md").exists():
            return p
    return current


def clean_markdown_to_plain(text):
    """
    將 Markdown 格式文字去除標記，還原為乾淨純文字供研究者直接閱讀與編輯
    去除開頭標題 #、項目符號 -/*、編號 1.、粗體 ** 及多餘符號
    """
    if not text:
        return ""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"^[-*+]\s*(\*\*[^*]+\*\*[:：]?\s*|\*[^*]+\*[:：]?\s*)?", "", line)
        line = re.sub(r"^\*\*[^*]+\*\*[:：]?\s*", "", line)
        line = re.sub(r"^\d+[\.、]\s*", "", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        line = re.sub(r"^[-*+_\s]+", "", line)
        line = re.sub(r'^["“”\'](.*)["“”\']$', r"\1", line)
        cleaned = line.strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def format_plain_to_markdown_bullets(plain_text, indent="  ", is_numbered=False):
    """將使用者輸入的純文字，在存檔時自動排版為標準 Markdown 條列格式"""
    if not plain_text or not plain_text.strip():
        return f"{indent}- (未填寫)"
    lines = []
    items = [l.strip() for l in plain_text.strip().splitlines() if l.strip()]
    for idx, l in enumerate(items, 1):
        clean_l = re.sub(r"^[-*+_\s]+", "", l)
        clean_l = re.sub(r"^\d+[\.、]\s*", "", clean_l)
        clean_l = clean_l.strip()
        if not clean_l:
            continue
        if is_numbered:
            lines.append(f"{indent}{idx}. {clean_l}")
        else:
            lines.append(f"{indent}- {clean_l}")
    if not lines:
        return f"{indent}- (未填寫)"
    return "\n".join(lines)


def parse_sub_items(sec_text, item_definitions):
    """
    依據各維度的子問題標籤（正規表達式）將大段落切分為各子項純文字字典
    item_definitions: list of (field_key, [regex_labels])
    """
    res = {k: "" for k, _ in item_definitions}
    patterns = []
    for k, labels in item_definitions:
        lbl_re = "|".join(labels)
        patterns.append(rf"(?P<{k}>^[ \t]*[-*]?\s*(?:\*\*)?(?:{lbl_re})(?:\s*\([^)\n]+\))?[:：]?(?:\*\*)?[:：]?)")
    combined = "|".join(patterns)
    matches = list(re.finditer(combined, sec_text, re.MULTILINE))
    
    if not matches:
        if item_definitions:
            res[item_definitions[0][0]] = clean_markdown_to_plain(sec_text)
        return res
        
    for i in range(len(matches)):
        m = matches[i]
        start = m.end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(sec_text)
        chunk = sec_text[start:end].strip()
        chunk = re.sub(r"^[:：]\s*", "", chunk).strip()
        for k, _ in item_definitions:
            if m.group(k):
                res[k] = clean_markdown_to_plain(chunk)
                break
    return res


def parse_quotes(text):
    """解析第七維度原文引述，回傳引文與出處清單"""
    quotes = []
    raw_lines = [l.strip() for l in text.splitlines() if l.strip()]
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        q_match = re.search(r'["“](.+?)["”]', line)
        if q_match:
            q_text = q_match.group(1).strip()
            q_src = ""
            if i + 1 < len(raw_lines):
                next_line = raw_lines[i+1]
                if any(k in next_line for k in ["—", "-", "Section", "p.", "頁"]):
                    q_src = re.sub(r"^\d+[\.、]\s*", "", next_line).strip('* "“”\'—-\t ')
                    i += 1
            quotes.append({"text": q_text, "source": q_src})
        i += 1
    return quotes


def parse_card_markdown(card_path):
    """解析單篇閱讀卡片 YAML 與各維度子問題項目"""
    try:
        content = card_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    card = {
        "filename": card_path.name,
        "path": card_path,
        "mtime": datetime.fromtimestamp(card_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        "raw_content": content,
        "bibtex_key": "",
        "title": card_path.stem,
        "first_author": "",
        "year": "",
        "journal": "",
        "doi": "",
        "source_md": "",
        "tags": [],
        "created_date": "",
        # 維度一
        "dim1_apa": "",
        "dim1_field": "",
        # 維度二
        "dim2_rqs": "",
        "dim2_theories": "",
        # 維度三
        "dim3_method": "",
        "dim3_sample": "",
        "dim3_context": "",
        "dim3_instruments": "",
        # 維度四
        "dim4_quantitative": "",
        "dim4_qualitative": "",
        # 維度五
        "dim5_author_limits": "",
        "dim5_critique": "",
        # 維度六
        "dim6_rq1": "",
        "dim6_rq2": "",
        "dim6_rq3": "",
        "dim6_gap": "",
        # 維度七
        "dim7_quotes": [],
    }

    # 解析 YAML Frontmatter
    fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k == "tags":
                    card["tags"] = re.findall(r"[\w-]+", v)
                elif k in card:
                    card[k] = v

    def extract_sec(num):
        pattern = rf"##\s*{num}\.\s*([^\n]+)\n(.*?)(?=\n##\s*\d+\.|\Z)"
        m = re.search(pattern, content, re.DOTALL)
        return m.group(2).strip() if m else ""

    # 解析維度 1
    d1 = parse_sub_items(extract_sec(1), [
        ("apa", [r"標準引用(?:\s*\(APA\s*7th\))?", r"APA(?:\s*7th)?", r"Reference"]),
        ("field", [r"研究領域", r"領域", r"Field"]),
        ("source_path", [r"原始文件路徑", r"文件路徑", r"Source Path"])
    ])
    card["dim1_apa"] = d1["apa"]
    card["dim1_field"] = clean_markdown_to_plain(d1["field"])
    if d1["source_path"]:
        card["source_md"] = clean_markdown_to_plain(d1["source_path"]).strip("` ")

    # 解析維度 2
    d2 = parse_sub_items(extract_sec(2), [
        ("rqs", [r"核心研究問題", r"研究問題", r"RQs"]),
        ("theories", [r"支撐理論框架", r"理論框架", r"理論架構", r"Theoretical Lens"])
    ])
    card["dim2_rqs"] = d2["rqs"]
    card["dim2_theories"] = d2["theories"]

    # 解析維度 3
    d3 = parse_sub_items(extract_sec(3), [
        ("method", [r"研究方法", r"Methodology", r"Method"]),
        ("sample", [r"研究對象與樣本量", r"研究對象", r"樣本量", r"樣本", r"Participants", r"Sample"]),
        ("context", [r"研究情境", r"情境", r"Context", r"Setting"]),
        ("instruments", [r"測量/評估架構", r"測量工具與評估規準", r"測量工具", r"評估規準", r"Instruments", r"Measures"])
    ])
    card["dim3_method"] = d3["method"]
    card["dim3_sample"] = d3["sample"]
    card["dim3_context"] = d3["context"]
    card["dim3_instruments"] = d3["instruments"]

    # 解析維度 4
    d4 = parse_sub_items(extract_sec(4), [
        ("quantitative", [r"量化統計結論", r"量化結論", r"量化統計", r"Quantitative Findings", r"Quantitative"]),
        ("qualitative", [r"質性發現與生態矩陣", r"質性發現與核心主題", r"質性發現", r"Qualitative Findings", r"Qualitative"])
    ])
    card["dim4_quantitative"] = d4["quantitative"]
    card["dim4_qualitative"] = d4["qualitative"]

    # 解析維度 5
    d5 = parse_sub_items(extract_sec(5), [
        ("author_limits", [r"作者承認之限制", r"作者承認限制", r"作者自陳限制", r"Author-Reported Limitations", r"Author Limitations"]),
        ("critique", [r"審查者獨立批判(?:\s*（對抗性審稿視角）)?", r"對抗性審稿視角", r"獨立批判", r"Adversarial Critique", r"Critical Limitations"])
    ])
    card["dim5_author_limits"] = d5["author_limits"]
    card["dim5_critique"] = d5["critique"]

    # 解析維度 6
    d6 = parse_sub_items(extract_sec(6), [
        ("rq1", [r"對\s*RQ1(?:\s*（[^）]+）)?的啟發", r"對\s*RQ1", r"RQ1"]),
        ("rq2", [r"對\s*RQ2(?:\s*（[^）]+）)?的啟發", r"對\s*RQ2", r"RQ2"]),
        ("rq3", [r"對\s*RQ3(?:\s*（[^）]+）)?的啟發", r"對\s*RQ3", r"RQ3"]),
        ("gap", [r"本研究可推進的空間(?:\s*（Research Gap）)?", r"本研究可推進的空間", r"Research Gap", r"研究空白", r"推進空間"])
    ])
    card["dim6_rq1"] = d6["rq1"]
    card["dim6_rq2"] = d6["rq2"]
    card["dim6_rq3"] = d6["rq3"]
    card["dim6_gap"] = d6["gap"]

    # 解析維度 7
    card["dim7_quotes"] = parse_quotes(extract_sec(7))

    return card


def build_markdown_card(data):
    """將各子欄位純文字重新組裝為完全符合七維 Schema 規格的標準 Markdown 卡片"""
    tags_str = ", ".join(data.get("tags", ["LiteratureCard"]))
    clean_title = data.get("title", "").replace('"', "")
    clean_journal = data.get("journal", "").replace('"', "")
    clean_date = data.get("created_date") or datetime.today().strftime("%Y-%m-%d")
    bibtex_key = data.get("bibtex_key", "")
    first_author = data.get("first_author", "")
    year = data.get("year", "")
    doi = data.get("doi", "")
    source_md = data.get("source_md", "")

    # 維度一組裝
    dim1_apa = data.get("dim1_apa", "").strip() or "(未填寫 APA 引用)"
    dim1_field = data.get("dim1_field", "").strip() or "(未填寫領域)"
    dim1_text = f"- **標準引用 (APA 7th)：** {dim1_apa}\n- **研究領域：** {dim1_field}\n- **原始文件路徑：** `{source_md}`"

    # 維度二組裝
    dim2_rqs_fmt = format_plain_to_markdown_bullets(data.get("dim2_rqs", ""), indent="  ", is_numbered=True)
    dim2_theories_fmt = format_plain_to_markdown_bullets(data.get("dim2_theories", ""), indent="  ", is_numbered=False)
    dim2_text = f"- **核心研究問題：**\n{dim2_rqs_fmt}\n- **支撐理論框架：**\n{dim2_theories_fmt}"

    # 維度三組裝
    dim3_method = data.get("dim3_method", "").strip() or "(未填寫研究方法)"
    dim3_sample_fmt = format_plain_to_markdown_bullets(data.get("dim3_sample", ""), indent="  ", is_numbered=False)
    dim3_context = data.get("dim3_context", "").strip() or "(未填寫研究情境)"
    dim3_instruments_fmt = format_plain_to_markdown_bullets(data.get("dim3_instruments", ""), indent="  ", is_numbered=False)
    dim3_text = f"- **研究方法：** {dim3_method}\n- **研究對象與樣本量：**\n{dim3_sample_fmt}\n- **研究情境：** {dim3_context}\n- **測量工具：**\n{dim3_instruments_fmt}"

    # 維度四組裝
    dim4_quant_fmt = format_plain_to_markdown_bullets(data.get("dim4_quantitative", ""), indent="  ", is_numbered=False)
    dim4_qual_fmt = format_plain_to_markdown_bullets(data.get("dim4_qualitative", ""), indent="  ", is_numbered=False)
    dim4_text = f"- **量化統計結論：**\n{dim4_quant_fmt}\n- **質性發現與核心主題：**\n{dim4_qual_fmt}"

    # 維度五組裝
    dim5_limits_fmt = format_plain_to_markdown_bullets(data.get("dim5_author_limits", ""), indent="  ", is_numbered=False)
    dim5_critique_fmt = format_plain_to_markdown_bullets(data.get("dim5_critique", ""), indent="  ", is_numbered=True)
    dim5_text = f"- **作者承認之限制：**\n{dim5_limits_fmt}\n- **審查者獨立批判（對抗性審稿視角）：**\n{dim5_critique_fmt}"

    # 維度六組裝
    dim6_rq1_fmt = format_plain_to_markdown_bullets(data.get("dim6_rq1", ""), indent="  ", is_numbered=False)
    dim6_rq2_fmt = format_plain_to_markdown_bullets(data.get("dim6_rq2", ""), indent="  ", is_numbered=False)
    dim6_gap_fmt = format_plain_to_markdown_bullets(data.get("dim6_gap", ""), indent="  ", is_numbered=False)
    
    dim6_parts = [
        f"- **對 RQ1（教學設計與鷹架）的啟發：**\n{dim6_rq1_fmt}",
        f"- **對 RQ2（認知歷程與轉變）的啟發：**\n{dim6_rq2_fmt}"
    ]
    if data.get("dim6_rq3", "").strip():
        dim6_rq3_fmt = format_plain_to_markdown_bullets(data.get("dim6_rq3", ""), indent="  ", is_numbered=False)
        dim6_parts.append(f"- **對 RQ3（人機協同瓶頸與實務障礙）的啟發：**\n{dim6_rq3_fmt}")
    dim6_parts.append(f"- **本研究可推進的空間（Research Gap）：**\n{dim6_gap_fmt}")
    dim6_text = "\n".join(dim6_parts)

    # 維度七組裝
    quotes = data.get("dim7_quotes", [])
    q_lines = []
    for idx, q in enumerate(quotes, 1):
        q_text = q.get("text", "").strip()
        q_src = q.get("source", "").strip()
        if q_text:
            clean_q = clean_markdown_to_plain(q_text)
            src_str = f"\n   — {q_src}" if q_src else ""
            q_lines.append(f'{idx}. *"{clean_q}"*{src_str}')
    dim7_text = "\n".join(q_lines) if q_lines else "1. *(未填寫引述)*"

    return f"""---
type: literature_card
card_version: 1.0
bibtex_key: {bibtex_key}
title: "{clean_title}"
first_author: "{first_author}"
year: {year}
journal: "{clean_journal}"
doi: "{doi}"
source_md: "{source_md}"
tags: [{tags_str}]
created_date: {clean_date}
---

# 文獻卡片：{first_author} ({year}) - {clean_title}

## 1. 文獻元數據與引用標識 (Metadata)
{dim1_text}

## 2. 核心研究問題與理論框架 (RQs & Theoretical Lens)
{dim2_text}

## 3. 研究設計與實證方法論 (Methodology & Context)
{dim3_text}

## 4. 關鍵實證數據與核心發現 (Empirical Findings)
{dim4_text}

## 5. 批判性審視與方法學盲點 (Critical Limitations)
{dim5_text}

## 6. 對本研究 PROJECT.md 的直接啟發 (Actionable Insights)
{dim6_text}

## 7. 核心原文引述與出處錨點 (Key Direct Quotes)
{dim7_text}
"""


def load_workspace(root_dir):
    """載入所有文獻與卡片，並完成關聯對應"""
    papers_dir = root_dir / "01_papers" / "extracted_text"
    cards_dir = root_dir / "02_notes" / "cards"

    papers = []
    cards = []

    if papers_dir.exists():
        for p in sorted(papers_dir.glob("*.md")):
            title = p.stem.replace("_", " ")
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for _ in range(15):
                        line = f.readline()
                        if line.startswith("# "):
                            title = line.replace("# ", "").strip()
                            break
            except Exception:
                pass
            papers.append({
                "filename": p.name,
                "path": p,
                "title": title,
                "size_kb": round(p.stat().st_size / 1024, 1),
                "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            })

    if cards_dir.exists():
        for c in sorted(cards_dir.glob("card_*.md")):
            parsed = parse_card_markdown(c)
            if parsed:
                cards.append(parsed)

    card_map = {}
    for c in cards:
        src = c.get("source_md", "")
        if src:
            card_map[Path(src).name] = c
        else:
            for p in papers:
                parts = p["filename"].lower().split("_")
                if len(parts) >= 2 and parts[0] in c["filename"].lower() and parts[1] in c["filename"].lower():
                    card_map[p["filename"]] = c
                    break

    completed = []
    pending = []

    for p in papers:
        c = card_map.get(p["filename"])
        if c:
            p["card"] = c
            completed.append(p)
        else:
            p["card"] = None
            pending.append(p)

    return papers, cards, completed, pending


# ==========================================
# 主應用程式邏輯
# ==========================================

root_dir = find_workspace_root()

# 側邊欄：工作區資訊與文獻統計
st.sidebar.title("📚 卡片管理控制台")
st.sidebar.markdown(f"**工作區目錄：**\n`{root_dir}`")

papers, cards, completed, pending = load_workspace(root_dir)

total_count = len(papers)
comp_count = len(completed)
percent = round((comp_count / total_count * 100), 1) if total_count else 0.0

st.sidebar.markdown("---")
st.sidebar.subheader("📊 文獻整理進度")
col_s1, col_s2 = st.sidebar.columns(2)
col_s1.metric("文獻總數", f"{total_count} 篇")
col_s2.metric("已建卡片", f"{comp_count} 篇")
st.sidebar.progress(percent / 100.0)
st.sidebar.caption(f"卡片完成率：**{percent}%** ({comp_count}/{total_count})")

st.sidebar.markdown("---")
search_term = st.sidebar.text_input("🔍 關鍵字篩選", placeholder="輸入作者或論文篇名...")

# 主頁面
st.title("學術文獻閱讀卡片庫維護與統計中心")
st.caption("支援在瀏覽器中直接檢閱各維度子項目、編輯並自動回寫本機卡片。直接輸入純文字資料，系統會自動轉換為標準結構。")

tab_completed, tab_pending, tab_pdf, tab_rag = st.tabs([
    f"🟢 已整理卡片庫 ({len(cards)} 篇)",
    f"⏳ 待整理文獻清單 ({len(pending)} 篇)",
    "📄 PDF 轉譯為 Markdown",
    "🧠 RAG 向量索引庫維護"
])

# ----------------------------------------------------
# 頁籤 1: 已整理卡片庫 (分項目獨立文字框)
# ----------------------------------------------------
with tab_completed:
    if not cards:
        st.info("目前尚無已建立之卡片。請從「待整理文獻清單」挑選論文進行整理！")
    else:
        card_options = {
            f"{c['first_author']} ({c['year']}) - {c['title'][:40]}... [{c['filename']}]": i 
            for i, c in enumerate(cards)
        }
        selected_label = st.selectbox("請選擇欲檢閱或修改的文獻卡片：", list(card_options.keys()))
        selected_idx = card_options[selected_label]
        target_card = cards[selected_idx]

        st.markdown(f"#### 正在檢閱與編輯：`{target_card['filename']}`")
        st.caption(f"最後修改時間：{target_card['mtime']} | 原文路徑：`{target_card.get('source_md', '未標註')}`")

        with st.form(key=f"edit_form_{target_card['filename']}"):
            
            # --- 第一維度 ---
            with st.expander("第一維度：基礎詮釋資料與引用標識 (Metadata)", expanded=False):
                col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
                edit_first_author = col_f1.text_input("第一作者 (first_author)", value=target_card.get("first_author", ""))
                edit_year = col_f2.text_input("發表年份 (year)", value=str(target_card.get("year", "")))
                edit_bibtex = col_f3.text_input("BibTeX 引用鍵 (bibtex_key)", value=target_card.get("bibtex_key", ""))
                
                col_f4, col_f5, col_f6 = st.columns([1, 1, 1])
                edit_journal = col_f4.text_input("期刊或研討會名稱 (journal)", value=target_card.get("journal", ""))
                edit_doi = col_f5.text_input("DOI 直連網址 (doi)", value=target_card.get("doi", ""))
                edit_tags_str = col_f6.text_input("主題標籤 (以逗號分隔)", value=", ".join(target_card.get("tags", [])))
                
                edit_title = st.text_input("論文完整篇名 (title)", value=target_card.get("title", ""))
                
                st.markdown("<p class='field-hint'><b>子項目 1：標準引用 (APA 7th 格式)</b></p>", unsafe_allow_html=True)
                edit_dim1_apa = st.text_area("APA 7th 參考文獻", value=target_card.get("dim1_apa", ""), height=70)
                
                st.markdown("<p class='field-hint'><b>子項目 2：研究領域</b></p>", unsafe_allow_html=True)
                edit_dim1_field = st.text_input("所屬學科領域 / 次領域", value=target_card.get("dim1_field", ""))

            # --- 第二維度 ---
            with st.expander("第二維度：核心研究問題與理論框架 (Research Questions & Theories)", expanded=True):
                st.markdown("<p class='field-hint'><b>子項目 1：核心研究問題 (Research Questions)</b></p>", unsafe_allow_html=True)
                st.caption("提示：原作者試圖解答的核心研究問題，多個問題請直接換行即可。")
                edit_dim2_rqs = st.text_area("研究試圖解答的核心問題", value=target_card.get("dim2_rqs", ""), height=120)
                
                st.markdown("<p class='field-hint'><b>子項目 2：支撐理論框架 (Theoretical Lens)</b></p>", unsafe_allow_html=True)
                st.caption("提示：論文採用的核心理論模型及操作化解釋。若為文獻綜述 (SLR)、技術工具開發或立場論文且原文無特定理論框架，請填寫「無特定單一理論框架」或「無」，切勿強行硬套。")
                edit_dim2_theories = st.text_area("支撐理論模型與概念架構", value=target_card.get("dim2_theories", ""), height=120)

            # --- 第三維度 ---
            with st.expander("第三維度：研究設計與實證方法論 (Methodology & Context)", expanded=False):
                st.markdown("<p class='field-hint'><b>子項目 1：研究方法 (Research Method)</b></p>", unsafe_allow_html=True)
                st.caption("提示：如準實驗設計、質性個案研究、問卷調查法、混合研究法或系統性文獻回顧 (SLR / PRISMA) 等。")
                edit_dim3_method = st.text_area("研究方法與設計類型", value=target_card.get("dim3_method", ""), height=70)

                st.markdown("<p class='field-hint'><b>子項目 2：研究對象與樣本量 (Participants & Sample)</b></p>", unsafe_allow_html=True)
                st.caption("提示：受試者樣本數 N、年齡、性別。若為文獻綜述請填寫「文獻樣本量：N = XX 篇」；若為概念論述或技術系統請填寫「不適用」。")
                edit_dim3_sample = st.text_area("受試對象與樣本特徵", value=target_card.get("dim3_sample", ""), height=80)

                st.markdown("<p class='field-hint'><b>子項目 3：研究情境 (Context & Setting)</b></p>", unsafe_allow_html=True)
                st.caption("提示：介入時間長度與環境。文獻綜述或桌面研究請填寫「不適用（桌面文獻回顧，無實體介入情境）」。")
                edit_dim3_context = st.text_area("實驗/調查之具體情境與脈絡", value=target_card.get("dim3_context", ""), height=70)

                st.markdown("<p class='field-hint'><b>子項目 4：測量工具與評估規準 (Instruments & Measures)</b></p>", unsafe_allow_html=True)
                st.caption("提示：具體量表全稱與信效度。若未使用心理量表（如質性訪談、系統日誌或文獻綜述）請填寫「無量表測量工具」或「不適用」，切勿捏造量表。")
                edit_dim3_instruments = st.text_area("測量工具與信效度架構", value=target_card.get("dim3_instruments", ""), height=80)

            # --- 第四維度 ---
            with st.expander("第四維度：關鍵實證數據與核心發現 (Empirical Findings)", expanded=True):
                st.markdown("<p class='field-hint'><b>子項目 1：量化統計結論 (Quantitative Findings)</b></p>", unsafe_allow_html=True)
                st.caption("提示：具體統計檢定值（如 F, t, p, 效果量 η_p^2 等）。純質性研究、立場文或非統計性綜述請誠實填寫「無量化統計檢定」，嚴禁虛構數值。")
                edit_dim4_quantitative = st.text_area("量化統計指標與數據", value=target_card.get("dim4_quantitative", ""), height=120)

                st.markdown("<p class='field-hint'><b>子項目 2：質性發現與核心主題 (Qualitative Findings / Key Themes)</b></p>", unsafe_allow_html=True)
                st.caption("提示：核心編碼主題與關鍵質性脈絡。純量化實驗無質性資料請填寫「無質性編碼資料」。")
                edit_dim4_qualitative = st.text_area("質性發現、主題矩陣與核心結論", value=target_card.get("dim4_qualitative", ""), height=130)

            # --- 第五維度 ---
            with st.expander("第五維度：批判性審視與方法學盲點 (Critical Limitations)", expanded=True):
                st.markdown("<p class='field-hint'><b>子項目 1：作者承認之限制 (Author-Reported Limitations)</b></p>", unsafe_allow_html=True)
                st.caption("提示：論文 Limitations 章節作者所提及的各項限制。若原文無獨立限制章節請註明。")
                edit_dim5_author_limits = st.text_area("作者自陳之研究限制", value=target_card.get("dim5_author_limits", ""), height=110)

                st.markdown("<p class='field-hint'><b>子項目 2：審查者獨立批判（對抗性審稿視角） (Adversarial Critique)</b></p>", unsafe_allow_html=True)
                st.caption("提示：指出方法學內部效度漏洞（如霍桑效應、指導偏差）、構念效度、外推邊界與生態限制（建議至少 2 點）。")
                edit_dim5_critique = st.text_area("審查者獨立批判觀點（效度威脅與生態限制）", value=target_card.get("dim5_critique", ""), height=130)

            # --- 第六維度 ---
            with st.expander("第六維度：對自身論文研究的直接啟發 (Actionable Insights for My Thesis)", expanded=True):
                st.markdown("<p class='field-hint'><b>子項目 1：對 RQ1（教學設計與鷹架）的啟發</b></p>", unsafe_allow_html=True)
                st.caption("提示：具體借鑑或警惕。若該文與 RQ1 無直接關聯，請直接填寫「與本 RQ 無直接關聯」，絕不強行牽強硬湊。")
                edit_dim6_rq1 = st.text_area("對個人研究問題 RQ1 的啟發", value=target_card.get("dim6_rq1", ""), height=90)

                st.markdown("<p class='field-hint'><b>子項目 2：對 RQ2（認知歷程與轉變）的啟發</b></p>", unsafe_allow_html=True)
                st.caption("提示：量表、日誌、測量工具或認知歷程之參考。若與 RQ2 無直接關聯，請直接填寫「與本 RQ 無直接關聯」。")
                edit_dim6_rq2 = st.text_area("對個人研究問題 RQ2 的啟發", value=target_card.get("dim6_rq2", ""), height=90)

                st.markdown("<p class='field-hint'><b>子項目 3：對 RQ3（人機協同瓶頸與實務障礙）的啟發（選填）</b></p>", unsafe_allow_html=True)
                st.caption("提示：人機協同瓶頸、反幻覺查核之借鑑。若與 RQ3 無直接關聯，請填寫「與本 RQ 無直接關聯」或留空。")
                edit_dim6_rq3 = st.text_area("對個人研究問題 RQ3 的啟發", value=target_card.get("dim6_rq3", ""), height=90)

                st.markdown("<p class='field-hint'><b>子項目 4：本研究可推進的空間（Research Gap）</b></p>", unsafe_allow_html=True)
                st.caption("提示：我們的碩士論文能在此基礎上推進哪一步？獨特利基為何？")
                edit_dim6_gap = st.text_area("對研究空白 (Research Gap) 的推進空間", value=target_card.get("dim6_gap", ""), height=100)

            # --- 第七維度 ---
            with st.expander("第七維度：核心原文引述與出處錨點 (Key Direct Quotes & Section Anchors)", expanded=False):
                quotes_list = target_card.get("dim7_quotes", [])
                q1 = quotes_list[0] if len(quotes_list) > 0 else {"text": "", "source": ""}
                q2 = quotes_list[1] if len(quotes_list) > 1 else {"text": "", "source": ""}
                q3 = quotes_list[2] if len(quotes_list) > 2 else {"text": "", "source": ""}

                st.markdown("<p class='field-hint'><b>子項目 1：核心英文原文引述一</b></p>", unsafe_allow_html=True)
                edit_q1_text = st.text_area("原文句子一", value=q1["text"], height=75)
                edit_q1_source = st.text_input("出處章節與頁碼一", value=q1["source"], placeholder="例如：Section 1. Introduction, p. 2.")

                st.markdown("<p class='field-hint'><b>子項目 2：核心英文原文引述二</b></p>", unsafe_allow_html=True)
                edit_q2_text = st.text_area("原文句子二", value=q2["text"], height=75)
                edit_q2_source = st.text_input("出處章節與頁碼二", value=q2["source"], placeholder="例如：Section 5. Discussion, p. 9.")

                st.markdown("<p class='field-hint'><b>子項目 3：核心英文原文引述三 (選填)</b></p>", unsafe_allow_html=True)
                edit_q3_text = st.text_area("原文句子三", value=q3["text"], height=75)
                edit_q3_source = st.text_input("出處章節與頁碼三", value=q3["source"], placeholder="例如：Section: Conclusion, p. 9.")

            # 提交儲存按鈕
            submit_save = st.form_submit_button("💾 儲存並更新卡片檔案")
            
            if submit_save:
                target_card["first_author"] = edit_first_author
                target_card["year"] = edit_year
                target_card["bibtex_key"] = edit_bibtex
                target_card["journal"] = edit_journal
                target_card["doi"] = edit_doi
                target_card["tags"] = [t.strip() for t in edit_tags_str.split(",") if t.strip()]
                target_card["title"] = edit_title
                
                target_card["dim1_apa"] = edit_dim1_apa
                target_card["dim1_field"] = edit_dim1_field
                
                target_card["dim2_rqs"] = edit_dim2_rqs
                target_card["dim2_theories"] = edit_dim2_theories
                
                target_card["dim3_method"] = edit_dim3_method
                target_card["dim3_sample"] = edit_dim3_sample
                target_card["dim3_context"] = edit_dim3_context
                target_card["dim3_instruments"] = edit_dim3_instruments
                
                target_card["dim4_quantitative"] = edit_dim4_quantitative
                target_card["dim4_qualitative"] = edit_dim4_qualitative
                
                target_card["dim5_author_limits"] = edit_dim5_author_limits
                target_card["dim5_critique"] = edit_dim5_critique
                
                target_card["dim6_rq1"] = edit_dim6_rq1
                target_card["dim6_rq2"] = edit_dim6_rq2
                target_card["dim6_rq3"] = edit_dim6_rq3
                target_card["dim6_gap"] = edit_dim6_gap

                new_quotes = []
                if edit_q1_text.strip():
                    new_quotes.append({"text": edit_q1_text.strip(), "source": edit_q1_source.strip()})
                if edit_q2_text.strip():
                    new_quotes.append({"text": edit_q2_text.strip(), "source": edit_q2_source.strip()})
                if edit_q3_text.strip():
                    new_quotes.append({"text": edit_q3_text.strip(), "source": edit_q3_source.strip()})
                target_card["dim7_quotes"] = new_quotes

                # 重組為標準 Markdown
                updated_md = build_markdown_card(target_card)
                
                try:
                    target_card["path"].write_text(updated_md, encoding="utf-8")
                    st.success(f"✓ 成功更新卡片檔案：`{target_card['path'].name}`！各子項目內容已直接覆寫至硬碟。")
                except Exception as err:
                    st.error(f"寫入檔案時發生錯誤：{err}")

# ----------------------------------------------------
# 頁籤 2: 待整理文獻清單
# ----------------------------------------------------
with tab_pending:
    st.subheader(f"待整理文獻清單 (共 {len(pending)} 篇尚未建立卡片)")
    st.caption("從下方清單挑選即將閱讀的文獻，複製提示語發送給 Agent，即可開始建立閱讀卡片。")

    filtered_pending = [
        p for p in pending
        if not search_term or (search_term.lower() in p["filename"].lower() or search_term.lower() in p["title"].lower())
    ]

    if not filtered_pending:
        st.success("目前無符合篩選條件的待整理文獻。")
    else:
        for idx, p in enumerate(filtered_pending, 1):
            with st.container():
                col_p1, col_p2 = st.columns([3, 1])
                with col_p1:
                    st.markdown(f"**{idx}. {p['title']}**")
                    st.caption(f"檔案路徑：`01_papers/extracted_text/{p['filename']}` ({p['size_kb']} KB)")
                with col_p2:
                    prompt_text = f"請使用 academic-reading-card Skill，幫我為 01_papers/extracted_text/{p['filename']} 產出標準閱讀卡片並存入 02_notes/cards/。"
                    st.caption("建立卡片提示語：")
                    st.code(prompt_text, language="text")
                st.markdown("---")

# ----------------------------------------------------
# 頁籤 3: PDF 轉譯為 Markdown (raw_pdf -> extracted_text)
# ----------------------------------------------------
with tab_pdf:
    st.subheader("📄 文獻 PDF 轉譯與文字清洗 (extract_pdf_to_md)")
    st.caption("將 `01_papers/raw_pdf/` 的文獻原件轉譯為結構化 Markdown，自動移除 References 龐大引用列表與排版雜音，輸出至 `01_papers/extracted_text/`。")

    raw_pdf_dir = root_dir / "01_papers" / "raw_pdf"
    extracted_text_dir = root_dir / "01_papers" / "extracted_text"

    raw_pdfs = sorted(list(raw_pdf_dir.glob("*.pdf"))) if raw_pdf_dir.exists() else []
    extracted_mds = sorted(list(extracted_text_dir.glob("*.md"))) if extracted_text_dir.exists() else []

    extracted_stems = {m.stem for m in extracted_mds}
    unconverted_pdfs = [p for p in raw_pdfs if p.stem not in extracted_stems]

    # 狀態統計卡片
    col_pdf1, col_pdf2, col_pdf3 = st.columns(3)
    col_pdf1.metric("在庫原始 PDF", f"{len(raw_pdfs)} 篇")
    col_pdf2.metric("已轉譯 Markdown", f"{len(extracted_mds)} 篇")
    col_pdf3.metric("待轉譯 PDF", f"{len(unconverted_pdfs)} 篇")

    st.markdown("---")

    # 批次或全量操作按鈕
    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        st.markdown("##### 🚀 批次增量轉譯（僅處理未轉譯者）")
        st.caption("自動比對檔名，僅針對尚未產生 Markdown 的 PDF 進行解析與文字清洗。")
        if st.button("▶ 執行增量轉譯 (未轉譯 PDF)", key="btn_convert_unconverted", use_container_width=True):
            if not unconverted_pdfs:
                st.info("目前所有原始 PDF 皆已完成轉譯！無需重複轉換。")
            elif not extract_pdf_to_md:
                st.error("找不到 `scripts/extract_pdf_to_md.py` 模組，請確認 scripts 目錄配置。")
            else:
                progress_bar = st.progress(0.0)
                status_text = st.empty()
                success_cnt = 0
                extracted_text_dir.mkdir(parents=True, exist_ok=True)

                for idx, pdf_p in enumerate(unconverted_pdfs, 1):
                    status_text.text(f"[{idx}/{len(unconverted_pdfs)}] 正在轉譯：{pdf_p.name} ...")
                    target_md = extracted_text_dir / f"{pdf_p.stem}.md"
                    ok = extract_pdf_to_md.convert_single_pdf(pdf_p, target_md)
                    if ok:
                        success_cnt += 1
                    progress_bar.progress(idx / len(unconverted_pdfs))

                status_text.empty()
                st.success(f"✓ 轉譯完成！成功將 {success_cnt}/{len(unconverted_pdfs)} 篇 PDF 轉為純淨 Markdown。")
                st.rerun()

    with col_btn2:
        st.markdown("##### 🔄 全量重新轉譯（覆寫現有 Markdown）")
        st.caption("重新解析 raw_pdf/ 下的所有 PDF 檔案並覆寫既有文字。")
        if st.button("⚠ 全量重新轉譯所有 PDF", key="btn_convert_all", use_container_width=True):
            if not raw_pdfs:
                st.warning("`01_papers/raw_pdf/` 中無任何 PDF 檔案！")
            elif not extract_pdf_to_md:
                st.error("找不到 `scripts/extract_pdf_to_md.py` 模組。")
            else:
                progress_bar = st.progress(0.0)
                status_text = st.empty()
                success_cnt = 0
                extracted_text_dir.mkdir(parents=True, exist_ok=True)

                for idx, pdf_p in enumerate(raw_pdfs, 1):
                    status_text.text(f"[{idx}/{len(raw_pdfs)}] 正在轉譯：{pdf_p.name} ...")
                    target_md = extracted_text_dir / f"{pdf_p.stem}.md"
                    ok = extract_pdf_to_md.convert_single_pdf(pdf_p, target_md)
                    if ok:
                        success_cnt += 1
                    progress_bar.progress(idx / len(raw_pdfs))

                status_text.empty()
                st.success(f"✓ 全量轉譯完成！共成功產出 {success_cnt}/{len(raw_pdfs)} 篇純淨 Markdown。")
                st.rerun()

    st.markdown("---")
    st.markdown("##### 📋 在庫 PDF 清單與轉譯對照表")
    if not raw_pdfs:
        st.info("目前 `01_papers/raw_pdf/` 中尚無文獻檔案。請先透過文獻下載流程下載 PDF。")
    else:
        pdf_display_data = []
        for p in raw_pdfs:
            is_done = p.stem in extracted_stems
            target_md = extracted_text_dir / f"{p.stem}.md"
            md_size_str = f"{round(target_md.stat().st_size / 1024, 1)} KB" if is_done and target_md.exists() else "--"
            pdf_display_data.append({
                "狀態": "✅ 已轉譯" if is_done else "⏳ 待轉譯",
                "PDF 檔名": p.name,
                "大小 (KB)": round(p.stat().st_size / 1024, 1),
                "轉譯 Markdown 大小": md_size_str
            })
        st.dataframe(pdf_display_data, use_container_width=True)

# ----------------------------------------------------
# 頁籤 4: RAG 向量索引庫維護 (vector_index & embeddings)
# ----------------------------------------------------
with tab_rag:
    st.subheader("🧠 本機 RAG 向量索引庫維護與檢索 (paper_retriever_mcp)")
    st.caption("基於 `BAAI/bge-base-en-v1.5`（768 維嵌入模型）建構雙檔解耦索引：結構文字儲存於 `vector_index.json`，密集向量矩陣儲存於 `vector_embeddings.npz`。")

    idx_file = root_dir / "01_papers" / "vector_index.json"
    vec_file = root_dir / "01_papers" / "vector_embeddings.npz"
    extracted_text_dir = root_dir / "01_papers" / "extracted_text"

    existing_mds = sorted(list(extracted_text_dir.glob("*.md"))) if extracted_text_dir.exists() else []

    # 讀取當前索引狀態
    idx_exists = idx_file.exists() and vec_file.exists()
    indexed_files = set()
    total_chunks = 0
    model_name = "BAAI/bge-base-en-v1.5"
    idx_updated_time = "--"

    if idx_exists:
        try:
            with open(idx_file, "r", encoding="utf-8") as f:
                idx_meta = json.load(f)
            total_chunks = len(idx_meta.get("chunks", []))
            indexed_files = set(idx_meta.get("metadata", {}).get("file_states", {}).keys())
            model_name = idx_meta.get("metadata", {}).get("embedding_model", model_name)
            idx_updated_time = idx_meta.get("metadata", {}).get("last_updated", idx_meta.get("metadata", {}).get("updated_at", "--"))
        except Exception:
            pass

    existing_md_names = {p.name for p in existing_mds}
    unindexed_mds = existing_md_names - indexed_files

    # 指標卡片
    col_rag1, col_rag2, col_rag3, col_rag4 = st.columns(4)
    col_rag1.metric("已索引篇數", f"{len(indexed_files)} 篇")
    col_rag2.metric("待增量編碼篇數", f"{len(unindexed_mds)} 篇")
    col_rag3.metric("總段落向量數 (Chunks)", f"{total_chunks} 塊")
    col_rag4.metric("索引狀態", "🟢 最新" if len(unindexed_mds) == 0 and idx_exists else "🟡 待更新")

    st.caption(f"嵌入模型：`{model_name}` | 索引最後更新時間：`{idx_updated_time}`")

    st.markdown("---")

    # 索引操作按鈕
    col_idx1, col_idx2 = st.columns([1, 1])

    with col_idx1:
        st.markdown("##### ⚡ 增量更新向量索引 (Incremental Build)")
        st.caption("僅針對新增或修改的 Markdown 文獻進行向量編碼，已編碼文獻 0 耗時直接沿用快取。")
        if st.button("▶ 執行增量更新 (推薦)", key="btn_build_incremental", use_container_width=True):
            if not existing_mds:
                st.warning("`01_papers/extracted_text/` 中無任何 Markdown 檔案，請先執行 PDF 轉譯！")
            elif not paper_retriever_mcp:
                st.error("找不到 `scripts/paper_retriever_mcp.py` 模組，請確認環境設定。")
            else:
                with st.spinner("正在進行語意切塊與 BGE 稠密向量計算，請稍候..."):
                    try:
                        res = paper_retriever_mcp.build_index_data(force=False)
                        if res.get("status") == "success":
                            st.success(f"✓ 索引更新成功！本次新編碼段落：{res.get('encoded_chunks', res.get('chunks_encoded', 0))} 塊 | 索引總段落數：{res.get('total_chunks', 0)} 塊。")
                            st.rerun()
                        else:
                            st.error(f"建立索引失敗：{res.get('message')}")
                    except Exception as err:
                        st.error(f"執行時發生錯誤：{err}")

    with col_idx2:
        st.markdown("##### 🔁 強制全量重新建置 (Force Rebuild)")
        st.caption("忽略快取，強制重新切割所有 Markdown 段落並計算 768 維稠密向量矩陣。")
        if st.button("⚠ 強制全量重新建置", key="btn_build_force", use_container_width=True):
            if not existing_mds:
                st.warning("`01_papers/extracted_text/` 中無任何 Markdown 檔案！")
            elif not paper_retriever_mcp:
                st.error("找不到 `scripts/paper_retriever_mcp.py` 模組。")
            else:
                with st.spinner("正在強制全量重新編碼所有文獻段落，請稍候..."):
                    try:
                        res = paper_retriever_mcp.build_index_data(force=True)
                        if res.get("status") == "success":
                            st.success(f"✓ 全量重建成功！共編碼 {res.get('encoded_chunks', res.get('chunks_encoded', 0))} 塊段落向量。")
                            st.rerun()
                        else:
                            st.error(f"重建索引失敗：{res.get('message')}")
                    except Exception as err:
                        st.error(f"執行時發生錯誤：{err}")

    st.markdown("---")

    # 即時語意檢索測試區
    st.markdown("##### 🔍 即時 RAG 語意檢索測試 (Semantic Search Test)")
    st.caption("測試向量索引的檢索品質：輸入英文或中文關鍵概念，系統自動以 BGE 餘弦相似度比對出最相關之論文原文段落與出處。")

    col_q1, col_q2 = st.columns([4, 1])
    with col_q1:
        test_query = st.text_input("輸入檢索查詢詞：", placeholder="例如：cognitive load measurement instruments 或 scaffolding AI agents", label_visibility="collapsed")
    with col_q2:
        top_k = st.number_input("返回段落數", min_value=1, max_value=10, value=3)

    if st.button("🔍 執行語意檢索", key="btn_run_search"):
        if not test_query.strip():
            st.warning("請先輸入查詢詞！")
        elif not idx_exists:
            st.error("尚未建立向量索引庫！請先點擊上方按鈕建立索引。")
        elif not paper_retriever_mcp:
            st.error("找不到 `scripts/paper_retriever_mcp.py` 模組。")
        else:
            with st.spinner("正在計算向量並檢索文獻段落..."):
                try:
                    search_res = paper_retriever_mcp.search_index_data(test_query.strip(), top_k=top_k)
                    if isinstance(search_res, list) and search_res and "error" in search_res[0]:
                        st.error(f"檢索錯誤：{search_res[0]['error']}")
                    else:
                        results = search_res if isinstance(search_res, list) else search_res.get("results", [])
                        if not results:
                            st.info("未檢索到相關文獻段落。")
                        else:
                            st.markdown(f"**檢索完成！共找到 {len(results)} 個高相關性段落：**")
                            for r_idx, chunk in enumerate(results, 1):
                                sim = chunk.get("relevance_score", chunk.get("similarity", 0.0))
                                fname = chunk.get("source_paper", chunk.get("file", "未知文獻"))
                                sec = chunk.get("section", "未標記章節")
                                txt = chunk.get("content", chunk.get("text", ""))

                                with st.expander(f"【{r_idx}】文獻：`{fname}` | 章節：`{sec}` (餘弦相似度: {sim:.4f})", expanded=(r_idx == 1)):
                                    st.markdown(f"**出處錨點：** `{fname} > {sec}`")
                                    st.text_area("段落原文內容", value=txt, height=130, key=f"rag_res_{r_idx}", disabled=True)
                except Exception as err:
                    st.error(f"檢索過程發生錯誤：{err}")

