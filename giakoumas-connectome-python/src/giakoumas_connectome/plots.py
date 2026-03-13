"""Common plotting functions used by the standalone notebooks and CLI."""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from . import _runtime  # noqa: F401

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LogNorm

from .analysis import (
    build_membership_contents,
    build_output_to_input_matrix,
    build_set_to_target_heatmap_matrix,
    count_nt_categories,
)
from .constants import PRIMARY_NTS, SUPERCLASS_ORDER
from .models import WorkflowReport

ANDY_THEME = {
    "axes.grid": False,
    "grid.linestyle": "--",
    "legend.framealpha": 1,
    "legend.facecolor": "white",
    "legend.shadow": False,
    "legend.fontsize": 14,
    "legend.title_fontsize": 14,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.labelsize": 12,
    "axes.titlesize": 16,
    "figure.dpi": 300,
}

SEZ_COLORS = {"SEZ": "#CCD27F", "Non-SEZ": "#54873A"}
NT_COLOR_MAP = {"ACH": "orange", "GABA": "#1f77b4", "GLUT": "#67afdb", "Other": "gray"}
SUPERCLASS_COLOR_MAP = {
    "sensory": "#dc143c",
    "ascending": "#ffa500",
    "central": "green",
    "descending": "#069af3",
    "motor": "#0000ff",
    "endocrine": "#9a0eea",
    "optic": "#c79fef",
    "visual_projection": "#ffc0cb",
    "visual_centrifugal": "#ff81c0",
}


def _display_label_map(report: WorkflowReport) -> dict[str, str]:
    set_names = list(report.sets)
    set_labels = list(report.workflow.set_labels)
    if len(set_names) != len(set_labels):
        raise ValueError(
            f"Workflow '{report.workflow.key}' defines {len(set_labels)} display labels "
            f"for {len(set_names)} input sets."
        )
    return dict(zip(set_names, set_labels, strict=True))


def _display_labels(report: WorkflowReport) -> list[str]:
    return list(_display_label_map(report).values())


def apply_plot_style() -> None:
    """Apply the original notebook plotting style."""

    sns.set_theme(style="white")
    plt.rcParams.update(ANDY_THEME)
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]


