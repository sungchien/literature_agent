"""
clean_markdown.py

Markdown 前處理工具

功能：

1. 移除行尾空白
2. 合併過多空白行
3. 標準化 Heading 前後空白
4. 統一列表格式
5. 修正 Code Block 前後空白
6. 移除 UTF-8 BOM
7. 保留 Markdown 原有內容
8. 修正 Table 前後空白行（避免 Markdown 預覽模式將接續文字誤判為表格最後一列）

使用方式：

python clean_markdown.py input.md

或

python clean_markdown.py input.md output.md
"""

from pathlib import Path
import re
import sys


# --------------------------------------------------------
# 基本清理
# --------------------------------------------------------

def remove_trailing_spaces(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines())


def normalize_blank_lines(text: str) -> str:
    """
    最多保留兩個連續空白行
    """
    return re.sub(r"\n{3,}", "\n\n", text)


# --------------------------------------------------------
# Heading
# --------------------------------------------------------

def normalize_headings(text: str) -> str:
    lines = text.split("\n")

    new_lines = []

    for line in lines:

        if re.match(r"^#{1,6}\S", line):
            hashes = re.match(r"^(#+)", line).group(1)
            title = line[len(hashes):].strip()
            line = f"{hashes} {title}"

        new_lines.append(line)

    return "\n".join(new_lines)


# --------------------------------------------------------
# List
# --------------------------------------------------------

def normalize_lists(text: str) -> str:

    lines = text.split("\n")

    result = []

    for line in lines:

        line = re.sub(r"^(\s*)[-*]\s+", r"\1- ", line)

        result.append(line)

    return "\n".join(result)


# --------------------------------------------------------
# Code Block
# --------------------------------------------------------

def normalize_code_blocks(text: str) -> str:

    lines = text.split("\n")

    output = []

    previous_is_code = False

    for line in lines:

        if line.startswith("```"):

            if output and output[-1] != "":
                output.append("")

            output.append(line)

            previous_is_code = not previous_is_code

            continue

        output.append(line)

    return "\n".join(output)


# --------------------------------------------------------
# UTF-8 BOM
# --------------------------------------------------------

def remove_bom(text: str):

    return text.lstrip("\ufeff")


# --------------------------------------------------------
# KaTeX Sanitizer
# --------------------------------------------------------

def normalize_katex(text: str) -> str:
    r"""
    修復因 Python 反斜線轉譯導致的 KaTeX 破損問題：
    1. 修復 \text, \frac, \beta, \right, \left, \times, \approx, \rightarrow, \Longleftrightarrow
    2. 確保獨立區塊公式 $$...$$ 內部無空白行，且上下維持單一空行
    """
    # 修正常見的 ASCII 轉譯破損
    text = text.replace(' eta', '\\beta').replace('\x08eta', '\\beta')
    text = text.replace('  pprox', ' \\approx ').replace('\x07pprox', '\\approx')
    text = text.replace(' ightarrow', '\\rightarrow').replace('\righterarrow', '\\rightarrow')
    text = text.replace(' ongleftrightarrow', '\\Longleftrightarrow')

    text = re.sub(r'[\x09\t\r\n\f]ext\{', r'\\text{', text)
    text = re.sub(r'[\x0c\f\r\n\t]rac\{', r'\\frac{', text)
    text = re.sub(r'[\x0d\r\n\t]ight\)', r'\\right)', text)
    text = re.sub(r'[\x0c\f\r\n\t]eft\(', r'\\left(', text)
    text = re.sub(r'[\x09\t\r\n\f]imes', r'\\times', text)

    # 修正區塊公式 $$...$$ 內部的換行破損
    def clean_display_math(match):
        inner = match.group(1).strip()
        inner_clean = re.sub(r'\s*\n\s*', ' ', inner)
        return f"\n\n$${inner_clean}$$\n\n"

    text = re.sub(r'\$\$\s*\n?([\s\S]*?)\n?\s*\$\$', clean_display_math, text)

    return text


# --------------------------------------------------------
# Bold & Blockquote & Table Sanitizers
# --------------------------------------------------------

def normalize_bold_spacing(text: str) -> str:
    """
    修正 VS Code Preview 中粗體字標記 ** 前未有空白導致無法渲染為粗體的問題。
    例如：：**粗體** -> ： **粗體**
    """
    lines = text.split("\n")
    new_lines = []
    in_code = False

    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            new_lines.append(line)
            continue

        if in_code:
            new_lines.append(line)
            continue

        # 修正全形標點/括號/冒號後直接黏著 ** 的情況
        line = re.sub(r'([：；，。】\)]|\*\*)\*\*([^\s*])', r'\1 **\2', line)
        # 修正中文漢字直接黏著 ** 的情況
        line = re.sub(r'([\u4e00-\u9fff])\*\*([\u4e00-\u9fff\w]+?)\*\*', r'\1 **\2**', line)
        new_lines.append(line)

    return "\n".join(new_lines)


def normalize_blockquotes(text: str) -> str:
    """
    修復加色區塊 (>) 中間出現空白行導致 VS Code 解析器將其拆分為多個獨立框線的問題。
    """
    lines = text.split("\n")
    final_lines = []
    in_bq = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith(">"):
            in_bq = True
            final_lines.append(line)
        elif in_bq:
            if stripped == "":
                # 檢查後續是否有 > 開頭的引言行
                next_is_bq = False
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith(">"):
                        next_is_bq = True
                        break
                    elif lines[j].strip() != "":
                        break
                if next_is_bq:
                    final_lines.append(">")
                else:
                    in_bq = False
                    final_lines.append(line)
            else:
                in_bq = False
                final_lines.append(line)
        else:
            final_lines.append(line)

    return "\n".join(final_lines)


