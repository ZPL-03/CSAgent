"""核查表头坐标、列单位和用户上传证据状态。"""

import hashlib
import json
from pathlib import Path

import pytest

from core.knowledge_ingestion import KnowledgeIngestionService
from core.knowledge_quality import assess_content, markdown_tables, project_table_columns
from core.retrieval_evidence import render_evidence
from core.table_structure import TableStructureError, html_tables_to_markdown


MATERIAL_TABLE = """<table>
<tr><td rowspan="2">材料</td><td colspan="2">弹性模量/GPa</td><td rowspan="2">剪切模量/GPa</td><td colspan="2">泊松比</td></tr>
<tr><td>纵向 $E_f$</td><td>横向 $E_{2f}$</td><td>$v_{12f}$</td><td>$v_{23f}$</td></tr>
<tr><td>纤维</td><td>233</td><td>23.1</td><td>8.96</td><td>0.2</td><td>0.4</td></tr>
<tr><td>基体</td><td></td><td>4.62</td><td>8.27</td><td colspan="2">0.36</td></tr>
</table>"""


def test_upload_multilevel_header_preserves_values_units_and_original(tmp_path):
    source = tmp_path / "material.md"
    source.write_text("# 碳纤维圆柱壳\n\n" + MATERIAL_TABLE, encoding="utf-8")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    service = KnowledgeIngestionService(base_dir=tmp_path / "runtime")
    result = service.ingest_file(source)
    chunks = [json.loads(line) for line in service.chunks_path.read_text(encoding="utf-8").splitlines()]
    chunk = next(row for row in chunks if row["table_evidence"])
    table = chunk["table_evidence"][0]
    table_rows = markdown_tables(chunk["content_markdown"])[0][2]
    bound = dict(zip(table_rows[0], table_rows[2]))
    assert bound["剪切模量/GPa"] == "8.96"
    assert bound["泊松比 / $v_{12f}$"] == "0.2"
    assert bound["泊松比 / $v_{23f}$"] == "0.4"
    assert table_rows[3] == ["基体", "", "4.62", "8.27", "0.36", "0.36"]
    assert table["dimensionless_columns"] == [4, 5]
    assert table["structure_issues"] == [] and chunk["content_quality_version"] == "3"
    packets, _ = render_evidence([chunk], [], 12000)
    assert json.loads(packets[0])["table_evidence"] == [table]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    assert MATERIAL_TABLE in Path(result.markdown_path).read_text(encoding="utf-8")
    service.rebuild_indexes()
    assert chunk in [json.loads(line) for line in service.chunks_path.read_text(encoding="utf-8").splitlines()]


@pytest.mark.parametrize("header", [
    "<thead><tr><td>Case</td><td colspan='2'>Value (mm)</td></tr><tr><td></td><td>x</td><td>y</td></tr></thead>",
    "<tr><th rowspan='2'>Case</th><th colspan='2'>Value (mm)</th></tr><tr><th>x</th><th>y</th></tr>",
])
def test_explicit_header_and_row_group_spans(header):
    html = "<table>" + header + "<tbody><tr><td rowspan='0'>A|B</td><td>1</td><td>2</td></tr><tr><td colspan='2'>3</td></tr></tbody></table>"
    rows = markdown_tables(html_tables_to_markdown(html))[0][2]
    assert rows[0] == ["Case", "Value (mm) / x", "Value (mm) / y"]
    assert rows[2:] == [[r"A\|B", "1", "2"], [r"A\|B", "3", "3"]]


@pytest.mark.parametrize("html", [
    "<table><tr><td colspan='bad'>A</td></tr></table>",
    "<table><tr><td rowspan='2'>A</td></tr></table>",
    "<table><tr><td>A</td><td rowspan='2'>B</td></tr><tr><td colspan='2'>C</td></tr></table>",
    "<table><tr><th rowspan='2'>A</th><th>B</th></tr><tr><td>C</td></tr></table>",
])
def test_invalid_span_preserves_source_and_blocks_evidence(tmp_path, html):
    with pytest.raises(TableStructureError):
        html_tables_to_markdown(html)
    service = KnowledgeIngestionService(base_dir=tmp_path)
    blocks = service._build_blocks("DOC", "material", tmp_path / "source.md", html, "text")
    chunk = service._build_chunks("DOC", "material", tmp_path / "source.md", blocks)[0]
    assert chunk["content_markdown"] == html
    assert chunk["content_quality_issues"] == ["table_structure_invalid"]
    assert chunk["retrieval_eligible"] is False
    assert not service._build_kg("DOC", "material", [chunk])[1]
    assert render_evidence([chunk], [], 12000)[0] == []


@pytest.mark.parametrize("text,issue", [
    ("| Material | E (GPa) | nu12 |\n| --- | --- | --- |\n| T700 | 135 | 0.3 | extra |", "table_row_width_inconsistent"),
    ("| Material | Modulus (GPa) | Modulus (GPa) |\n| --- | --- | --- |\n| | $E_1$ | $E_2$ |\n| T700 | 135 | 9 |", "table_header_alignment_ambiguous"),
])
def test_unresolved_markdown_structure_cannot_be_projected(text, issue):
    quality = assess_content(text)
    assert quality["table_evidence"][0]["structure_issues"] == [issue]
    assert quality["retrieval_eligible"] is False
    assert project_table_columns(text, quality) is None


def test_explicit_unit_row_is_not_ambiguous_header():
    quality = assess_content("| Material | E1 | E2 |\n| --- | --- | --- |\n| | GPa | GPa |\n| T700 | 135 | 9 |")
    assert quality["retrieval_eligible"] is True
    assert quality["table_evidence"][0]["structure_issues"] == []
