from __future__ import annotations

"""标记检索证据的解析完整性与适用范围，不补写公式、单位或试验条件。"""

import re
from typing import Any


QUALITY_VERSION = "3"
QUALITY_FIELDS = [
    "content_quality_version", "content_quality_issues", "retrieval_eligible",
    "evidence_kind", "evidence_usage", "applicability_context", "table_evidence",
]
FORMULA_MISSING = re.compile(r"formula[-_ ]not[-_ ]decoded|formula[-_ ](?:missing|unrecognized)", re.I)
TABLE_CAPTION = re.compile(r"^\s*(?:Table\s+|表\s*)\d+(?:[.\-－]\d+)*\b", re.I)
APPROXIMATION = re.compile(
    r"近似|忽略不计|可以忽略|可忽略|可视为|相比很小|一般很小|"
    r"\b(?:approximately|approximation|negligible|neglected|approximated)\b", re.I,
)
CONDITION = re.compile(
    r"当.{1,100}时|仅适用|适用于|前提|条件下|假设|对于|在.{1,80}范围|"
    r"\b(?:provided that|assuming|under|valid for|subject to|for the case|if|when)\b", re.I,
)
DEFINITION = re.compile(
    r"定义|分别代表|分别表示|本构|应力.{0,5}应变关系|式中|其中|"
    r"\b(?:defined as|denotes|constitutive|where)\b", re.I,
)
PERFORMANCE_TABLE = re.compile(r"buckling|\bload\b|pressure|strength|屈曲|载荷|承载|强度|压力", re.I)
UNIT = re.compile(
    r"(?<![A-Za-z])(?:[GMkmunµμ]?Pa|[kmunµμ]?N|[cmunµμ]?m|kg|g|s|Hz|K|J|W)(?![A-Za-z0-9_])|"
    r"%|‰|°|无量纲|层数|数量|dimensionless|non[- ]?dimensional|\(\s*[-–]\s*\)|\b(?:ratio|BLF|count|number)\b", re.I,
)
NUMBER = re.compile(r"(?<![A-Za-z0-9])[-+−]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
GENERIC_HEADER = re.compile(r"^(?:col(?:umn)?\s*\d*|unnamed(?::\s*\d+)?|列\s*\d*|[-–—]+)?$", re.I)
MATRIX = re.compile(
    r"\\begin\s*\{(array|[bpBvV]?matrix)\}\s*(?:\{[lcr|\s]+\})?(.*?)\\end\s*\{\1\}", re.S,
)
INDEXED_CELL = re.compile(r"(?:\\bar\{)?([A-Za-z])\}?_\{?(\d)(\d)\}?")
MATERIAL_HEADER = re.compile(r"^(?:materials?|composites?|材料(?:体系|牌号|名称|型号)?|材质)$", re.I)
IDENTIFIER_HEADER = re.compile(
    r"^(?:case|id|no\.?|mode|specimen|sample|materials?|composites?|layup|stacking sequence|"
    r"stiffener type|description|序号|编号|试件|模态|材料(?:体系|牌号|名称|型号)?|材质|铺层|说明)$", re.I,
)
ELASTIC_HEADER = re.compile(r"模量|modulus|^[EG](?:[123]{1,2})\b", re.I)
POISSON_HEADER = re.compile(r"泊松比|poisson(?:['’]s)?\s*ratio", re.I)
POISSON_SYMBOL = re.compile(r"(?:v|u|nu|ν)[123]{2}", re.I)
ROW_CONDITIONS = {
    "geometry": re.compile(r"长度|宽度|厚度|半径|直径|高度|跨距|length|width|thickness|radius|diameter|height|span", re.I),
    "layup": re.compile(r"^铺层(?:$|[（(]|顺序|角|方案)|角度|layup|stacking|angle", re.I),
    "loading": re.compile(r"工况|加载方式|载荷类型|载荷方向|边界条件|load case|loading|boundary|support", re.I),
}


def formula_quality_issues(text: str) -> list[str]:
    """检查缺失占位和可直接核对的矩阵行列结构，不猜测应变符号的含义。"""
    issues: set[str] = set()
    if FORMULA_MISSING.search(text):
        issues.add("formula_not_decoded")
    for match in MATRIX.finditer(text):
        body = match.group(2)
        if r"\begin" in body:
            continue
        rows = [re.split(r"(?<!\\)&", row.strip()) for row in re.split(r"\\\\(?:\[[^\]]*\])?", body) if row.strip()]
        if len({len(row) for row in rows}) > 1:
            issues.add("matrix_shape_inconsistent")
            continue
        size = len(rows)
        if size < 3 or any(len(row) != size for row in rows):
            continue
        cells = [[INDEXED_CELL.fullmatch(re.sub(r"\s+", "", cell)) for cell in row] for row in rows]
        # 只有每个元素都是两位索引且对角线给出坐标轴时，才检查索引位置。
        # C12 与 C21 均允许；数值矩阵、稀疏矩阵和一般表达式不套用此规则。
        if not all(all(row) for row in cells):
            continue
        axes = []
        for index in range(size):
            diagonal = cells[index][index]
            if diagonal.group(2) != diagonal.group(3):
                break
            axes.append(diagonal.group(2))
        if len(axes) != size:
            continue
        if any(
            sorted((cell.group(2), cell.group(3))) != sorted((axes[i], axes[j]))
            for i, row in enumerate(cells) for j, cell in enumerate(row)
        ):
            issues.add("matrix_index_inconsistent")
    return sorted(issues)


def scope_passages(text: str) -> list[str]:
    """保留含条件或近似判断的完整原文段落，供检索和图谱共同携带。"""
    return list(dict.fromkeys(
        part.strip() for part in re.split(r"\n\s*\n", text)
        if part.strip() and not part.lstrip().startswith(("|", "$$"))
        and (APPROXIMATION.search(part) or CONDITION.search(part))
    ))


def markdown_tables(text: str) -> list[tuple[int, int, list[list[str]]]]:
    """返回表格行区间和单元格，区间用于保留原文顺序及列投影。"""
    lines = text.splitlines()
    tables = []
    start = 0
    while start < len(lines):
        if not lines[start].strip().startswith("|"):
            start += 1
            continue
        end = start
        while end < len(lines) and lines[end].strip().startswith("|") and lines[end].strip().endswith("|"):
            end += 1
        rows = [[cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip()[1:-1])] for line in lines[start:end]]
        if len(rows) >= 3 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1]):
            tables.append((start, end, rows))
        start = max(start + 1, end)
    return tables


