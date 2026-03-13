from __future__ import annotations

import pandas as pd

from giakoumas_connectome.hops import (
    build_target_path_tables,
    build_thresholded_adjacency,
    compute_hop_counts,
    flatten_hop_collections,
)


def make_connections() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"pre_root_id": 1, "post_root_id": 10, "neuropil": "GNG", "syn_count": 6, "nt_type": "ACH"},
            {"pre_root_id": 10, "post_root_id": 20, "neuropil": "GNG", "syn_count": 6, "nt_type": "ACH"},
            {"pre_root_id": 3, "post_root_id": 30, "neuropil": "GNG", "syn_count": 6, "nt_type": "ACH"},
            {"pre_root_id": 2, "post_root_id": 40, "neuropil": "GNG", "syn_count": 6, "nt_type": "ACH"},
        ]
    )


def make_classification() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"root_id": 10, "super_class": "central", "class": "central", "nerve": "PhN"},
            {"root_id": 20, "super_class": "motor", "class": "motor", "nerve": "MxLbN"},
            {"root_id": 30, "super_class": "motor", "class": "motor", "nerve": "AN"},
            {"root_id": 40, "super_class": "central", "class": "central", "nerve": "OCN"},
        ]
    )


def test_compute_hop_counts_counts_each_source_by_minimum_hop_depth() -> None:
    adjacency = build_thresholded_adjacency(make_connections(), min_synapses=5)
    superclass_lookup = make_classification().set_index("root_id")["super_class"].to_dict()

    counts = compute_hop_counts(
        pd.DataFrame({"root_id": [1, 3, 2]}),
        adjacency,
        superclass_lookup,
        target_class="motor",
        max_hops=3,
    )

    by_hop = counts.set_index("hop")["count"]
    assert by_hop.loc["1"] == 1
    assert by_hop.loc["2"] == 1
    assert by_hop.loc[">3"] == 1


def test_build_target_path_tables_annotates_origin_and_hop_metadata() -> None:
    collections = {
        "Test": {"Set A": pd.DataFrame({"root_id": [1, 3]})},
        "PSO-SA": {"DCSO": pd.DataFrame({"root_id": [10]})},
    }

    tables = build_target_path_tables(
        collections,
        make_connections(),
        make_classification(),
        target_class="motor",
        min_synapses=5,
        max_hops=2,
    )

    frame = tables["Test:Set A"]
    path_row = frame.loc[frame["src"] == 1].iloc[0]
    assert path_row["motor_root_id"] == 20
    assert path_row["hop_1"] == 10
    assert path_row["hop_1_superclass"] == "central"
    assert path_row["hop_1_origin"] == "PSO-SA:DCSO"
    assert path_row["hop_2"] == 20
    assert path_row["hop_2_nerve"] == "MxLbN"


def test_flatten_hop_collections_prefixes_generic_set_labels() -> None:
    panels = flatten_hop_collections(
        {
            "StN-SA": {"Set 1": pd.DataFrame({"root_id": [1]})},
            "PSO-SA": {"DCSO": pd.DataFrame({"root_id": [2]})},
        }
    )

    assert panels[0][0] == "StN-SA Set 1"
    assert panels[1][0] == "DCSO"
