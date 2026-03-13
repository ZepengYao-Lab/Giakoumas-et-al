"""Project discovery and data loading."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .models import RepositoryTables, WorkflowConfig

CONNECTION_COLUMNS = ["pre_root_id", "post_root_id", "neuropil", "syn_count", "nt_type"]


def discover_project_root(start: Path | None = None) -> Path:
    """Find the standalone project root from the current directory or its parents."""

    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "data" / "flywire_data").is_dir() and (candidate / "data" / "input").is_dir():
            return candidate
    raise FileNotFoundError(
        f"Could not locate the standalone project root from '{current}'. "
        "Expected 'data/flywire_data' and 'data/input'."
    )


def _resolve_existing_path(root: Path, relative_candidates: list[str]) -> Path:
    for relative_path in relative_candidates:
        candidate = root / relative_path
        if candidate.exists():
            return candidate
    attempted = ", ".join(relative_candidates)
    raise FileNotFoundError(f"Could not find any of: {attempted}")


def default_output_dir(project_root: Path, workflow: WorkflowConfig) -> Path:
    """Return the default output directory for a workflow."""

    return (project_root / "output" / workflow.output_dirname).resolve()


def load_root_id_table(path: Path) -> pd.DataFrame:
    """Load one root-id CSV into the canonical one-column layout."""

    return pd.read_csv(path, usecols=["root_id"]).dropna().drop_duplicates().reset_index(drop=True)


def load_repository_tables(project_root: Path) -> RepositoryTables:
    """Load the copied FlyWire tables required by the streamlined notebooks."""

    connections_path = _resolve_existing_path(
        project_root,
        [
            "data/flywire_data/connections.csv",
            "data/flywire_data/connections.csv.gz",
            "data/flywire_data/connections.csv.zip",
        ],
    )
    classification_path = _resolve_existing_path(
        project_root,
        ["data/flywire_data/classification.csv.gz", "data/flywire_data/classification.csv"],
    )
    neurons_path = _resolve_existing_path(
        project_root,
        ["data/flywire_data/neurons.csv.gz", "data/flywire_data/neurons.csv"],
    )
    neuropil_path = _resolve_existing_path(
        project_root,
        ["data/flywire_data/neuropil_synapse_table.csv.gz", "data/flywire_data/neuropil_synapse_table.csv"],
    )

    connections = pd.read_csv(connections_path, usecols=CONNECTION_COLUMNS)
    classification = pd.read_csv(classification_path, usecols=["root_id", "side"])
    classification_other = pd.read_csv(
        classification_path,
        usecols=["root_id", "super_class", "class", "nerve"],
    )
    neurons = pd.read_csv(neurons_path, usecols=["root_id", "nt_type"])
    neuropil_synapse = pd.read_csv(
        neuropil_path,
        usecols=["root_id", "input synapses", "output synapses"],
    ).rename(
        columns={
            "input synapses": "input_synapses",
            "output synapses": "output_synapses",
        }
    )

    neurons_data = neurons.merge(
        classification.merge(neuropil_synapse, on="root_id", how="outer"),
        on="root_id",
        how="outer",
    )

    return RepositoryTables(
        connections=connections,
        classification=classification,
        classification_other=classification_other,
        neurons=neurons,
        neurons_data=neurons_data,
    )


def _set_sort_key(path: Path) -> tuple[int, str]:
    match = re.fullmatch(r"set_(\d+)", path.stem)
    return (int(match.group(1)) if match else 10**9, path.stem)


def load_workflow_inputs(project_root: Path, workflow: WorkflowConfig) -> list[tuple[str, pd.DataFrame]]:
    """Load numeric set_*.csv inputs for a configured workflow."""

    input_root = project_root / "data" / workflow.input_dir
    set_paths = sorted(
        (
            path
            for path in input_root.glob("set_*.csv")
            if re.fullmatch(r"set_(\d+)", path.stem)
        ),
        key=_set_sort_key,
    )
    if not set_paths:
        raise FileNotFoundError(f"No numeric set_*.csv files found under '{input_root}'.")

    inputs: list[tuple[str, pd.DataFrame]] = []
    for path in set_paths:
        inputs.append((path.stem, load_root_id_table(path)))
    return inputs


def load_named_input_tables(project_root: Path, relative_paths: dict[str, str]) -> dict[str, pd.DataFrame]:
    """Load a named collection of root-id CSVs relative to the standalone project root."""

    return {
        label: load_root_id_table(project_root / relative_path)
        for label, relative_path in relative_paths.items()
    }
