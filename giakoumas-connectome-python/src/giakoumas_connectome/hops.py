"""Hop-count and Sankey helpers extracted from the hop-visualization notebooks."""

from __future__ import annotations

import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Iterable, Mapping

from . import _runtime  # noqa: F401

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .analysis import aggregate_pairwise_outputs, as_root_id_frame
from .config import get_workflow_config
from .constants import HOP_COLOR_MAP, HOP_ORDER
from .data import discover_project_root, load_named_input_tables, load_workflow_inputs
from .plots import apply_plot_style

MXLBN_INPUT_PATHS = {
    "Sugar/Water": "data/input/MxLbN-SA/sugar_water_GRNs.csv",
    "Bitter": "data/input/MxLbN-SA/bitter_GRNs.csv",
    "Ir94e": "data/input/MxLbN-SA/Ir94e_GRNs.csv",
    "Taste Peg": "data/input/MxLbN-SA/taste_peg_GRNs.csv",
}


def load_default_hop_collections(project_root: Path | None = None) -> dict[str, dict[str, pd.DataFrame]]:
    """Load the PhN, PSO-SA, and MxLbN sets used by the hop notebooks."""

    resolved_root = discover_project_root(project_root)
    phn = get_workflow_config("phn")
    pso = get_workflow_config("pso-sa")

    phn_inputs = {
        label: frame
        for label, (_, frame) in zip(phn.set_labels, load_workflow_inputs(resolved_root, phn), strict=True)
    }
    pso_inputs = {
        label: frame
        for label, (_, frame) in zip(pso.set_labels, load_workflow_inputs(resolved_root, pso), strict=True)
    }
    mxlbn_inputs = load_named_input_tables(resolved_root, MXLBN_INPUT_PATHS)

    return {
        "StN-SA": phn_inputs,
        "PSO-SA": pso_inputs,
        "MxLbN": mxlbn_inputs,
    }


def flatten_hop_collections(collections: Mapping[str, Mapping[str, pd.DataFrame]]) -> list[tuple[str, pd.DataFrame]]:
    """Flatten grouped collections into ordered Sankey panels."""

    panels: list[tuple[str, pd.DataFrame]] = []
    for collection_name, sets_dict in collections.items():
        for set_label, frame in sets_dict.items():
            panel_label = f"{collection_name} {set_label}" if set_label.lower().startswith("set ") else set_label
            panels.append((panel_label, frame))
    return panels


def build_thresholded_adjacency(
    connections: pd.DataFrame,
    *,
    min_synapses: int = 5,
) -> defaultdict[int, set[int]]:
    """Build a pair-thresholded adjacency list for hop searches."""

    edge_df = (
        connections.groupby(["pre_root_id", "post_root_id"], as_index=False)
        .agg(syn_count=("syn_count", "sum"))
        .loc[lambda frame: frame["syn_count"] >= min_synapses, ["pre_root_id", "post_root_id"]]
    )

    adjacency: defaultdict[int, set[int]] = defaultdict(set)
    for pre_root_id, post_root_id in edge_df.itertuples(index=False):
        adjacency[int(pre_root_id)].add(int(post_root_id))
    return adjacency


def compute_hop_counts(
    source_ids: pd.DataFrame | pd.Series | Iterable[int],
    adjacency: Mapping[int, set[int]],
    superclass_lookup: Mapping[int, str],
    *,
    target_class: str,
    max_hops: int = 3,
) -> pd.DataFrame:
    """Count how many source neurons reach a target superclass within 1..N hops."""

    if isinstance(source_ids, (pd.DataFrame, pd.Series)):
        roots = as_root_id_frame(source_ids)["root_id"].astype(int).unique().tolist()
    else:
        roots = [int(root_id) for root_id in source_ids]

    counts = {hop: 0 for hop in HOP_ORDER}
    for source_root_id in roots:
        if source_root_id not in adjacency:
            counts[">3"] += 1
            continue

        visited = {source_root_id}
        queue = deque([(source_root_id, 0)])
        found_hop: int | None = None

        while queue and found_hop is None:
            node, distance = queue.popleft()
            if distance >= max_hops:
                continue
            for neighbor in adjacency[node]:
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                next_distance = distance + 1
                if superclass_lookup.get(neighbor) == target_class:
                    found_hop = next_distance
                    break
                queue.append((neighbor, next_distance))

        if found_hop in (1, 2, 3):
            counts[str(found_hop)] += 1
        else:
            counts[">3"] += 1

    return pd.DataFrame({"hop": HOP_ORDER, "count": [counts[hop] for hop in HOP_ORDER]})


