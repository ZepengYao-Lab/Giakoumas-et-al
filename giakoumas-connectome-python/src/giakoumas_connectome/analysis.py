"""Reusable notebook-derived analysis functions."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from .constants import SECONDARY_NTS, SEZ_NEUROPILS
from .models import SecondOrderResult, ThirdOrderResult

PAIRWISE_COLUMNS = [
    "pre_root_id",
    "post_root_id",
    "syn_count",
    "neuropil",
    "nt_type",
    "location_of_connection",
]


def _empty_pairwise_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=PAIRWISE_COLUMNS)


def _root_id_strings(values: Iterable[object]) -> set[str]:
    return {str(value) for value in values if pd.notna(value)}


def as_root_id_frame(root_ids: pd.DataFrame | pd.Series) -> pd.DataFrame:
    """Normalize a root_id collection into a one-column DataFrame."""

    if isinstance(root_ids, pd.Series):
        frame = root_ids.to_frame(name="root_id")
    else:
        if "root_id" not in root_ids.columns:
            raise KeyError("Expected a column named 'root_id'.")
        frame = root_ids[["root_id"]].copy()
    return frame.dropna().drop_duplicates().reset_index(drop=True)


def classify_connection_location(neuropil: str) -> str:
    """Classify a neuropil as SEZ-local or outside the SEZ."""

    return "local" if neuropil in SEZ_NEUROPILS else "outside_SEZ"


def collapse_neuropil_name(neuropil: str) -> str:
    """Collapse sided neuropil names into a side-agnostic label."""

    if neuropil.endswith(("_L", "_R")):
        return neuropil[:-2]
    return neuropil


def add_neuropil_remap(frame: pd.DataFrame, source_col: str = "neuropil") -> pd.DataFrame:
    """Return a copy of a connectivity frame with a side-collapsed neuropil column."""

    if frame.empty:
        remapped = frame.copy()
        remapped["neuropil_remap"] = pd.Series(dtype=object)
        return remapped

    remapped = frame.copy()
    remapped["neuropil_remap"] = remapped[source_col].map(collapse_neuropil_name)
    return remapped


def aggregate_pairwise_outputs(
    root_ids: pd.DataFrame | pd.Series,
    connections: pd.DataFrame,
    min_synapses: int = 5,
) -> pd.DataFrame:
    """Aggregate outputs for a root-id set with pair-level thresholding."""

    sources = as_root_id_frame(root_ids)
    if sources.empty:
        return _empty_pairwise_frame()

    merged = sources.merge(
        connections[["pre_root_id", "post_root_id", "neuropil", "syn_count", "nt_type"]],
        left_on="root_id",
        right_on="pre_root_id",
        how="inner",
    ).drop(columns="root_id")

    if merged.empty:
        return _empty_pairwise_frame()

    summed = (
        merged.groupby(["pre_root_id", "post_root_id"], as_index=False, sort=False)
        .agg(syn_count=("syn_count", "sum"))
    )
    summed = summed.loc[summed["syn_count"] >= min_synapses].copy()
    if summed.empty:
        return _empty_pairwise_frame()

    strongest = merged.loc[
        merged.groupby(["pre_root_id", "post_root_id"])["syn_count"].idxmax(),
        ["pre_root_id", "post_root_id", "neuropil", "nt_type"],
    ]
    connectivity = summed.merge(
        strongest,
        on=["pre_root_id", "post_root_id"],
        how="left",
    )
    connectivity["location_of_connection"] = connectivity["neuropil"].map(classify_connection_location)
    return connectivity.sort_values(["pre_root_id", "post_root_id"]).reset_index(drop=True)


def summarize_targets(connectivity: pd.DataFrame, upstream_column: str, synapse_column: str) -> pd.DataFrame:
    """Summarize pairwise outputs into one row per postsynaptic neuron."""

    if connectivity.empty:
        return pd.DataFrame(columns=["root_id", upstream_column, synapse_column, "const"])

    summary = (
        connectivity.groupby("post_root_id", as_index=False)
        .agg(
            **{
                upstream_column: ("pre_root_id", "nunique"),
                synapse_column: ("syn_count", "sum"),
            }
        )
        .rename(columns={"post_root_id": "root_id"})
    )
    summary["const"] = 1
    return summary.sort_values("root_id").reset_index(drop=True)


def build_second_order(
    sensory_neurons: pd.DataFrame | pd.Series,
    connections: pd.DataFrame,
    set_name: str,
    upstream_label: str,
    min_synapses: int = 5,
) -> SecondOrderResult:
    """Build second-order edges and nodes for one input set."""

    connectivity = aggregate_pairwise_outputs(sensory_neurons, connections, min_synapses=min_synapses)
    nodes = summarize_targets(
        connectivity,
        upstream_column=f"upstream_{set_name}_{upstream_label}",
        synapse_column=f"{set_name}_syn_count",
    )
    return SecondOrderResult(connectivity=connectivity, nodes=nodes)


def remove_root_ids(
    result: SecondOrderResult,
    root_ids_to_remove: Iterable[object],
) -> tuple[SecondOrderResult, list[str]]:
    """Remove nodes that overlap with a provided root-id set."""

    blocked_ids = _root_id_strings(root_ids_to_remove)
    if not blocked_ids:
        return result, []

    node_mask = result.nodes["root_id"].astype(str).isin(blocked_ids)
    removed_ids = sorted(result.nodes.loc[node_mask, "root_id"].astype(str).unique())

    filtered_nodes = result.nodes.loc[~node_mask].reset_index(drop=True)
    filtered_connectivity = result.connectivity.loc[
        ~result.connectivity["post_root_id"].astype(str).isin(blocked_ids)
    ].reset_index(drop=True)

    return SecondOrderResult(connectivity=filtered_connectivity, nodes=filtered_nodes), removed_ids


def attach_neuron_metadata(nodes: pd.DataFrame, neurons_data: pd.DataFrame) -> pd.DataFrame:
    """Merge node summaries with neuron metadata without dropping unmatched rows."""

    if nodes.empty:
        return nodes.copy()
    return nodes.merge(neurons_data, on="root_id", how="left")


def classify_neurons(
    neurons: pd.DataFrame | pd.Series,
    connections: pd.DataFrame,
    min_synapses: int = 5,
) -> pd.DataFrame:
    """Classify neurons as local or projection based on outputs outside the SEZ."""

    roots = as_root_id_frame(neurons)
    connectivity = aggregate_pairwise_outputs(roots, connections, min_synapses=min_synapses)
    projection_synapses = (
        connectivity.loc[connectivity["location_of_connection"] == "outside_SEZ"]
        .groupby("pre_root_id", as_index=False)
        .agg(_projection_synapses=("syn_count", "sum"))
        .rename(columns={"pre_root_id": "root_id"})
    )

    classified = roots.merge(projection_synapses, on="root_id", how="left")
    classified["_projection_synapses"] = classified["_projection_synapses"].fillna(0).astype(int)
    classified["neuron_type"] = np.where(
        classified["_projection_synapses"] > 0,
        "projection",
        "local",
    )
    return classified.rename(columns={"_projection_synapses": "#_projection_synapses"})


def build_third_order(
    second_order_connectivity: pd.DataFrame,
    second_order_nodes: pd.DataFrame,
    connections: pd.DataFrame,
    set_name: str,
    min_second_order_synapses: int = 5,
    min_third_order_synapses: int = 5,
    extra_excluded_post_root_ids: Iterable[object] | None = None,
) -> ThirdOrderResult:
    """Build third-order edges and nodes for one second-order set."""

    valid_second_order_sources = (
        second_order_connectivity.loc[second_order_connectivity["syn_count"] >= min_second_order_synapses, "post_root_id"]
        .drop_duplicates()
        .to_frame(name="root_id")
    )

    raw_connectivity = aggregate_pairwise_outputs(
        valid_second_order_sources,
        connections,
        min_synapses=min_third_order_synapses,
    )
    if raw_connectivity.empty:
        empty_nodes = pd.DataFrame(
            columns=["root_id", f"upstream_{set_name}_2Ns", f"{set_name}_syn_count", "const"]
        )
        return ThirdOrderResult(
            raw_connectivity=raw_connectivity,
            connectivity=raw_connectivity.copy(),
            nodes=empty_nodes,
        )

    blocked_ids = _root_id_strings(second_order_nodes["root_id"])
    if extra_excluded_post_root_ids is not None:
        blocked_ids.update(_root_id_strings(extra_excluded_post_root_ids))

    filtered_connectivity = raw_connectivity.loc[
        ~raw_connectivity["post_root_id"].astype(str).isin(blocked_ids)
    ].reset_index(drop=True)

    nodes = summarize_targets(
        filtered_connectivity,
        upstream_column=f"upstream_{set_name}_2Ns",
        synapse_column=f"{set_name}_syn_count",
    )
    return ThirdOrderResult(
        raw_connectivity=raw_connectivity,
        connectivity=filtered_connectivity,
        nodes=nodes,
    )


def build_interset_synapse_matrix(
    outputs_by_set: dict[str, pd.DataFrame],
    input_sets: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Build a set-to-set synapse matrix from pairwise outputs."""

    labels = list(input_sets)
    matrix = pd.DataFrame(0, index=labels, columns=labels, dtype=int)
    input_ids = {
        label: set(frame["root_id"].astype(str))
        for label, frame in input_sets.items()
    }

    for source_label, outputs in outputs_by_set.items():
        if outputs.empty:
            continue
        post_ids = outputs["post_root_id"].astype(str)
        for target_label in labels:
            mask = post_ids.isin(input_ids[target_label])
            matrix.loc[source_label, target_label] = int(outputs.loc[mask, "syn_count"].sum())
    return matrix


