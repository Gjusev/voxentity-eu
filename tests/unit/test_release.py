"""Bundle builder and validator agree on the run layout runs/<name>/predictions.jsonl."""

import json

import pytest

from voxentity_eu.commands import QualityGateFailed
from voxentity_eu.release import REQUIRED_FILES, build_bundle, cli_release_validate


def test_bundle_lists_runs_and_validates_them(tmp_path):
    src = tmp_path / "src"
    (src / "runs" / "sys-a").mkdir(parents=True)
    (src / "runs" / "sys-a" / "predictions.jsonl").write_text("{}\n")
    out = tmp_path / "bundle"
    build_bundle(src, out)
    for rel in REQUIRED_FILES:  # isolate the run-layout check from other gates
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        if not (out / rel).exists():
            (out / rel).write_text("{}\n")
    cli_release_validate(str(out))  # complete bundle passes
    assert json.loads((out / "bundle_manifest.json").read_text())["runs"] == ["sys-a"]
    (out / "predictions" / "sys-a" / "predictions.jsonl").unlink()
    with pytest.raises(QualityGateFailed, match="without predictions: sys-a"):
        cli_release_validate(str(out))
