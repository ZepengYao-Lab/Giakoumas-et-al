from __future__ import annotations

from pathlib import Path

import pandas as pd

from giakoumas_connectome.inputs import (
    build_direct_input_report,
    build_target_input_percentage_table,
    neuronal_inputs,
)
from giakoumas_connectome.models import (
    RepositoryTables,
    SecondOrderResult,
    ThirdOrderResult,
    WorkflowConfig,
    WorkflowReport,
    WorkflowSetReport,
)


def make_connections() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"pre_root_id": 1, "post_root_id": 10, "neuropil": "GNG", "syn_count": 5, "nt_type": "ACH"},
            {"pre_root_id": 2, "post_root_id": 10, "neuropil": "GNG", "syn_count": 5, "nt_type": "ACH"},
            {"pre_root_id": 3, "post_root_id": 10, "neuropil": "GNG", "syn_count": 10, "nt_type": "ACH"},
            {"pre_root_id": 1, "post_root_id": 11, "neuropil": "GNG", "syn_count": 5, "nt_type": "ACH"},
            {"pre_root_id": 4, "post_root_id": 1, "neuropil": "GNG", "syn_count": 6, "nt_type": "ACH"},
            {"pre_root_id": 2, "post_root_id": 1, "neuropil": "GNG", "syn_count": 7, "nt_type": "ACH"},
            {"pre_root_id": 5, "post_root_id": 1, "neuropil": "GNG", "syn_count": 5, "nt_type": "ACH"},
            {"pre_root_id": 1, "post_root_id": 1, "neuropil": "GNG", "syn_count": 8, "nt_type": "ACH"},
            {"pre_root_id": 6, "post_root_id": 2, "neuropil": "GNG", "syn_count": 6, "nt_type": "ACH"},
        ]
    )


def make_tables() -> RepositoryTables:
    classification_other = pd.DataFrame(
        [
            {"root_id": 1, "super_class": "sensory", "class": "sensory", "nerve": "PhN"},
            {"root_id": 2, "super_class": "central", "class": "central", "nerve": "aPhN"},
            {"root_id": 4, "super_class": "sensory", "class": "sensory", "nerve": "AN"},
            {"root_id": 5, "super_class": "motor", "class": "motor", "nerve": "NCC"},
            {"root_id": 6, "super_class": "ascending", "class": "ascending", "nerve": "OCN"},
        ]
    )
    return RepositoryTables(
        connections=make_connections(),
        classification=pd.DataFrame({"root_id": [1, 2], "side": ["L", "R"]}),
        classification_other=classification_other,
        neurons=pd.DataFrame({"root_id": [1, 2], "nt_type": ["ACH", "GABA"]}),
        neurons_data=pd.DataFrame({"root_id": [1, 2], "nt_type": ["ACH", "GABA"]}),
    )


def make_workflow_report() -> WorkflowReport:
    empty_second = SecondOrderResult(connectivity=pd.DataFrame(), nodes=pd.DataFrame())
    empty_third = ThirdOrderResult(raw_connectivity=pd.DataFrame(), connectivity=pd.DataFrame(), nodes=pd.DataFrame())

    workflow = WorkflowConfig(
        key="pso-sa",
        display_name="PSO-SA",
        description="test workflow",
        notebook_title="PSO-SA",
        input_dir="input/PSO_SA",
        output_dirname="pso_sa",
        upstream_label="PSO_SAs",
        set_labels=("DCSO", "aPhN1"),
        set_colors=("#cf4848", "orange"),
        second_order_upset_title="",
        third_order_upset_title="",
        set_to_second_order_title="",
        set_axis_label="PSO-SA Set",
        second_to_third_order_title="",
        synapse_counts_title="",
    )

    sets = {
        "set_1": WorkflowSetReport(
            set_name="set_1",
            input_nodes=pd.DataFrame({"root_id": [1]}),
            input_synapse_counts=pd.DataFrame(),
            first_order_outputs=pd.DataFrame(),
            second_order=empty_second,
            second_order_nodes=pd.DataFrame({"root_id": [10, 11]}),
            second_order_outputs=pd.DataFrame(),
            third_order=empty_third,
            third_order_nodes=pd.DataFrame(),
            third_order_outputs=pd.DataFrame(),
        ),
        "set_2": WorkflowSetReport(
            set_name="set_2",
            input_nodes=pd.DataFrame({"root_id": [2]}),
            input_synapse_counts=pd.DataFrame(),
            first_order_outputs=pd.DataFrame(),
            second_order=empty_second,
            second_order_nodes=pd.DataFrame({"root_id": [20]}),
            second_order_outputs=pd.DataFrame(),
            third_order=empty_third,
            third_order_nodes=pd.DataFrame(),
            third_order_outputs=pd.DataFrame(),
        ),
    }

    return WorkflowReport(
        workflow=workflow,
        project_root=Path("/tmp"),
        output_dir=Path("/tmp/output"),
        sets=sets,
        summary=pd.DataFrame(),
        first_order_set_matrix=pd.DataFrame(),
    )


def test_neuronal_inputs_filters_by_postsynaptic_root_and_threshold() -> None:
    inputs = neuronal_inputs(pd.DataFrame({"root_id": [10]}), make_connections(), min_synapses=5)

    assert sorted(inputs["pre_root_id"].tolist()) == [1, 2, 3]
    assert inputs["post_root_id"].nunique() == 1


def test_build_target_input_percentage_table_matches_notebook_logic() -> None:
    _, percentages = build_target_input_percentage_table(
        pd.DataFrame({"root_id": [10, 11]}),
        make_connections(),
        [pd.DataFrame({"root_id": [1]}), pd.DataFrame({"root_id": [2]})],
        min_synapses=5,
    )

    by_root = percentages.set_index("root_id")
    assert by_root.loc[10, "total_input_synapses"] == 20
    assert by_root.loc[10, "source_input_synapses"] == 10
    assert by_root.loc[10, "source_input_fraction"] == 0.5
    assert by_root.loc[11, "source_input_fraction"] == 1.0


def test_build_direct_input_report_counts_superclasses_and_excludes_self_inputs() -> None:
    report = build_direct_input_report(make_workflow_report(), make_tables(), min_synapses=5)

    summary = report.second_order_input_percentage_summary.set_index("set_label")
    assert summary.loc["DCSO", "mean_input_fraction_from_sets"] == 0.75

    direct_counts = report.direct_input_superclass_counts
    assert direct_counts.loc["DCSO", "sensory"] == 2
    assert direct_counts.loc["DCSO", "central"] == 1
    assert direct_counts.loc["DCSO", "motor"] == 1

    no_self_counts = report.direct_input_superclass_counts_no_self
    assert no_self_counts.loc["DCSO", "sensory"] == 1
    assert no_self_counts.loc["DCSO", "central"] == 1
    assert no_self_counts.loc["DCSO", "motor"] == 1

    nerve_counts = report.direct_input_superclass_nerve_counts_no_self
    assert nerve_counts.loc["DCSO", "sensory | AN"] == 1
    assert nerve_counts.loc["DCSO", "central | aPhN"] == 1
    assert nerve_counts.loc["aPhN1", "ascending | OCN"] == 1
