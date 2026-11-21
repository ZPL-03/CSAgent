"""将解析器返回的 HTML 单元格跨度转换为有明确列关系的 Markdown 表格。"""

from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString


class TableStructureError(ValueError):
    """显式行列跨度无法组成无歧义表格。"""


def _table_rows(table) -> list[list[str]]:
    if table.find("table") is not None:
        raise TableStructureError("nested_table")
    rows = table.find_all("tr")
    while rows and not rows[0].find_all(["th", "td"], recursive=False):
        rows.pop(0)
    if not rows:
        return []
    grid = [{} for _ in rows]
    spans = []
    header_end = 0
    header_open = True
    for row_index, row in enumerate(rows):
        cells = row.find_all(["th", "td"], recursive=False)
        is_header = row.parent.name == "thead" or bool(cells) and all(cell.name == "th" for cell in cells)
        if header_open and is_header:
            header_end = row_index + 1
        else:
            header_open = False
        group_end = row_index + 1
        while group_end < len(rows) and rows[group_end].parent is row.parent:
            group_end += 1
        column = 0
        for cell in cells:
            if cell.find(["td", "th", "tr"]) is not None:
                raise TableStructureError("nested_cell")
            raw_height, raw_width = str(cell.get("rowspan", "1")), str(cell.get("colspan", "1"))
            if not raw_height.isdecimal() or not raw_width.isdecimal():
                raise TableStructureError("invalid_span")
            height, width = int(raw_height) or group_end - row_index, int(raw_width)
            if width < 1 or width > 1000 or row_index + height > group_end:
                raise TableStructureError("span_out_of_bounds")
            while column in grid[row_index]:
                column += 1
            value = " ".join(cell.get_text(" ", strip=True).split()).replace("|", r"\|")
            identity = len(spans)
            spans.append((row_index, row_index + height))
            for i in range(row_index, row_index + height):
                for j in range(column, column + width):
                    if j in grid[i]:
                        raise TableStructureError("overlapping_span")
                    grid[i][j] = (identity, value)
            column += width
    if not spans:
        return []
    if not header_end:
        # 无 thead/th 时，首行的显式跨行决定表头深度，不从数值大小猜测列含义。
        header_end = max(end for start, end in spans if start == 0)
        while any(start < header_end < end for start, end in spans):
            header_end = max(end for start, end in spans if start < header_end)
    elif any(start < header_end < end for start, end in spans):
        raise TableStructureError("header_span_crosses_body")
    width = max(max(row, default=-1) for row in grid) + 1
    headers = []
    for column in range(width):
        labels = {}
        for row in grid[:header_end]:
            identity, value = row.get(column, (-1, ""))
            if value:
                labels[identity] = value
        headers.append(" / ".join(labels.values()))
    # 只有显式合并单元格共享值，空单元格不补写材料参数。
    body = [[row.get(column, (-1, ""))[1] for column in range(width)] for row in grid[header_end:]]
    return [headers, ["---"] * width, *body]


def html_tables_to_markdown(text: str) -> str | None:
    """仅替换 HTML 表格，保留同一块的其他原文；无表格时返回 None。"""
    soup = BeautifulSoup(text, "html.parser")
    tables = [table for table in soup.find_all("table") if table.find_parent("table") is None]
    if not tables:
        return None
    for table in tables:
        rows = _table_rows(table)
        rendered = "\n".join("| " + " | ".join(row) + " |" for row in rows)
        table.replace_with(NavigableString("\n\n" + rendered + "\n\n"))
    return soup.decode(formatter=None).strip()
