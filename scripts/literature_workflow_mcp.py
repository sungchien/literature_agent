"""
scripts/literature_workflow_mcp.py

學術文獻全流程 MCP 伺服器（Literature Workflow MCP Server）
整合五大核心工具：
1. search_candidate_papers: 檢索 OpenAlex 並生成候選文獻評估清單（引導研究者人機協同勾選 [x]）
2. download_selected_papers: 依勾選狀態自動下載 OA PDF，提示人工自圖書館取得封閉期刊
3. convert_pdfs_to_markdown: 批次將 raw_pdf 轉譯為純淨 Markdown，剔除 References 噪音
4. build_paper_index: 為 extracted_text 建立標題感知之向量檢索索引
5. search_paper_chunks: 依據自然語言查詢檢索最相關之論文精華段落

支援雙模運作：
- 命令列 CLI 模式：提供個別功能手動執行與除錯
- MCP stdio 模式：提供 Antigravity / Claude Desktop 等 Agent 自主調用
"""

import io
import os
import sys
import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any

# 確保 Windows 終端輸出為 UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 將專案根目錄加入模組搜尋路徑
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.fetch_openalex import (
    search_candidate_papers,
    download_selected_papers,
    CANDIDATE_MD_FILE
)
from scripts.extract_pdf_to_md import convert_all_pdfs
from scripts.paper_retriever_mcp import (
    build_index_data,
    search_index_data
)

# =====================================================================
# 工具執行輔助函式（捕捉 stdout 作為 MCP 回傳文字）
# =====================================================================

def capture_output(func, *args, **kwargs) -> str:
    """攔截函式執行時之標準輸出，作為 MCP 回傳之結構化訊息"""
    old_stdout = sys.stdout
    redirected = io.StringIO()
    try:
        sys.stdout = redirected
        func(*args, **kwargs)
    finally:
        sys.stdout = old_stdout
    return redirected.getvalue().strip()

# =====================================================================
# MCP JSON-RPC 2.0 協議處理
# =====================================================================

def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """處理標準 JSON-RPC 2.0 MCP 請求協議"""
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "academic-literature-workflow",
                    "version": "2.0.0"
                }
            }
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "search_candidate_papers",
                        "description": "向 OpenAlex 檢索指定主題的學術文獻候選清單，並生成 01_papers/candidate_papers.md。執行後請務必向研究者提示前往檔案審閱期刊來源與摘要，並將欲納入之論文標記為 [x]。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "學術檢索關鍵字或研究主題語句（例如：'AI Agents in Higher Education scaffolding'）"
                                },
                                "start_year": {
                                    "type": "integer",
                                    "description": "文獻發表起始年份（預設 2022）",
                                    "default": 2022
                                },
                                "max_candidates": {
                                    "type": "integer",
                                    "description": "候選文獻檢索數量（預設 10 篇）",
                                    "default": 10
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "download_selected_papers",
                        "description": "讀取 01_papers/candidate_papers.md 中研究者勾選為 [x] 的論文，自動將合法 Open Access PDF 下載至 01_papers/raw_pdf/，並對封閉訂閱期刊提供 DOI 與建議檔名指引。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "convert_pdfs_to_markdown",
                        "description": "批次將 01_papers/raw_pdf/ 目錄下的所有 PDF 轉譯為純淨 Markdown 文本，自動剔除 References 引用清單與出版噪音，存放至 01_papers/extracted_text/。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "build_paper_index",
                        "description": "掃描 01_papers/extracted_text/ 下的所有 Markdown 論文，以標題與段落為界建立語意倒排索引並儲存為 01_papers/vector_index.json。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "search_paper_chunks",
                        "description": "於本地論文索引庫中進行語意檢索，依據查詢問題回傳最相關之論文精華段落、所屬章節與文獻出處。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "欲查詢的研究概念或問題（例如：'How does AI scaffolding reduce cognitive load?'）"
                                },
                                "top_k": {
                                    "type": "integer",
                                    "description": "回傳之最相關段落數量（預設 3 篇）",
                                    "default": 3
                                }
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        }

    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "search_candidate_papers":
            q = args.get("query", "")
            sy = args.get("start_year", 2022)
            mc = args.get("max_candidates", 10)
            log = capture_output(search_candidate_papers, q, max_candidates=mc, start_year=sy)
            msg = (
                f"[系統執行紀錄]\n{log}\n\n"
                f"[重要提示]：候選清單已成功輸出至 01_papers/candidate_papers.md！\n"
                f"請主動提示研究者打開檔案，審查各篇論文之發表來源（Source 期刊）與摘要（Abstract），"
                f"確認具備學術品質後將標題旁的 [ ] 改為 [x]。待研究者確認完成後，再行調用 download_selected_papers 工具。"
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": msg}]}
            }

        elif tool_name == "download_selected_papers":
            log = capture_output(download_selected_papers)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": log if log else "下載程序已執行完成。"}]}
            }

        elif tool_name == "convert_pdfs_to_markdown":
            log = capture_output(convert_all_pdfs)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": log if log else "PDF 轉譯與文字清洗程序已執行完成。"}]}
            }

        elif tool_name == "build_paper_index":
            res = build_index_data()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False, indent=2)}]}
            }

        elif tool_name == "search_paper_chunks":
            query = args.get("query", "")
            top_k = args.get("top_k", 3)
            hits = search_index_data(query, top_k)
            if not hits:
                formatted_text = f"未在本地文獻庫中找到與『{query}』直接相關的段落。"
            else:
                lines = [f"### 針對關鍵字『{query}』之檢索結果（Top {len(hits)} 筆）：\n"]
                for i, h in enumerate(hits, 1):
                    lines.append(f"#### [{i}] 來源：`{h.get('source_paper', h.get('file'))}` | 章節：`{h.get('section')}` (評分: {h.get('relevance_score', h.get('score'))})")
                    lines.append(f"> {h.get('content', h.get('text'))}\n")
                formatted_text = "\n".join(lines)

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": formatted_text}]}
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"未知的工具：{tool_name}"}
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"不支援的方法：{method}"}
    }

# =====================================================================
# 主執行程序（CLI 命令列 / stdio 監聽雙模）
# =====================================================================

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "search":
            q = sys.argv[2] if len(sys.argv) > 2 else "AI Agents higher education"
            search_candidate_papers(q, max_candidates=10, start_year=2022)
        elif cmd == "download":
            download_selected_papers()
        elif cmd == "convert":
            convert_all_pdfs()
        elif cmd == "build" or cmd == "index":
            res = build_index_data()
            print(json.dumps(res, ensure_ascii=False, indent=2))
        elif cmd == "query" or cmd == "search_chunks":
            q = sys.argv[2] if len(sys.argv) > 2 else "scaffolding"
            print(json.dumps(search_index_data(q), ensure_ascii=False, indent=2))
        else:
            print("使用方式（命令列模式）：")
            print("  python scripts/literature_workflow_mcp.py search [關鍵字]   # 檢索候選論文清單")
            print("  python scripts/literature_workflow_mcp.py download          # 下載 candidate_papers.md 已勾選論文")
            print("  python scripts/literature_workflow_mcp.py convert           # 批次將 PDF 轉譯清洗為 Markdown")
            print("  python scripts/literature_workflow_mcp.py index             # 重建本地論文向量索引庫")
            print("  python scripts/literature_workflow_mcp.py query [關鍵字]    # 測試檢索論文精華段落")
        return

    # 無參數時啟動標準 MCP stdio 監聽
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            resp = handle_mcp_request(req)
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