def plot_hop_grid(
    collections: Mapping[str, Mapping[str, pd.DataFrame]],
    connections: pd.DataFrame,
    classification: pd.DataFrame,
    *,
    targets: tuple[str, ...] = ("motor", "endocrine"),
    min_synapses: int = 5,
    max_hops: int = 3,
) -> tuple[plt.Figure, np.ndarray]:
    """Plot the multi-workflow hop summary grid from the notebook."""

    apply_plot_style()
    adjacency = build_thresholded_adjacency(connections, min_synapses=min_synapses)
    superclass_lookup = classification.set_index("root_id")["super_class"].to_dict()

    n_rows = len(targets)
    n_cols = len(collections)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 5), sharey=False)
    axes = np.array(axes, dtype=object).reshape(n_rows, n_cols)

    for row_index, target_class in enumerate(targets):
        for col_index, (collection_name, sets_dict) in enumerate(collections.items()):
            ax = axes[row_index, col_index]
            all_rows: list[pd.DataFrame] = []
            ordered_labels = list(sets_dict)

            for set_label, roots in sets_dict.items():
                counts = compute_hop_counts(
                    roots,
                    adjacency,
                    superclass_lookup,
                    target_class=target_class,
                    max_hops=max_hops,
                )
                counts["set"] = set_label
                all_rows.append(counts)

            hop_frame = pd.concat(all_rows, ignore_index=True)
            hop_frame["hop"] = pd.Categorical(hop_frame["hop"], HOP_ORDER, ordered=True)
            hop_frame["set"] = pd.Categorical(hop_frame["set"], ordered_labels, ordered=True)
            pivot = hop_frame.pivot(index="set", columns="hop", values="count").fillna(0)

            bottom = np.zeros(len(pivot), dtype=int)
            for hop in HOP_ORDER:
                values = pivot[hop].to_numpy(dtype=int)
                ax.bar(
                    pivot.index,
                    values,
                    bottom=bottom,
                    color=HOP_COLOR_MAP[hop],
                    label=f"{hop} hop{'s' if hop != '1' else ''}",
                )
                bottom += values

            ax.set_title(f"{collection_name} to {target_class.capitalize()}", fontsize=14)
            if row_index == n_rows - 1:
                ax.set_xlabel("Sets", fontsize=12)
            if col_index == 0:
                ax.set_ylabel("Number of Cells", fontsize=12)
            ax.tick_params(labelsize=10)

            if row_index == 0 and col_index == n_cols - 1:
                ax.legend(title="Hops", frameon=False)

    fig.tight_layout()
    return fig, axes


def build_origin_map(collections: Mapping[str, Mapping[str, pd.DataFrame]]) -> dict[int, list[str]]:
    """Map each root ID to every workflow/set label it belongs to."""

    origin_map: dict[int, list[str]] = {}
    for collection_name, sets_dict in collections.items():
        for set_label, frame in sets_dict.items():
            for root_id in as_root_id_frame(frame)["root_id"].astype(int).unique():
                origin_map.setdefault(int(root_id), []).append(f"{collection_name}:{set_label}")
    return origin_map


def find_target_paths_upto_n(
    source_root_id: int,
    adjacency: Mapping[int, set[int]],
    superclass_lookup: Mapping[int, str],
    *,
    target_class: str,
    max_hops: int,
) -> dict[int, list[list[int]]]:
    """Return all shortest target-ending paths within the hop budget."""

    parents: defaultdict[int, list[int]] = defaultdict(list)
    distances = {int(source_root_id): 0}
    queue = deque([int(source_root_id)])
    targets: set[int] = set()

    while queue:
        node = queue.popleft()
        distance = distances[node]
        if distance >= max_hops:
            continue

        for neighbor in adjacency[node]:
            next_distance = distance + 1
            if next_distance > max_hops:
                continue
            if neighbor not in distances:
                distances[neighbor] = next_distance
                queue.append(neighbor)
            if distances[neighbor] == next_distance:
                parents[neighbor].append(node)
            if superclass_lookup.get(neighbor) == target_class:
                targets.add(neighbor)

    if not targets:
        return {}

    def build_paths(node: int) -> list[list[int]]:
        if node == source_root_id:
            return [[source_root_id]]
        paths: list[list[int]] = []
        for parent in parents[node]:
            for path in build_paths(parent):
                paths.append(path + [node])
        return paths

    return {target_root_id: build_paths(target_root_id) for target_root_id in targets}


