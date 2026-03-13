from __future__ import annotations

import pandas as pd

from giakoumas_workflow.analysis import (
    aggregate_pairwise_outputs,
    build_second_order,
    build_third_order,
    classify_neurons,
    remove_root_ids,
)


def make_connections() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"pre_root_id": 1, "post_root_id": 10, "neuropil": "GNG", "syn_count": 3, "nt_type": "ACH"},
            {"pre_root_id": 1, "post_root_id": 10, "neuropil": "SMP_R", "syn_count": 4, "nt_type": "ACH"},
            {"pre_root_id": 1, "post_root_id": 2, "neuropil": "GNG", "syn_count": 6, "nt_type": "ACH"},
            {"pre_root_id": 2, "post_root_id": 10, "neuropil": "GNG", "syn_count": 5, "nt_type": "GABA"},
            {"pre_root_id": 10, "post_root_id": 20, "neuropil": "AVLP_R", "syn_count": 6, "nt_type": "ACH"},
            {"pre_root_id": 10, "post_root_id": 1, "neuropil": "GNG", "syn_count": 6, "nt_type": "ACH"},
            {"pre_root_id": 10, "post_root_id": 10, "neuropil": "GNG", "syn_count": 6, "nt_type": "ACH"},
        ]
    )


def test_aggregate_pairwise_outputs_sums_pairs_and_keeps_strongest_annotation() -> None:
    connections = make_connections()
    roots = pd.DataFrame({"root_id": [1, 2]})

    outputs = aggregate_pairwise_outputs(roots, connections, min_synapses=5)

    pair = outputs.loc[
        (outputs["pre_root_id"] == 1) & (outputs["post_root_id"] == 10)
    ].iloc[0]
    assert pair["syn_count"] == 7
    assert pair["neuropil"] == "SMP_R"
    assert pair["location_of_connection"] == "outside_SEZ"


def test_second_order_cleanup_removes_first_order_overlap() -> None:
    connections = make_connections()
    roots = pd.DataFrame({"root_id": [1, 2]})

    second_order = build_second_order(
        sensory_neurons=roots,
        connections=connections,
        set_name="set_1",
        upstream_label="StN_SAs",
        min_synapses=5,
    )
    cleaned, removed = remove_root_ids(second_order, {1, 2})

    assert removed == ["2"]
    assert cleaned.nodes["root_id"].tolist() == [10]
    assert cleaned.connectivity["post_root_id"].tolist() == [10, 10]


def test_classify_neurons_marks_projection_cells() -> None:
    connections = make_connections()
    neurons = pd.DataFrame({"root_id": [10]})

    classified = classify_neurons(neurons, connections, min_synapses=5)

    row = classified.iloc[0]
    assert row["neuron_type"] == "projection"
    assert row["#_projection_synapses"] == 6


def test_third_order_can_optionally_exclude_first_order_roots() -> None:
    connections = make_connections()
    roots = pd.DataFrame({"root_id": [1, 2]})
    second_order = build_second_order(
        sensory_neurons=roots,
        connections=connections,
        set_name="set_1",
        upstream_label="StN_SAs",
        min_synapses=5,
    )
    second_order, _ = remove_root_ids(second_order, {1, 2})

    default_third = build_third_order(
        second_order_connectivity=second_order.connectivity,
        second_order_nodes=second_order.nodes,
        connections=connections,
        set_name="set_1",
        min_second_order_synapses=5,
        min_third_order_synapses=5,
    )
    strict_third = build_third_order(
        second_order_connectivity=second_order.connectivity,
        second_order_nodes=second_order.nodes,
        connections=connections,
        set_name="set_1",
        min_second_order_synapses=5,
        min_third_order_synapses=5,
        extra_excluded_post_root_ids={1, 2},
    )

    assert sorted(default_third.raw_connectivity["post_root_id"].tolist()) == [1, 10, 20]
    assert sorted(default_third.nodes["root_id"].tolist()) == [1, 20]
    assert strict_third.nodes["root_id"].tolist() == [20]
