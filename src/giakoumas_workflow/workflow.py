"""High-level workflow runner."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .analysis import (
    attach_neuron_metadata,
    build_second_order,
    build_third_order,
    classify_neurons,
    remove_root_ids,
)
from .data import discover_repository_root, load_repository_tables, load_workflow_inputs
from .models import WorkflowConfig, WorkflowRunResult


def _write_unique_ids(path: Path, values: pd.Series) -> None:
    pd.DataFrame({"unique_root_id": values.drop_duplicates()}).to_csv(path, index=False)


def _fill_classification_defaults(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["neuron_type"] = frame["neuron_type"].fillna("local")
    frame["#_projection_synapses"] = frame["#_projection_synapses"].fillna(0).astype(int)
    return frame


def run_workflow(
    workflow: WorkflowConfig,
    repository_root: Path | None = None,
    output_dir: Path | None = None,
    min_synapses: int = 5,
    exclude_first_order_from_third_order: bool = False,
) -> WorkflowRunResult:
    """Run one configured workflow and write a clean output bundle."""

    repo_root = discover_repository_root(repository_root)
    tables = load_repository_tables(repo_root)
    set_inputs = load_workflow_inputs(repo_root, workflow)
    all_first_order_ids = {
        str(root_id)
        for _, frame in set_inputs
        for root_id in frame["root_id"].tolist()
    }

    target_output_dir = (
        output_dir.resolve()
        if output_dir is not None
        else (repo_root / "output" / "python_workflows" / workflow.output_dirname).resolve()
    )
    target_output_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, object]] = []
    for set_name, sensory_neurons in set_inputs:
        second_order = build_second_order(
            sensory_neurons=sensory_neurons,
            connections=tables.connections,
            set_name=set_name,
            upstream_label=workflow.upstream_label,
            min_synapses=min_synapses,
        )
        second_order, removed_second_order_ids = remove_root_ids(second_order, all_first_order_ids)
        second_nodes = attach_neuron_metadata(second_order.nodes, tables.neurons_data)
        second_classification = classify_neurons(
            second_nodes[["root_id"]],
            tables.connections,
            min_synapses=min_synapses,
        )
        second_nodes = _fill_classification_defaults(
            second_nodes.merge(second_classification, on="root_id", how="left")
        )

        third_order = build_third_order(
            second_order_connectivity=second_order.connectivity,
            second_order_nodes=second_nodes,
            connections=tables.connections,
            set_name=set_name,
            min_second_order_synapses=min_synapses,
            min_third_order_synapses=min_synapses,
            extra_excluded_post_root_ids=all_first_order_ids if exclude_first_order_from_third_order else None,
        )
        third_nodes = attach_neuron_metadata(third_order.nodes, tables.neurons_data)

        second_order.connectivity.to_csv(target_output_dir / f"{set_name}_second_order_edges.csv", index=False)
        _write_unique_ids(
            target_output_dir / f"{set_name}_second_order_unique_pre_ids.csv",
            second_order.connectivity["pre_root_id"],
        )
        _write_unique_ids(
            target_output_dir / f"{set_name}_second_order_unique_post_ids.csv",
            second_order.connectivity["post_root_id"],
        )
        second_nodes.to_csv(target_output_dir / f"{set_name}_2Ns_classified.csv", index=False)

        third_order.connectivity.to_csv(target_output_dir / f"{set_name}_third_order_edges.csv", index=False)
        _write_unique_ids(
            target_output_dir / f"{set_name}_third_order_unique_pre_ids.csv",
            third_order.connectivity["pre_root_id"],
        )
        _write_unique_ids(
            target_output_dir / f"{set_name}_third_order_unique_post_ids.csv",
            third_order.connectivity["post_root_id"],
        )
        third_nodes.to_csv(target_output_dir / f"{set_name}_3Ns.csv", index=False)

        summary_rows.append(
            {
                "set_name": set_name,
                "first_order_inputs": sensory_neurons["root_id"].nunique(),
                "second_order_edges": len(second_order.connectivity),
                "second_order_nodes": second_nodes["root_id"].nunique(),
                "removed_first_order_from_second_order": len(removed_second_order_ids),
                "second_order_projection_neurons": int((second_nodes["neuron_type"] == "projection").sum()),
                "second_order_local_neurons": int((second_nodes["neuron_type"] == "local").sum()),
                "third_order_raw_edges": len(third_order.raw_connectivity),
                "third_order_edges": len(third_order.connectivity),
                "third_order_nodes": third_nodes["root_id"].nunique(),
                "third_order_first_order_overlap_before_filter": len(
                    set(third_order.raw_connectivity["post_root_id"].astype(str)) & all_first_order_ids
                ),
                "exclude_first_order_from_third_order": exclude_first_order_from_third_order,
            }
        )

    summary = pd.DataFrame(summary_rows).sort_values("set_name").reset_index(drop=True)
    summary_path = target_output_dir / "workflow_summary.csv"
    summary.to_csv(summary_path, index=False)

    manifest_path = target_output_dir / "workflow_manifest.json"
    manifest = {
        "workflow": workflow.key,
        "description": workflow.description,
        "repository_root": str(repo_root),
        "output_dir": str(target_output_dir),
        "min_synapses": min_synapses,
        "exclude_first_order_from_third_order": exclude_first_order_from_third_order,
        "set_count": len(set_inputs),
        "summary_csv": str(summary_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return WorkflowRunResult(
        workflow=workflow,
        repository_root=repo_root,
        output_dir=target_output_dir,
        summary=summary,
        manifest_path=manifest_path,
    )
