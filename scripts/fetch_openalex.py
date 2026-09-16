"""
scripts/fetch_openalex.py

OpenAlex 學術文獻自動化檢索與 PDF 下載工具
用途：依據關鍵字檢索具備 Open Access 全文之論文，並依工程標準下載至 01_papers/raw_pdf/
"""

import os
import re
import sys
import json
import requests
from pathlib import Path

# 定義工作區目錄常數
RAW_PDF_DIR = Path("01_papers/raw_pdf")
METADATA_FILE = Path("01_papers/downloaded_metadata.json")

def sanitize_filename(name: str) -> str:
    """清理檔名中的非法字元，替換為安全字元"""
    return re.sub(r'[\\/*?:"<>| ]', '_', name)

def search_and_download_papers(query: str, max_results: int = 5, start_year: int = 2022):
    """
    透過 OpenAlex API 搜尋論文並自動下載 OA PDF
    """
    # 確保儲存目錄存在
    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 正在向 OpenAlex 檢索主題：『{query}』...")
    print(f"📅 限制年份：{start_year} 年至今 | 🎯 目標篇數：{max_results} 篇")
    
    # 組裝 OpenAlex REST API 請求端點
    api_url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "filter": f"publication_year:{start_year}-2026,is_oa:true,has_fulltext:true",
        "sort": "cited_by_count:desc",
        "per-page": max_results * 2  # 多抓取一倍筆數，以防部分 PDF 連結失效
    }
    
    # 遵守 OpenAlex 禮貌原則（Polite Pool）：加入 User-Agent
    headers = {
        "User-Agent": "ThesisLiteratureAgent/1.0 (mailto:student@university.edu)"
    }
    
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ API 請求失敗：{e}")
        return

    results = data.get("results", [])
    if not results:
        print("⚠️ 未找到符合條件的開放取用論文，請嘗試調整檢索關鍵字。")
        return

    downloaded_records = []
    success_count = 0

    for item in results:
        if success_count >= max_results:
            break

        title = item.get("title") or "Untitled"
        pub_year = item.get("publication_year") or "UnknownYear"
        cited_count = item.get("cited_by_count", 0)
        
        # 提取第一作者姓氏
        authorships = item.get("authorships", [])
        if authorships and "author" in authorships[0]:
            first_author = authorships[0]["author"].get("display_name", "Author").split()[-1]
        else:
            first_author = "Author"

        # 取得 PDF 下載直連網址
        best_oa_location = item.get("best_oa_location") or {}
        pdf_url = best_oa_location.get("pdf_url") or item.get("open_access", {}).get("oa_url")

        if not pdf_url or not pdf_url.startswith("http"):
            continue

        # 產生標準化安全檔名：年份_第一作者_標題縮寫.pdf
        short_title = sanitize_filename(title[:35].strip())
        safe_author = sanitize_filename(first_author)
        filename = f"{pub_year}_{safe_author}_{short_title}.pdf"
        target_path = RAW_PDF_DIR / filename

        print(f"\n📥 [{success_count + 1}/{max_results}] 發現目標論文：")
        print(f"   篇名：{title}")
        print(f"   年份：{pub_year} | 作者：{first_author} | 被引用數：{cited_count}")
        print(f"   PDF 來源：{pdf_url}")

        # 下載 PDF 串流
        try:
            download_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            pdf_resp = requests.get(pdf_url, headers=download_headers, stream=True, timeout=20)
            
            # 檢查是否為真正的 PDF 格式
            content_type = pdf_resp.headers.get("Content-Type", "")
            if pdf_resp.status_code == 200 and ("pdf" in content_type or pdf_url.lower().endswith(".pdf")):
                with open(target_path, "wb") as f:
                    for chunk in pdf_resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"   ✅ 下載成功！儲存至：{target_path}")
                
                # 記錄元數據
                downloaded_records.append({
                    "filename": filename,
                    "title": title,
                    "first_author": first_author,
                    "year": pub_year,
                    "doi": item.get("doi"),
                    "cited_by_count": cited_count,
                    "openalex_id": item.get("id"),
                    "pdf_url": pdf_url
                })
                success_count += 1
            else:
                print(f"   ⚠️ 跳過：遠端伺服器回傳格式非 PDF（Content-Type: {content_type}）。")
        except Exception as err:
            print(f"   ❌ 下載失敗：{err}")

    # 保存元數據清單供後續章節使用
    if downloaded_records:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(downloaded_records, f, ensure_ascii=False, indent=2)
        print(f"\n✨ 任務完成！共成功下載 {success_count} 篇文獻。")
        print(f"📑 元數據已寫入索引檔：{METADATA_FILE}")
    else:
        print("\n⚠️ 本次檢索未成功下載任何 PDF，可能受出版商防爬蟲機制限制，建議更換關鍵字。")

if __name__ == "__main__":
    search_topic = "AI Agents in Higher Education scaffolding"
    if len(sys.argv) > 1:
        search_topic = " ".join(sys.argv[1:])
    search_and_download_papers(search_topic, max_results=5, start_year=2022)
