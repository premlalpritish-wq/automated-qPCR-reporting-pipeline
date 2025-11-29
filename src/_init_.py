# src/__init__.py
"""
automated_qpcr package entrypoint.

Expose the main helper functions/modules for external import.
"""
from .parser import read_raw_csv, CT_UNDETERMINED
from .cleaner import normalize_sample_names, detect_outliers_by_replicate
from .qc import ntc_check, replicate_variance_check, housekeeping_consistency
from .analysis import compute_mean_ct, compute_delta_ct, compute_ddct
from .melt import detect_melt_peaks
from .reporter import render_report_md, md_to_pdf

__all__ = [
    "read_raw_csv",
    "CT_UNDETERMINED",
    "normalize_sample_names",
    "detect_outliers_by_replicate",
    "ntc_check",
    "replicate_variance_check",
    "housekeeping_consistency",
    "compute_mean_ct",
    "compute_delta_ct",
    "compute_ddct",
    "detect_melt_peaks",
    "render_report_md",
    "md_to_pdf",
]