def save_figure(fig: plt.Figure, path: Path) -> Path:
    """Persist a matplotlib figure and return the saved path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format=path.suffix.lstrip(".") or "svg", bbox_inches="tight")
    return path


def plot_first_order_heatmap(
    matrix: pd.DataFrame,
    title: str,
    display_labels: list[str] | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Plot a set-to-set synapse heatmap."""

    apply_plot_style()
    if display_labels is not None:
        frame = matrix.copy()
        frame.index = display_labels
        frame.columns = display_labels
    else:
        frame = matrix

    fig, ax = plt.subplots(figsize=(1.4 * max(len(frame.columns), 3), 1.2 * max(len(frame.index), 3)))
    sns.heatmap(frame, annot=True, fmt="d", cmap="viridis", cbar_kws={"label": "Synapses"}, square=True, ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Downstream set")
    ax.set_ylabel("Upstream set")
    ax.tick_params(axis="x", rotation=0, labelsize=12)
    ax.tick_params(axis="y", rotation=0, labelsize=12)
    return fig, ax


def plot_order_counts(report: WorkflowReport) -> tuple[plt.Figure, plt.Axes]:
    """Plot first-, second-, and third-order node counts per set."""

    apply_plot_style()
    summary = report.summary.copy()
    summary["label"] = _display_labels(report)
    x = np.arange(len(summary))
    width = 0.25

    fig, ax = plt.subplots(figsize=(max(6, len(summary) * 1.4), 4.5))
    ax.bar(x - width, summary["first_order_inputs"], width=width, label="1N inputs", color="#264653")
    ax.bar(x, summary["second_order_nodes"], width=width, label="2Ns", color="#2A9D8F")
    ax.bar(x + width, summary["third_order_nodes"], width=width, label="3Ns", color="#E76F51")
    ax.set_xticks(x)
    ax.set_xticklabels(summary["label"])
    ax.set_ylabel("Neuron count")
    ax.set_title(f"{report.workflow.display_name}: node counts by set")
    ax.legend(frameon=False)
    return fig, ax


def _stacked_bar(
    counts: pd.DataFrame,
    title: str,
    ylabel: str,
    figsize: tuple[float, float] | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    apply_plot_style()
    fig, ax = plt.subplots(figsize=figsize or (max(6, len(counts.index) * 1.4), 4.5))
    counts.plot(kind="bar", stacked=True, ax=ax, width=0.8, color=sns.color_palette("Set2", n_colors=counts.shape[1]))
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Set")
    ax.tick_params(axis="x", rotation=0)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    return fig, ax


def plot_location_outputs(report: WorkflowReport, order: str) -> tuple[plt.Figure, plt.Axes]:
    """Plot SEZ-local vs non-SEZ outputs for the chosen order."""

    apply_plot_style()
    labels = _display_labels(report)
    local_synapses: list[int] = []
    non_sez_synapses: list[int] = []
    for _, set_report in zip(labels, report.sets.values(), strict=True):
        connectivity = set_report.second_order_outputs if order == "second" else set_report.third_order_outputs
        local_synapses.append(
            int(connectivity.loc[connectivity["location_of_connection"] == "local", "syn_count"].sum())
        )
        non_sez_synapses.append(
            int(connectivity.loc[connectivity["location_of_connection"] == "outside_SEZ", "syn_count"].sum())
        )

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(5, 4) if len(labels) <= 3 else (6, 5))
    ax.bar(x, local_synapses, width=0.8, color=SEZ_COLORS["SEZ"], label="SEZ")
    ax.bar(x, non_sez_synapses, width=0.8, bottom=local_synapses, color=SEZ_COLORS["Non-SEZ"], label="Non-SEZ")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=18 if len(labels) <= 3 else 12)
    ax.tick_params(axis="y", labelsize=16 if len(labels) <= 3 else 12)
    ax.set_ylabel("# Synapses", fontsize=20 if len(labels) <= 3 else 14)
    ax.set_title(f"Location of {'2N' if order == 'second' else '3N'} Outputs", fontsize=22 if len(labels) <= 3 else 20)
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    fig.tight_layout()
    return fig, ax


def plot_superclass_distribution(report: WorkflowReport, order: str) -> tuple[plt.Figure, plt.Axes]:
    """Plot superclass counts for second- or third-order nodes."""

    apply_plot_style()
    labels = _display_labels(report)
    rows = []
    for label, set_report in zip(labels, report.sets.values(), strict=True):
        nodes = set_report.second_order_nodes if order == "second" else set_report.third_order_nodes
        superclass_counts = nodes["super_class"].fillna("unknown").value_counts()
        row = {"set_name": label}
        for name, value in superclass_counts.items():
            row[name] = int(value)
        rows.append(row)

    counts = pd.DataFrame(rows).fillna(0).set_index("set_name").astype(int)
    ordered_columns = [name for name in SUPERCLASS_ORDER if name in counts.columns]
    extras = sorted(col for col in counts.columns if col not in ordered_columns)
    counts = counts[ordered_columns + extras]
    colors = [SUPERCLASS_COLOR_MAP.get(column, "#bdbdbd") for column in counts.columns]

    figsize = (6, 5.5) if len(labels) <= 3 else (8, 7) if order == "second" else (8, 4)
    ax = counts.plot(
        kind="bar",
        stacked=True,
        figsize=figsize,
        color=colors,
        width=0.8 if order == "second" else 0.6 if len(labels) <= 3 else 0.8,
        legend=False,
        rot=0,
    )
    fig = ax.figure
    ax.set_title(f"Superclasses of {'2Ns' if order == 'second' else '3Ns'}", fontsize=22 if len(labels) <= 3 else 26 if order == "second" else 20)
    ax.set_ylabel(f"# {'2Ns' if order == 'second' else '3Ns'}", fontsize=16 if order == "second" else 18)
    if order == "second":
        ax.set_xlabel(report.workflow.set_axis_label, fontsize=16)
    else:
        ax.set_xlabel("")
    ax.tick_params(axis="x", labelrotation=0, labelsize=14 if order == "second" else 15)
    ax.tick_params(axis="y", labelsize=14 if order == "second" else 16 if len(labels) <= 3 else 14)
    ax.legend(
        labels=[column.replace("_", " ") for column in counts.columns],
        title="Superclass",
        bbox_to_anchor=(1.02 if order == "second" else 1, 1),
        loc="upper left",
        frameon=False,
        fontsize=12 if order == "second" else 14 if len(labels) <= 3 else 10,
    )
    fig.tight_layout()
    return fig, ax


