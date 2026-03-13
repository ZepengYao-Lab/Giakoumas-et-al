"""Input-side analyses extracted from the PSO/aPhN notebooks."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .analysis import as_root_id_frame
from .constants import DIRECT_INPUT_NERVE_ORDER, DIRECT_INPUT_SUPERCLASS_ORDER
from .models import DirectInputReport, RepositoryTables, WorkflowReport

INPUT_COLUMNS = ["pre_root_id", "post_root_id", "neuropil", "syn_count", "nt_type"]


def _label_map(report: WorkflowReport) -> dict[str, str]:
    set_names = list(report.sets)
    set_labels = list(report.workflow.set_labels)
    if len(set_names) != len(set_labels):
        raise ValueError(
            f"Workflow '{report.workflow.key}' defines {len(set_labels)} display labels "
            f"for {len(set_names)} input sets."
        )
    return dict(zip(set_names, set_labels, strict=True))


def _combined_root_ids(root_id_frames: Iterable[pd.DataFrame | pd.Series]) -> set[str]:
    combined: set[str] = set()
    for frame in root_id_frames:
        combined.update(as_root_id_frame(frame)["root_id"].astype(str))
    return combined


def neuronal_inputs(
    neurons_of_interest: pd.DataFrame | pd.Series,
    connections_df: pd.DataFrame,
    min_synapses: int = 5,
) -> pd.DataFrame:
    """Return notebook-style direct inputs to a postsynaptic neuron set."""

    targets = as_root_id_frame(neurons_of_interest)
    if targets.empty:
        return pd.DataFrame(columns=INPUT_COLUMNS)

    connectivity = targets.merge(
        connections_df[INPUT_COLUMNS],
        left_on="root_id",
        right_on="post_root_id",
        how="inner",
    ).drop(columns="root_id")
    return connectivity.loc[connectivity["syn_count"] >= min_synapses].reset_index(drop=True)


def build_direct_input_root_tables(
    target_sets_by_name: dict[str, pd.DataFrame],
    connections: pd.DataFrame,
    *,
    exclude_self: bool = False,
    min_synapses: int = 5,
) -> dict[str, pd.DataFrame]:
    """Collect unique upstream root IDs for each target set."""

    tables: dict[str, pd.DataFrame] = {}
    for set_name, target_nodes in target_sets_by_name.items():
        upstream = neuronal_inputs(target_nodes, connections, min_synapses=min_synapses)[["pre_root_id"]]
        upstream = upstream.drop_duplicates().reset_index(drop=True)
        if exclude_self:
            blocked_ids = set(as_root_id_frame(target_nodes)["root_id"].astype(str))
            upstream = upstream.loc[~upstream["pre_root_id"].astype(str).isin(blocked_ids)].reset_index(drop=True)
        tables[set_name] = upstream
    return tables


def classify_direct_input_superclasses(
    input_root_tables: dict[str, pd.DataFrame],
    classification: pd.DataFrame,
    label_map: dict[str, str],
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Classify direct inputs by superclass and count them per set."""

    classified_tables: dict[str, pd.DataFrame] = {}
    observed_classes: set[str] = set()

    for set_name, root_table in input_root_tables.items():
        classified = root_table.merge(
            classification[["root_id", "super_class"]],
            left_on="pre_root_id",
            right_on="root_id",
            how="left",
        ).drop(columns="root_id")
        classified["super_class"] = classified["super_class"].fillna("unclassified")
        observed_classes.update(classified["super_class"].unique().tolist())
        classified_tables[set_name] = classified.sort_values(["super_class", "pre_root_id"]).reset_index(drop=True)

    ordered_classes = [name for name in DIRECT_INPUT_SUPERCLASS_ORDER if name in observed_classes]
    extras = sorted(name for name in observed_classes if name not in ordered_classes)
    columns = ordered_classes + extras

    rows: list[dict[str, object]] = []
    for set_name, classified in classified_tables.items():
        counts = classified["super_class"].value_counts()
        row = {"set_label": label_map[set_name]}
        for column in columns:
            row[column] = int(counts.get(column, 0))
        rows.append(row)

    counts_frame = pd.DataFrame(rows).set_index("set_label")
    return classified_tables, counts_frame.astype(int) if not counts_frame.empty else counts_frame