def table_evidence(text: str) -> list[dict[str, Any]]:
    """绑定列单位、无量纲定义和逐行条件，区分材料参数与结构性能结果。"""
    result = []
    for _, _, rows in markdown_tables(text):
        header, _, *data = rows
        material_columns = [i for i, name in enumerate(header) if MATERIAL_HEADER.fullmatch(name)]
        identifier_columns = [i for i, name in enumerate(header) if IDENTIFIER_HEADER.fullmatch(name)]
        elastic_columns = [i for i, name in enumerate(header) if ELASTIC_HEADER.search(name)]
        # 裸符号 u12 也可能表示位移；仅在成组弹性参数中识别为泊松比。
        dimensionless_columns = [i for i, name in enumerate(header) if POISSON_HEADER.search(name) or (
            len(elastic_columns) >= 2 and POISSON_SYMBOL.fullmatch(re.sub(r"[\s${}_\\]", "", name))
        )]
        # 数量单元格从数值开始；标准编号、材料牌号等文本中的数字不构成量纲缺失。
        numeric_cells_by_column = {
            i: [row[i] for row in data if i < len(row) and NUMBER.match(row[i].lstrip("$ "))]
            for i in range(len(header))
        }
        numeric = [i for i, cells in numeric_cells_by_column.items() if cells]
        numeric = [i for i in numeric if i not in identifier_columns]
        missing_headers = [i for i in numeric if GENERIC_HEADER.fullmatch(header[i]) or NUMBER.fullmatch(header[i])]
        missing_units = []
        for i in numeric:
            # 子表头中的独立单位可以绑定本列，数据行内单位要求逐行明确。
            subheader = data[0][i] if data and i < len(data[0]) else ""
            unit_row = bool(subheader and not NUMBER.search(subheader) and UNIT.search(subheader))
            numeric_cells = numeric_cells_by_column[i]
            if i not in dimensionless_columns and not UNIT.search(header[i]) and not unit_row and not all(UNIT.search(cell) for cell in numeric_cells):
                missing_units.append(i)
        conditions = {
            group: [i for i, name in enumerate(header) if pattern.search(name)]
            for group, pattern in ROW_CONDITIONS.items()
        }
        conditions["material"] = material_columns
        # 仅用具有值且量纲可判定的条件列；两列几何尺寸仍属于同一类条件。
        valid_conditions = {group: [i for i in indexes if i not in missing_units and i not in missing_headers]
                            for group, indexes in conditions.items()}
        observations = [row for row in data if any(i < len(row) and NUMBER.search(row[i]) for i in numeric)]
        row_groups = [{group for group, indexes in valid_conditions.items()
                       if any(i < len(row) and row[i] for i in indexes)} for row in observations]
        row_context = bool(row_groups) and all(
            len(groups) >= 2 and groups & {"geometry", "loading"} for groups in row_groups
        )
        material_properties = bool(material_columns and observations) and all(
            any(i < len(row) and row[i] for i in material_columns) for row in observations
        ) and len(elastic_columns) >= 2 and not any(
            conditions[group] for group in ("geometry", "layup", "loading")
        )
        condition_required = bool(PERFORMANCE_TABLE.search(text)) and not material_properties
        result.append({
            "headers": header, "numeric_columns": numeric,
            "structure_issues": table_structure_issues(rows, numeric),
            "identifier_columns": identifier_columns, "dimensionless_columns": dimensionless_columns,
            "missing_header_columns": missing_headers, "missing_unit_columns": missing_units,
            "table_role": "material_properties" if material_properties else "result_table" if condition_required else "other",
            "condition_required": condition_required,
            "condition_columns": valid_conditions,
            "condition_context_present": bool(CONDITION.search(text)) or row_context,
            "condition_context": scope_passages(text),
            "usage": "source_conditions_only",
        })
    return result


