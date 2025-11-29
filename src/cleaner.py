import pandas as pd
import numpy as np
import re


def normalize_sample_names(df: pd.DataFrame, pattern_map: dict = None) -> pd.DataFrame:
    # Example: unify "ctrl", "control" -> Control
    def norm(s):
        if pd.isna(s):
            return s
        s = s.strip()
        s = re.sub(r"\s+", "_", s)
        s = s.replace("-", "_")
        return s
    df['Sample'] = df['Sample'].apply(norm)
    # apply pattern_map if provided (regex to replacement)
    if pattern_map:
        for pat, repl in pattern_map.items():
            df['Sample'] = df['Sample'].str.replace(pat, repl, regex=True)
    return df


def detect_outliers_by_replicate(df: pd.DataFrame, variance_limit: float):
    outlier_flags = []
    for (sample, target), group in df.groupby(['Sample', 'Target']):
        ct_vals = group['CT'].dropna().values
        if len(ct_vals) == 0:
            outlier_flags.append(((sample, target), "all_undetermined"))
            continue
        sd = float(pd.Series(ct_vals).std(ddof=0))
        rng = float(pd.Series(ct_vals).max() - pd.Series(ct_vals).min())
        if sd > variance_limit or rng > variance_limit:
            outlier_flags.append(((sample, target), dict(sd=sd, rng=rng)))
    return outlier_flags
