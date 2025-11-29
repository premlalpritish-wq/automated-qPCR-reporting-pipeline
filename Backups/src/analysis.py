import pandas as pd
import numpy as np
from typing import Dict


def compute_mean_ct(df: pd.DataFrame) -> pd.DataFrame:
    # returns DataFrame indexed by Sample, Target with mean CT and n_rep
    summary = df.groupby(['Sample', 'Target'])['CT'].agg(
        ['mean', 'count', 'std']).reset_index()
    summary = summary.rename(
        columns={'mean': 'CT_mean', 'count': 'n_rep', 'std': 'CT_sd'})
    return summary


def compute_delta_ct(summary_df: pd.DataFrame, housekeeping: str) -> pd.DataFrame:
    # summary_df: columns Sample,Target,CT_mean
    pivot = summary_df.pivot(
        index='Sample', columns='Target', values='CT_mean')
    if housekeeping not in pivot.columns:
        raise KeyError(f"Housekeeping {housekeeping} missing from data")
    # ΔCT = CT(target) - CT(housekeeping)
    delta = pivot.subtract(pivot[housekeeping], axis=0)
    delta = delta.drop(columns=[housekeeping], errors='ignore')
    # convert back to long form
    delta_long = delta.stack().reset_index()
    delta_long.columns = ['Sample', 'Target', 'DeltaCT']
    return delta_long


def compute_ddct(delta_df: pd.DataFrame, control_sample_name: str) -> pd.DataFrame:
    """
    Compute DeltaDeltaCT and FoldChange robustly.

    - If an exact control sample name exists in delta_df['Sample'], use it.
    - Otherwise, treat control_sample_name as a keyword and use the mean ΔCT
      of samples whose Sample string contains that keyword (case-insensitive).
    - If no control samples are found, DeltaDeltaCT will be NaN and FoldChange NaN.
    """
    import numpy as np

    df = delta_df.copy()
    # ensure columns
    if not {"Sample", "Target", "DeltaCT"}.issubset(df.columns):
        raise KeyError(
            "delta_df must contain columns: Sample, Target, DeltaCT")

    # find control rows
    ctrl_exact = df[df["Sample"] == control_sample_name]
    if not ctrl_exact.empty:
        # control provided as exact sample name(s)
        control_means = ctrl_exact.set_index('Target')['DeltaCT']
    else:
        # treat control_sample_name as a keyword and match samples containing it (case-insensitive)
        keyword = str(control_sample_name).lower()
        ctrl_matches = df[df['Sample'].str.lower(
        ).str.contains(keyword, na=False)]
        if not ctrl_matches.empty:
            control_means = ctrl_matches.groupby('Target')['DeltaCT'].mean()
        else:
            # no control found: create empty series (will lead to NaNs below)
            control_means = pd.Series(dtype=float)

    # compute DeltaDeltaCT per row: ΔΔCT = ΔCT(sample) - control_mean_for_target
    def _get_control_mean_for_target(target):
        try:
            return float(control_means.loc[target])
        except Exception:
            return np.nan

    df['DeltaDeltaCT'] = df.apply(lambda row: (
        row['DeltaCT'] - _get_control_mean_for_target(row['Target'])), axis=1)
    # Fold change: 2^(-ΔΔCT)
    df['FoldChange'] = df['DeltaDeltaCT'].apply(
        lambda x: float(2 ** (-x)) if pd.notna(x) else float('nan'))
    return df
