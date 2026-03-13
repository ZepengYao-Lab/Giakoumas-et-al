"""Command-line interface for the streamlined Python workflows."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import WORKFLOWS, get_workflow_config
from .workflow import run_workflow


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""

    parser = argparse.ArgumentParser(
        prog="giakoumas-workflow",
        description="Run streamlined Python workflows for the Giakoumas et al. repository.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List the available workflows.")
    list_parser.set_defaults(command="list")

    run_parser = subparsers.add_parser("run", help="Run one workflow and export fresh CSVs.")
    run_parser.add_argument("workflow", help="Workflow key, for example: phn, pso-sa, aphn1, aphn2.")
    run_parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root. Defaults to the current directory or one of its parents.",
    )
    run_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to <repo>/output/python_workflows/<workflow>.",
    )
    run_parser.add_argument(
        "--min-synapses",
        type=int,
        default=5,
        help="Minimum pair-level synapse threshold used throughout the workflow.",
    )
    run_parser.add_argument(
        "--exclude-first-order-from-third-order",
        action="store_true",
        help="Filter first-order sensory IDs out of third-order outputs.",
    )
    return parser


def _print_workflow_list() -> None:
    for key in sorted(WORKFLOWS):
        workflow = WORKFLOWS[key]
        print(f"{workflow.key}: {workflow.description}")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        _print_workflow_list()
        return 0

    workflow = get_workflow_config(args.workflow)
    result = run_workflow(
        workflow=workflow,
        repository_root=args.repo_root,
        output_dir=args.output_dir,
        min_synapses=args.min_synapses,
        exclude_first_order_from_third_order=args.exclude_first_order_from_third_order,
    )

    print(f"Workflow: {result.workflow.key}")
    print(f"Output directory: {result.output_dir}")
    print(f"Manifest: {result.manifest_path}")
    for row in result.summary.itertuples(index=False):
        print(
            f"{row.set_name}: "
            f"2Ns={row.second_order_nodes}, "
            f"3Ns={row.third_order_nodes}, "
            f"3N edges={row.third_order_edges}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
