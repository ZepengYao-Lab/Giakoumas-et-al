from __future__ import annotations

from pathlib import Path

from giakoumas_connectome.config import get_workflow_config
from giakoumas_connectome.data import load_workflow_inputs


def test_load_workflow_inputs_only_keeps_numeric_sets(tmp_path: Path) -> None:
    (tmp_path / "data" / "flywire_data").mkdir(parents=True)
    input_root = tmp_path / "data" / "input" / "PhN"
    input_root.mkdir(parents=True)

    (input_root / "set_1.csv").write_text("root_id\n1\n", encoding="utf-8")
    (input_root / "set_2.csv").write_text("root_id\n2\n", encoding="utf-8")
    (input_root / "set_7x.csv").write_text("root_id\n7\n", encoding="utf-8")

    inputs = load_workflow_inputs(tmp_path, get_workflow_config("phn"))

    assert [name for name, _ in inputs] == ["set_1", "set_2"]
