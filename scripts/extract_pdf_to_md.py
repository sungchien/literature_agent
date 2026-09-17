"""
scripts/extract_pdf_to_md.py

學術文獻 PDF 轉譯與文字清洗工具
用途：批次讀取 01_papers/raw_pdf/ 下的所有文獻，
      消除排版雜音與參考文獻清單，輸出純淨 Markdown 至 01_papers/extracted_text/
"""

import os
import re
import sys
from pathlib import Path

# 設定 Windows 終端輸出編碼
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# 定義工作區目錄常數
RAW_PDF_DIR = Path("01_papers/raw_pdf")
EXTRACTED_TEXT_DIR = Path("01_papers/extracted_text")

def clean_academic_markdown(md_text: str) -> str:
    """
    清洗學術文字噪音：
    1. 移除 References / Bibliography 之後的龐大引用列表
    2. 消除多餘的頁碼與出版聲明行
    3. 合併連續過多空白行
    """
    lines = md_text.split("\n")
    cleaned_lines = []
    
    # 常見參考文獻標題樣式
    ref_pattern = re.compile(r"^#{1,3}\s*(references|bibliography|works cited|參考文獻)", re.IGNORECASE)
    # 常見頁碼與無效噪音樣式
    noise_pattern = re.compile(r"^(page \d+|\d+\s*/\s*\d+|downloaded from|https?://doi\.org/)", re.IGNORECASE)

    for line in lines:
        stripped = line.strip()
        
        # 截斷檢測：一旦讀到 References 章節標題，終止後續解析以節省空間
        if ref_pattern.match(stripped):
            cleaned_lines.append("\n\n---\n*（備註：系統已自動截斷後續 References 引用列表，以維護上下文純淨度）*")
            break
            
        # 噪音濾除：跳過純頁碼與常見版權行
        if noise_pattern.match(stripped):
            continue
            
        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines)
    # 正規化多重空行，最多保留兩個換行
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result

def convert_all_pdfs():
    """批次將 raw_pdf 下的所有 PDF 轉換為乾淨 Markdown"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("[錯誤] 未檢測到 PyMuPDF 套件，請先執行：pip install PyMuPDF pymupdf4llm")
        return

    # 確保輸出目錄存在
    EXTRACTED_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_files = list(RAW_PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"[警告] 在 {RAW_PDF_DIR} 找不到任何 PDF 檔案，請先執行下載腳本。")
        return

    print(f"[進度] 開始批次轉譯學術文獻（共 {len(pdf_files)} 篇）...\n")

    for idx, pdf_path in enumerate(pdf_files, 1):
        target_md_path = EXTRACTED_TEXT_DIR / f"{pdf_path.stem}.md"
        print(f"[{idx}/{len(pdf_files)}] 正在解析：{pdf_path.name}")

        try:
            # 優先嘗試 pymupdf4llm 進行結構化轉譯
            import pymupdf4llm
            raw_md = pymupdf4llm.to_markdown(str(pdf_path))
        except Exception:
            # 若無 pymupdf4llm，降級使用標準 PyMuPDF 解析
            doc = fitz.open(pdf_path)
            pages_text = []
            for page_num, page in enumerate(doc):
                pages_text.append(f"## Page {page_num + 1}\n\n" + page.get_text())
            raw_md = "\n\n".join(pages_text)

        # 執行學術文字工程清洗
        cleaned_md = clean_academic_markdown(raw_md)

        # 寫入目標檔案
        with open(target_md_path, "w", encoding="utf-8") as f:
            f.write(cleaned_md)

        file_size_kb = target_md_path.stat().st_size / 1024
        print(f"   [成功] 轉譯成功！輸出檔案：{target_md_path.name} ({file_size_kb:.1f} KB)")

    print(f"\n[完成] 全數轉譯完成！所有乾淨文字檔已妥善存放於：{EXTRACTED_TEXT_DIR}")

if __name__ == "__main__":
    convert_all_pdfs()
