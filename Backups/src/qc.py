from typing import Dict, List, Tuple
import pandas as pd
import numpy as np


def ntc_check(df: pd.DataFrame, ntc_name="NTC", ntc_threshold=35.0) -> Dict:
    # find NTC wells for each target
    df_ntc = df[df['Sample'].str.contains(ntc_name, na=False)]
    results = {}
    for target, g in df_ntc.groupby('Target'):
        if g['CT'].isna().all():
            results[target] = {"status": "pass",
                               "notes": "No amplification in NTC"}
        else:
            max_ct = g['CT'].max(skipna=True)
            if max_ct >= ntc_threshold or np.isnan(max_ct):
                results[target] = {"status": "pass",
                                   "notes": f"Max NTC CT {max_ct}"}
            else:
                results[target] = {"status": "fail",
                                   "notes": f"NTC amplification at CT {max_ct}"}
    return results


def replicate_variance_check(df: pd.DataFrame, variance_limit=0.3) -> List[Dict]:
    fails = []
    for (sample, target), g in df.groupby(['Sample', 'Target']):
        ct = g['CT'].dropna()
        if len(ct) <= 1:
            # can't compute variance — treat as warning
            continues = {"sample": sample, "target": target,
                         "status": "warn", "notes": "insufficient replicates"}
            fails.append(continues)
            continue
        sd = float(ct.std(ddof=0))
        rng = float(ct.max() - ct.min())
        if sd > variance_limit or rng > variance_limit:
            fails.append({"sample": sample, "target": target,
                         "status": "fail", "sd": sd, "range": rng})
        else:
            fails.append({"sample": sample, "target": target,
                         "status": "pass", "sd": sd, "range": rng})
    return fails


def housekeeping_consistency(df: pd.DataFrame, hk_genes: List[str], var_limit=0.3) -> Dict:
    df_hk = df[df['Target'].isin(hk_genes)]
    results = {}
    for hk in hk_genes:
        g = df_hk[df_hk['Target'] == hk]
        if g.empty:
            results[hk] = {"status": "missing",
                           "notes": "No housekeeping measurements"}
            continue
        sd = float(g['CT'].dropna().std(ddof=0))
        results[hk] = {"status": "pass" if sd <=
                       var_limit else "fail", "sd": sd}
    return results
