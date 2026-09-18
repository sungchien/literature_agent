"""
scripts/literature_workflow_mcp.py

學術文獻全流程 MCP 伺服器（Literature Workflow MCP Server）
整合核心工具鏈：
1. search_candidate_papers: 檢索 OpenAlex 並生成流水號候選文獻評估清單
2. get_candidate_papers: 讀取候選論文清單與詳細摘要欄位
3. review_candidate_papers: 依研究者決策批次更新審查標記（Human-in-the-Loop [+] 採納 / [-] 排除 / [ ] 待定）
4. download_selected_papers: 依採納狀態自動下載 OA PDF，提示人工調閱封閉期刊
5. convert_pdfs_to_markdown: 批次將 raw_pdf 轉譯為純淨 Markdown，剔除 References 噪音
6. build_paper_index: 為 extracted_text 建立標題感知之向量檢索索引
7. search_paper_chunks: 依據自然語言查詢檢索最相關之論文精華段落

支援雙模運作：
- 命令列 CLI 模式：提供個別功能手動執行、審查與除錯
- MCP stdio 模式：提供 Antigravity / Claude Desktop 等 Agent 自主調用，支援人機協同審查
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
    review_candidate_papers,
    get_candidate_papers_summary,
    apply_review_decisions,
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
                        "description": "向 OpenAlex 檢索指定主題的學術文獻候選清單，生成流水號 candidate_papers_XX.md 與專屬獲取追蹤檔案。執行後請向研究者展示論文摘要並由研究者進行人機協同品質審查。",
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
                        "name": "get_candidate_papers",
                        "description": "讀取指定候選清單（或最新清單）的論文詳細欄位（包含序號、審查狀態、篇名、來源期刊、年份、DOI 與完整摘要），供 Agent 於對話視窗向研究者呈現以進行審查。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "sequence": {
                                    "type": "string",
                                    "description": "候選清單兩位數流水號（例如 '01', '02'），預設讀取最新清單",
                                    "default": ""
                                }
                            }
                        }
                    },
                    {
                        "name": "review_candidate_papers",
                        "description": "依據研究者在對話視窗中的確認決策，程式化更新指定候選清單中的文獻審查狀態（支援【逐筆單篇更新】或【批次多篇更新】，標記 [+] 採納、[-] 排除、[ ] 保留待定），並自動同步更新 Frontmatter 統計與專屬追蹤檔。落實人機協同（Human-in-the-Loop）。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "sequence": {
                                    "type": "string",
                                    "description": "候選清單流水號（例如 '01'），若未指定則預設使用最新一份清單",
                                    "default": ""
                                },
                                "decisions": {
                                    "type": "object",
                                    "description": "論文序號對應審查決策之鍵值對。可傳入單篇進行逐筆審查（例如 {'1': '+'}），亦可傳入多篇進行批次審查（例如 {'1': '+', '2': '-', '3': ' '}）。鍵為論文序號，值為決策：'+'（採納）、'-'（排除）、' '（保留待定）。",
                                    "additionalProperties": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["decisions"]
                        }
                    },
                    {
                        "name": "download_selected_papers",
                        "description": "讀取候選清單中標記為 [+] 的採納論文，自動將合法 Open Access PDF 下載至 01_papers/raw_pdf/，更新專屬獲取追蹤報告，並對封閉訂閱期刊提供 DOI 與調閱檔名指引。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "sequence": {
                                    "type": "string",
                                    "description": "指定下載之候選清單流水號（例如 '01'），預設使用最新清單",
                                    "default": ""
                                }
                            }
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
            summary = get_candidate_papers_summary()
            papers_preview = ""
            if "papers" in summary and summary["papers"]:
                lines = []
                for p in summary["papers"]:
                    lines.append(f"[{p['index']}] 《{p['title']}》 | 來源：{p['source']} | {p['authors_year']}")
                    lines.append(f"    摘要重點：{p['abstract'][:140]}..." if len(p['abstract']) > 140 else f"    摘要：{p['abstract']}")
                papers_preview = "\n".join(lines)

            msg = (
                f"[系統執行紀錄]\n{log}\n\n"
                f"📋 【人機協同審查指引（Human-in-the-Loop Protocol）】：\n"
                f"候選文獻已成功輸出至 01_papers/{summary.get('file', 'candidate_papers_XX.md')}，摘要概覽如下：\n\n"
                f"{papers_preview}\n\n"
                f"⚠️ 【關鍵暫停點】：請 Agent 依據研究者的需求進行人機協同品質把關，支援以下兩種審查模式：\n"
                f"  1. 【批次快速審查】：若研究者一次給予多篇指令（如「採納 1 與 3，排除 2」），Agent 調用 `review_candidate_papers(decisions={{\"1\": \"+\", \"2\": \"-\", \"3\": \"+\"}})` 批次更新。\n"
                f"  2. 【逐筆引導審查】：若研究者要求一篇一篇看，Agent 請先展示第 1 篇的詳細摘要與專業評估建議，詢問研究者決策；研究者核定後調用 `review_candidate_papers(decisions={{\"1\": \"+\"}})` 寫入，再繼續呈現第 2 篇，依此類推。\n"
                f"審查確認完畢後，Agent 方可調用 `download_selected_papers` 下載採納全文。"
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": msg}]}
            }

        elif tool_name == "get_candidate_papers":
            seq = args.get("sequence") or None
            res = get_candidate_papers_summary(seq)
            if "error" in res:
                msg = f"[讀取失敗] {res['error']}"
            else:
                msg = json.dumps(res, ensure_ascii=False, indent=2)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": msg}]}
            }

        elif tool_name == "review_candidate_papers":
            seq = args.get("sequence") or None
            decisions = args.get("decisions", {})
            res = apply_review_decisions(seq, decisions)
            if "error" in res:
                msg = f"[審查更新失敗] {res['error']}"
            else:
                msg = (
                    f"✅ {res['message']}\n\n"
                    f"下一步建議：請 Agent 接續調用 `download_selected_papers` 工具，自動下載標記為 [+] 的 OA 全文文獻。"
                )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": msg}]}
            }

        elif tool_name == "download_selected_papers":
            seq = args.get("sequence") or None
            log = capture_output(download_selected_papers, seq)
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
        elif cmd == "review":
            seq = sys.argv[2] if len(sys.argv) > 2 else None
            review_candidate_papers(seq)
        elif cmd == "download":
            seq = sys.argv[2] if len(sys.argv) > 2 else None
            download_selected_papers(seq)
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
            print("  python scripts/literature_workflow_mcp.py review [序號]     # 啟動終端機互動審查工具")
            print("  python scripts/literature_workflow_mcp.py download [序號]   # 下載已標記 [+] 之採納論文")
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