def build_target_path_tables(
    collections: Mapping[str, Mapping[str, pd.DataFrame]],
    connections: pd.DataFrame,
    classification: pd.DataFrame,
    *,
    target_class: str = "motor",
    min_synapses: int = 5,
    max_hops: int = 2,
) -> dict[str, pd.DataFrame]:
    """Build annotated path tables for the hop-visualization notebook."""

    adjacency = build_thresholded_adjacency(connections, min_synapses=min_synapses)
    superclass_lookup = classification.set_index("root_id")["super_class"].to_dict()
    nerve_lookup = classification.set_index("root_id")["nerve"].fillna("unknown").replace("", "unknown").to_dict()
    origin_map = build_origin_map(collections)

    tables: dict[str, pd.DataFrame] = {}
    target_column = f"{target_class}_root_id"

    for collection_name, sets_dict in collections.items():
        for set_label, roots in sets_dict.items():
            table_key = f"{collection_name}:{set_label}"
            raw_paths: list[tuple[int, int, list[int]]] = []

            for source_root_id in as_root_id_frame(roots)["root_id"].astype(int).unique():
                target_paths = find_target_paths_upto_n(
                    int(source_root_id),
                    adjacency,
                    superclass_lookup,
                    target_class=target_class,
                    max_hops=max_hops,
                )
                for target_root_id, paths in target_paths.items():
                    for path in paths:
                        raw_paths.append((int(source_root_id), int(target_root_id), path))

            if not raw_paths:
                tables[table_key] = pd.DataFrame(columns=["src", target_column, "path_found"])
                continue

            max_nodes = max(len(path) for _, _, path in raw_paths)
            rows: list[dict[str, object]] = []
            for source_root_id, target_root_id, path in raw_paths:
                row = {
                    "src": source_root_id,
                    target_column: target_root_id,
                    "path_found": True,
                }
                for hop_index in range(max_nodes):
                    row[f"hop_{hop_index}"] = path[hop_index] if hop_index < len(path) else ""
                rows.append(row)

            frame = pd.DataFrame(rows)
            if "hop_1" in frame.columns:
                frame["hop_1_superclass"] = frame["hop_1"].map(superclass_lookup).fillna("unknown")
                frame["hop_1_origin"] = frame["hop_1"].map(
                    lambda value: ";".join(origin_map.get(int(value), [])) if value != "" else ""
                )
            if "hop_2" in frame.columns:
                frame["hop_2_nerve"] = frame["hop_2"].map(nerve_lookup).fillna("unknown")

            hop_columns = [column for column in frame.columns if re.fullmatch(r"hop_\d+", column)]
            frame["num_hops"] = frame[hop_columns[1:]].ne("").sum(axis=1) if len(hop_columns) > 1 else 0
            sort_columns = [column for column in ("num_hops", "hop_1_superclass", "hop_1", "hop_1_origin") if column in frame]
            frame = frame.sort_values(sort_columns).reset_index(drop=True)

            ordered_columns = ["src", target_column, "path_found", "hop_0"]
            if "hop_1" in frame.columns:
                ordered_columns.extend(["hop_1", "hop_1_superclass", "hop_1_origin"])
            if "hop_2" in frame.columns:
                ordered_columns.extend(["hop_2", "hop_2_nerve"])
            for hop_index in range(3, max_nodes):
                ordered_columns.append(f"hop_{hop_index}")

            tables[table_key] = frame[ordered_columns]

    return tables


def export_target_path_tables(path_tables: Mapping[str, pd.DataFrame], output_dir: Path) -> dict[str, Path]:
    """Write annotated hop-path tables to disk."""

    output_dir.mkdir(parents=True, exist_ok=True)
    saved: dict[str, Path] = {}

    for table_key, table in path_tables.items():
        if table.empty:
            continue
        safe_name = re.sub(r"[^a-z0-9]+", "_", table_key.lower()).strip("_")
        path = output_dir / f"{safe_name}.csv"
        table.to_csv(path, index=False)
        saved[table_key] = path

    return saved


def build_global_superclass_color_map(classification: pd.DataFrame) -> dict[str, str]:
    """Build the global Sankey color map used across all panels."""

    try:
        import plotly.express as px
    except ModuleNotFoundError as exc:
        raise RuntimeError("The 'plotly' package is required for Sankey figures.") from exc

    all_classes = sorted(classification["super_class"].dropna().unique().tolist())
    palette = px.colors.qualitative.Safe
    return {super_class: palette[index % len(palette)] for index, super_class in enumerate(all_classes)}


