#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
學術文獻閱讀卡片庫維護與統計系統 (Academic Reading Card Hub & Manager)
功能：
1. 掃描 01_papers/extracted_text 與 02_notes/cards
2. 比對「已整理卡片」與「待整理文獻」清單與統計比例
3. 產生整合式護眼書卷風 Generative UI 儀表板 (card_hub.html)，支援純文字視覺化修改並直接回寫卡片
4. 支援終端機命令列快速查詢與合規性連動
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

# Windows terminal UTF-8 encoding safeguard
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def find_workspace_root():
    """自動偵測專案工作區根目錄 (包含 01_papers 或 PROJECT.md)"""
    current = Path.cwd()
    for p in [current, current.parent, current.parent / "my_thesis_workspace", current / "my_thesis_workspace"]:
        if (p / "01_papers").exists() or (p / "PROJECT.md").exists():
            return p
    return current


def parse_card_markdown(card_path):
    """解析單篇閱讀卡片之 YAML Frontmatter 與七大維度內容"""
    try:
        with open(card_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return None

    card_data = {
        "filename": card_path.name,
        "filepath": str(card_path).replace("\\", "/"),
        "mtime": datetime.fromtimestamp(card_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        "bibtex_key": "",
        "title": card_path.stem,
        "first_author": "",
        "year": "",
        "journal": "",
        "doi": "",
        "source_md": "",
        "tags": [],
        "created_date": "",
        "raw_content": content,
        "dim1": "",
        "dim2": "",
        "dim3": "",
        "dim4": "",
        "dim5": "",
        "dim6": "",
        "dim7": "",
    }

    # 解析 YAML Frontmatter
    fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        for line in fm_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k == "tags":
                    card_data["tags"] = re.findall(r"[\w-]+", v)
                elif k in card_data:
                    card_data[k] = v

    # 提取七大維度內容
    def extract_section(num):
        pattern = rf"##\s*{num}\.\s*([^\n]+)\n(.*?)(?=\n##\s*\d+\.|\Z)"
        m = re.search(pattern, content, re.DOTALL)
        return m.group(2).strip() if m else ""

    card_data["dim1"] = extract_section(1)
    card_data["dim2"] = extract_section(2)
    card_data["dim3"] = extract_section(3)
    card_data["dim4"] = extract_section(4)
    card_data["dim5"] = extract_section(5)
    card_data["dim6"] = extract_section(6)
    card_data["dim7"] = extract_section(7)

    return card_data


def scan_workspace(root_dir):
    """掃描工作區文獻庫與卡片庫，進行雙向比對"""
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
                "filepath": str(p).replace("\\", "/"),
                "stem": p.stem,
                "title": title,
                "size_kb": round(p.stat().st_size / 1024, 1),
                "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            })

    if cards_dir.exists():
        for c in sorted(cards_dir.glob("card_*.md")):
            c_info = parse_card_markdown(c)
            if c_info:
                cards.append(c_info)

    card_source_map = {}
    for c in cards:
        src = c.get("source_md", "")
        if src:
            card_source_map[Path(src).name] = c
        else:
            for p in papers:
                parts = p["stem"].lower().split("_")
                c_base = c["filename"].lower()
                if len(parts) >= 2 and parts[0] in c_base and parts[1] in c_base:
                    card_source_map[p["filename"]] = c
                    break

    completed_papers = []
    pending_papers = []

    for p in papers:
        matched_card = card_source_map.get(p["filename"])
        if matched_card:
            p["card"] = matched_card
            completed_papers.append(p)
        else:
            p["card"] = None
            pending_papers.append(p)

    return {
        "root": str(root_dir).replace("\\", "/"),
        "total_papers": len(papers),
        "completed_count": len(completed_papers),
        "pending_count": len(pending_papers),
        "progress_percent": round((len(completed_papers) / len(papers) * 100), 1) if papers else 0.0,
        "cards": cards,
        "completed_papers": completed_papers,
        "pending_papers": pending_papers
    }


def print_cli_summary(data):
    """終端機格式化輸出統計摘要"""
    print("=" * 66)
    print("📚 學術文獻閱讀卡片庫維護與統計系統 (Academic Card Hub)")
    print("=" * 66)
    print(f"工作區根目錄：{data['root']}")
    print(f"文獻總數　　：{data['total_papers']} 篇")
    print(f"已整理卡片　：{data['completed_count']} 篇 ({data['progress_percent']}%)")
    print(f"待整理文獻　：{data['pending_count']} 篇")
    print("-" * 66)

    print("\n🟢 【已整理卡片清單】(隨時可再次檢閱與修訂):")
    if not data["cards"]:
        print("  (尚無已建立之卡片)")
    else:
        for idx, c in enumerate(data["cards"], 1):
            author = c.get("first_author") or "未知作者"
            yr = c.get("year") or "年份未詳"
            title = c.get("title") or c["filename"]
            print(f"  {idx}. [{c['filename']}]")
            print(f"     👤 {author} ({yr}) - {title[:48]}...")
            print(f"     🕒 最後修改: {c['mtime']} | 來源: {c.get('source_md') or '未綁定'}")

    print("\n⏳ 【待整理文獻清單】(尚未建立卡片):")
    if not data["pending_papers"]:
        print("  🎉 所有文獻皆已整理成標準卡片！")
    else:
        for idx, p in enumerate(data["pending_papers"], 1):
            print(f"  {idx:2d}. {p['filename']} ({p['size_kb']} KB)")
            print(f"      📄 {p['title'][:60]}")

    print("-" * 66)
    print("💡 提示：執行 `--dashboard` 即可更新視覺化儀表板！")
    print("=" * 66)


def generate_html_hub(data, output_path):
    """生成整合式護眼書卷風 Generative UI 儀表板 (card_hub.html)"""
    data_json = json.dumps(data, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>學術閱讀卡片庫維護與統計中心 (Card Hub)</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    /* 容器過渡與自訂滾動條 */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(100, 116, 139, 0.2); border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: rgba(100, 116, 139, 0.35); }}
    input:focus, textarea:focus, select:focus {{
      outline: none;
      box-shadow: 0 0 0 2px #2563eb;
    }}
  </style>
</head>
<body class="bg-[#fbfbfa] text-[#1e293b] antialiased min-h-screen p-4 md:p-6 pb-24 selection:bg-[#bfdbfe] selection:text-[#1e3a8a]">

  <!-- Top Hero Header: Warm White Card with Clean Borders -->
  <header class="max-w-7xl mx-auto bg-white border border-[#e2e8f0] rounded-2xl p-6 shadow-sm mb-6">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-2 mb-2">
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#eff6ff] text-[#1e40af] border border-[#bfdbfe]">
            文獻卡片庫系統
          </span>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#f0fdf4] text-[#166534] border border-[#bbf7d0]">
            純文字即時修訂
          </span>
        </div>
        <h1 class="text-xl md:text-2xl font-bold tracking-tight text-[#0f172a]">
          學術文獻閱讀卡片庫維護與統計中心 (Card Hub)
        </h1>
        <p class="text-xs md:text-sm text-[#475569] mt-1 leading-relaxed">
          掌握工作區七維卡片整理進度，支援「已整理文獻隨時再次閱讀修訂」與「待整理文獻一鍵產生提示詞」。
        </p>
      </div>

      <!-- Quick Action Button -->
      <div class="flex items-center gap-2">
        <button type="button" onclick="refreshData()" class="px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#f8fafc] hover:bg-[#f1f5f9] text-[#334155] border border-[#cbd5e1] transition flex items-center gap-1.5 shadow-xs">
          <span>🔄</span> 重新整理清單
        </button>
      </div>
    </div>

    <!-- Statistics Overview Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3.5 mt-5 pt-4 border-t border-[#f1f5f9]">
      <div class="bg-[#f8fafc] border border-[#e2e8f0] rounded-xl p-3.5">
        <div class="text-xs font-medium text-[#64748b]">文獻總數</div>
        <div class="text-xl md:text-2xl font-bold text-[#0f172a] mt-1" id="statTotal">{data['total_papers']} <span class="text-xs font-normal text-[#64748b]">篇</span></div>
      </div>

      <div class="bg-[#f0fdf4] border border-[#bbf7d0] rounded-xl p-3.5">
        <div class="text-xs font-semibold text-[#166534] flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-[#16a34a]"></span> 已整理卡片
        </div>
        <div class="text-xl md:text-2xl font-bold text-[#166534] mt-1" id="statCompleted">{data['completed_count']} <span class="text-xs font-normal text-[#64748b]">篇</span></div>
      </div>

      <div class="bg-[#fefce8] border border-[#fef08a] rounded-xl p-3.5">
        <div class="text-xs font-semibold text-[#854d0e] flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-[#ca8a04]"></span> 待整理文獻
        </div>
        <div class="text-xl md:text-2xl font-bold text-[#854d0e] mt-1" id="statPending">{data['pending_count']} <span class="text-xs font-normal text-[#64748b]">篇</span></div>
      </div>

      <div class="bg-[#eff6ff] border border-[#bfdbfe] rounded-xl p-3.5">
        <div class="text-xs font-semibold text-[#1e40af] flex justify-between">
          <span>文獻整理進度</span>
          <span id="statPercent" class="font-mono font-bold">{data['progress_percent']}%</span>
        </div>
        <div class="w-full bg-[#e2e8f0] rounded-full h-2.5 mt-2.5 overflow-hidden">
          <div class="bg-gradient-to-r from-[#2563eb] to-[#3b82f6] h-2.5 rounded-full transition-all duration-500" style="width: {data['progress_percent']}%"></div>
        </div>
      </div>
    </div>
  </header>

  <!-- Main View Container -->
  <main class="max-w-7xl mx-auto space-y-6">

    <!-- View Switcher Tabs -->
    <div class="flex items-center justify-between border-b border-[#e2e8f0] pb-2">
      <div class="flex items-center gap-3">
        <button type="button" id="tabCompletedBtn" onclick="switchTab('completed')" class="px-4 py-2 rounded-xl text-xs font-bold bg-[#f0fdf4] text-[#166534] border border-[#bbf7d0] transition flex items-center gap-2 shadow-xs">
          <span>🟢 已整理卡片庫</span>
          <span class="px-2 py-0.5 rounded-full text-[11px] bg-white text-[#166534] font-semibold border border-[#bbf7d0]">{data['completed_count']}</span>
        </button>
        <button type="button" id="tabPendingBtn" onclick="switchTab('pending')" class="px-4 py-2 rounded-xl text-xs font-bold bg-white hover:bg-[#f8fafc] text-[#64748b] border border-[#e2e8f0] transition flex items-center gap-2 shadow-xs">
          <span>⏳ 待整理文獻清單</span>
          <span class="px-2 py-0.5 rounded-full text-[11px] bg-[#f1f5f9] text-[#64748b] font-semibold">{data['pending_count']}</span>
        </button>
      </div>

      <!-- Quick Search Filter -->
      <div class="w-64">
        <input type="text" id="searchInput" oninput="filterLists()" placeholder="搜尋作者、標題或關鍵字..." class="w-full text-xs bg-white text-[#0f172a] border border-[#cbd5e1] rounded-lg px-3 py-2 shadow-xs">
      </div>
    </div>

    <!-- TAB 1: Completed Cards View -->
    <section id="completedSection" class="space-y-4">
      <div id="completedList" class="grid grid-cols-1 gap-4">
        <!-- Rendered via JS -->
      </div>
    </section>

    <!-- TAB 2: Pending Papers View -->
    <section id="pendingSection" class="space-y-4 hidden">
      <div id="pendingList" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Rendered via JS -->
      </div>
    </section>

  </main>

  <!-- Modal: In-place Card Re-curator & Editor -->
  <div id="editModal" class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs hidden flex items-center justify-center p-3 md:p-6">
    <div class="bg-white border border-[#e2e8f0] rounded-2xl w-full max-w-5xl max-h-[92vh] flex flex-col shadow-xl overflow-hidden">
      
      <!-- Modal Header -->
      <div class="p-4 md:p-5 border-b border-[#e2e8f0] flex items-center justify-between bg-[#f8fafc]">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="px-2.5 py-0.5 rounded text-xs font-semibold bg-[#eff6ff] text-[#1e40af] border border-[#bfdbfe]">
              文獻再次閱讀修訂模式
            </span>
            <span id="modalCardFilename" class="font-mono text-xs text-[#64748b]">card_name.md</span>
          </div>
          <h2 id="modalCardTitle" class="text-base font-bold text-[#0f172a]">論文標題</h2>
        </div>
        <button type="button" onclick="closeEditModal()" class="text-[#64748b] hover:text-[#0f172a] text-xl px-2 py-1 rounded-lg">✕</button>
      </div>

      <!-- Modal Body (7 Dimensions Plain Text Editor) -->
      <div class="p-5 overflow-y-auto space-y-4 text-xs">
        
        <div class="p-3 bg-[#eff6ff] rounded-xl border border-[#bfdbfe] text-[#1e40af]">
          💡 <strong>純文字填寫提示：</strong> 所有欄位直接輸入純文字即可，不需手動填寫 Markdown 符號（如 <code>- </code> 或 <code>##</code>）。系統存檔時會自動為您排版。
        </div>

        <!-- 第一維度 -->
        <div class="p-4 rounded-xl bg-[#f8fafc] border border-[#e2e8f0]">
          <div class="font-bold text-[#0f172a] mb-2">第一維度：文獻基本資料與引用 (Metadata)</div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-2.5">
            <div>
              <label class="block text-[#475569] mb-1 font-medium">第一作者</label>
              <input type="text" id="editFirstAuthor" class="w-full bg-white text-[#0f172a] border border-[#cbd5e1] rounded-lg p-2">
            </div>
            <div>
              <label class="block text-[#475569] mb-1 font-medium">發表年份</label>
              <input type="text" id="editYear" class="w-full bg-white text-[#0f172a] border border-[#cbd5e1] rounded-lg p-2">
            </div>
            <div>
              <label class="block text-[#475569] mb-1 font-medium">BibTeX 引用代碼</label>
              <input type="text" id="editBibtex" class="w-full bg-white text-[#0f172a] border border-[#cbd5e1] rounded-lg p-2 font-mono">
            </div>
          </div>
        </div>

        <!-- 第二維度 -->
        <div class="p-4 rounded-xl bg-[#f8fafc] border border-[#e2e8f0]">
          <div class="font-bold text-[#0f172a] mb-2">第二維度：核心研究問題與理論框架 (Research Questions & Theories)</div>
          <textarea id="editDim2" rows="3" class="w-full bg-white text-[#0f172a] border border-[#cbd5e1] rounded-lg p-2.5 leading-relaxed" placeholder="直接輸入核心問題與理論依據，多項請換行..."></textarea>
        </div>

        <!-- 第三維度 -->
        <div class="p-4 rounded-xl bg-[#f8fafc] border border-[#e2e8f0]">
          <div class="font-bold text-[#0f172a] mb-2">第三維度：研究設計與實證方法論 (Methodology & Context)</div>
          <textarea id="editDim3" rows="3" class="w-full bg-white text-[#0f172a] border border-[#cbd5e1] rounded-lg p-2.5 leading-relaxed" placeholder="輸入研究方法、對象樣本與測量工具..."></textarea>
        </div>

        <!-- 第四維度 -->
        <div class="p-4 rounded-xl bg-[#f8fafc] border border-[#e2e8f0]">
          <div class="font-bold text-[#0f172a] mb-2">第四維度：關鍵實證數據與核心發現 (Empirical Findings)</div>
          <textarea id="editDim4" rows="3" class="w-full bg-white text-[#0f172a] border border-[#cbd5e1] rounded-lg p-2.5 leading-relaxed" placeholder="記錄統計檢定值或重要質性發現..."></textarea>
        </div>

        <!-- 第五維度 -->
        <div class="p-4 rounded-xl bg-[#f8fafc] border border-[#e2e8f0]">
          <div class="font-bold text-[#0f172a] mb-2">第五維度：批判性審視與方法學盲點 (Critical Limitations)</div>
          <textarea id="editDim5" rows="3" class="w-full bg-white text-[#0f172a] border border-[#cbd5e1] rounded-lg p-2.5 leading-relaxed" placeholder="記錄研究限制與您的獨立批判觀點..."></textarea>
        </div>

        <!-- 第六維度 -->
        <div class="p-4 rounded-xl bg-[#f0f9ff] border-2 border-[#bae6fd]">
          <div class="font-bold text-[#0369a1] mb-2 flex items-center justify-between">
            <span>第六維度：對自身論文研究的直接啟發 (Actionable Insights)</span>
            <span class="text-[11px] font-normal text-[#0284c7]">可隨時追加重讀後的啟發</span>
          </div>
          <textarea id="editDim6" rows="5" class="w-full bg-white text-[#0f172a] border border-[#7dd3fc] rounded-lg p-3 leading-relaxed" placeholder="直接輸入這篇文獻對您論文開題與研究問題的指引與啟發..."></textarea>
        </div>

        <!-- 第七維度 -->
        <div class="p-4 rounded-xl bg-[#f8fafc] border border-[#e2e8f0]">
          <div class="font-bold text-[#0f172a] mb-2">第七維度：重要原文引述與出處錨點 (Key Quotes & Anchors)</div>
          <textarea id="editDim7" rows="2" class="w-full bg-white text-[#0f172a] border border-[#cbd5e1] rounded-lg p-2.5 leading-relaxed" placeholder="直接貼上 1 至 3 段重要英文句子與頁碼..."></textarea>
        </div>

      </div>

      <!-- Modal Footer -->
      <div class="p-4 border-t border-[#e2e8f0] flex items-center justify-between bg-[#f8fafc]">
        <div class="text-xs text-[#64748b]">修改完成後點選儲存，系統將自動轉換為標準格式更新卡片檔案。</div>
        <div class="flex items-center gap-2">
          <button type="button" onclick="closeEditModal()" class="px-4 py-2 rounded-xl text-xs bg-white hover:bg-[#f1f5f9] text-[#334155] border border-[#cbd5e1] font-medium shadow-xs">
            取消
          </button>
          <button type="button" onclick="saveModalChanges()" class="px-4 py-2 rounded-xl text-xs font-semibold bg-[#1e40af] hover:bg-[#1d4ed8] text-white shadow-xs flex items-center gap-1.5">
            💾 儲存並更新卡片檔案
          </button>
        </div>
      </div>

    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast" class="fixed top-5 right-5 z-50 transition-all transform -translate-y-16 opacity-0 pointer-events-none">
    <div id="toastBox" class="px-4 py-2.5 rounded-xl bg-[#0f172a] text-white text-xs font-semibold shadow-lg">
      ✓ 完成
    </div>
  </div>

  <script>
    const HUB_DATA = {data_json};
    let activeCard = null;

    function cleanMarkdownToPlain(text) {{
      if (!text) return "";
      return text.split('\\n')
        .map(l => l.trim())
        .filter(Boolean)
        .map(l => l.replace(/^#+\\s*/, ''))
        .map(l => l.replace(/^[-*]\\s*(\\*[^*]+\\*[:：]\\s*|\\*[^*]+\\*[:：]\\s*)?/, ''))
        .map(l => l.replace(/^\\d+[\\.、]\\s*/, ''))
        .map(l => l.replace(/\\*\\*([^*]+)\\*\\*/g, '$1'))
        .map(l => l.replace(/^["“”\'](.*)["“”\']$/, '$1'))
        .join('\\n');
    }}

    function renderCompleted() {{
      const container = document.getElementById('completedList');
      if (!HUB_DATA.cards || HUB_DATA.cards.length === 0) {{
        container.innerHTML = `
          <div class="p-8 text-center bg-white rounded-2xl border border-[#e2e8f0] text-[#64748b]">
            目前尚未整理任何卡片。請從「待整理文獻清單」選取論文開始整理！
          </div>`;
        return;
      }}

      container.innerHTML = HUB_DATA.cards.map((c, i) => `
        <div class="bg-white border border-[#e2e8f0] rounded-2xl p-5 shadow-xs hover:border-[#cbd5e1] transition">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <div class="flex items-center gap-2 mb-1.5">
                <span class="px-2.5 py-0.5 rounded text-xs font-semibold bg-[#f0fdf4] text-[#166534] border border-[#bbf7d0]">
                  已整理卡片
                </span>
                <span class="font-mono text-xs text-[#64748b]">${{c.filename}}</span>
                <span class="text-[11px] text-[#94a3b8]">🕒 ${{c.mtime}}</span>
              </div>
              <h3 class="text-base font-bold text-[#0f172a]">${{c.title || c.filename}}</h3>
              <div class="text-xs text-[#64748b] mt-1">
                👤 作者：<span class="text-[#0f172a] font-medium">${{c.first_author || '未標註'}}</span> (${{c.year || ''}}) | 
                📄 原文：<code class="text-[#2563eb] font-mono text-[11px]">${{c.source_md || '無標籤'}}</code>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex items-center gap-2 shrink-0">
              <button type="button" onclick="openEditModal(${{i}})" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-[#eff6ff] hover:bg-[#dbeafe] text-[#1e40af] border border-[#bfdbfe] transition flex items-center gap-1.5 shadow-xs">
                ✏️ 再次閱讀並修改
              </button>
              <button type="button" onclick="copyCardMarkdown(${{i}})" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#f8fafc] hover:bg-[#f1f5f9] text-[#334155] border border-[#cbd5e1] transition flex items-center gap-1 shadow-xs">
                📋 複製
              </button>
            </div>
          </div>

          <!-- Highlight Preview (Dimension 6 Insights) -->
          <div class="mt-3.5 pt-3 border-t border-[#f1f5f9] text-xs">
            <div class="text-[#1e40af] font-semibold mb-1 flex items-center gap-1">
              <span>💡 第六維度摘要（對自身研究的直接啟發）：</span>
            </div>
            <div class="bg-[#f8fafc] border border-[#e2e8f0] rounded-xl p-3 text-[#334155] leading-relaxed line-clamp-3 whitespace-pre-line">
              ${{cleanMarkdownToPlain(c.dim6).slice(0, 260) + '...' || '尚未撰寫啟發'}}
            </div>
          </div>
        </div>
      `).join('');
    }}

    function renderPending() {{
      const container = document.getElementById('pendingList');
      if (!HUB_DATA.pending_papers || HUB_DATA.pending_papers.length === 0) {{
        container.innerHTML = `
          <div class="col-span-2 p-8 text-center bg-white rounded-2xl border border-[#e2e8f0] text-[#166534]">
            🎉 所有文獻皆已整理成標準卡片！
          </div>`;
        return;
      }}

      container.innerHTML = HUB_DATA.pending_papers.map((p, i) => `
        <div class="bg-white border border-[#e2e8f0] rounded-2xl p-4.5 shadow-xs hover:border-[#cbd5e1] transition flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="px-2.5 py-0.5 rounded text-xs font-semibold bg-[#fefce8] text-[#854d0e] border border-[#fef08a]">
                待整理 (${{p.size_kb}} KB)
              </span>
              <span class="text-[11px] text-[#64748b] font-mono">${{p.filename.split('_')[0] || ''}}</span>
            </div>
            <h4 class="text-sm font-bold text-[#0f172a] leading-snug mb-1">${{p.title}}</h4>
            <code class="block text-[11px] font-mono text-[#64748b] truncate mb-3">${{p.filename}}</code>
          </div>

          <div class="pt-3 border-t border-[#f1f5f9] flex items-center justify-between">
            <span class="text-[11px] text-[#64748b]">尚未建立卡片</span>
            <button type="button" onclick="copyPromptForPaper('${{p.filename}}')" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#eff6ff] hover:bg-[#dbeafe] text-[#1e40af] border border-[#bfdbfe] transition flex items-center gap-1.5 shadow-xs">
              🚀 複製建立指令
            </button>
          </div>
        </div>
      `).join('');
    }}

    function switchTab(tab) {{
      const cSec = document.getElementById('completedSection');
      const pSec = document.getElementById('pendingSection');
      const cBtn = document.getElementById('tabCompletedBtn');
      const pBtn = document.getElementById('tabPendingBtn');

      if (tab === 'completed') {{
        cSec.classList.remove('hidden');
        pSec.classList.add('hidden');
        cBtn.className = "px-4 py-2 rounded-xl text-xs font-bold bg-[#f0fdf4] text-[#166534] border border-[#bbf7d0] transition flex items-center gap-2 shadow-xs";
        pBtn.className = "px-4 py-2 rounded-xl text-xs font-bold bg-white hover:bg-[#f8fafc] text-[#64748b] border border-[#e2e8f0] transition flex items-center gap-2 shadow-xs";
      }} else {{
        cSec.classList.add('hidden');
        pSec.classList.remove('hidden');
        cBtn.className = "px-4 py-2 rounded-xl text-xs font-bold bg-white hover:bg-[#f8fafc] text-[#64748b] border border-[#e2e8f0] transition flex items-center gap-2 shadow-xs";
        pBtn.className = "px-4 py-2 rounded-xl text-xs font-bold bg-[#fefce8] text-[#854d0e] border border-[#fef08a] transition flex items-center gap-2 shadow-xs";
      }}
    }}

    function openEditModal(idx) {{
      activeCard = HUB_DATA.cards[idx];
      if (!activeCard) return;

      document.getElementById('modalCardFilename').innerText = activeCard.filename;
      document.getElementById('modalCardTitle').innerText = activeCard.title || activeCard.filename;

      document.getElementById('editFirstAuthor').value = activeCard.first_author || '';
      document.getElementById('editYear').value = activeCard.year || '';
      document.getElementById('editBibtex').value = activeCard.bibtex_key || '';

      document.getElementById('editDim2').value = cleanMarkdownToPlain(activeCard.dim2 || '');
      document.getElementById('editDim3').value = cleanMarkdownToPlain(activeCard.dim3 || '');
      document.getElementById('editDim4').value = cleanMarkdownToPlain(activeCard.dim4 || '');
      document.getElementById('editDim5').value = cleanMarkdownToPlain(activeCard.dim5 || '');
      document.getElementById('editDim6').value = cleanMarkdownToPlain(activeCard.dim6 || '');
      document.getElementById('editDim7').value = cleanMarkdownToPlain(activeCard.dim7 || '');

      document.getElementById('editModal').classList.remove('hidden');
    }}

    function closeEditModal() {{
      document.getElementById('editModal').classList.add('hidden');
      activeCard = null;
    }}

    function saveModalChanges() {{
      if (!activeCard) return;
      activeCard.first_author = document.getElementById('editFirstAuthor').value;
      activeCard.year = document.getElementById('editYear').value;
      activeCard.bibtex_key = document.getElementById('editBibtex').value;

      activeCard.dim2 = document.getElementById('editDim2').value;
      activeCard.dim3 = document.getElementById('editDim3').value;
      activeCard.dim4 = document.getElementById('editDim4').value;
      activeCard.dim5 = document.getElementById('editDim5').value;
      activeCard.dim6 = document.getElementById('editDim6').value;
      activeCard.dim7 = document.getElementById('editDim7').value;

      const updatedMd = rebuildMarkdown(activeCard);
      activeCard.raw_content = updatedMd;

      navigator.clipboard.writeText(updatedMd).then(() => {{
        showToast("✓ 卡片修改內容已複製到剪貼簿！可直接存檔。");
      }});

      const blob = new Blob([updatedMd], {{ type: 'text/markdown;charset=utf-8;' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = activeCard.filename;
      a.click();
      URL.revokeObjectURL(url);

      closeEditModal();
      renderCompleted();
    }}

    function formatPlainToBullets(plain) {{
      if (!plain || !plain.trim()) return "  - (未填寫)";
      return plain.trim().split('\\n')
        .map(l => l.trim())
        .filter(Boolean)
        .map(l => l.startsWith('-') || l.startsWith('*') ? `  ${{l}}` : `  - ${{l}}`)
        .join('\\n');
    }}

    function rebuildMarkdown(c) {{
      return `---
type: literature_card
card_version: 1.0
bibtex_key: ${{c.bibtex_key}}
title: "${{c.title.replace(/"/g, '')}}"
first_author: "${{c.first_author}}"
year: ${{c.year}}
journal: "${{c.journal.replace(/"/g, '')}}"
doi: "${{c.doi}}"
source_md: "${{c.source_md}}"
tags: [${{c.tags.join(', ')}}]
created_date: ${{c.created_date || '2026-10-09'}}
---

# 文獻卡片：${{c.first_author}} (${{c.year}}) - ${{c.title}}

## 1. 文獻元數據與引用標識 (Metadata)
${{c.dim1}}

## 2. 核心研究問題與理論框架 (RQs & Theoretical Lens)
${{formatPlainToBullets(c.dim2)}}

## 3. 研究設計與實證方法論 (Methodology & Context)
${{formatPlainToBullets(c.dim3)}}

## 4. 關鍵實證數據與核心發現 (Empirical Findings)
${{formatPlainToBullets(c.dim4)}}

## 5. 批判性審視與方法學盲點 (Critical Limitations)
${{formatPlainToBullets(c.dim5)}}

## 6. 對本研究 PROJECT.md 的直接啟發 (Actionable Insights)
${{formatPlainToBullets(c.dim6)}}

## 7. 重要原文引述與出處錨點 (Key Quotes & Anchors)
${{formatPlainToBullets(c.dim7)}}
`;
    }}

    function copyCardMarkdown(idx) {{
      const c = HUB_DATA.cards[idx];
      if (!c) return;
      navigator.clipboard.writeText(c.raw_content).then(() => {{
        showToast(`✓ 已複製 ${{c.filename}} 的 Markdown！`);
      }});
    }}

    function copyPromptForPaper(fn) {{
      const prompt = `請使用 academic-reading-card Skill，幫我為 01_papers/extracted_text/${{fn}} 產生審核面板，協助我進行數據核對並親筆撰寫第 6 維度，確認後存入 02_notes/cards/。`;
      navigator.clipboard.writeText(prompt).then(() => {{
        showToast("✓ 已複製建立卡片提示詞！請貼入對話框發送。");
      }});
    }}

    function filterLists() {{
      const q = document.getElementById('searchInput').value.toLowerCase().trim();
      if (!q) {{
        renderCompleted();
        renderPending();
        return;
      }}
      const filteredCompleted = HUB_DATA.cards.filter(c => 
        c.filename.toLowerCase().includes(q) || 
        (c.title && c.title.toLowerCase().includes(q)) ||
        (c.first_author && c.first_author.toLowerCase().includes(q))
      );
      const filteredPending = HUB_DATA.pending_papers.filter(p =>
        p.filename.toLowerCase().includes(q) ||
        (p.title && p.title.toLowerCase().includes(q))
      );

      const cContainer = document.getElementById('completedList');
      cContainer.innerHTML = filteredCompleted.map((c, i) => `
        <div class="bg-white border border-[#e2e8f0] rounded-2xl p-5">
          <div class="flex items-center justify-between">
            <h3 class="font-bold text-[#0f172a]">${{c.title}}</h3>
            <button onclick="openEditModal(${{i}})" class="text-xs bg-[#eff6ff] text-[#1e40af] px-3 py-1.5 rounded-lg border border-[#bfdbfe]">修改</button>
          </div>
        </div>
      `).join('') || '<div class="text-[#64748b] text-xs p-4">無符合之已整理卡片</div>';

      const pContainer = document.getElementById('pendingList');
      pContainer.innerHTML = filteredPending.map(p => `
        <div class="bg-white border border-[#e2e8f0] rounded-2xl p-4">
          <h4 class="font-bold text-[#0f172a] text-xs">${{p.title}}</h4>
          <button onclick="copyPromptForPaper('${{p.filename}}')" class="mt-2 text-xs bg-[#eff6ff] text-[#1e40af] px-2.5 py-1 rounded border border-[#bfdbfe]">複製指令</button>
        </div>
      `).join('') || '<div class="text-[#64748b] text-xs p-4">無符合之待整理文獻</div>';
    }}

    function showToast(msg) {{
      const t = document.getElementById('toast');
      document.getElementById('toastBox').innerText = msg;
      t.classList.remove('opacity-0', '-translate-y-16');
      t.classList.add('opacity-100', 'translate-y-0');
      setTimeout(() => {{
        t.classList.remove('opacity-100', 'translate-y-0');
        t.classList.add('-translate-y-16');
      }}, 3000);
    }}

    function refreshData() {{
      showToast("請在終端機執行 python manage_cards.py --dashboard 更新資料");
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      renderCompleted();
      renderPending();
    }});
  </script>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def main():
    parser = argparse.ArgumentParser(description="學術文獻閱讀卡片庫維護與統計系統")
    parser.add_argument("--status", action="store_true", help="顯示工作區卡片統計與比對摘要")
    parser.add_argument("--dashboard", action="store_true", help="生成或更新卡片維護中心 (card_hub.html)")
    parser.add_argument("--root", type=str, default="", help="指定工作區根目錄路徑")
    args = parser.parse_args()

    root_dir = Path(args.root) if args.root else find_workspace_root()
    data = scan_workspace(root_dir)

    print_cli_summary(data)

    if args.dashboard or not args.status:
        hub_path = root_dir / "skills" / "academic_reading_card" / "resources" / "card_hub.html"
        hub_path.parent.mkdir(parents=True, exist_ok=True)
        generate_html_hub(data, hub_path)
        print(f"\n[OK] 儀表板已更新至：{hub_path}")

        artifact_dir = Path(r"C:\Users\Leo\.gemini\antigravity\brain\02be9c50-c1c2-4515-81cd-0caae49365be")
        if artifact_dir.exists():
            artifact_hub = artifact_dir / "card_hub.html"
            generate_html_hub(data, artifact_hub)
            print(f"[OK] 對話 Artifact 儀表板已同步至：{artifact_hub}")


if __name__ == "__main__":
    main()
