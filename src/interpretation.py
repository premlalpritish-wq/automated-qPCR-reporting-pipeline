# src/interpretation.py
import numpy as np
import pandas as pd
from typing import Dict, Any, List


def _safe_get(d: Dict, key, default=None):
    try:
        return d.get(key, default)
    except Exception:
        return default


def generate_interpretation(ddct_df: pd.DataFrame,
                            qc_ntc: Dict[str, Dict[str, Any]],
                            qc_reps: List[Dict[str, Any]],
                            qc_hk: Dict[str, Dict[str, Any]]) -> str:
    """
    Robust interpretation generator for qPCR results.

    Inputs:
      - ddct_df: DataFrame with columns ['Sample','Target','DeltaCT','DeltaDeltaCT','FoldChange'] (long form)
      - qc_ntc: dict keyed by Target -> {"status":"pass"/"fail", "notes":...}
      - qc_reps: list of dicts per (sample,target) with 'status' keys
      - qc_hk: dict keyed by housekeeping gene -> {"status": "pass"/"fail"/"missing", "sd": value}

    Returns:
      - Multi-paragraph interpretation string.
    """
    paragraphs: List[str] = []

    # ---------- 1) NTC ----------
    try:
        if qc_ntc and all(v.get("status") == "pass" for v in qc_ntc.values()):
            paragraphs.append(
                "The no-template control (NTC) showed no detectable amplification across targets, "
                "indicating no evidence of contamination or widespread primer-dimer artifacts."
            )
        elif qc_ntc:
            # one or more targets failed NTC
            failed = [t for t, v in qc_ntc.items() if v.get("status")
                      != "pass"]
            paragraphs.append(
                f"NTC amplification was detected for target(s): {', '.join(failed)}; "
                "exercise caution — consider checking reagents and plate setup for contamination."
            )
        else:
            paragraphs.append(
                "No NTC information was available for this run."
            )
    except Exception:
        paragraphs.append(
            "NTC QC could not be evaluated due to unexpected QC output format.")

    # ---------- 2) Housekeeping ----------
    try:
        if not qc_hk:
            paragraphs.append(
                "No housekeeping gene (HK) measurements were provided; normalization could not be validated."
            )
            hk_pass = False
        else:
            # qc_hk is dict per gene
            hk_statuses = {}
            for gene, info in qc_hk.items():
                st = _safe_get(info, "status", "missing")
                hk_statuses[gene] = st

            passed_genes = [g for g, s in hk_statuses.items() if s == "pass"]
            failed_genes = [g for g, s in hk_statuses.items() if s == "fail"]
            missing_genes = [g for g, s in hk_statuses.items()
                             if s in ("missing", None)]

            if passed_genes and not failed_genes:
                paragraphs.append(
                    f"Housekeeping gene(s) {', '.join(passed_genes)} displayed acceptable stability and were used for normalization."
                )
                hk_pass = True
            else:
                notes = []
                if passed_genes:
                    notes.append(f"passed: {', '.join(passed_genes)}")
                if failed_genes:
                    notes.append(f"failed: {', '.join(failed_genes)}")
                if missing_genes:
                    notes.append(f"missing: {', '.join(missing_genes)}")
                paragraphs.append(
                    "Housekeeping QC flags detected (" +
                    "; ".join(notes) + "). "
                    "Normalization may be unreliable for some comparisons."
                )
                hk_pass = False
    except Exception:
        paragraphs.append(
            "Housekeeping QC could not be evaluated due to unexpected QC output format.")
        hk_pass = False

    # ---------- 3) Replicate consistency ----------
        # ---------- 3) Replicate consistency ----------
    try:
        rep_failures = [r for r in (qc_reps or [])
                        if r.get("status") == "fail"]
        if len(rep_failures) == 0:
            paragraphs.append(
                "Technical replicates showed acceptable variance for most samples/targets.")
            reps_ok = True
        else:
            # show up to 5 problematic groups
            sample_targets = [
                f"{r.get('sample')}|{r.get('target')}" for r in rep_failures[:5]]
            paragraphs.append(
                f"Some technical replicate groups showed high variance (examples: {', '.join(sample_targets)}). "
                "These should be inspected — outlier replicate removal or repeat measurements may be needed."
            )
            reps_ok = False
    except Exception:
        paragraphs.append("Replicate variance checks could not be evaluated.")
        reps_ok = False

    # ---------- 4) Expression interpretation ----------
    try:
        if ddct_df is None or ddct_df.empty:
            paragraphs.append(
                "Insufficient data to compute ΔCT/ΔΔCT and fold-changes.")
            # return early
            return "\n\n".join(paragraphs)

        # Ensure required columns exist
        required_cols = {"Sample", "Target",
                         "DeltaCT", "DeltaDeltaCT", "FoldChange"}
        if not required_cols.issubset(set(ddct_df.columns)):
            paragraphs.append(
                "ΔCT/ΔΔCT table missing required columns; cannot generate expression summary.")
            return "\n\n".join(paragraphs)

        # determine control naming strategy: if 'Control' exists use it, else infer samples starting with 'Control'
        controls = ddct_df[ddct_df["Sample"].str.contains("Control", na=False)]
        if controls.empty:
            # try exact 'Control' row fallback
            controls = ddct_df[ddct_df["Sample"] == "Control"]

        # Group by target and summarize
        for target in sorted(ddct_df["Target"].unique()):
            sub = ddct_df[ddct_df["Target"] == target].copy()
            # compute mean ΔCT per sample group (if multiple control samples exist, they were included in ddct_df)
            # calculate mean ΔCT for controls vs non-controls
            ctrl_mask = sub["Sample"].str.contains("Control", na=False)
            exp_mask = ~ctrl_mask

            if ctrl_mask.sum() == 0:
                # No explicit controls found; compute baseline as the minimum ΔCT across samples (conservative)
                baseline = sub["DeltaCT"].min()
            else:
                baseline = sub.loc[ctrl_mask, "DeltaCT"].mean()

            # compute ΔΔCT for experimental samples relative to baseline if not already present
            # (ddct_df may already have DeltaDeltaCT calculated vs a control sample)
            # We will present the mean ΔΔCT for non-control samples if available
            if exp_mask.sum() == 0:
                # only controls present
                paragraphs.append(
                    f"For {target}, only control samples were present; no experimental comparison performed.")
                continue

            exp_rows = sub.loc[exp_mask]
            # if DeltaDeltaCT present, use it; else compute as DeltaCT - baseline
            if "DeltaDeltaCT" in exp_rows.columns:
                mean_ddct = exp_rows["DeltaDeltaCT"].mean()
            else:
                mean_ddct = (exp_rows["DeltaCT"] - baseline).mean()

            mean_fc = exp_rows["FoldChange"].mean(
            ) if "FoldChange" in exp_rows.columns else float(2 ** (-mean_ddct))

            # categorize magnitude
            if mean_ddct <= -3:
                magnitude = "strongly upregulated"
            elif mean_ddct <= -1:
                magnitude = "moderately upregulated"
            elif mean_ddct >= 3:
                magnitude = "strongly downregulated"
            elif mean_ddct >= 1:
                magnitude = "moderately downregulated"
            else:
                magnitude = "not substantially changed"

            paragraphs.append(
                f"For **{target}**, experimental samples show mean ΔΔCT = {mean_ddct:.2f}, "
                f"corresponding to a mean fold change ≈ {mean_fc:.2f}. This suggests the gene is {magnitude}."
            )

    except Exception as e:
        paragraphs.append(
            "Unable to generate expression-level interpretation due to an internal error.")

    # ---------- 5) Confidence statement ----------
    try:
        if (qc_ntc and all(v.get("status") == "pass" for v in qc_ntc.values())) and hk_pass and reps_ok:
            paragraphs.append(
                "All primary QC criteria passed (NTC, housekeeping stability, replicate variance). "
                "The expression changes reported are therefore considered reliable for this run."
            )
        else:
            paragraphs.append(
                "At least one QC criterion failed or raised warnings; interpret fold-change values with caution and consider repeating critical samples."
            )
    except Exception:
        paragraphs.append(
            "Final confidence assessment could not be completed due to unexpected QC formats.")

    return "\n\n".join(paragraphs)