def normalize_tables(text: str) -> str:
    """
    1. 移除 Markdown 表格內部的多餘空白行（防範表格分裂與雙倍行距問題）。
    2. 確保表格結束後若緊接著一般文字、標題或清單，兩者之間必須有且僅有一個空白行分隔，
       防範 Markdown 預覽模式（如 VS Code、GitHub、Puppeteer）將後續文字誤判為表格的最後一列。
    3. 確保表格開始前若有文字，亦保留一個空白行分隔。
    """
    lines = text.split("\n")
    new_lines = []
    in_table = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        is_table_row = stripped.startswith('|') and '|' in stripped[1:]

        if is_table_row:
            if not in_table:
                # 表格開始：若前一行不是空白行且不是標題，確保前方有空行分隔
                if new_lines and new_lines[-1].strip() != "" and not new_lines[-1].strip().startswith("#"):
                    new_lines.append("")
                in_table = True
            new_lines.append(line)
        elif in_table:
            if stripped == "":
                # 檢查後續是否有接續的表格行（處理表格內部意外夾雜的空行）
                next_is_table = False
                for j in range(i + 1, len(lines)):
                    next_stripped = lines[j].strip()
                    if next_stripped == "":
                        continue
                    if next_stripped.startswith('|') and '|' in next_stripped[1:]:
                        next_is_table = True
                    break

                if next_is_table:
                    # 表格內部意外空行，予以移除
                    continue
                else:
                    # 表格正式結束
                    in_table = False
                    if new_lines and new_lines[-1].strip() != "":
                        new_lines.append("")
                    continue
            else:
                # 表格結束，後面緊接著非空白行（文字、標題、清單等）
                # 核心修復：在表格與接續內容之間強制補入一個空白行
                in_table = False
                if new_lines and new_lines[-1].strip() != "":
                    new_lines.append("")
                new_lines.append(line)
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def remove_icons_and_emojis(text: str) -> str:
    """
    依專案規範：講義內容與程式碼輸出嚴禁使用 Icons 與 Emoji。
    將常見裝飾性 Emoji/Icons 替換為空字串或中英文純文字標籤。
    """
    icon_replacements = {
        "\U0001F50D": "[查詢]",
        "\U0001F4C5": "",
        "\U0001F3AF": "[目標]",
        "\u274C": "[錯誤]",
        "\u26A0\uFE0F": "[警告]",
        "\u26A0": "[警告]",
        "\u2705": "[成功]",
        "\U0001F512": "[封閉]",
        "\U0001F4E5": "[下載]",
        "\u2728": "",
        "\U0001F4CB": "[清單]",
        "\U0001F449": "",
        "\U0001F680": "[啟動]",
        "\U0001F4CA": "[統計]",
        "\U0001F4CC": "[指引]",
        "\U0001F4A1": "[提示]",
        "\U0001F389": "",
        "\U0001F4D1": "",
        "\U0001F6E0\uFE0F": "[工具]",
        "\U0001F6E0": "[工具]",
    }
    for icon, repl in icon_replacements.items():
        text = text.replace(icon, repl)

    # 清除其餘通用 Unicode Emoji 與雜項裝飾符號
    emoji_pattern = re.compile(
        r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]'
    )
    text = emoji_pattern.sub('', text)
    return text


def normalize_literal_dollars(text: str) -> str:
    r"""
    轉譯純文字中的金額美金符號 $50 -> \$50，防範同一段落多個 $ 被 VS Code 誤判為 KaTeX 數學區塊。
    """
    text = re.sub(r'(?<!\\)\$(\d+(?:,\d+)*(?:\.\d+)?)\s*(元|位|人|秒|分|倍|%|萬)?', r'\\$\1 \2', text)
    text = re.sub(r'\\\$(\d+(?:,\d+)*(?:\.\d+)?)\s+', r'\\$\1 ', text)
    return text


# --------------------------------------------------------
# Main Pipeline
# --------------------------------------------------------

def clean_markdown(text: str):

    text = remove_bom(text)

    text = remove_trailing_spaces(text)

    text = remove_icons_and_emojis(text)

    text = normalize_headings(text)

    text = normalize_lists(text)

    text = normalize_code_blocks(text)

    text = normalize_katex(text)

    text = normalize_tables(text)

    text = normalize_bold_spacing(text)

    text = normalize_blockquotes(text)

    text = normalize_literal_dollars(text)

    text = normalize_blank_lines(text)


    return text.strip() + "\n"


# --------------------------------------------------------
# CLI
# --------------------------------------------------------

def main():

    if len(sys.argv) < 2:

        print(
            "Usage:\n"
            "python clean_markdown.py input.md [output.md]"
        )

        sys.exit(1)

    input_file = Path(sys.argv[1])

    if len(sys.argv) >= 3:

        output_file = Path(sys.argv[2])

    else:

        output_file = input_file

    text = input_file.read_text(
        encoding="utf-8"
    )

    cleaned = clean_markdown(text)

    with open(output_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(cleaned)

    print(f"Markdown cleaned: {output_file}")


if __name__ == "__main__":
    main()