"""
scripts/paper_retriever_mcp.py

學術論文稠密向量檢索專用工具與 MCP 伺服器
基於 sentence-transformers 與 BAAI/bge-base-en-v1.5 高效學術語意嵌入模型（768 維度）
採用【文字 / 向量雙檔解耦架構（Decoupled Text & Vector Storage）】：
1. 01_papers/vector_index.json: 儲存論文段落文字、章節標籤與檔案時間戳快取（輕量、純文字、可讀性高）
2. 01_papers/vector_embeddings.npz: 儲存 (N, 768) 之 float32 二進位密集向量矩陣（體積小、極速載入）

支援高效能【增量更新（Incremental Indexing）】機制：
- 僅對新加入或內容有異動的 Markdown 論文調用模型計算 768 維向量
- 未異動之文獻直接沿用既有向量（Cache Hit，0 耗時）
- 自動清理已從目錄移除之過期論文（Prune）

提供工具與命令列指令：
- CLI 批次建置：python scripts/paper_retriever_mcp.py build [--force]
- CLI 語意檢索：python scripts/paper_retriever_mcp.py search "查詢詞"
- MCP 工具：search_paper_chunks
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, *args, **kwargs):
        return iterable

# 設定 Windows 終端輸出編碼（標準輸出與標準錯誤皆統一 UTF-8）
for stream in [sys.stdout, sys.stderr]:
    if hasattr(stream, "reconfigure") and getattr(stream, "encoding", "").lower() != "utf-8":
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

# 針對 Windows Anaconda / Miniconda 環境，自動補齊 Library\bin 等 DLL 搜尋目錄以防 PIL/SSL ImportError
if sys.platform == "win32":
    py_dir = Path(sys.executable).parent
    for extra_dir in [py_dir, py_dir / "Library" / "bin", py_dir / "Scripts", py_dir / "DLLs"]:
        if extra_dir.exists():
            extra_dir_str = str(extra_dir)
            if extra_dir_str not in os.environ.get("PATH", ""):
                os.environ["PATH"] = extra_dir_str + os.pathsep + os.environ.get("PATH", "")
            if hasattr(os, "add_dll_directory"):
                try:
                    os.add_dll_directory(extra_dir_str)
                except Exception:
                    pass


# 定義工作區目錄與雙檔常數
PAPERS_DIR = Path("01_papers")
EXTRACTED_DIR = PAPERS_DIR / "extracted_text"
INDEX_FILE = PAPERS_DIR / "vector_index.json"          # 輕量結構化文字與元數據
VECTORS_FILE = PAPERS_DIR / "vector_embeddings.npz"    # 二進位稠密向量矩陣

# 模型設定：採用 BAAI/bge-base-en-v1.5 稠密嵌入模型（768 維度，僅約 438 MB，記憶體友善且推論極速）
MODEL_NAME = "BAAI/bge-base-en-v1.5"

# 全域模型與雙檔記憶體快取（MCP 行程常駐，檢索時零磁碟 I/O 開銷）
_MODEL = None
_CACHED_PAYLOAD: Optional[Dict[str, Any]] = None
_CACHED_VECTORS = None  # numpy.ndarray (N, 768)
_INDEX_MTIME: float = 0.0
_VECTORS_MTIME: float = 0.0


def get_embedding_model():
    """延遲加載並快取 SentenceTransformer 模型實例"""
    global _MODEL
    if _MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as e:
            raise ImportError(
                f"加載 sentence-transformers 失敗（{e}）！\n"
                "請在終端機中執行安裝指令：pip install sentence-transformers numpy"
            )
        # 加載 BAAI/bge-base-en-v1.5 嵌入模型（768 維度，~438 MB）
        _MODEL = SentenceTransformer(MODEL_NAME)
    return _MODEL
    return _MODEL


def tokenize(text: str) -> List[str]:
    """簡易斷詞：提取英文單字與連續漢字，用於段落最小長度過濾"""
    return re.findall(r'[a-zA-Z]{2,}|[\u4e00-\u9fa5]', text.lower())


def chunk_markdown_file(file_path: Path) -> List[Dict[str, Any]]:
    """將 Markdown 檔案依據標題與雙換行切分為結構化段落區塊（Chunks）"""
    chunks = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    current_section = "Introduction / Overview"
    buffer = []
    chunk_counter = 1

    for line in lines:
        stripped = line.strip()
        # 遇到 Markdown 標題時，更新當前章節名稱並封裝前置區塊
        if stripped.startswith("#"):
            if buffer:
                chunk_text = " ".join(buffer).strip()
                if len(tokenize(chunk_text)) >= 15:  # 過濾過短的瑣碎行
                    chunks.append({
                        "chunk_id": f"{file_path.stem}_chunk_{chunk_counter}",
                        "file": file_path.name,
                        "section": current_section,
                        "text": chunk_text
                    })
                    chunk_counter += 1
                buffer = []
            current_section = stripped.lstrip("#").strip()
            continue

        if stripped == "":
            if buffer:
                chunk_text = " ".join(buffer).strip()
                if len(tokenize(chunk_text)) >= 20:
                    chunks.append({
                        "chunk_id": f"{file_path.stem}_chunk_{chunk_counter}",
                        "file": file_path.name,
                        "section": current_section,
                        "text": chunk_text
                    })
                    chunk_counter += 1
                buffer = []
        else:
            buffer.append(stripped)

    if buffer:
        chunk_text = " ".join(buffer).strip()
        if len(tokenize(chunk_text)) >= 15:
            chunks.append({
                "chunk_id": f"{file_path.stem}_chunk_{chunk_counter}",
                "file": file_path.name,
                "section": current_section,
                "text": chunk_text
            })

    return chunks


def load_index_and_vectors() -> Tuple[Optional[Dict[str, Any]], Any]:
    """讀取並快取雙檔：vector_index.json 與 vector_embeddings.npz"""
    global _CACHED_PAYLOAD, _CACHED_VECTORS, _INDEX_MTIME, _VECTORS_MTIME
    if not INDEX_FILE.exists() or not VECTORS_FILE.exists():
        return None, None

    try:
        import numpy as np
    except ImportError:
        raise ImportError("未檢測到 numpy 套件！請在終端機中執行：pip install numpy")

    try:
        idx_mtime = INDEX_FILE.stat().st_mtime
        vec_mtime = VECTORS_FILE.stat().st_mtime
        if (
            _CACHED_PAYLOAD is None
            or _CACHED_VECTORS is None
            or idx_mtime != _INDEX_MTIME
            or vec_mtime != _VECTORS_MTIME
        ):
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                _CACHED_PAYLOAD = json.load(f)
            with np.load(VECTORS_FILE) as data:
                _CACHED_VECTORS = data["embeddings"]
            _INDEX_MTIME = idx_mtime
            _VECTORS_MTIME = vec_mtime
        return _CACHED_PAYLOAD, _CACHED_VECTORS
    except Exception:
        return None, None


def build_index_data(force: bool = False, verbose: bool = True) -> Dict[str, Any]:
    """
    建立或增量更新本地文獻之【雙檔解耦向量索引】。
    
    儲存架構：
    - 01_papers/vector_index.json: 儲存文本、章節、時間戳元數據（輕量好讀）
    - 01_papers/vector_embeddings.npz: 儲存 (N, 768) 之 float32 二進位矩陣（高效緊湊）
    
    支援【增量更新（Incremental Indexing）】機制：
    1. 讀取現有 vector_index.json 中的檔案狀態（mtime、size、chunk_count）與 npz 向量矩陣。
    2. 比對 extracted_text/*.md：
       - 若檔案時間戳與大小相同 -> 判定為未異動，直接沿用舊段落與舊向量（Cache Hit，0 耗時）。
       - 若檔案為新加入或有修改 -> 切割段落並加入待計算清單。
       - 若已刪除檔案 -> 自動從索引庫中移除。
    3. 僅對真正新增/異動的段落調用 BAAI/bge-base-en-v1.5 進行向量編碼，大幅減少運算等待時間。
    
    參數:
        force: 若為 True，則忽略快取強制全量重新編碼所有檔案。
        verbose: 若為 True，在終端機中顯示 TQDM 處理進度條與階段統計。
    """
    global _CACHED_PAYLOAD, _CACHED_VECTORS, _INDEX_MTIME, _VECTORS_MTIME

    try:
        import numpy as np
    except ImportError:
        return {
            "status": "error",
            "message": "未檢測到 numpy 套件！請在終端機中執行：pip install numpy"
        }

    if not EXTRACTED_DIR.exists():
        return {
            "status": "error",
            "message": f"未找到目錄 {EXTRACTED_DIR}，請先執行 PDF 轉譯腳本產出 Markdown 論文。"
        }

    md_files = sorted(list(EXTRACTED_DIR.glob("*.md")))
    if not md_files:
        return {
            "status": "error",
            "message": f"在 {EXTRACTED_DIR} 找不到任何 Markdown 檔案，請先執行文字轉譯腳本。"
        }

    # 1. 讀取既有雙檔索引以支援增量快取
    existing_file_states: Dict[str, Dict[str, Any]] = {}
    existing_chunks_by_file: Dict[str, List[Dict[str, Any]]] = {}
    existing_vectors_by_file: Dict[str, List[Any]] = {}

    if not force:
        existing_payload, existing_vectors = load_index_and_vectors()
        if (
            existing_payload
            and existing_vectors is not None
            and isinstance(existing_payload, dict)
        ):
            cached_model = existing_payload.get("metadata", {}).get("embedding_model")
            existing_chunks = existing_payload.get("chunks", [])
            # 檢查嵌入模型與維度是否一致，且段落數與向量列數完全吻合
            if (
                cached_model == MODEL_NAME
                and len(existing_chunks) == len(existing_vectors)
            ):
                existing_file_states = existing_payload.get("metadata", {}).get("file_states", {})
                for c, vec in zip(existing_chunks, existing_vectors):
                    fname = c.get("file")
                    if fname:
                        existing_chunks_by_file.setdefault(fname, []).append(c)
                        existing_vectors_by_file.setdefault(fname, []).append(vec)

    # 2. 檢驗每一篇 Markdown 檔案：命中快取 vs 需重新編碼
    final_chunks: List[Dict[str, Any]] = []
    final_vectors_list: List[Any] = []
    new_file_states: Dict[str, Dict[str, Any]] = {}
    chunks_to_encode: List[Dict[str, Any]] = []
    newly_processed_files: List[str] = []
    cached_files_count = 0
    cached_chunks_count = 0

    if verbose:
        print("\n========================================================")
        print("🚀 開始建置/更新本地學術論文雙檔向量索引庫")
        print(f"📁 文獻來源：{EXTRACTED_DIR.resolve()}（共 {len(md_files)} 篇 Markdown 論文）")
        print(f"⚙️ 執行模式：{'【強制全量重建】(--force)' if force else '【智慧增量更新】(比對快取)'}")
        print("========================================================")
        sys.stdout.flush()

    file_iterator = tqdm(md_files, desc="📄 論文結構感知分塊與快取比對", unit="篇", file=sys.stdout) if verbose else md_files

    for md_file in file_iterator:
        fname = md_file.name
        fstat = md_file.stat()
        mtime = fstat.st_mtime
        size = fstat.st_size

        prev_state = existing_file_states.get(fname)
        is_cached = (
            not force
            and prev_state is not None
            and prev_state.get("mtime") == mtime
            and prev_state.get("size") == size
            and fname in existing_chunks_by_file
            and fname in existing_vectors_by_file
            and len(existing_chunks_by_file[fname]) == len(existing_vectors_by_file[fname])
            and len(existing_chunks_by_file[fname]) > 0
        )

        if is_cached:
            # 命中快取：直接沿用現有 chunks 與 npz 向量矩陣對應列
            reused_chunks = existing_chunks_by_file[fname]
            reused_vecs = existing_vectors_by_file[fname]
            final_chunks.extend(reused_chunks)
            final_vectors_list.extend(reused_vecs)
            new_file_states[fname] = prev_state
            cached_files_count += 1
            cached_chunks_count += len(reused_chunks)
        else:
            # 快取失效或新加入：重新切塊並標記待編碼
            fresh_chunks = chunk_markdown_file(md_file)
            if fresh_chunks:
                chunks_to_encode.extend(fresh_chunks)
                newly_processed_files.append(fname)
                new_file_states[fname] = {
                    "mtime": mtime,
                    "size": size,
                    "chunk_count": len(fresh_chunks)
                }

    # 3. 處理「無需任何重新編碼」的快速退出情況
    if not chunks_to_encode:
        # 檢查是否有被刪除的論文需要修剪（Prune）
        is_pruned = len(existing_chunks_by_file) > len(new_file_states)
        if is_pruned:
            final_mat = np.array(final_vectors_list, dtype=np.float32)
            index_payload = {
                "metadata": {
                    "total_papers": len(md_files),
                    "total_chunks": len(final_chunks),
                    "embedding_model": MODEL_NAME,
                    "embedding_dim": int(final_mat.shape[1]) if len(final_mat) > 0 else 768,
                    "embedding_file": VECTORS_FILE.name,
                    "storage_format": "decoupled_json_and_npz",
                    "last_updated": datetime.now().isoformat(),
                    "file_states": new_file_states
                },
                "chunks": final_chunks
            }
            INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(index_payload, f, ensure_ascii=False, indent=2)
            np.savez_compressed(VECTORS_FILE, embeddings=final_mat)

            _CACHED_PAYLOAD = index_payload
            _CACHED_VECTORS = final_mat
            _INDEX_MTIME = INDEX_FILE.stat().st_mtime
            _VECTORS_MTIME = VECTORS_FILE.stat().st_mtime

            if verbose:
                print(f"\n✅ 增量維護完成（已修剪過期檔案）：在庫 {len(md_files)} 篇論文全數命中快取，共 {len(final_chunks)} 個區塊，無需重複計算向量！\n")

            return {
                "status": "success",
                "mode": "incremental_prune",
                "message": f"增量維護完成（已清理已刪除檔案）：在庫 {len(md_files)} 篇論文全數命中快取，共 {len(final_chunks)} 個區塊，無需重複計算向量！",
                "total_papers": len(md_files),
                "total_chunks": len(final_chunks),
                "cached_papers": cached_files_count,
                "encoded_papers": 0,
                "index_file": str(INDEX_FILE),
                "vectors_file": str(VECTORS_FILE)
            }

        if verbose:
            print(f"\n⚡ 雙檔索引已是最新狀態：全數 {len(md_files)} 篇論文均命中快取（共 {cached_chunks_count} 個區塊），無需重複計算向量！\n")

        return {
            "status": "success",
            "mode": "cache_hit",
            "message": f"雙檔索引已是最新狀態：全數 {len(md_files)} 篇論文均命中快取（共 {cached_chunks_count} 個區塊），無需重複計算向量！",
            "total_papers": len(md_files),
            "total_chunks": len(final_chunks),
            "cached_papers": cached_files_count,
            "encoded_papers": 0,
            "index_file": str(INDEX_FILE),
            "vectors_file": str(VECTORS_FILE)
        }

    # 4. 僅對需要新計算向量的段落調用嵌入模型
    if verbose:
        print(f"\n🧠 載入嵌入模型 [{MODEL_NAME}] 進行稠密向量特徵編碼...")
        print(f"📊 待編碼文獻：{len(newly_processed_files)} 篇 | 待編碼區塊：{len(chunks_to_encode)} 個 (快取沿用：{cached_chunks_count} 個)")
        sys.stdout.flush()

    try:
        model = get_embedding_model()
    except ImportError as e:
        return {
            "status": "error",
            "message": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"加載嵌入模型 {MODEL_NAME} 失敗：{e}"
        }

    texts = [chunk["text"] for chunk in chunks_to_encode]
    batch_size = 16
    try:
        # 分批編碼新增或修改的文字段落，啟用 L2 歸一化與標準輸出 TQDM 進度條
        encoded_batches = []
        batch_starts = list(range(0, len(texts), batch_size))
        batch_iter = tqdm(batch_starts, desc="⚡ BGE-Base 稠密向量編碼", unit="批", file=sys.stdout) if verbose else batch_starts

        for start_idx in batch_iter:
            batch_texts = texts[start_idx : start_idx + batch_size]
            batch_vecs = model.encode(
                batch_texts,
                batch_size=len(batch_texts),
                show_progress_bar=False,
                normalize_embeddings=True
            )
            encoded_batches.append(batch_vecs)

        new_embeddings = np.vstack(encoded_batches) if encoded_batches else np.empty((0, 768), dtype=np.float32)
    except Exception as e:
        return {
            "status": "error",
            "message": f"向量編碼過程發生錯誤：{e}"
        }

    # 合併既有快取與新編碼區塊
    final_chunks.extend(chunks_to_encode)
    final_vectors_list.extend(new_embeddings)
    final_mat = np.array(final_vectors_list, dtype=np.float32)
    dim = int(final_mat.shape[1]) if len(final_mat) > 0 else 768

    # 5. 寫入雙檔解耦架構
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 檔案一：輕量 JSON 結構（無肥大浮點數陣列，僅存文字段落與元數據）
    index_payload = {
        "metadata": {
            "total_papers": len(md_files),
            "total_chunks": len(final_chunks),
            "embedding_model": MODEL_NAME,
            "embedding_dim": dim,
            "embedding_file": VECTORS_FILE.name,
            "storage_format": "decoupled_json_and_npz",
            "last_updated": datetime.now().isoformat(),
            "file_states": new_file_states
        },
        "chunks": final_chunks
    }
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_payload, f, ensure_ascii=False, indent=2)

    # 檔案二：NumPy 壓縮二進位檔案（存放形狀為 (N, 768) 之矩陣）
    np.savez_compressed(VECTORS_FILE, embeddings=final_mat)

    # 更新記憶體快取
    _CACHED_PAYLOAD = index_payload
    _CACHED_VECTORS = final_mat
    _INDEX_MTIME = INDEX_FILE.stat().st_mtime
    _VECTORS_MTIME = VECTORS_FILE.stat().st_mtime

    json_kb = INDEX_FILE.stat().st_size / 1024
    npz_kb = VECTORS_FILE.stat().st_size / 1024

    if verbose:
        print(f"\n💾 成功儲存【雙檔解耦向量資料庫】：")
        print(f"   • 文字元數據：{INDEX_FILE} ({json_kb:.1f} KB)")
        print(f"   • 密集向量檔：{VECTORS_FILE} ({npz_kb:.1f} KB, shape: {final_mat.shape})")
        print(f"🎉 索引完成！總文獻：{len(md_files)} 篇 | 總區塊：{len(final_chunks)} 個 | 向量維度：{dim} 維\n")

    mode_label = "全量強制重建" if force else "增量更新"
    return {
        "status": "success",
        "mode": "force_rebuild" if force else "incremental",
        "message": (
            f"成功完成【{mode_label}】雙檔向量索引！\n"
            f"• 沿用快取：{cached_files_count} 篇（{cached_chunks_count} 區塊）\n"
            f"• 新編碼：{len(newly_processed_files)} 篇（{len(chunks_to_encode)} 區塊）\n"
            f"• 文獻總計：{len(md_files)} 篇、共 {len(final_chunks)} 個語意區塊（{dim} 維）\n"
            f"• 儲存輸出：{INDEX_FILE.name}（結構化文字）+ {VECTORS_FILE.name}（二進位矩陣）"
        ),
        "index_file": str(INDEX_FILE),
        "vectors_file": str(VECTORS_FILE),
        "total_papers": len(md_files),
        "total_chunks": len(final_chunks),
        "cached_papers": cached_files_count,
        "encoded_papers": len(newly_processed_files),
        "encoded_chunks": len(chunks_to_encode),
        "embedding_model": MODEL_NAME,
        "embedding_dim": dim
    }


def search_index_data(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """在雙檔索引庫中依據查詢詞計算 BGE-M3 向量餘弦相似度，回傳 Top-K 精華段落"""
    try:
        import numpy as np
    except ImportError:
        return [{"error": "未檢測到 numpy 套件！請在終端機中執行：pip install numpy"}]

    if not INDEX_FILE.exists() or not VECTORS_FILE.exists():
        return [{"error": "尚未建立雙檔向量索引，請先呼叫 build_paper_index 工具建置索引。"}]

    payload, vectors_mat = load_index_and_vectors()
    if not payload or vectors_mat is None:
        return [{"error": "無法讀取向量索引檔案，請重新建置索引。"}]

    chunks = payload.get("chunks", [])
    if not chunks or len(chunks) != len(vectors_mat):
        return [{"error": "索引文字段落數與向量矩陣維度不匹配，請呼叫 build_paper_index(force=True) 重建索引。"}]

    cleaned_query = query.strip()
    if not cleaned_query:
        return [{"error": "查詢語句為空，請提供具體的學術問題或關鍵詞彙。"}]

    # 載入模型並計算查詢向量
    try:
        model = get_embedding_model()
    except ImportError as e:
        return [{"error": str(e)}]
    except Exception as e:
        return [{"error": f"加載嵌入模型失敗：{e}"}]

    try:
        query_vec = model.encode(cleaned_query, normalize_embeddings=True)
    except Exception as e:
        return [{"error": f"查詢向量化失敗：{e}"}]

    # 極速向量矩陣內積計算（由於兩者皆經過 L2 歸一化，相似度即等於向量內積）
    try:
        q_vec = np.array(query_vec, dtype=np.float32)
        sims = np.dot(vectors_mat, q_vec)
    except Exception as e:
        return [{"error": f"矩陣內積計算錯誤：{e}"}]

    if len(sims) == 0:
        return [{"message": "未能計算任何段落之相似度評分。"}]

    # 依相似度由高至低取得 Top-K 索引
    actual_top_k = min(top_k, len(sims))
    if len(sims) <= actual_top_k:
        top_indices = np.argsort(sims)[::-1]
    else:
        # 使用 argpartition 達成 O(N) 局部排序加速
        partition_indices = np.argpartition(sims, -actual_top_k)[-actual_top_k:]
        top_indices = partition_indices[np.argsort(sims[partition_indices])[::-1]]

    formatted_results = []
    for rank, idx in enumerate(top_indices, 1):
        score = float(sims[idx])
        chunk = chunks[idx]
        formatted_results.append({
            "rank": rank,
            "relevance_score": round(score, 4),
            "source_paper": chunk.get("file", ""),
            "section": chunk.get("section", ""),
            "content": chunk.get("text", ""),
            "chunk_id": chunk.get("chunk_id", "")
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
                    "version": "2.2.0"
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
                        "name": "search_paper_chunks",
                        "description": "使用 BAAI/bge-base-en-v1.5 稠密向量比對（768 維度），在已建立雙檔索引的論文庫中進行學術事實檢索，回傳最相關的原文精華段落、章節標籤與出處文獻。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "欲查詢的學術英文問題或概念關鍵詞組（若使用者以中文發問，Agent 必須先自動提煉為精確的學術英文關鍵詞，例如：'cognitive load measurement scale instrument'，以確保與 BGE-Base 英文向量及英文論文庫完美匹配）"
                                },
                                "top_k": {
                                    "type": "integer",
                                    "description": "回傳的最相關段落筆數（預設為 3）",
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

        if tool_name == "search_paper_chunks":
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
        cmd = sys.argv[1].lower()
        if cmd == "build":
            force_rebuild = "--force" in sys.argv or "-f" in sys.argv
            res = build_index_data(force=force_rebuild, verbose=True)
            if not res or res.get("status") != "success":
                print(f"❌ 索引建置失敗：{res.get('message') if res else '未知錯誤'}")
        elif cmd == "search":
            q = sys.argv[2] if len(sys.argv) > 2 else "cognitive load"
            print(json.dumps(search_index_data(q), ensure_ascii=False, indent=2))
        else:
            print(f"未知指令：{cmd}。用法：python scripts/paper_retriever_mcp.py [build [--force] | search <查詢詞>]")
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
