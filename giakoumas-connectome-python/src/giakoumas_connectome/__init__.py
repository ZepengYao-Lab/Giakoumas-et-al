"""Notebook-friendly Python workflows for the Giakoumas connectome analyses."""

from .config import WORKFLOWS, get_workflow_config
from .hops import load_default_hop_collections
from .inputs import build_direct_input_report, export_direct_input_report
from .reports import build_workflow_report, export_standard_figures, run_full_report, save_report_tables

__all__ = [
    "WORKFLOWS",
    "build_direct_input_report",
    "build_workflow_report",
    "export_direct_input_report",
    "export_standard_figures",
    "get_workflow_config",
    "load_default_hop_collections",
    "run_full_report",
    "save_report_tables",
]
