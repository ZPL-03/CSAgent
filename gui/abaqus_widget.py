"""ABAQUS 结果展示组件。"""

from __future__ import annotations

from typing import Iterable

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from gui.interactive_view import InteractivePlotWidget


def _fmt(value: object, digits: int = 3) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


class AbaqusWidget(QWidget):
    """展示有限元校核结果与交互式模态视图。"""

    HEADERS = ["候选样本", "正式编号", "状态", "极限压力", "屈曲压力", "面密度", "结论", "失效模式"]

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict] = []

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._refresh_detail)

        self.detail_browser = QTextBrowser()
        self.preview_widget = InteractivePlotWidget("完成 ABAQUS 校核后，这里会显示可旋转的模态云图。")

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.detail_browser, 2)
        right_layout.addWidget(self.preview_widget, 3)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        splitter = QSplitter()
        splitter.addWidget(self.table)
        splitter.addWidget(right_widget)
        splitter.setSizes([720, 620])

        layout = QHBoxLayout(self)
        layout.addWidget(splitter)

    def update_results(self, results: Iterable[dict]) -> None:
        self.results = list(results)
        self.table.setRowCount(len(self.results))
        for row, result in enumerate(self.results):
            values = [
                result.get("display_name", result.get("session_candidate_id", "-")),
                result.get("candidate_id", ""),
                result.get("status", ""),
                _fmt(result.get("ultimate_pressure_MPa")),
                _fmt(result.get("linear_buckling_pressure_MPa")),
                _fmt(result.get("weight_kg_per_m2")),
                result.get("verdict", "-"),
                result.get("failure_mode", "-"),
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        if self.results:
            self.table.selectRow(0)
        else:
            self.detail_browser.setHtml("<p>暂无 ABAQUS 结果。</p>")
            self.preview_widget.clear_scene("暂无结果预览。")

    def reset_view(self) -> None:
        if hasattr(self, "detail_browser"):
            self.detail_browser.clear()
        self.preview_widget.reset_plotter()

    def append_or_update_result(self, result: dict) -> None:
        updated = False
        for index, current in enumerate(self.results):
            if current.get("session_candidate_id") == result.get("session_candidate_id"):
                self.results[index] = result
                updated = True
                break
        if not updated:
            self.results.append(result)
        self.update_results(self.results)

    def _refresh_detail(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self.detail_browser.setHtml("<p>请选择结果查看详情。</p>")
            self.preview_widget.clear_scene("请选择结果查看模态云图。")
            return

        result = self.results[rows[0].row()]
        html = (
            f"<h3>{result.get('display_name', result.get('session_candidate_id', '-'))}</h3>"
            f"<p><b>正式编号：</b>{result.get('candidate_id')}<br>"
            f"<b>状态：</b>{result.get('status')}<br>"
            f"<b>工况：</b>{result.get('load_summary', '-')}<br>"
            f"<b>边界条件：</b>{result.get('boundary_summary', '-')}<br>"
            f"<b>极限压力：</b>{_fmt(result.get('ultimate_pressure_MPa'))} MPa<br>"
            f"<b>线性屈曲压力：</b>{_fmt(result.get('linear_buckling_pressure_MPa'))} MPa<br>"
            f"<b>极限压力依据：</b>{result.get('ultimate_pressure_basis', '-')}<br>"
            f"<b>Riks 最大 LPF：</b>{_fmt(result.get('riks_lpf_max'))}<br>"
            f"<b>缺陷幅值：</b>{_fmt(result.get('imperfection_amplitude_mm'))} mm<br>"
            f"<b>面密度：</b>{_fmt(result.get('weight_kg_per_m2'))} kg/m^2<br>"
            f"<b>最大位移：</b>{_fmt(result.get('max_displacement_mm'))} mm<br>"
            f"<b>失效模式：</b>{result.get('failure_mode', '-')}<br>"
            f"<b>结论：</b>{result.get('verdict', '-')}</p>"
            f"<p><b>工程说明：</b>{result.get('diagnosis_summary', '-')}</p>"
            f"<p><b>线性屈曲 ODB：</b>{result.get('linear_buckling_odb', result.get('abaqus_odb', '-'))}</p>"
            f"<p><b>后屈曲 ODB：</b>{result.get('postbuckling_odb', '-')}</p>"
            f"<p><b>INP：</b>{result.get('abaqus_inp', '-')}</p>"
            f"<p><b>模态数据：</b>{result.get('visualization_json', '-')}</p>"
            f"<p><b>工件目录：</b>{result.get('artifact_dir', '-')}</p>"
            f"<p><b>特征值：</b>{result.get('mode_eigenvalues', [])}</p>"
        )
        if result.get("error_log"):
            html += f"<h4>错误日志</h4><pre>{result.get('error_log')}</pre>"
        self.detail_browser.setHtml(html)
        self.preview_widget.show_mode_shape(result)
