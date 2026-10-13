"""Report figures: well-formed SVG from real summaries; nothing when runs are missing."""

import xml.etree.ElementTree as ET
from pathlib import Path

from voxentity_eu.reporting.charts import cell_accuracy_svg, deltas_svg, write_figures


def _summary(acc):
    cells = {f"{loc}|{e}": {"n": 20, "correct": int(20 * acc), "slot_accuracy": acc}
             for loc in ("de-DE", "fr-FR") for e in ("email", "phone")}
    return {"cells_locale_entity": cells}


def test_svgs_parse():
    runs = {"a": _summary(0.5), "b": _summary(0.0), "c": _summary(1.0)}
    ET.fromstring(cell_accuracy_svg(runs, [("a", "A"), ("b", "B")], "c"))  # 0% bars included
    ET.fromstring(deltas_svg([{"label": "A − B", "point_difference": -0.03, "ci95": [-0.07, 0.01], "n": 240}]))


def test_no_figures_without_runs(tmp_path: Path):
    assert write_figures({"whisper-turbo-slots": {}}, tmp_path / "figures") == []
    assert not (tmp_path / "figures").exists()