def build_membership_contents(
    nodes_by_set: dict[str, pd.DataFrame],
    display_labels: dict[str, str],
    suffix: str,
) -> dict[str, set[str]]:
    """Build an UpSet-compatible contents dictionary from workflow node tables."""

    return {
        f"{display_labels[set_name]} {suffix}": {
            str(root_id)
            for root_id in nodes["root_id"].dropna().astype(str).unique().tolist()
        }
        for set_name, nodes in nodes_by_set.items()
    }


def build_output_to_input_matrix(
    outputs_by_set: dict[str, pd.DataFrame],
    target_nodes_by_set: dict[str, pd.DataFrame],
    display_labels: dict[str, str],
) -> pd.DataFrame:
    """Build a set-by-set matrix of synapses from one order into another order's node sets."""

    ordered_labels = [display_labels[set_name] for set_name in display_labels]
    matrix = pd.DataFrame(0, index=ordered_labels, columns=ordered_labels, dtype=int)
    target_ids = {
        set_name: set(frame["root_id"].dropna().astype(str))
        for set_name, frame in target_nodes_by_set.items()
    }

    for source_set_name, outputs in outputs_by_set.items():
        source_label = display_labels[source_set_name]
        post_ids = outputs["post_root_id"].astype(str)
        for target_set_name, label in display_labels.items():
            mask = post_ids.isin(target_ids[target_set_name])
            matrix.loc[source_label, label] = int(outputs.loc[mask, "syn_count"].sum())
    return matrix