def _as_rgba(color: str, alpha: float) -> str:
    try:
        from plotly.colors import hex_to_rgb
    except ModuleNotFoundError as exc:
        raise RuntimeError("The 'plotly' package is required for Sankey figures.") from exc

    if color.startswith("rgba("):
        return color
    if color.startswith("rgb("):
        return color.replace("rgb(", "rgba(").replace(")", f",{alpha})")
    if color.startswith("#"):
        red, green, blue = hex_to_rgb(color)
        return f"rgba({red},{green},{blue},{alpha})"
    return color


def build_hop_connectivity(
    source_roots: pd.DataFrame | pd.Series | Iterable[int],
    connections: pd.DataFrame,
    classification: pd.DataFrame,
    *,
    min_synapses: int = 5,
) -> pd.DataFrame:
    """Build one hop of Sankey connectivity with downstream superclass labels."""

    if isinstance(source_roots, (pd.DataFrame, pd.Series)):
        roots = as_root_id_frame(source_roots)
    else:
        roots = as_root_id_frame(pd.Series(list(source_roots), name="root_id"))
    outputs = aggregate_pairwise_outputs(roots, connections, min_synapses=min_synapses)
    if outputs.empty:
        return pd.DataFrame(columns=["pre_root_id", "post_root_id", "output_super_class", "syn_count"])

    merged = outputs.merge(
        classification[["root_id", "super_class"]],
        left_on="post_root_id",
        right_on="root_id",
        how="left",
    ).drop(columns="root_id")
    merged["output_super_class"] = merged["super_class"].fillna("unknown")
    return merged[["pre_root_id", "post_root_id", "output_super_class", "syn_count"]]


def make_sankey_trace(
    roots: pd.DataFrame | pd.Series,
    title: str,
    connections: pd.DataFrame,
    classification: pd.DataFrame,
    *,
    min_synapses: int = 5,
    color_map: dict[str, str] | None = None,
):
    """Build a Plotly Sankey trace for one neuron set."""

    try:
        import plotly.graph_objects as go
    except ModuleNotFoundError as exc:
        raise RuntimeError("The 'plotly' package is required for Sankey figures.") from exc

    downstream_color_map = color_map or build_global_superclass_color_map(classification)
    source_roots = as_root_id_frame(roots)["root_id"].tolist()
    hop1 = build_hop_connectivity(source_roots, connections, classification, min_synapses=min_synapses)
    hop2 = build_hop_connectivity(hop1["post_root_id"].unique(), connections, classification, min_synapses=min_synapses)
    hop3 = build_hop_connectivity(hop2["post_root_id"].unique(), connections, classification, min_synapses=min_synapses)

    flow1 = (
        hop1.groupby("output_super_class")["syn_count"]
        .sum()
        .reset_index(name="count")
        .assign(source=title)
    )
    merged_12 = pd.merge(
        hop1,
        hop2,
        left_on="post_root_id",
        right_on="pre_root_id",
        suffixes=("_1", "_2"),
    )
    flow2 = (
        merged_12.groupby(["output_super_class_1", "output_super_class_2"])["syn_count_2"]
        .sum()
        .reset_index(name="count")
    )
    merged_23 = pd.merge(
        hop2,
        hop3,
        left_on="post_root_id",
        right_on="pre_root_id",
        suffixes=("_2", "_3"),
    )
    flow3 = (
        merged_23.groupby(["output_super_class_2", "output_super_class_3"])["syn_count_3"]
        .sum()
        .reset_index(name="count")
    )

    column_1 = [title]
    column_2 = [f"1: {value}" for value in sorted(hop1["output_super_class"].dropna().unique().tolist())]
    column_3 = [f"2: {value}" for value in sorted(hop2["output_super_class"].dropna().unique().tolist())]
    column_4 = [f"3: {value}" for value in sorted(hop3["output_super_class"].dropna().unique().tolist())]
    nodes = column_1 + column_2 + column_3 + column_4
    node_index = {node: index for index, node in enumerate(nodes)}

    node_colors = [
        "lightgrey" if node == title else downstream_color_map.get(node.split(": ", 1)[1], "#bdbdbd")
        for node in nodes
    ]

    source: list[int] = []
    target: list[int] = []
    value: list[int] = []
    link_colors: list[str] = []

    def add_links(flow_frame: pd.DataFrame, source_column: str, target_column: str) -> None:
        for _, row in flow_frame.iterrows():
            source_id = node_index[row[source_column]]
            target_id = node_index[row[target_column]]
            source.append(source_id)
            target.append(target_id)
            value.append(int(row["count"]))
            link_colors.append(_as_rgba(node_colors[source_id], 0.5))

    if not flow1.empty:
        flow1 = flow1.rename(columns={"source": "src", "output_super_class": "dst"})
        flow1["dst"] = flow1["dst"].map(lambda value: f"1: {value}")
        add_links(flow1, "src", "dst")

    if not flow2.empty:
        flow2 = flow2.rename(columns={"output_super_class_1": "src", "output_super_class_2": "dst"})
        flow2["src"] = flow2["src"].map(lambda value: f"1: {value}")
        flow2["dst"] = flow2["dst"].map(lambda value: f"2: {value}")
        add_links(flow2, "src", "dst")

    if not flow3.empty:
        flow3 = flow3.rename(columns={"output_super_class_2": "src", "output_super_class_3": "dst"})
        flow3["src"] = flow3["src"].map(lambda value: f"2: {value}")
        flow3["dst"] = flow3["dst"].map(lambda value: f"3: {value}")
        add_links(flow3, "src", "dst")

    incoming = dict.fromkeys(nodes, 0)
    outgoing = dict.fromkeys(nodes, 0)
    for source_id, target_id, edge_value in zip(source, target, value, strict=True):
        outgoing[nodes[source_id]] += edge_value
        incoming[nodes[target_id]] += edge_value
    customdata = [f"Incoming: {incoming[node]}<br>Outgoing: {outgoing[node]}" for node in nodes]

    x_positions = [0.0] * len(column_1) + [0.33] * len(column_2) + [0.66] * len(column_3) + [1.0] * len(column_4)
    y_positions: list[float] = []
    for column in (column_1, column_2, column_3, column_4):
        if len(column) == 1:
            y_positions.append(0.5)
        elif column:
            y_positions.extend(np.linspace(0, 1, len(column)).tolist())

    return go.Sankey(
        name=title,
        arrangement="snap",
        node=dict(
            label=nodes,
            x=x_positions,
            y=y_positions,
            color=node_colors,
            pad=8,
            thickness=12,
            line=dict(color="black", width=0.3),
            customdata=customdata,
            hovertemplate="%{customdata}<extra>%{label}</extra>",
        ),
        link=dict(source=source, target=target, value=value, color=link_colors),
    )


