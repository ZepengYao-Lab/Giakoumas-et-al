"""Command-line interface for the standalone connectome project."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import WORKFLOWS, get_workflow_config
from .reports import run_full_report


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""

    parser = argparse.ArgumentParser(
        prog="giakoumas-connectome",
        description="Run the standalone Giakoumas connectome reports.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List the available workflows.")

    run_parser = subparsers.add_parser("run", help="Run one workflow and export tables and figures.")
    run_parser.add_argument("workflow", help="Workflow key, for example: phn, pso-sa, aphn1, aphn2.")
    run_parser.add_argument("--project-root", type=Path, default=None, help="Standalone project root.")
    run_parser.add_argument("--output-dir", type=Path, default=None, help="Custom output directory.")
    run_parser.add_argument("--min-synapses", type=int, default=5, help="Pair-level synapse threshold.")
    run_parser.add_argument(
        "--exclude-first-order-from-third-order",
        action="store_true",
        help="Also remove first-order sensory IDs from the third-order node list.",
    )
    run_parser.add_argument(
        "--no-figures",
        action="store_true",
        help="Write tables only.",
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
    report = run_full_report(
        workflow=workflow,
        project_root=args.project_root,
        output_dir=args.output_dir,
        min_synapses=args.min_synapses,
        exclude_first_order_from_third_order=args.exclude_first_order_from_third_order,
        export_figures=not args.no_figures,
    )

    print(f"Workflow: {report.workflow.display_name}")
    print(f"Output directory: {report.output_dir}")
    if report.manifest_path is not None:
        print(f"Manifest: {report.manifest_path}")
    for row in report.summary.itertuples(index=False):
        print(
            f"{row.set_name}: "
            f"inputs={row.first_order_inputs}, "
            f"2Ns={row.second_order_nodes}, "
            f"3Ns={row.third_order_nodes}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