def classify_direct_input_superclass_nerves(
    input_root_tables: dict[str, pd.DataFrame],
    classification: pd.DataFrame,
    label_map: dict[str, str],
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Classify direct inputs by superclass and nerve identity."""

    classified_tables: dict[str, pd.DataFrame] = {}
    combined_tables: list[pd.DataFrame] = []

    super_order = {name: index for index, name in enumerate(DIRECT_INPUT_SUPERCLASS_ORDER)}
    nerve_order = {name: index for index, name in enumerate(DIRECT_INPUT_NERVE_ORDER)}

    for set_name, root_table in input_root_tables.items():
        classified = root_table.merge(
            classification[["root_id", "super_class", "nerve"]],
            left_on="pre_root_id",
            right_on="root_id",
            how="left",
        ).drop(columns="root_id")
        classified["super_class"] = classified["super_class"].fillna("unclassified")
        classified["nerve"] = classified["nerve"].fillna("no_nerve").replace("", "no_nerve")
        classified["superclass_nerve"] = classified["super_class"] + " | " + classified["nerve"]
        classified["set_label"] = label_map[set_name]
        classified_tables[set_name] = classified.sort_values(
            ["super_class", "nerve", "pre_root_id"]
        ).reset_index(drop=True)
        combined_tables.append(classified)

    if not combined_tables:
        return classified_tables, pd.DataFrame()

    combined = pd.concat(combined_tables, ignore_index=True)
    present_pairs = (
        combined[["super_class", "nerve", "superclass_nerve"]]
        .drop_duplicates()
        .assign(
            super_order=lambda frame: frame["super_class"].map(super_order).fillna(len(super_order)),
            nerve_order=lambda frame: frame["nerve"].map(nerve_order).fillna(len(nerve_order)),
        )
        .sort_values(["super_order", "nerve_order", "superclass_nerve"])
    )
    pair_labels = present_pairs["superclass_nerve"].tolist()

    counts = pd.DataFrame(
        0,
        index=[label_map[set_name] for set_name in input_root_tables],
        columns=pair_labels,
        dtype=int,
    )
    for set_name, label in label_map.items():
        label_counts = (
            combined.loc[combined["set_label"] == label, "superclass_nerve"]
            .value_counts()
            .reindex(pair_labels, fill_value=0)
        )
        counts.loc[label, pair_labels] = label_counts.to_numpy()

    return classified_tables, counts


def build_target_input_percentage_table(
    target_nodes: pd.DataFrame | pd.Series,
    connections: pd.DataFrame,
    source_sets: Iterable[pd.DataFrame | pd.Series],
    *,
    min_synapses: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Quantify the fraction of each target neuron's input coming from the source sets."""

    targets = as_root_id_frame(target_nodes)
    inputs = neuronal_inputs(targets, connections, min_synapses=min_synapses)
    source_root_ids = _combined_root_ids(source_sets)
    post_root_ids = inputs["post_root_id"].astype(str) if not inputs.empty else pd.Series(dtype=object)
    pre_root_ids = inputs["pre_root_id"].astype(str) if not inputs.empty else pd.Series(dtype=object)

    rows: list[dict[str, object]] = []
    for root_id in targets["root_id"].tolist():
        neuron_inputs = inputs.loc[post_root_ids == str(root_id)]
        total_input_synapses = int(neuron_inputs["syn_count"].sum())
        source_input_synapses = int(
            neuron_inputs.loc[pre_root_ids.loc[neuron_inputs.index].isin(source_root_ids), "syn_count"].sum()
        )
        rows.append(
            {
                "root_id": root_id,
                "total_input_synapses": total_input_synapses,
                "source_input_synapses": source_input_synapses,
                "source_input_fraction": (
                    float(source_input_synapses / total_input_synapses) if total_input_synapses > 0 else 0.0
                ),
            }
        )

    return inputs, pd.DataFrame(rows)


def build_direct_input_report(
    workflow_report: WorkflowReport,
    tables: RepositoryTables,
    *,
    min_synapses: int = 5,
) -> DirectInputReport:
    """Build the PSO/aPhN direct-input analyses as reusable tables."""

    label_map = _label_map(workflow_report)
    first_order_sets = {
        set_name: set_report.input_nodes
        for set_name, set_report in workflow_report.sets.items()
    }

    second_order_inputs: dict[str, pd.DataFrame] = {}
    second_order_input_percentages: dict[str, pd.DataFrame] = {}
    summary_rows: list[dict[str, object]] = []

    for set_name, set_report in workflow_report.sets.items():
        inputs, percentages = build_target_input_percentage_table(
            set_report.second_order_nodes[["root_id"]],
            tables.connections,
            first_order_sets.values(),
            min_synapses=min_synapses,
        )
        second_order_inputs[set_name] = inputs
        second_order_input_percentages[set_name] = percentages
        fractions = percentages["source_input_fraction"] if not percentages.empty else pd.Series(dtype=float)
        summary_rows.append(
            {
                "set_name": set_name,
                "set_label": label_map[set_name],
                "second_order_neurons": int(len(percentages)),
                "mean_input_fraction_from_sets": float(fractions.mean()) if not fractions.empty else 0.0,
                "median_input_fraction_from_sets": float(fractions.median()) if not fractions.empty else 0.0,
                "min_input_fraction_from_sets": float(fractions.min()) if not fractions.empty else 0.0,
                "max_input_fraction_from_sets": float(fractions.max()) if not fractions.empty else 0.0,
            }
        )

    direct_inputs = build_direct_input_root_tables(
        first_order_sets,
        tables.connections,
        exclude_self=False,
        min_synapses=min_synapses,
    )
    direct_inputs_no_self = build_direct_input_root_tables(
        first_order_sets,
        tables.connections,
        exclude_self=True,
        min_synapses=min_synapses,
    )

    _, direct_input_superclass_counts = classify_direct_input_superclasses(
        direct_inputs,
        tables.classification_other,
        label_map,
    )
    _, direct_input_superclass_counts_no_self = classify_direct_input_superclasses(
        direct_inputs_no_self,
        tables.classification_other,
        label_map,
    )
    direct_input_superclass_nerve_no_self_by_set, direct_input_superclass_nerve_counts_no_self = (
        classify_direct_input_superclass_nerves(
            direct_inputs_no_self,
            tables.classification_other,
            label_map,
        )
    )

    return DirectInputReport(
        second_order_input_percentages=second_order_input_percentages,
        second_order_input_percentage_summary=pd.DataFrame(summary_rows),
        direct_inputs_by_set=direct_inputs,
        direct_inputs_no_self_by_set=direct_inputs_no_self,
        direct_input_superclass_counts=direct_input_superclass_counts,
        direct_input_superclass_counts_no_self=direct_input_superclass_counts_no_self,
        direct_input_superclass_nerve_no_self_by_set=direct_input_superclass_nerve_no_self_by_set,
        direct_input_superclass_nerve_counts_no_self=direct_input_superclass_nerve_counts_no_self,
    )


def export_direct_input_report(report: DirectInputReport, output_dir: Path) -> dict[str, Path]:
    """Write the direct-input analysis tables to disk."""

    table_dir = output_dir / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)

    saved: dict[str, Path] = {}
    summary_path = table_dir / "second_order_input_percentage_summary.csv"
    report.second_order_input_percentage_summary.to_csv(summary_path, index=False)
    saved["second_order_input_percentage_summary"] = summary_path

    superclass_path = table_dir / "direct_input_superclass_counts.csv"
    report.direct_input_superclass_counts.to_csv(superclass_path)
    saved["direct_input_superclass_counts"] = superclass_path

    superclass_no_self_path = table_dir / "direct_input_superclass_counts_excluding_self.csv"
    report.direct_input_superclass_counts_no_self.to_csv(superclass_no_self_path)
    saved["direct_input_superclass_counts_excluding_self"] = superclass_no_self_path

    superclass_nerve_path = table_dir / "direct_input_superclass_nerve_counts_excluding_self.csv"
    report.direct_input_superclass_nerve_counts_no_self.to_csv(superclass_nerve_path)
    saved["direct_input_superclass_nerve_counts_excluding_self"] = superclass_nerve_path

    for set_name, percentages in report.second_order_input_percentages.items():
        set_dir = table_dir / set_name
        set_dir.mkdir(parents=True, exist_ok=True)

        direct_inputs_path = set_dir / f"{set_name}_direct_inputs.csv"
        report.direct_inputs_by_set[set_name].to_csv(direct_inputs_path, index=False)
        saved[f"{set_name}_direct_inputs"] = direct_inputs_path

        direct_inputs_no_self_path = set_dir / f"{set_name}_direct_inputs_excluding_self.csv"
        report.direct_inputs_no_self_by_set[set_name].to_csv(direct_inputs_no_self_path, index=False)
        saved[f"{set_name}_direct_inputs_excluding_self"] = direct_inputs_no_self_path

        percentages_path = set_dir / f"{set_name}_second_order_input_percentages.csv"
        percentages.to_csv(percentages_path, index=False)
        saved[f"{set_name}_second_order_input_percentages"] = percentages_path

        superclass_nerve_table_path = set_dir / f"{set_name}_direct_inputs_superclass_nerve_excluding_self.csv"
        report.direct_input_superclass_nerve_no_self_by_set[set_name].to_csv(
            superclass_nerve_table_path,
            index=False,
        )
        saved[f"{set_name}_direct_inputs_superclass_nerve_excluding_self"] = superclass_nerve_table_path

    return saved
