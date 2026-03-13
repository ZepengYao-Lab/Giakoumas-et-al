"""Notebook-oriented workflow/report builders."""

from __future__ import annotations

import json
from pathlib import Path

from . import _runtime  # noqa: F401

import matplotlib.pyplot as plt
import pandas as pd

from .analysis import (
    add_neuropil_remap,
    aggregate_pairwise_outputs,
    attach_neuron_metadata,
    build_output_to_input_matrix,
    build_set_to_target_heatmap_matrix,
    build_interset_synapse_matrix,
    build_second_order,
    build_third_order,
    classify_neurons,
    get_synapse_counts_for_set,
    remove_root_ids,
)
from .config import get_workflow_config
from .data import default_output_dir, discover_project_root, load_repository_tables, load_workflow_inputs
from .models import WorkflowConfig, WorkflowReport, WorkflowSetReport
from .plots import (
    plot_first_order_heatmap,
    plot_input_synapse_counts,
    plot_location_outputs,
    plot_nt_distribution,
    plot_order_counts,
    plot_second_order_interset_heatmap,
    plot_second_order_upset,
    plot_second_to_third_order_heatmap,
    plot_set_to_second_order_heatmap,
    plot_superclass_distribution,
    plot_third_order_upset,
    plot_top_regions,
    save_figure,
)


def _merge_node_metadata(nodes: pd.DataFrame, tables) -> pd.DataFrame:
    merged = attach_neuron_metadata(nodes, tables.neurons_data)
    return merged.merge(tables.classification_other, on="root_id", how="left")


