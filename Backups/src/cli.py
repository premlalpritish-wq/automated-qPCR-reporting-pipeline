import argparse
from datetime import datetime
import pandas as pd
from parser import read_raw_csv
from cleaner import normalize_sample_names, detect_outliers_by_replicate
from qc import ntc_check, replicate_variance_check, housekeeping_consistency
from analysis import compute_mean_ct, compute_delta_ct, compute_ddct
from reporter import render_report_md, md_to_pdf, build_plots_and_context
import yaml
import os
from interpretation import generate_interpretation


def qc_summary_to_markdown(qc_ntc, qc_reps, qc_hk):
    """
    Build a small readable markdown table summarizing QC.
    qc_ntc: dict target -> {status, notes}
    qc_reps: list of dicts with keys sample,target,status,notes
    qc_hk: dict gene -> {status, sd, mean_ct, notes}
    """
    rows = []
    # NTC
    if qc_ntc:
        for tgt, info in qc_ntc.items():
            rows.append(
                ("NTC", info.get("status", "unknown"), info.get("notes", "")))
    else:
        rows.append(("NTC", "missing", "No NTC provided"))

    # Replicate variance: summarize counts by status
    if qc_reps:
        warns = [f"{r.get('sample')}|{r.get('target')}" for r in qc_reps if r.get(
            'status') != 'pass']
        notes = "; ".join(warns) if warns else "All replicates OK"
        rows.append(("Replicate variance", "Warn" if warns else "Pass", notes))
    else:
        rows.append(("Replicate variance", "missing", "No replicate QC"))

    # Housekeeping: include per-gene stats if available
    if qc_hk:
        hk_notes = []
        hk_status = "Pass"
        for gene, info in qc_hk.items():
            st = info.get("status", "missing")
            mean = info.get("mean_ct")
            sd = info.get("sd")
            if mean is not None and sd is not None:
                hk_notes.append(f"{gene}: mean={mean:.2f}, SD={sd:.2f} ({st})")
            else:
                hk_notes.append(f"{gene}: {st}")
            if st != "pass":
                hk_status = "Warn"
        rows.append(("Housekeeping", hk_status, "; ".join(hk_notes)))
    else:
        rows.append(("Housekeeping", "missing", "No housekeeping QC"))

    # transform to markdown
    md = "| Test | Status | Notes |\n|---|---|---|\n"
    for t, s, n in rows:
        md += f"| {t} | {s} | {n} |\n"
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--config", default="config.yml")
    ap.add_argument("--output-md", default="report.md")
    ap.add_argument("--output-pdf", default=None)
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    df = read_raw_csv(args.input)
    df = normalize_sample_names(df)

    qc_ntc = ntc_check(df, ntc_name="NTC",
                       ntc_threshold=cfg['qc']['ntc_ct_threshold'])
    qc_reps = replicate_variance_check(
        df, variance_limit=cfg['qc']['replicate_variance_max'])
    qc_hk = housekeeping_consistency(
        df, cfg['experiment']['housekeeping_genes'], var_limit=cfg['qc']['housekeeping_variance_max'])

    summary_df = compute_mean_ct(df)
    # choose first housekeeping for analysis
    hk = cfg['experiment']['housekeeping_genes'][0]
    delta = compute_delta_ct(summary_df, hk)
    control_name = cfg['experiment']['control_condition_name']
    ddct = compute_ddct(delta, control_name)

    # prepare asset folder
    run_ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    output_base = os.path.join("reports", f"run_{run_ts}")
    os.makedirs(output_base, exist_ok=True)

    # { (sample,target): {'temp': np.array([...]), 'fluo': np.array([...])}, ... }
    melt_data = {}

    plots = build_plots_and_context(df, ddct, melt_data, output_base)

    # normalize plot paths to be relative to the report.md location and use forward slashes
    def _norm_path(p):
        if not p:
            return p
        # list of files
        if isinstance(p, list):
            return [os.path.relpath(x, start=os.path.dirname(os.path.abspath(args.output_md))).replace("\\", "/") for x in p]
        return os.path.relpath(p, start=os.path.dirname(os.path.abspath(args.output_md))).replace("\\", "/")

    plots_normalized = {}
    for k, v in plots.items():
        plots_normalized[k] = _norm_path(v)

    # build nicely rounded summary lines
    summary_lines = []
    for _, row in ddct.iterrows():
        fc = row.get("FoldChange")
        if pd.notna(fc):
            summary_lines.append(
                f"{row['Target']} | {row['Sample']}: Fold-change {fc:.2f}")
        else:
            summary_lines.append(
                f"{row['Target']} | {row['Sample']}: Fold-change NA")

    # build QC markdown table
    qc_table_md = qc_summary_to_markdown(qc_ntc, qc_reps, qc_hk)

    # build the context once (with normalized plots)
    context = {
        "experiment_name": "Auto qPCR run",
        "date": datetime.now().strftime(cfg['report']['date_format']),
        "analyst": cfg['report'].get('author', 'Auto'),
        "summary": summary_lines,
        "qc_table_md": qc_table_md,
        "ct_table": summary_df.to_markdown(index=False),
        "ddct_table": ddct.to_markdown(index=False),
        "plots": plots_normalized,
        "interpretation": generate_interpretation(ddct, qc_ntc, qc_reps, qc_hk)
    }

    md = render_report_md(args.output_md, context)
    print("Wrote", md)
    if args.output_pdf:
        pdf = md_to_pdf(md, args.output_pdf)
        print("Wrote", pdf)


if __name__ == "__main__":
    main()