def plot_stacked_sankey_panels(
    panels: list[tuple[str, pd.DataFrame]],
    connections: pd.DataFrame,
    classification: pd.DataFrame,
    *,
    min_synapses: int = 5,
    title: str = "All Sankey Panels in One Portrait Figure",
    panel_height: int = 300,
    width: int = 534,
):
    """Plot the portrait multi-panel Sankey figure from the notebook."""

    try:
        from plotly.subplots import make_subplots
    except ModuleNotFoundError as exc:
        raise RuntimeError("The 'plotly' package is required for Sankey figures.") from exc

    if not panels:
        raise ValueError("Expected at least one Sankey panel.")

    color_map = build_global_superclass_color_map(classification)
    figure = make_subplots(
        rows=len(panels),
        cols=1,
        shared_xaxes=False,
        shared_yaxes=False,
        vertical_spacing=0.02,
        specs=[[{"type": "sankey"}] for _ in panels],
    )

    for row_index, (panel_label, roots) in enumerate(panels, start=1):
        figure.add_trace(
            make_sankey_trace(
                roots,
                panel_label,
                connections,
                classification,
                min_synapses=min_synapses,
                color_map=color_map,
            ),
            row=row_index,
            col=1,
        )

    figure.update_layout(
        height=panel_height * len(panels),
        width=width,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(size=10),
        title=title,
    )
    return figure


def save_plotly_figure(
    figure,
    path: Path,
    *,
    width: int | None = None,
    height: int | None = None,
    scale: int = 2,
) -> Path:
    """Write a Plotly figure to disk with a clear compatibility error if export fails."""

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        figure.write_image(path, width=width, height=height, scale=scale)
    except ValueError as exc:
        raise RuntimeError(
            "Static Plotly export requires compatible Plotly and Kaleido versions. "
            "Install the project dependencies from this package before exporting Sankey figures."
        ) from exc
    return path
