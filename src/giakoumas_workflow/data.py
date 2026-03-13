"""Repository discovery and input-table loading."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .models import RepositoryTables, WorkflowConfig

CONNECTION_COLUMNS = ["pre_root_id", "post_root_id", "neuropil", "syn_count", "nt_type"]


def discover_repository_root(start: Path | None = None) -> Path:
    """Find the repository root from the current directory or one of its parents."""

    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "flywire_data").is_dir() and (candidate / "input").is_dir():
            return candidate
    raise FileNotFoundError(
        f"Could not locate the repository root from '{current}'. "
        "Expected directories named 'flywire_data' and 'input'."
    )


def _resolve_existing_path(root: Path, relative_candidates: list[str]) -> Path:
    for relative_path in relative_candidates:
        candidate = root / relative_path
        if candidate.exists():
            return candidate
    attempted = ", ".join(relative_candidates)
    raise FileNotFoundError(f"Could not find any of: {attempted}")


def load_repository_tables(repository_root: Path) -> RepositoryTables:
    """Load the core FlyWire-derived tables required by the Python workflows."""

    connections_path = _resolve_existing_path(
        repository_root,
        [
            "flywire_data/connections.csv",
            "flywire_data/connections.csv.gz",
            "flywire_data/connections.csv.zip",
        ],
    )
    classification_path = _resolve_existing_path(
        repository_root,
        ["flywire_data/classification.csv.gz", "flywire_data/classification.csv"],
    )
    neurons_path = _resolve_existing_path(
        repository_root,
        ["flywire_data/neurons.csv.gz", "flywire_data/neurons.csv"],
    )
    neuropil_path = _resolve_existing_path(
        repository_root,
        ["flywire_data/neuropil_synapse_table.csv.gz", "flywire_data/neuropil_synapse_table.csv"],
    )

    connections = pd.read_csv(connections_path, usecols=CONNECTION_COLUMNS)
    classification = pd.read_csv(classification_path, usecols=["root_id", "side"])
    classification_other = pd.read_csv(
        classification_path,
        usecols=["root_id", "super_class", "class"],
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


def load_workflow_inputs(repository_root: Path, workflow: WorkflowConfig) -> list[tuple[str, pd.DataFrame]]:
    """Load all set_*.csv inputs for a configured workflow."""

    input_root = repository_root / workflow.input_dir
    set_paths = sorted(
        (
            path
            for path in input_root.glob("set_*.csv")
            if re.fullmatch(r"set_(\d+)", path.stem)
        ),
        key=_set_sort_key,
    )
    if not set_paths:
        raise FileNotFoundError(f"No set_*.csv files found under '{input_root}'.")

    inputs: list[tuple[str, pd.DataFrame]] = []
    for path in set_paths:
        frame = pd.read_csv(path, usecols=["root_id"]).dropna().drop_duplicates().reset_index(drop=True)
        inputs.append((path.stem, frame))
    return inputs
