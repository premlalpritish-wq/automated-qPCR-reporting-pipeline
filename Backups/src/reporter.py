# src/reporter.py
import jinja2
import pandas as pd
from datetime import datetime
import os
import subprocess
import tempfile
import markdown
import matplotlib.pyplot as plt

# Markdown template with embedded images section
TEMPLATE_MD = """
# Automated qPCR Analysis Report

**Experiment:** {{ experiment_name }}
**Date:** {{ date }}
**Analyst:** {{ analyst }}

## Summary of Results
{% for s in summary %}
- {{ s }}
{% endfor %}

## QC Summary

{{ qc_table_md | safe }}

## Cleaned CT Table
{{ ct_table }}

## ΔCT / ΔΔCT Analysis
{{ ddct_table }}

## Plots
{% if plots.replicate_distribution %}
### Replicate distributions
![Replicate distribution]({{ plots.replicate_distribution }})
{% endif %}

{% if plots.ddct_bars %}
### ΔCT / ΔΔCT fold-change
![ΔΔCT fold-change]({{ plots.ddct_bars }})
{% endif %}

{% if plots.fold_change %}
### Fold change (2^-ΔΔCT)
![Fold change]({{ plots.fold_change }})
{% endif %}

{% if plots.melt_examples %}
### Example melt curves
{% for p in plots.melt_examples %}
![Melt curve]({{ p }})
{% endfor %}
{% endif %}

## Interpretation
{{ interpretation }}
"""


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
    return path


def render_report_md(output_path: str, context: dict):
    env = jinja2.Environment()
    tpl = env.from_string(TEMPLATE_MD)
    md = tpl.render(**context)
    # write utf-8 to avoid Windows issues
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)
    return output_path


def md_to_pdf(md_path: str, pdf_path: str):
    # prefer wkhtmltopdf or fallback to pandoc default engine
    try:
        subprocess.check_call(
            ["pandoc", md_path, "-o", pdf_path, "--pdf-engine=wkhtmltopdf"])
        return pdf_path
    except Exception:
        try:
            subprocess.check_call(["pandoc", md_path, "-o", pdf_path])
            return pdf_path
        except Exception as e:
            raise RuntimeError(
                "PDF generation failed. Install wkhtmltopdf or LaTeX.") from e

# -------------------------
# Plot helpers (matplotlib)
# -------------------------