def plot_nt_distribution(report: WorkflowReport, order: str, location: str) -> tuple[plt.Figure, plt.Axes]:
    """Plot neurotransmitter-type connection counts for a given order and location."""

    apply_plot_style()
    labels = _display_labels(report)
    metric = "connections" if order == "second" else "synapses"
    rows = []
    for label, set_report in zip(labels, report.sets.values(), strict=True):
        connectivity = set_report.second_order_outputs if order == "second" else set_report.third_order_outputs
        counts = count_nt_categories(connectivity, location=location, metric=metric)
        rows.append({"set_name": label, **counts})

    frame = pd.DataFrame(rows).set_index("set_name")
    frame = frame[["ACH", "GABA", "GLUT", "Other"]]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(5, 4) if len(labels) <= 3 else (6, 5))
    bottom = np.zeros(len(labels), dtype=int)
    for nt in ["ACH", "GABA", "GLUT", "Other"]:
        values = frame[nt].to_numpy()
        ax.bar(x, values, width=0.8, bottom=bottom, color=NT_COLOR_MAP[nt], label=nt)
        bottom += values

    location_label = "SEZ" if location == "local" else "Non-SEZ"
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=18 if len(labels) <= 3 else 12)
    ax.tick_params(axis="y", labelsize=14 if len(labels) <= 3 else 12)
    if order == "second":
        ylabel = "# Outputs" if len(labels) <= 3 else "# Connections"
    else:
        ylabel = "Number of Connections"
    ax.set_ylabel(ylabel, fontsize=16 if len(labels) <= 3 else 14)
    ax.set_title(f"NT Types for {'2N' if order == 'second' else '3N'} {location_label} Outputs", fontsize=16)
    ax.legend(title="NT", frameon=False, bbox_to_anchor=(1.02, 1), fontsize=10)
    fig.tight_layout()
    return fig, ax


