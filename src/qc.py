from typing import Dict, List, Any
import pandas as pd
import numpy as np


def ntc_check(
    df: pd.DataFrame,
    ntc_name: str = "NTC",
    ntc_threshold: float = None,
    config: Dict[str, Any] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Backwards-compatible NTC check.
    Accepts either ntc_threshold explicitly (old callers) OR a config dict (new callers).
    Returns: { target: {"status": "pass"|"fail", "notes": str} }
    """
    # resolution order: explicit arg > config > default
    if ntc_threshold is None:
        ntc_threshold = 35.0
        if config and config.get("qc") and "ntc_ct_threshold" in config["qc"]:
            try:
                ntc_threshold = float(config["qc"]["ntc_ct_threshold"])
            except Exception:
                pass

    df_ntc = df[df["Sample"].str.contains(ntc_name, na=False)]
    results: Dict[str, Dict[str, str]] = {}

    for target, g in df_ntc.groupby("Target"):
        if g["CT"].isna().all():
            results[target] = {"status": "pass",
                               "notes": "No amplification in NTC"}
            continue

        # max CT among NTCs for this target
        try:
            max_ct = float(g["CT"].max(skipna=True))
        except Exception:
            max_ct = float("nan")

        if np.isnan(max_ct) or max_ct >= ntc_threshold:
            results[target] = {"status": "pass",
                               "notes": f"Max NTC CT {max_ct}"}
        else:
            results[target] = {"status": "fail",
                               "notes": f"NTC amplification at CT {max_ct}"}

    return results


def replicate_variance_check(
    df: pd.DataFrame,
    variance_limit: float = None,
    config: Dict[str, Any] = None,
) -> List[Dict[str, Any]]:
    """
    Backwards-compatible replicate variance check.
    Accepts either variance_limit explicitly (old callers) OR a config dict (new callers).

    Returns a list of dicts with keys:
      sample, target, n_rep, status (pass|fail|warn), notes(list), ct_mean, ct_sd, ct_range, confidence
    """
    qc_cfg = (config or {}).get("qc", {})
    if variance_limit is None:
        variance_limit = float(qc_cfg.get("replicate_variance_max", 0.3))
    else:
        # ensure numeric
        variance_limit = float(variance_limit)

    min_reps = int(qc_cfg.get("min_replicates", 2))
    range_limit = float(qc_cfg.get("replicate_range_max", variance_limit))

    conf_cfg = (config or {}).get("confidence", {})
    high_cfg = conf_cfg.get("high", {})
    medium_cfg = conf_cfg.get("medium", {})

    results: List[Dict[str, Any]] = []

    for (sample, target), g in df.groupby(["Sample", "Target"]):
        ct_series = g["CT"].dropna().astype(float)
        n_rep = int(len(ct_series))

        entry = {
            "sample": sample,
            "target": target,
            "n_rep": n_rep,
            "status": None,
            "notes": [],
            "ct_mean": None,
            "ct_sd": None,
            "ct_range": None,
            "confidence": "low",
        }

        if n_rep < min_reps:
            entry["status"] = "warn"
            entry["notes"].append("insufficient_replicates")
            if n_rep == 1:
                entry["ct_mean"] = float(ct_series.iloc[0])
            results.append(entry)
            continue

        mean_ct = float(ct_series.mean())
        sd_ct = float(ct_series.std(ddof=1)) if n_rep > 1 else float("nan")
        rng = float(ct_series.max() - ct_series.min())

        entry["ct_mean"] = mean_ct
        entry["ct_sd"] = sd_ct
        entry["ct_range"] = rng

        if (not np.isnan(sd_ct) and sd_ct > variance_limit) or rng > range_limit:
            entry["status"] = "fail"
            entry["notes"].append(
                f"replicate_variance_high (sd={sd_ct:.3f}, range={rng:.3f})")
        else:
            entry["status"] = "pass"

        # Confidence evaluation (best-effort)
        try:
            hc_min_reps = int(high_cfg.get("min_replicates", 3))
            hc_max_var = float(high_cfg.get("max_replicate_variance", 0.2))
            if n_rep >= hc_min_reps and (not np.isnan(sd_ct) and sd_ct <= hc_max_var):
                entry["confidence"] = "high"
            else:
                mc_min_reps = int(medium_cfg.get("min_replicates", 2))
                mc_max_var = float(medium_cfg.get(
                    "max_replicate_variance", 0.5))
                if n_rep >= mc_min_reps and (not np.isnan(sd_ct) and sd_ct <= mc_max_var):
                    entry["confidence"] = "medium"
                else:
                    entry["confidence"] = "low"
        except Exception:
            entry["confidence"] = "low"

        results.append(entry)

    return results


def housekeeping_consistency(
    df: pd.DataFrame,
    hk_genes: List[str],
    var_limit: float = None,
    config: Dict[str, Any] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Backwards-compatible housekeeping consistency check.
    Accepts either var_limit explicitly (old callers) OR config dict.
    Returns: { gene: {"status": "pass"|"fail"|"missing", "sd": float or None, "notes": str } }
    """
    if var_limit is None:
        var_limit = (config or {}).get("qc", {}).get(
            "housekeeping_variance_max", 0.3)
    try:
        var_limit = float(var_limit)
    except Exception:
        var_limit = 0.3

    df_hk = df[df["Target"].isin(hk_genes)]
    results: Dict[str, Dict[str, Any]] = {}

    for hk in hk_genes:
        g = df_hk[df_hk["Target"] == hk]
        if g.empty:
            results[hk] = {"status": "missing", "sd": None,
                           "notes": "No housekeeping measurements"}
            continue

        ct_vals = g["CT"].dropna().astype(float)
        if len(ct_vals) == 0:
            results[hk] = {"status": "missing", "sd": None,
                           "notes": "All housekeeping CTs are NaN"}
            continue

        sd = float(ct_vals.std(ddof=1)) if len(ct_vals) > 1 else float("nan")
        status = "pass" if (not np.isnan(sd) and sd <= var_limit) else "fail"
        notes = ""
        if np.isnan(sd):
            notes = "single replicate only — SD unavailable"
        results[hk] = {"status": status, "sd": sd, "notes": notes}

    return results