def plot_replicate_distribution(df: pd.DataFrame, out_path: str):
    """
    Boxplot + individual points per Sample/Target combination.
    Expects df with columns: Sample, Target, CT
    """
    ensure_dir(os.path.dirname(out_path))
    # prepare grouping key: Sample | Target
    df_plot = df.copy()
    df_plot['group'] = df_plot['Sample'].astype(
        str) + " | " + df_plot['Target'].astype(str)
    # remove NaN CTs
    df_plot = df_plot.dropna(subset=['CT'])
    groups = df_plot['group'].unique()
    # build lists of CTs per group
    data = [df_plot.loc[df_plot['group'] == g, 'CT'].astype(
        float).values for g in groups]
    plt.figure(figsize=(max(6, len(groups)*0.5), 4))
    # boxplot (matplotlib)
    plt.boxplot(data, labels=groups, showfliers=True)
    # overlay individual points
    for i, g in enumerate(groups, start=1):
        y = df_plot.loc[df_plot['group'] == g, 'CT'].astype(float).values
        x = [i]*len(y)
        plt.scatter(x, y, s=10)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('CT')
    plt.title('Replicate CT distributions (Sample | Target)')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_ddct_bar(ddct_df: pd.DataFrame, out_path: str):
    """
    Bar chart of DeltaDeltaCT and fold changes.
    Expects ddct_df with columns: Sample, Target, DeltaCT, DeltaDeltaCT, FoldChange
    """
    ensure_dir(os.path.dirname(out_path))
    # create pivot or grouped bars by Target with samples on x-axis
    # For simplicity, plot fold-change per Sample|Target
    ddct_df = ddct_df.copy()
    ddct_df['label'] = ddct_df['Sample'].astype(
        str) + " | " + ddct_df['Target'].astype(str)
    labels = ddct_df['label'].tolist()
    fc = ddct_df['FoldChange'].astype(float).tolist()
    x = range(len(labels))
    plt.figure(figsize=(max(6, len(labels)*0.5), 4))
    plt.bar(x, fc)
    plt.xticks(x, labels, rotation=45, ha='right')
    plt.ylabel('Fold change (2^-ΔΔCT)')
    plt.title('Fold change per Sample | Target')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_ddct_values(ddct_df: pd.DataFrame, out_path: str):
    """
    Bar chart of DeltaDeltaCT values (for completeness).
    """
    ensure_dir(os.path.dirname(out_path))
    ddct_df = ddct_df.copy()
    ddct_df['label'] = ddct_df['Sample'].astype(
        str) + " | " + ddct_df['Target'].astype(str)
    labels = ddct_df['label'].tolist()
    values = ddct_df['DeltaDeltaCT'].astype(float).tolist()
    x = range(len(labels))
    plt.figure(figsize=(max(6, len(labels)*0.5), 4))
    plt.bar(x, values)
    plt.xticks(x, labels, rotation=45, ha='right')
    plt.ylabel('ΔΔCT')
    plt.title('ΔΔCT per Sample | Target')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_melt_examples(melt_data: dict, out_dir: str, max_examples: int = 6):
    """
    melt_data: dict keyed by (Sample, Target) -> dict with 'temp' and 'fluo' arrays
    saves up to max_examples PNGs, returns list of file paths
    """
    ensure_dir(out_dir)
    out_files = []
    count = 0
    for (sample, target), series in melt_data.items():
        if count >= max_examples:
            break
        temp = series.get('temp')
        fluo = series.get('fluo')
        if temp is None or fluo is None:
            continue
        fname = os.path.join(
            out_dir, f"melt_{sample}_{target}.png".replace(" ", "_"))
        plt.figure(figsize=(6, 3))
        plt.plot(temp, fluo)
        plt.xlabel('Temperature (°C)')
        plt.ylabel('Fluorescence')
        plt.title(f"Melt: {sample} | {target}")
        plt.tight_layout()
        plt.savefig(fname, dpi=150)
        plt.close()
        out_files.append(fname)
        count += 1
    return out_files

# -------------------------
# High-level wrapper
# -------------------------


def build_plots_and_context(df_ct: pd.DataFrame, ddct_df: pd.DataFrame, melt_data: dict, output_base: str):
    """
    df_ct: original CT DataFrame with columns Sample, Target, CT
    ddct_df: ddct long table (Sample, Target, DeltaCT, DeltaDeltaCT, FoldChange)
    melt_data: as expected by plot_melt_examples
    output_base: directory where report assets will be written (e.g., "reports/assets/run_2025-10-20T12-00-00")
    returns dict of plot paths suitable for the reporter context
    """
    assets_dir = ensure_dir(os.path.join(output_base, "assets"))
    plots = {}
    # replicate distribution
    rd_path = os.path.join(assets_dir, "replicate_distribution.png")
    try:
        plots['replicate_distribution'] = plot_replicate_distribution(
            df_ct, rd_path)
    except Exception as e:
        plots['replicate_distribution'] = None

    # ddct fold-change bar
    fc_path = os.path.join(assets_dir, "fold_change.png")
    try:
        plots['fold_change'] = plot_ddct_bar(ddct_df, fc_path)
    except Exception:
        plots['fold_change'] = None

    # ddct values (ΔΔCT)
    ddct_path = os.path.join(assets_dir, "ddct_values.png")
    try:
        plots['ddct_bars'] = plot_ddct_values(ddct_df, ddct_path)
    except Exception:
        plots['ddct_bars'] = None

    # melt examples (up to 6)
    melt_dir = os.path.join(assets_dir, "melt_examples")
    try:
        melt_files = plot_melt_examples(
            melt_data or {}, melt_dir, max_examples=6)
        plots['melt_examples'] = melt_files
    except Exception:
        plots['melt_examples'] = []

    return plots

# -------------------------
# End of file
# -------------------------