def _fill_projection_defaults(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["neuron_type"] = frame["neuron_type"].fillna("local")
    frame["#_projection_synapses"] = frame["#_projection_synapses"].fillna(0).astype(int)
    return frame


def _label_map(workflow_config: WorkflowConfig, set_names: list[str]) -> dict[str, str]:
    if len(set_names) != len(workflow_config.set_labels):
        raise ValueError(
            f"Workflow '{workflow_config.key}' defines {len(workflow_config.set_labels)} labels "
            f"for {len(set_names)} input sets."
        )
    return dict(zip(set_names, workflow_config.set_labels, strict=True))


def build_workflow_report(
    workflow: str | WorkflowConfig,
    project_root: Path | None = None,
    output_dir: Path | None = None,
    min_synapses: int = 5,
    exclude_first_order_from_third_order: bool = False,
) -> WorkflowReport:
    """Build a complete workflow report from the copied standalone data."""

    workflow_config = get_workflow_config(workflow) if isinstance(workflow, str) else workflow
    resolved_root = discover_project_root(project_root)
    tables = load_repository_tables(resolved_root)
    set_inputs = load_workflow_inputs(resolved_root, workflow_config)
    all_first_order_ids = {
        str(root_id)
        for _, frame in set_inputs
        for root_id in frame["root_id"].tolist()
    }

    resolved_output_dir = (
        output_dir.resolve() if output_dir is not None else default_output_dir(resolved_root, workflow_config)
    )
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    input_map = {set_name: frame for set_name, frame in set_inputs}
    first_order_outputs_by_set: dict[str, pd.DataFrame] = {}
    set_reports: dict[str, WorkflowSetReport] = {}
    summary_rows: list[dict[str, object]] = []

    for set_name, input_nodes in set_inputs:
        first_order_outputs = add_neuropil_remap(
            aggregate_pairwise_outputs(input_nodes, tables.connections, min_synapses=min_synapses)
        )
        input_synapse_counts = get_synapse_counts_for_set(input_nodes, tables.connections, min_synapses=min_synapses)
        second_order = build_second_order(
            sensory_neurons=input_nodes,
            connections=tables.connections,
            set_name=set_name,
            upstream_label=workflow_config.upstream_label,
            min_synapses=min_synapses,
        )
        second_order, removed_second_order_ids = remove_root_ids(second_order, all_first_order_ids)
        second_order_nodes = _merge_node_metadata(second_order.nodes, tables)
        second_projection = classify_neurons(second_order_nodes[["root_id"]], tables.connections, min_synapses=min_synapses)
        second_order_nodes = _fill_projection_defaults(
            second_order_nodes.merge(second_projection, on="root_id", how="left")
        )
        second_order_outputs = add_neuropil_remap(
            aggregate_pairwise_outputs(second_order_nodes[["root_id"]], tables.connections, min_synapses=min_synapses)
        )

        third_order = build_third_order(
            second_order_connectivity=second_order.connectivity,
            second_order_nodes=second_order_nodes,
            connections=tables.connections,
            set_name=set_name,
            min_second_order_synapses=min_synapses,
            min_third_order_synapses=min_synapses,
            extra_excluded_post_root_ids=all_first_order_ids if exclude_first_order_from_third_order else None,
        )
        third_order_nodes = _merge_node_metadata(third_order.nodes, tables)
        third_projection = classify_neurons(third_order_nodes[["root_id"]], tables.connections, min_synapses=min_synapses)
        third_order_nodes = _fill_projection_defaults(
            third_order_nodes.merge(third_projection, on="root_id", how="left")
        )
        third_order_outputs = add_neuropil_remap(
            aggregate_pairwise_outputs(third_order_nodes[["root_id"]], tables.connections, min_synapses=min_synapses)
        )

        first_order_outputs_by_set[set_name] = first_order_outputs
        set_reports[set_name] = WorkflowSetReport(
            set_name=set_name,
            input_nodes=input_nodes,
            input_synapse_counts=input_synapse_counts,
            first_order_outputs=first_order_outputs,
            second_order=second_order,
            second_order_nodes=second_order_nodes,
            second_order_outputs=second_order_outputs,
            third_order=third_order,
            third_order_nodes=third_order_nodes,
            third_order_outputs=third_order_outputs,
        )

        summary_rows.append(
            {
                "set_name": set_name,
                "first_order_inputs": int(input_nodes["root_id"].nunique()),
                "first_order_outputs": int(first_order_outputs["post_root_id"].nunique()),
                "second_order_edges": int(len(second_order.connectivity)),
                "second_order_nodes": int(second_order_nodes["root_id"].nunique()),
                "removed_first_order_from_second_order": int(len(removed_second_order_ids)),
                "second_order_projection_neurons": int((second_order_nodes["neuron_type"] == "projection").sum()),
                "second_order_local_neurons": int((second_order_nodes["neuron_type"] == "local").sum()),
                "third_order_edges": int(len(third_order.connectivity)),
                "third_order_nodes": int(third_order_nodes["root_id"].nunique()),
                "third_order_projection_neurons": int((third_order_nodes["neuron_type"] == "projection").sum()),
                "third_order_local_neurons": int((third_order_nodes["neuron_type"] == "local").sum()),
            }
        )

    first_order_matrix = build_interset_synapse_matrix(first_order_outputs_by_set, input_map)
    summary = pd.DataFrame(summary_rows).sort_values("set_name").reset_index(drop=True)
    highlight_synapse_counts = (
        get_synapse_counts_for_set(
            pd.DataFrame({"root_id": list(workflow_config.highlight_root_ids)}),
            tables.connections,
            min_synapses=min_synapses,
        )
        if workflow_config.highlight_root_ids
        else None
    )
    return WorkflowReport(
        workflow=workflow_config,
        project_root=resolved_root,
        output_dir=resolved_output_dir,
        sets=set_reports,
        summary=summary,
        first_order_set_matrix=first_order_matrix,
        highlight_synapse_counts=highlight_synapse_counts,
    )


def save_report_tables(report: WorkflowReport, output_dir: Path | None = None) -> WorkflowReport:
    """Write workflow tables and manifest to disk."""

    target_output_dir = output_dir.resolve() if output_dir is not None else report.output_dir
    table_dir = target_output_dir / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    label_map = _label_map(report.workflow, list(report.sets))

    report.summary.to_csv(table_dir / "workflow_summary.csv", index=False)
    report.first_order_set_matrix.to_csv(table_dir / "first_order_set_to_set_matrix.csv")
    first_order_display = report.first_order_set_matrix.copy()
    first_order_display.index = list(label_map.values())
    first_order_display.columns = list(label_map.values())
    first_order_display.to_csv(table_dir / "first_order_set_to_set_matrix_display_labels.csv")

    second_order_interset_matrix = build_output_to_input_matrix(
        {set_name: set_report.second_order_outputs for set_name, set_report in report.sets.items()},
        {set_name: set_report.second_order_nodes for set_name, set_report in report.sets.items()},
        label_map,
    )
    second_order_interset_matrix.to_csv(table_dir / "second_order_set_to_set_matrix.csv")

    set_to_second_order_matrix = build_set_to_target_heatmap_matrix(
        {set_name: set_report.second_order.connectivity for set_name, set_report in report.sets.items()},
        label_map,
    )
    set_to_second_order_matrix.to_csv(table_dir / "set_to_second_order_matrix.csv")

    second_to_third_order_matrix = build_set_to_target_heatmap_matrix(
        {set_name: set_report.third_order.connectivity for set_name, set_report in report.sets.items()},
        label_map,
    )
    second_to_third_order_matrix.to_csv(table_dir / "second_to_third_order_matrix.csv")

    for set_name, set_report in report.sets.items():
        set_dir = table_dir / set_name
        set_dir.mkdir(parents=True, exist_ok=True)
        set_report.input_nodes.to_csv(set_dir / f"{set_name}_inputs.csv", index=False)
        set_report.input_synapse_counts.to_csv(set_dir / f"{set_name}_input_synapse_counts.csv", index=False)
        set_report.first_order_outputs.to_csv(set_dir / f"{set_name}_first_order_outputs.csv", index=False)
        set_report.second_order.connectivity.to_csv(set_dir / f"{set_name}_second_order_edges.csv", index=False)
        set_report.second_order_nodes.to_csv(set_dir / f"{set_name}_2Ns.csv", index=False)
        set_report.second_order_outputs.to_csv(set_dir / f"{set_name}_2N_outputs.csv", index=False)
        set_report.third_order.connectivity.to_csv(set_dir / f"{set_name}_third_order_edges.csv", index=False)
        set_report.third_order_nodes.to_csv(set_dir / f"{set_name}_3Ns.csv", index=False)
        set_report.third_order_outputs.to_csv(set_dir / f"{set_name}_3N_outputs.csv", index=False)

    if report.highlight_synapse_counts is not None:
        report.highlight_synapse_counts.to_csv(table_dir / "highlight_input_synapse_counts.csv", index=False)

    manifest = {
        "workflow": report.workflow.key,
        "display_name": report.workflow.display_name,
        "project_root": str(report.project_root),
        "output_dir": str(target_output_dir),
        "table_dir": str(table_dir),
    }
    manifest_path = target_output_dir / "report_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report.manifest_path = manifest_path
    return report


def export_standard_figures(report: WorkflowReport, output_dir: Path | None = None) -> dict[str, Path]:
    """Generate and save the standard figure suite used by the thin notebooks."""

    target_output_dir = output_dir.resolve() if output_dir is not None else report.output_dir
    figure_dir = target_output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    saved: dict[str, Path] = {}
    figure_builders = {
        "first_order_set_heatmap": lambda: plot_first_order_heatmap(
            report.first_order_set_matrix,
            title=f"{report.workflow.display_name}: first-order set-to-set synapses",
            display_labels=list(report.workflow.set_labels),
        ),
        "input_synapse_counts": lambda: plot_input_synapse_counts(report),
        "node_counts": lambda: plot_order_counts(report),
        "second_order_upset": lambda: plot_second_order_upset(report),
        "second_order_interset_heatmap": lambda: plot_second_order_interset_heatmap(report),
        "set_to_second_order_heatmap": lambda: plot_set_to_second_order_heatmap(report),
        "second_order_locations": lambda: plot_location_outputs(report, order="second"),
        "second_order_superclasses": lambda: plot_superclass_distribution(report, order="second"),
        "second_order_nt_local": lambda: plot_nt_distribution(report, order="second", location="local"),
        "second_order_nt_non_sez": lambda: plot_nt_distribution(
            report,
            order="second",
            location="outside_SEZ",
        ),
        "third_order_upset": lambda: plot_third_order_upset(report),
        "second_to_third_order_heatmap": lambda: plot_second_to_third_order_heatmap(report),
        "third_order_locations": lambda: plot_location_outputs(report, order="third"),
        "third_order_superclasses": lambda: plot_superclass_distribution(report, order="third"),
        "third_order_nt_local": lambda: plot_nt_distribution(report, order="third", location="local"),
        "third_order_nt_non_sez": lambda: plot_nt_distribution(
            report,
            order="third",
            location="outside_SEZ",
        ),
    }

    for stem, builder in figure_builders.items():
        fig, _ = builder()
        saved[stem] = save_figure(fig, figure_dir / f"{stem}.svg")
        fig.clf()
        plt.close(fig)

    second_top_fig, _ = plot_top_regions(report, order="second")
    saved["second_order_top_regions"] = save_figure(second_top_fig, figure_dir / "second_order_top_regions.svg")
    second_top_fig.clf()
    plt.close(second_top_fig)

    third_top_fig, _ = plot_top_regions(report, order="third")
    saved["third_order_top_regions"] = save_figure(third_top_fig, figure_dir / "third_order_top_regions.svg")
    third_top_fig.clf()
    plt.close(third_top_fig)

    return saved


def run_full_report(
    workflow: str | WorkflowConfig,
    project_root: Path | None = None,
    output_dir: Path | None = None,
    min_synapses: int = 5,
    exclude_first_order_from_third_order: bool = False,
    export_figures: bool = True,
) -> WorkflowReport:
    """Build a workflow report and write its tables and figures to disk."""

    report = build_workflow_report(
        workflow=workflow,
        project_root=project_root,
        output_dir=output_dir,
        min_synapses=min_synapses,
        exclude_first_order_from_third_order=exclude_first_order_from_third_order,
    )
    report = save_report_tables(report)
    if export_figures:
        export_standard_figures(report)
    return report