def _sort_columns_by_convergence(matrix: pd.DataFrame) -> pd.DataFrame:
    if matrix.empty or matrix.shape[1] == 0:
        return matrix

    ordered_rows = matrix.index.tolist()
    nonzero = matrix.ne(0)
    display_order = (
        nonzero.T
        .sort_values(by=ordered_rows[::-1], ascending=True)
        .index
    )
    return matrix.loc[ordered_rows, display_order]


def build_set_to_target_heatmap_matrix(
    connectivity_by_set: dict[str, pd.DataFrame],
    display_labels: dict[str, str],
) -> pd.DataFrame:
    """Build a set-by-target matrix used for the set-to-2N and 2N-to-3N heatmaps."""

    ordered_labels = [display_labels[set_name] for set_name in display_labels]
    grouped_by_set: dict[str, pd.Series] = {}
    ordered_targets: list[object] = []

    for set_name, connectivity in connectivity_by_set.items():
        grouped = (
            connectivity.groupby("post_root_id")["syn_count"]
            .sum()
            .astype(int)
        )
        grouped_by_set[display_labels[set_name]] = grouped
        for post_root_id in grouped.index.tolist():
            if post_root_id not in ordered_targets:
                ordered_targets.append(post_root_id)

    matrix = pd.DataFrame(0, index=ordered_labels, columns=ordered_targets, dtype=int)
    for label, grouped in grouped_by_set.items():
        if grouped.empty:
            continue
        matrix.loc[label, grouped.index.tolist()] = grouped.to_numpy()
    return _sort_columns_by_convergence(matrix)


def get_synapse_counts_for_set(
    set_df: pd.DataFrame | pd.Series,
    connections: pd.DataFrame,
    min_synapses: int = 5,
) -> pd.DataFrame:
    """Aggregate total input and output synapses for a root-id set."""

    roots = as_root_id_frame(set_df)
    conn = connections.loc[connections["syn_count"] >= min_synapses]

    outputs = (
        conn.groupby("pre_root_id")["syn_count"]
        .sum()
        .reset_index()
        .rename(columns={"pre_root_id": "root_id", "syn_count": "output_synapses"})
    )
    inputs = (
        conn.groupby("post_root_id")["syn_count"]
        .sum()
        .reset_index()
        .rename(columns={"post_root_id": "root_id", "syn_count": "input_synapses"})
    )

    synapse_counts = roots.merge(outputs, on="root_id", how="left").merge(inputs, on="root_id", how="left")
    synapse_counts[["output_synapses", "input_synapses"]] = (
        synapse_counts[["output_synapses", "input_synapses"]]
        .fillna(0)
        .astype(int)
    )
    return synapse_counts


def count_nt_categories(
    connectivity: pd.DataFrame,
    location: str | None = None,
    metric: str = "connections",
) -> dict[str, int]:
    """Count neurotransmitter categories by connection rows or summed synapses."""

    if location is not None:
        subset = connectivity.loc[connectivity["location_of_connection"] == location]
    else:
        subset = connectivity

    if metric == "connections":
        counts = {
            "ACH": int((subset["nt_type"] == "ACH").sum()),
            "GABA": int((subset["nt_type"] == "GABA").sum()),
            "GLUT": int((subset["nt_type"] == "GLUT").sum()),
            "Other": int(subset["nt_type"].isin(SECONDARY_NTS).sum()),
        }
        return counts

    if metric == "synapses":
        counts = {
            "ACH": int(subset.loc[subset["nt_type"] == "ACH", "syn_count"].sum()),
            "GABA": int(subset.loc[subset["nt_type"] == "GABA", "syn_count"].sum()),
            "GLUT": int(subset.loc[subset["nt_type"] == "GLUT", "syn_count"].sum()),
            "Other": int(subset.loc[subset["nt_type"].isin(SECONDARY_NTS), "syn_count"].sum()),
        }
        return counts

    raise ValueError("metric must be either 'connections' or 'synapses'.")