def table_structure_issues(rows: list[list[str]], numeric: list[int]) -> list[str]:
    """列宽必须一致；残留在数据区的多列子表头不能作为数值行使用。"""
    if any(len(row) != len(rows[0]) for row in rows):
        return ["table_row_width_inconsistent"]

    def scalar(value: str) -> bool:
        return bool(NUMBER.fullmatch(re.sub(r"[\s$]", "", UNIT.sub("", value))))

    def unit_label(value: str) -> bool:
        for candidate in (value, re.sub(r"\s*\([^)]*\)\s*$", "", value)):
            tail = re.sub(r"\\(?:mathrm|textrm|text)\b", "", candidate)
            tail = re.sub(r"°\s*[CF]", "", tail)
            tail = re.sub(r"(?<=[A-Za-z])[-+−]?[0-9⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+", "", tail)
            tail = UNIT.sub("", tail)
            if UNIT.search(candidate) and not re.sub(r"[\s${}\\()[\]/·.*^0-9+−–-]", "", tail):
                return True
        return False

    # 横向规格、纵向属性的表不采用逐列观测的表头判据。
    if sum(scalar(value) for value in rows[0]) >= 2:
        return []
    observed = [index for index in numeric if any(scalar(row[index]) for row in rows[2:])]
    for row in rows[2:]:
        values = [row[index].strip().strip("$").strip() for index in observed]
        if any(re.match(r"^(?:[<>≤≥≈~]\s*)?[-+−]?(?:\d|\.\d)", value) for value in values):
            break
        labels = 0
        for index, value in zip(observed, values):
            header = rows[0][index]
            quantitative = UNIT.search(header) or UNIT.search(value) or "$" in row[index] or rows[0].count(header) > 1
            if quantitative and not unit_label(value) and re.search(r"[A-Za-z\u0370-\u03ff\u3400-\u9fff]", value):
                labels += 1
        if labels >= 2:
            return ["table_header_alignment_ambiguous"]
    return []


def project_table_columns(text: str, quality: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    """保留有依据的列作为独立证据，完整原表仍由调用方保存到待核对集。"""
    issues = set(quality["content_quality_issues"])
    tables = markdown_tables(text)
    if not issues or not issues <= {"table_headers_missing", "table_units_missing"} or len(tables) != 1:
        return None
    table = quality["table_evidence"][0]
    if table["table_role"] not in {"material_properties", "result_table"}:
        return None
    start, end, rows = tables[0]
    headers, _, *data = rows
    if any(len(row) != len(headers) for row in rows):
        return None
    excluded = set(table["missing_header_columns"]) | set(table["missing_unit_columns"])
    # 空分隔列及无数据列不进入视图，避免把侧边统计布局当成材料参数。
    selected = [i for i, name in enumerate(headers) if i not in excluded and name and any(row[i] for row in data)]
    identifiers = set(table["identifier_columns"]) & set(selected)
    if not identifiers or not (set(table["numeric_columns"]) & set(selected)):
        return None
    if not all(any(row[i] for i in identifiers) for row in data):
        return None
    rendered = ["| " + " | ".join(row[i] for i in selected) + " |" for row in rows]
    lines = text.splitlines()
    projected = "\n".join([*lines[:start], *rendered, *lines[end:]])
    return projected, {
        "source_column_indices": selected,
        "excluded_columns": [{"index": i, "header": headers[i], "issues": [
            issue for issue, indexes in (("table_headers_missing", table["missing_header_columns"]),
                                         ("table_units_missing", table["missing_unit_columns"])) if i in indexes
        ]} for i in sorted(excluded)],
    }

def assess_content(text: str, *, inherited_issues: list[str] | None = None) -> dict[str, Any]:
    """返回可序列化质量元数据；语法完整不表示公式已获科学正确性验证。"""
    issues = set(inherited_issues or []) | set(formula_quality_issues(text))
    tables = table_evidence(text)
    for table in tables:
        issues.update(table["structure_issues"])
        if table["missing_header_columns"]:
            issues.add("table_headers_missing")
        if table["missing_unit_columns"]:
            issues.add("table_units_missing")
        if table["numeric_columns"] and table["condition_required"] and not table["condition_context_present"]:
            issues.add("table_conditions_missing")
    scope = scope_passages(text)
    kind = (
        "approximation" if APPROXIMATION.search(text) else
        "table" if tables else
        "definition" if DEFINITION.search(text) else
        "conditional" if scope else
        "formula" if "$$" in text or r"\[" in text else "text"
    )
    return {
        "content_quality_version": QUALITY_VERSION,
        "content_quality_issues": sorted(issues),
        "retrieval_eligible": not issues,
        "evidence_kind": kind,
        "evidence_usage": "review_required" if issues else "source_conditions_only" if tables or scope else "reference",
        "applicability_context": scope,
        "table_evidence": tables,
    }
