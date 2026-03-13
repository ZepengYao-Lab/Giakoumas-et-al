"""Lightweight data models used by the workflow package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class WorkflowConfig:
    """Static configuration for one notebook-derived workflow."""

    key: str
    description: str
    input_dir: str
    output_dirname: str
    upstream_label: str


@dataclass
class RepositoryTables:
    """Data tables loaded from the repository."""

    connections: pd.DataFrame
    classification: pd.DataFrame
    classification_other: pd.DataFrame
    neurons: pd.DataFrame
    neurons_data: pd.DataFrame


@dataclass
class SecondOrderResult:
    """Pairwise second-order connectivity plus summarized nodes."""

    connectivity: pd.DataFrame
    nodes: pd.DataFrame


@dataclass
class ThirdOrderResult:
    """Raw and filtered third-order connectivity plus summarized nodes."""

    raw_connectivity: pd.DataFrame
    connectivity: pd.DataFrame
    nodes: pd.DataFrame


@dataclass
class WorkflowRunResult:
    """Artifacts returned by a workflow run."""

    workflow: WorkflowConfig
    repository_root: Path
    output_dir: Path
    summary: pd.DataFrame
    manifest_path: Path
