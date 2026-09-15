import os
import sys

def convert_pdf_to_md(pdf_path):
    """
    使用 PyMuPDF (fitz) 將 PDF 檔案內容轉成 Markdown 格式並儲存為同名 .md 檔
    """
    try:
        import fitz  # PyMuPDF 套件
    except ImportError:
        print("❌ 未檢測到 PyMuPDF 套件，請先執行命令安裝：pip install PyMuPDF")
        return None

    # 優先嘗試使用 pymupdf4llm 轉 Markdown (若有安裝)，否則使用內建 fitz get_text
    try:
        import pymupdf4llm
        md_content = pymupdf4llm.to_markdown(pdf_path)
    except Exception:
        doc = fitz.open(pdf_path)
        md_pages = []
        for i, page in enumerate(doc):
            try:
                # fitz 的 page.get_text("markdown") 可直接輸出 Markdown 格式
                text = page.get_text("markdown")
            except Exception:
                text = page.get_text("text")
            md_pages.append(f"## Page {i + 1}\n\n{text}")
        md_content = "\n\n".join(md_pages)

    # 產出 .md 檔案檔名（與原 PDF 同檔名，副檔名改為 .md）
    base_name = os.path.splitext(pdf_path)[0]
    md_filepath = f"{base_name}.md"

    with open(md_filepath, "w", encoding="utf-8") as f:
        f.write(md_content)

    return md_filepath

def search_and_convert_weekly_pdf(week_input, folder_path="."):
    """
    根據輸入週次比對檔名開頭，存在則轉存為 Markdown，不存在則提示沒有發現當週講義。
    """
    # 自動將輸入補齊為兩位數字 (例如 '2' 轉為 '02')
    week_str = str(week_input).strip().zfill(2)

    matched_files = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf") and filename.startswith(week_str):
            matched_files.append(filename)

    # 比對發現沒有相對應的檔案
    if not matched_files:
        print("沒有發現當週講義。")
        return

    # 比對發現有對應檔案
    for pdf_file in matched_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        print(f"✅ 發現當週講義檔名：{pdf_file}")
        print("正在使用 PyMuPDF 轉換為 Markdown 格式...")
        
        md_result = convert_pdf_to_md(pdf_path)
        if md_result:
            print(f"✨ 轉換成功！已儲存至：{md_result}")

def main():
    print("========================================")
    print("  當週課程 PDF 轉 Markdown 工具 (PyMuPDF)")
    print("========================================")

    while True:
        user_input = input("\n請輸入代表週次的數字 (02到16，輸入 q 離開): ").strip()

        if user_input.lower() in ['q', 'exit', 'quit']:
            print("程式已結束。")
            break

        if not user_input.isdigit():
            print("請輸入有效的數字！")
            continue

        search_and_convert_weekly_pdf(user_input)

if __name__ == "__main__":
    main()
