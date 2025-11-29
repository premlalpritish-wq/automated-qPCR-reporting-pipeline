# src/cli.py
import argparse
from datetime import datetime
import pandas as pd
from parser import read_raw_csv
from cleaner import normalize_sample_names, detect_outliers_by_replicate
from qc import ntc_check, replicate_variance_check, housekeeping_consistency
from analysis import compute_mean_ct, compute_delta_ct, compute_ddct
from reporter import render_report_md, md_to_pdf
from plots import build_plots_and_context
import yaml
import os
from pathlib import Path
import pathlib
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


def _norm_path_for_md(p, output_md):
    """Return a path relative to output_md (for markdown) using forward slashes."""
    if not p:
        return p
    out_md_dir = Path(output_md).resolve().parent
    if isinstance(p, (list, tuple)):
        return [str(Path(x).resolve().relative_to(out_md_dir).as_posix()) for x in p]
    return str(Path(p).resolve().relative_to(out_md_dir).as_posix())


def _to_file_uri(p):
    """Return file:// URI for a single path or list of URIs for a list.
       Return None for falsy/invalid entries so callers can filter them out."""
    if p is None:
        return None
    # list of files -> filter empty and convert each
    if isinstance(p, (list, tuple)):
        out = []
        for itm in p:
            if not itm:
                continue
            try:
                out.append(Path(itm).resolve().as_uri())
            except Exception:
                continue
        return out if out else None
    # single path
    if isinstance(p, str) and p.strip():
        try:
            return Path(p).resolve().as_uri()
        except Exception:
            return None
    return None


def main():
    ap = argparse.ArgumentParser(
        description="Automated qPCR -> report pipeline")
    ap.add_argument("--input", required=True, help="Raw qPCR CSV input")
    ap.add_argument("--config", default="config.yml", help="YAML config file")
    ap.add_argument("--output-md", default="report.md",
                    help="Output Markdown path")
    ap.add_argument("--output-pdf", default=None,
                    help="Output PDF path (optional)")
    args = ap.parse_args()

    # Load config safely
    with open(args.config, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    # Read and normalize raw data
    df = read_raw_csv(args.input)
    df = normalize_sample_names(df)

    # Run QC checks
    qc_ntc = ntc_check(df, ntc_name="NTC",
                       ntc_threshold=cfg['qc']['ntc_ct_threshold'])
    qc_reps = replicate_variance_check(
        df, variance_limit=cfg['qc']['replicate_variance_max'])
    qc_hk = housekeeping_consistency(
        df, cfg['experiment']['housekeeping_genes'], var_limit=cfg['qc']['housekeeping_variance_max'])

    # Analysis
    summary_df = compute_mean_ct(df)
    hk = cfg['experiment']['housekeeping_genes'][0]
    delta = compute_delta_ct(summary_df, hk)
    control_name = cfg['experiment']['control_condition_name']
    ddct = compute_ddct(delta, control_name)

    # Prepare output folder for assets
    run_ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    output_base = os.path.join("reports", f"run_{run_ts}")
    os.makedirs(output_base, exist_ok=True)

    # placeholder for melt curve data if available
    melt_data = {}

    # build plots (this should produce file paths in the output_base/assets folder)
    plots = build_plots_and_context(df, ddct, melt_data, output_base) or {}

    # normalize plot paths for markdown (relative)
    plots_normalized = {}
    for k, v in plots.items():
        plots_normalized[k] = _norm_path_for_md(v, args.output_md)

    # convert normalized relative paths into absolute file:// URIs for wkhtml/pandoc template variables
    plots_clean = {}
    for k, v in plots_normalized.items():
        uri = _to_file_uri(v)
        if uri:
            plots_clean[k] = uri

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

    # build the final context once (with absolute URIs for plots)
    context = {
        "title": cfg['report'].get('title', "Automated qPCR Analysis Report"),
        "experiment_name": cfg['report'].get('experiment_name', "Auto qPCR run"),
        "date": datetime.now().strftime(cfg['report']['date_format']),
        "analyst": cfg['report'].get('author', 'Auto'),
        "summary": summary_lines,
        "qc_table_md": qc_table_md,
        "ct_table": summary_df.to_markdown(index=False),
        "ddct_table": ddct.to_markdown(index=False),
        "plots": plots_clean,
        "logo": cfg['report'].get('logo', "templates/logo.png"),
        "interpretation": generate_interpretation(ddct, qc_ntc, qc_reps, qc_hk)
    }

    # Debugging aid: uncomment to print what plots will be injected
    # print("DEBUG plots_for_template:", plots_clean)

    # Render markdown (this writes YAML front matter + body)
    md = render_report_md(args.output_md, context)
    print("Wrote", md)

    # Generate PDF (if requested)
    if args.output_pdf:
        # Call md_to_pdf - md_to_pdf is robust and will fallback to HTML if PDF engine missing.
        pdf = md_to_pdf(md, args.output_pdf)
        print("Wrote", pdf)


if __name__ == "__main__":
    main()