def plot_top_regions(report: WorkflowReport, order: str, top_n: int = 12) -> tuple[plt.Figure, np.ndarray]:
    """Plot top non-SEZ regions for the chosen order across all sets."""

    apply_plot_style()
    outputs = [
        set_report.second_order_outputs if order == "second" else set_report.third_order_outputs
        for set_report in report.sets.values()
    ]
    combined = pd.concat(outputs, ignore_index=True)
    non_sez = combined.loc[~combined["neuropil_remap"].isin({"GNG", "PRW", "SAD", "FLA", "CAN"})]
    top_regions = (
        non_sez.groupby("neuropil_remap")["syn_count"].sum().sort_values(ascending=False).head(top_n).index.tolist()
    )

    labels = _display_labels(report)
    n_sets = len(labels)
    ncols = 2
    nrows = int(np.ceil(n_sets / ncols))
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(12, 4.2 * nrows))
    axes = np.array(axes).reshape(-1)

    for ax, label, set_report in zip(axes, labels, report.sets.values()):
        connectivity = set_report.second_order_outputs if order == "second" else set_report.third_order_outputs
        subset = connectivity.loc[connectivity["neuropil_remap"].isin(top_regions)]
        data = []
        for region in top_regions:
            region_subset = subset.loc[subset["neuropil_remap"] == region]
            data.append(
                {
                    "region": region,
                    "ACH": int(region_subset.loc[region_subset["nt_type"] == "ACH", "syn_count"].sum()),
                    "GABA": int(region_subset.loc[region_subset["nt_type"] == "GABA", "syn_count"].sum()),
                    "GLUT": int(region_subset.loc[region_subset["nt_type"] == "GLUT", "syn_count"].sum()),
                    "Other": int(
                        region_subset.loc[~region_subset["nt_type"].isin(PRIMARY_NTS), "syn_count"].sum()
                    ),
                }
            )
        frame = pd.DataFrame(data).set_index("region")
        frame.plot(
            kind="bar",
            stacked=True,
            ax=ax,
            width=0.85,
            color=[NT_COLOR_MAP["ACH"], NT_COLOR_MAP["GABA"], NT_COLOR_MAP["GLUT"], NT_COLOR_MAP["Other"]],
        )
        ax.set_title(label)
        ax.set_ylabel("Synapses")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=90)
        legend = ax.get_legend()
        if legend is not None:
            legend.remove()

    for ax in axes[n_sets:]:
        ax.set_visible(False)

    first_visible = next(ax for ax in axes if ax.get_visible())
    handles, legend_labels = first_visible.get_legend_handles_labels()
    fig.legend(handles, legend_labels, bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    fig.suptitle(
        f"{report.workflow.display_name}: top non-SEZ regions for {'2Ns' if order == 'second' else '3Ns'}",
        y=1.02,
    )
    fig.tight_layout()
    return fig, axes


def plot_upset(contents: dict[str, set[str]], title: str) -> tuple[plt.Figure, np.ndarray]:
    """Plot an UpSet diagram using the original notebook settings."""

    try:
        from upsetplot import UpSet, from_contents
    except ModuleNotFoundError as exc:
        raise RuntimeError("The 'upsetplot' package is required to render UpSet figures.") from exc

    if not contents:
        raise ValueError("Cannot build an UpSet figure from an empty contents dictionary.")

    apply_plot_style()
    warnings.filterwarnings("ignore", category=FutureWarning, module="upsetplot")

    upset_data = from_contents(contents)
    fig = plt.figure(figsize=(10, 6), dpi=400)
    upset = UpSet(
        upset_data,
        subset_size="count",
        show_counts=False,
        element_size=30,
        sort_categories_by="-input",
    )
    upset.plot(fig=fig)

    intersection_ax = max(fig.axes, key=lambda ax: len(ax.patches), default=None)
    if intersection_ax is not None:
        for patch in intersection_ax.patches:
            height = patch.get_height()
            if height and height > 0:
                intersection_ax.text(
                    patch.get_x() + patch.get_width() / 2,
                    height,
                    f"{int(height)}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                )

    for ax in fig.axes:
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(axis="x", which="both", labelbottom=False, bottom=False)
        ax.tick_params(axis="y", which="major", labelsize=12)

    fig.suptitle(title, fontsize=16)
    return fig, np.array(fig.axes, dtype=object)


def plot_second_order_upset(report: WorkflowReport) -> tuple[plt.Figure, np.ndarray]:
    """Plot intersections of second-order neurons across sets."""

    label_map = _display_label_map(report)
    contents = build_membership_contents(
        {set_name: set_report.second_order_nodes for set_name, set_report in report.sets.items()},
        label_map,
        suffix="2Ns",
    )
    return plot_upset(contents, title=report.workflow.second_order_upset_title)


def plot_third_order_upset(report: WorkflowReport) -> tuple[plt.Figure, np.ndarray]:
    """Plot intersections of third-order neurons across sets."""

    label_map = _display_label_map(report)
    contents = build_membership_contents(
        {set_name: set_report.third_order_nodes for set_name, set_report in report.sets.items()},
        label_map,
        suffix="3Ns",
    )
    return plot_upset(contents, title=report.workflow.third_order_upset_title)


def plot_second_order_interset_heatmap(report: WorkflowReport) -> tuple[plt.Figure, plt.Axes]:
    """Plot the 2N-to-2N synapse matrix across sets."""

    label_map = _display_label_map(report)
    matrix = build_output_to_input_matrix(
        {set_name: set_report.second_order_outputs for set_name, set_report in report.sets.items()},
        {set_name: set_report.second_order_nodes for set_name, set_report in report.sets.items()},
        label_map,
    )

    apply_plot_style()
    fig, ax = plt.subplots(figsize=(max(6, len(matrix.columns) * 1.7), max(5, len(matrix.index) * 1.5)))
    sns.heatmap(
        matrix,
        cmap="viridis",
        annot=True,
        fmt="d",
        xticklabels=True,
        yticklabels=True,
        square=True,
        vmin=0,
        ax=ax,
    )
    ax.set_title("2N to 2N Synapses", fontsize=18)
    ax.set_ylabel("Upstream 2Ns", fontsize=14)
    ax.set_xlabel("Downstream 2Ns", fontsize=14)
    ax.tick_params(axis="x", rotation=0, labelsize=12)
    ax.tick_params(axis="y", rotation=0, labelsize=12)
    fig.tight_layout()
    return fig, ax


def _plot_target_connectivity_heatmap(
    matrix: pd.DataFrame,
    title: str,
    ylabel: str,
    xlabel: str,
) -> tuple[plt.Figure, plt.Axes]:
    apply_plot_style()
    vmax = int(matrix.to_numpy().max()) if matrix.size else 0
    norm = LogNorm(vmin=1, vmax=max(1, vmax)) if vmax > 0 else None

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        matrix,
        norm=norm,
        cmap=sns.cubehelix_palette(as_cmap=True),
        xticklabels=False,
        yticklabels=True,
        cbar_kws={"label": "# synapses (log scale)" if norm is not None else "# synapses"},
        ax=ax,
    )
    ax.tick_params(axis="y", labelsize=15, rotation=0)
    ax.set_title(title, fontsize=18)
    ax.set_xlabel(xlabel, fontsize=16)
    ax.set_ylabel(ylabel, fontsize=16)
    fig.tight_layout()
    return fig, ax


def plot_set_to_second_order_heatmap(report: WorkflowReport) -> tuple[plt.Figure, plt.Axes]:
    """Plot first-order-set to second-order-node connectivity."""

    label_map = _display_label_map(report)
    matrix = build_set_to_target_heatmap_matrix(
        {set_name: set_report.second_order.connectivity for set_name, set_report in report.sets.items()},
        label_map,
    )
    return _plot_target_connectivity_heatmap(
        matrix,
        title=report.workflow.set_to_second_order_title,
        ylabel=report.workflow.set_axis_label,
        xlabel="2Ns",
    )


def plot_second_to_third_order_heatmap(report: WorkflowReport) -> tuple[plt.Figure, plt.Axes]:
    """Plot 2N-to-3N connectivity by input set."""

    label_map = _display_label_map(report)
    matrix = build_set_to_target_heatmap_matrix(
        {set_name: set_report.third_order.connectivity for set_name, set_report in report.sets.items()},
        label_map,
    )
    return _plot_target_connectivity_heatmap(
        matrix,
        title=report.workflow.second_to_third_order_title,
        ylabel=report.workflow.set_axis_label,
        xlabel="3Ns",
    )


def plot_input_synapse_counts(report: WorkflowReport) -> tuple[plt.Figure, plt.Axes]:
    """Plot total input vs output synapse counts for all first-order root IDs."""

    apply_plot_style()
    fig, ax = plt.subplots(figsize=(8, 6))

    labels = _display_labels(report)
    colors = list(report.workflow.set_colors)
    if len(colors) < len(labels):
        colors.extend(["#808080"] * (len(labels) - len(colors)))

    for label, color, set_report in zip(labels, colors, report.sets.values(), strict=True):
        synapse_counts = set_report.input_synapse_counts
        ax.scatter(
            synapse_counts["input_synapses"],
            synapse_counts["output_synapses"],
            label=label,
            color=color,
            alpha=0.7,
        )

    if report.highlight_synapse_counts is not None and not report.highlight_synapse_counts.empty:
        ax.scatter(
            report.highlight_synapse_counts["input_synapses"],
            report.highlight_synapse_counts["output_synapses"],
            label=report.workflow.highlight_label,
            color="black",
            marker="x",
            s=100,
            alpha=0.7,
        )

    ax.set_xlabel("Total Input Synapses", fontsize=18)
    ax.set_ylabel("Total Output Synapses", fontsize=18)
    ax.set_title(report.workflow.synapse_counts_title, fontsize=20)
    ax.legend(title="Set", loc="upper left", bbox_to_anchor=(1, 1), frameon=False, fontsize=12)
    ax.tick_params(axis="x", labelsize=16)
    ax.tick_params(axis="y", labelsize=16)
    fig.tight_layout()
    return fig, ax


def plot_direct_input_superclasses(
    counts: pd.DataFrame,
    *,
    title: str,
    ylabel: str = "# upstream neurons",
) -> tuple[plt.Figure, plt.Axes]:
    """Plot direct-input superclass counts using the original notebook palette."""

    apply_plot_style()
    figsize = (6, 5.5) if len(counts.index) <= 3 else (8, 6)
    colors = [
        "#9e9e9e" if column == "unclassified" else SUPERCLASS_COLOR_MAP.get(column, "#9e9e9e")
        for column in counts.columns
    ]

    ax = counts.plot(
        kind="bar",
        stacked=True,
        figsize=figsize,
        color=colors,
        width=0.8,
        legend=False,
        rot=0,
    )
    fig = ax.figure
    ax.set_title(title, fontsize=20 if len(counts.index) <= 3 else 18)
    ax.set_ylabel(ylabel, fontsize=16)
    ax.tick_params(axis="x", labelrotation=0, labelsize=14)
    ax.tick_params(axis="y", labelsize=14)
    ax.legend(
        title="Superclass",
        labels=[column.replace("_", " ") for column in counts.columns],
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        frameon=False,
        fontsize=12,
    )
    fig.tight_layout()
    return fig, ax


def plot_direct_input_superclass_nerve(
    counts: pd.DataFrame,
    *,
    title: str,
    ylabel: str = "# upstream neurons",
) -> tuple[plt.Figure, plt.Axes]:
    """Plot direct-input superclass/nerve combinations using the notebook layout."""

    apply_plot_style()
    figsize = (8, 6) if len(counts.index) <= 3 else (10, 6)
    cmap = plt.get_cmap("tab20")
    palette = cmap(np.linspace(0, 1, max(len(counts.columns), 1)))

    ax = counts.plot(
        kind="bar",
        stacked=True,
        figsize=figsize,
        color=palette,
        width=0.8,
        legend=False,
        rot=0,
    )
    fig = ax.figure
    ax.set_title(title, fontsize=18)
    ax.set_ylabel(ylabel, fontsize=16)
    ax.tick_params(axis="x", labelrotation=0, labelsize=14)
    ax.tick_params(axis="y", labelsize=14)
    ax.legend(
        title="Superclass | nerve",
        labels=list(counts.columns),
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        frameon=False,
        fontsize=10,
    )
    fig.tight_layout()
    return fig, ax
