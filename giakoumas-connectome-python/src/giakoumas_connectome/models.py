"""Lightweight data models used throughout the standalone project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class WorkflowConfig:
    """Static configuration for one notebook family."""

    key: str
    display_name: str
    description: str
    notebook_title: str
    input_dir: str
    output_dirname: str
    upstream_label: str
    set_labels: tuple[str, ...]
    set_colors: tuple[str, ...]
    second_order_upset_title: str
    third_order_upset_title: str
    set_to_second_order_title: str
    set_axis_label: str
    second_to_third_order_title: str
    synapse_counts_title: str
    highlight_root_ids: tuple[int, ...] = ()
    highlight_label: str = "Set X"


@dataclass
class RepositoryTables:
    """Core tables loaded from the copied project data directory."""

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
class WorkflowSetReport:
    """All tables derived for a single set within a workflow."""

    set_name: str
    input_nodes: pd.DataFrame
    input_synapse_counts: pd.DataFrame
    first_order_outputs: pd.DataFrame
    second_order: SecondOrderResult
    second_order_nodes: pd.DataFrame
    second_order_outputs: pd.DataFrame
    third_order: ThirdOrderResult
    third_order_nodes: pd.DataFrame
    third_order_outputs: pd.DataFrame


@dataclass
class WorkflowReport:
    """A complete workflow report ready for notebooks, CLI export, or tests."""

    workflow: WorkflowConfig
    project_root: Path
    output_dir: Path
    sets: dict[str, WorkflowSetReport]
    summary: pd.DataFrame
    first_order_set_matrix: pd.DataFrame
    highlight_synapse_counts: pd.DataFrame | None = None
    manifest_path: Path | None = None


@dataclass
class DirectInputReport:
    """Direct-input tables derived from an existing workflow report."""

    second_order_input_percentages: dict[str, pd.DataFrame]
    second_order_input_percentage_summary: pd.DataFrame
    direct_inputs_by_set: dict[str, pd.DataFrame]
    direct_inputs_no_self_by_set: dict[str, pd.DataFrame]
    direct_input_superclass_counts: pd.DataFrame
    direct_input_superclass_counts_no_self: pd.DataFrame
    direct_input_superclass_nerve_no_self_by_set: dict[str, pd.DataFrame]
    direct_input_superclass_nerve_counts_no_self: pd.DataFrame
