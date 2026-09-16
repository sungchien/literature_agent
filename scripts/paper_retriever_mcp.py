"""
scripts/paper_retriever_mcp.py

學術論文檢索專用 MCP 伺服器（Model Context Protocol Server）
提供兩大標準工具：
1. build_paper_index: 為 01_papers/extracted_text/ 建立段落向量索引
2. search_paper_chunks: 依據查詢語句檢索最相關之論文精華段落
"""

import os
import sys
import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any

# 定義工作區目錄常數
EXTRACTED_DIR = Path("01_papers/extracted_text")
INDEX_FILE = Path("01_papers/vector_index.json")

# =====================================================================
# 核心檢索引擎：分塊與輕量語意相似度演算法
# =====================================================================

def tokenize(text: str) -> List[str]:
    """簡易斷詞：提取英文單字與連續漢字"""
    return re.findall(r'[a-zA-Z]{2,}|[\u4e00-\u9fa5]', text.lower())

def chunk_markdown_file(file_path: Path) -> List[Dict[str, Any]]:
    """將 Markdown 檔案依據標題與雙換行切分為結構化段落區塊（Chunks）"""
    chunks = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    current_section = "Introduction / Overview"
    buffer = []

    for line in lines:
        stripped = line.strip()
        # 遇到 Markdown 標題時，更新當前章節名稱
        if stripped.startswith("#"):
            if buffer:
                chunk_text = " ".join(buffer).strip()
                if len(tokenize(chunk_text)) >= 15:  # 過濾過短的瑣碎行
                    chunks.append({
                        "file": file_path.name,
                        "section": current_section,
                        "text": chunk_text
                    })
                buffer = []
            current_section = stripped.lstrip("#").strip()
            continue

        if stripped == "":
            if buffer:
                chunk_text = " ".join(buffer).strip()
                if len(tokenize(chunk_text)) >= 20:
                    chunks.append({
                        "file": file_path.name,
                        "section": current_section,
                        "text": chunk_text
                    })
                buffer = []
        else:
            buffer.append(stripped)

    if buffer:
        chunk_text = " ".join(buffer).strip()
        if len(tokenize(chunk_text)) >= 15:
            chunks.append({
                "file": file_path.name,
                "section": current_section,
                "text": chunk_text
            })

    return chunks

def build_index_data() -> Dict[str, Any]:
    """掃描所有 Markdown 論文並建立可檢索之索引字典"""
    md_files = list(EXTRACTED_DIR.glob("*.md"))
    if not md_files:
        return {"error": f"在 {EXTRACTED_DIR} 找不到任何 Markdown 檔案，請先執行文字轉譯腳本。"}

    all_chunks = []
    for md_file in md_files:
        chunks = chunk_markdown_file(md_file)
        all_chunks.extend(chunks)

    # 計算詞頻與反向文件頻率 (TF-IDF 特徵)
    doc_count = len(all_chunks)
    df = {}
    for chunk in all_chunks:
        words = set(tokenize(chunk["text"]))
        for w in words:
            df[w] = df.get(w, 0) + 1

    idf = {w: math.log((doc_count + 1) / (count + 1)) + 1 for w, count in df.items()}

    # 封裝索引資料結構
    index_payload = {
        "metadata": {
            "total_papers": len(md_files),
            "total_chunks": doc_count
        },
        "idf": idf,
        "chunks": all_chunks
    }

    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_payload, f, ensure_ascii=False, indent=2)

    return {
        "status": "success",
        "message": f"成功為 {len(md_files)} 篇論文建立索引，共切割為 {doc_count} 個語意段落區塊！",
        "index_file": str(INDEX_FILE)
    }

def search_index_data(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """在索引庫中依據查詢詞計算餘弦關聯度，回傳 Top-K 精準段落"""
    if not INDEX_FILE.exists():
        return [{"error": "尚未建立向量索引檔，請先呼叫 build_paper_index 工具。"}]

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        index_payload = json.load(f)

    idf = index_payload.get("idf", {})
    chunks = index_payload.get("chunks", [])
    query_tokens = tokenize(query)

    if not query_tokens:
        return [{"error": "查詢語句為空或未包含有效關鍵詞彙。"}]

    scores = []
    for chunk in chunks:
        chunk_tokens = tokenize(chunk["text"])
        chunk_token_set = set(chunk_tokens)
        
        # 計算相似度分數（詞頻加權內積）
        score = 0.0
        for qt in query_tokens:
            if qt in chunk_token_set:
                tf = chunk_tokens.count(qt) / len(chunk_tokens)
                score += tf * idf.get(qt, 1.0)

        if score > 0:
            scores.append((score, chunk))

    # 依相關度由高至低排序
    scores.sort(key=lambda x: x[0], reverse=True)
    top_results = scores[:top_k]

    formatted_results = []
    for rank, (score, chunk) in enumerate(top_results, 1):
        formatted_results.append({
            "rank": rank,
            "relevance_score": round(score, 4),
            "source_paper": chunk["file"],
            "section": chunk["section"],
            "content": chunk["text"]
        })

    return formatted_results if formatted_results else [{"message": "在現有論文庫中未檢索到高度相關段落，請嘗試更換查詢詞。"}]

# =====================================================================
# MCP 標準協議處理器（標準 stdio JSON-RPC 介面）
# =====================================================================

def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """處理來自 Antigravity Agent 的 JSON-RPC 協議請求"""
    method = request.get("method")
    req_id = request.get("id")

    # 1. 協議初始化握手
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "academic-paper-retriever",
                    "version": "1.0.0"
                }
            }
        }

    # 2. 宣告可用工具清單
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "build_paper_index",
                        "description": "掃描 01_papers/extracted_text/ 下的所有 Markdown 論文，為所有段落建立檢索索引。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "search_paper_chunks",
                        "description": "在已索引的論文庫中，針對特定學術概念或研究問題進行語意檢索，回傳最相關的原文精華段落與出處。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "欲查詢的學術問題或關鍵詞彙（例如：'cognitive load in AI writing'）"
                                },
                                "top_k": {
                                    "type": "integer",
                                    "description": "回傳的最相關段落筆数（預設為 3）",
                                    "default": 3
                                }
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        }

    # 3. 執行工具調用
    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "build_paper_index":
            exec_res = build_index_data()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(exec_res, ensure_ascii=False, indent=2)}]
                }
            }

        elif tool_name == "search_paper_chunks":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 3)
            exec_res = search_index_data(query, top_k)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(exec_res, ensure_ascii=False, indent=2)}]
                }
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"未知的工具名稱：{tool_name}"}
            }

    # 其他未支援方法之預設回應
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {}
    }

def main():
    """主循環：監聽 stdin 並將回應寫入 stdout（stdio 模式）"""
    # 支援手動命令列除錯：若提供參數直接在本機執行
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "build":
            print(json.dumps(build_index_data(), ensure_ascii=False, indent=2))
        elif cmd == "search":
            q = sys.argv[2] if len(sys.argv) > 2 else "scaffolding"
            print(json.dumps(search_index_data(q), ensure_ascii=False, indent=2))
        return

    # 標準 MCP stdio 監聽
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
