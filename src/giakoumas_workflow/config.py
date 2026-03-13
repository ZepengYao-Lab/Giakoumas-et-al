"""Workflow registry."""

from __future__ import annotations

from .models import WorkflowConfig

WORKFLOWS = {
    "phn": WorkflowConfig(
        key="phn",
        description="Six-set StN/PhN sensory-axon workflow from input/PhN.",
        input_dir="input/PhN",
        output_dirname="phn",
        upstream_label="StN_SAs",
    ),
    "pso-sa": WorkflowConfig(
        key="pso-sa",
        description="Three-set PSO/DCSO sensory-axon workflow from input/PSO_SA.",
        input_dir="input/PSO_SA",
        output_dirname="pso_sa",
        upstream_label="PSO_SAs",
    ),
    "aphn1": WorkflowConfig(
        key="aphn1",
        description="Three-set aPhN1 sensory-axon workflow from input/aPhN/aPhN1.",
        input_dir="input/aPhN/aPhN1",
        output_dirname="aphn1",
        upstream_label="aPhN1_SAs",
    ),
    "aphn2": WorkflowConfig(
        key="aphn2",
        description="Three-set aPhN2 sensory-axon workflow from input/aPhN/aPhN2.",
        input_dir="input/aPhN/aPhN2",
        output_dirname="aphn2",
        upstream_label="aPhN2_SAs",
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
    """Normalize user input into a workflow key."""

    return WORKFLOW_ALIASES.get(name.strip().lower(), name.strip().lower())


def get_workflow_config(name: str) -> WorkflowConfig:
    """Return the workflow configuration for a user-supplied name."""

    key = normalize_workflow_name(name)
    if key not in WORKFLOWS:
        valid = ", ".join(sorted(WORKFLOWS))
        raise KeyError(f"Unknown workflow '{name}'. Valid workflows: {valid}.")
    return WORKFLOWS[key]
