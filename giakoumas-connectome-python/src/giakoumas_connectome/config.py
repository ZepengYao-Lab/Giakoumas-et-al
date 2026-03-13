"""Workflow registry for the standalone notebook project."""

from __future__ import annotations

from .models import WorkflowConfig

WORKFLOWS = {
    "phn": WorkflowConfig(
        key="phn",
        display_name="PhN",
        description="Six-set pharyngeal sensory-axon workflow based on copied inputs from data/input/PhN.",
        notebook_title="PhN Connectome Analysis",
        input_dir="input/PhN",
        output_dirname="phn",
        upstream_label="StN_SAs",
        set_labels=("Set 1", "Set 2", "Set 3", "Set 4", "Set 5", "Set 6"),
        set_colors=("#cf4848", "orange", "#3489eb", "purple", "#66cc66", "gold"),
        second_order_upset_title="Intersections of 2Ns Across StN Sets",
        third_order_upset_title="Intersections of 3Ns Across StN Sets",
        set_to_second_order_title="StN-SA Sets to 2N Connectivity",
        set_axis_label="StN-SA Set",
        second_to_third_order_title="2N to 3N Connectivity by StN-SA Set",
        synapse_counts_title="Synapse Counts for All StN-SA Root IDs",
        highlight_root_ids=(
            720575940625471896,
            720575940610897906,
            720575940634755041,
            720575940635501560,
            720575940645524003,
            720575940604782624,
            720575940641265549,
            720575940619316603,
        ),
    ),
    "pso-sa": WorkflowConfig(
        key="pso-sa",
        display_name="PSO-SA",
        description="Three-set PSO/DCSO workflow based on copied inputs from data/input/PSO_SA.",
        notebook_title="PSO-SA Connectome Analysis",
        input_dir="input/PSO_SA",
        output_dirname="pso_sa",
        upstream_label="PSO_SAs",
        set_labels=("DCSO", "aPhN1", "aPhN2"),
        set_colors=("#cf4848", "orange", "#3489eb"),
        second_order_upset_title="Intersections of 2Ns Across PSO-SA Sets",
        third_order_upset_title="Intersections of 3Ns Across PSO-SA Sets",
        set_to_second_order_title="PSO-SA Sets to 2N Connectivity",
        set_axis_label="PSO-SA Set",
        second_to_third_order_title="2N to 3N Connectivity by PSO-SA Set",
        synapse_counts_title="Synapse Counts for All PSO-SA Root IDs",
        highlight_root_ids=(720575940612420118,),
    ),
    "aphn1": WorkflowConfig(
        key="aphn1",
        display_name="aPhN1-SA",
        description="Three-set aPhN1 workflow based on copied inputs from data/input/aPhN/aPhN1.",
        notebook_title="aPhN1-SA Connectome Analysis",
        input_dir="input/aPhN/aPhN1",
        output_dirname="aphn1",
        upstream_label="aPhN1_SAs",
        set_labels=("Set 1", "Set 2", "Set 3"),
        set_colors=("#cf4848", "orange", "#3489eb"),
        second_order_upset_title="Intersections of 2Ns Across aPhN1-SA Sets",
        third_order_upset_title="Intersections of 3Ns Across aPhN1-SA Sets",
        set_to_second_order_title="aPhN1-SA Sets to 2N Connectivity",
        set_axis_label="aPhN1-SA Set",
        second_to_third_order_title="2N to 3N Connectivity by aPhN1-SA Set",
        synapse_counts_title="Synapse Counts for All aPhN1-SA Root IDs",
    ),
    "aphn2": WorkflowConfig(
        key="aphn2",
        display_name="aPhN2-SA",
        description="Three-set aPhN2 workflow based on copied inputs from data/input/aPhN/aPhN2.",
        notebook_title="aPhN2-SA Connectome Analysis",
        input_dir="input/aPhN/aPhN2",
        output_dirname="aphn2",
        upstream_label="aPhN2_SAs",
        set_labels=("Set 1", "Set 2", "Set 3"),
        set_colors=("#cf4848", "orange", "#3489eb"),
        second_order_upset_title="Intersections of 2Ns Across aPhN2-SA Sets",
        third_order_upset_title="Intersections of 3Ns Across aPhN2-SA Sets",
        set_to_second_order_title="aPhN2-SA Sets to 2N Connectivity",
        set_axis_label="aPhN2-SA Set",
        second_to_third_order_title="2N to 3N Connectivity by aPhN2-SA Set",
        synapse_counts_title="Synapse Counts for All aPhN2-SA Root IDs",
    ),
}

WORKFLOW_ALIASES = {
    "phn": "phn",
    "stn": "phn",
    "stn-sa": "phn",
    "pso-sa": "pso-sa",
    "pso_sa": "pso-sa",
    "dcso": "pso-sa",
    "aphn1": "aphn1",
    "a_phn1": "aphn1",
    "aphn2": "aphn2",
    "a_phn2": "aphn2",
}


def normalize_workflow_name(name: str) -> str:
    """Normalize a user-facing workflow name into a registry key."""

    return WORKFLOW_ALIASES.get(name.strip().lower(), name.strip().lower())


def get_workflow_config(name: str) -> WorkflowConfig:
    """Return the workflow configuration for a user-supplied name."""

    key = normalize_workflow_name(name)
    if key not in WORKFLOWS:
        valid = ", ".join(sorted(WORKFLOWS))
        raise KeyError(f"Unknown workflow '{name}'. Valid workflows: {valid}.")
    return WORKFLOWS[key]
