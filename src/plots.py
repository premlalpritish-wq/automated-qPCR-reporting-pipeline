# src/plots.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib
matplotlib.use("Agg")


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
    return path


def plot_replicate_distribution(df: pd.DataFrame, out_path: str):
    ensure_dir(os.path.dirname(out_path))

    df_plot = df.copy()
    df_plot = df_plot[~df_plot['CT'].isin(
        [None, '', 'Undetermined', 'NA'])].copy()
    df_plot['CT'] = pd.to_numeric(df_plot['CT'], errors='coerce')
    df_plot = df_plot.dropna(subset=['CT'])

    if df_plot.empty:
        plt.figure(figsize=(6, 3))
        plt.text(0.5, 0.5, "No CT data for replicate distribution", ha='center')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()
        return out_path

    df_plot['group'] = df_plot['Sample'].astype(
        str) + " | " + df_plot['Target'].astype(str)
    groups = df_plot['group'].unique()
    data = [df_plot.loc[df_plot['group'] == g, 'CT'].astype(
        float).values for g in groups]

    plt.figure(figsize=(max(6, len(groups)*0.6), 4))
    plt.boxplot(data, labels=groups, showfliers=True)

    for i, g in enumerate(groups, start=1):
        y = df_plot.loc[df_plot['group'] == g, 'CT'].astype(float).values
        x = np.full_like(y, i, dtype=float)
        plt.scatter(x, y, s=10)

    plt.xticks(rotation=45, ha='right')
    plt.ylabel('CT')
    plt.title('Replicate CT distributions (Sample | Target)')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_ddct_bar(ddct_df: pd.DataFrame, out_path: str):
    ensure_dir(os.path.dirname(out_path))

    if ddct_df is None or ddct_df.empty:
        plt.figure(figsize=(6, 3))
        plt.text(0.5, 0.5, "No ΔΔCT / fold-change data", ha='center')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()
        return out_path

    df = ddct_df.copy()
    df = df.dropna(subset=['FoldChange'])

    if df.empty:
        plt.figure(figsize=(6, 3))
        plt.text(0.5, 0.5, "No fold-change values available", ha='center')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()
        return out_path

    df['label'] = df['Sample'].astype(str) + " | " + df['Target'].astype(str)
    labels = df['label'].tolist()
    fc = df['FoldChange'].astype(float).tolist()

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
    ensure_dir(os.path.dirname(out_path))

    if ddct_df is None or ddct_df.empty:
        plt.figure(figsize=(6, 3))
        plt.text(0.5, 0.5, "No ΔΔCT values", ha='center')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()
        return out_path

    df = ddct_df.copy()
    df = df.dropna(subset=['DeltaDeltaCT'])

    if df.empty:
        plt.figure(figsize=(6, 3))
        plt.text(0.5, 0.5, "No ΔΔCT values available", ha='center')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()
        return out_path

    df['label'] = df['Sample'].astype(str) + " | " + df['Target'].astype(str)
    labels = df['label'].tolist()
    values = df['DeltaDeltaCT'].astype(float).tolist()

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


def build_plots_and_context(df_ct: pd.DataFrame, ddct_df: pd.DataFrame, melt_data: dict, output_base: str):
    assets_dir = ensure_dir(os.path.join(output_base, "assets"))
    plots = {}

    rd_path = os.path.join(assets_dir, "replicate_distribution.png")
    try:
        plots['replicate_distribution'] = plot_replicate_distribution(
            df_ct, rd_path)
    except Exception:
        plots['replicate_distribution'] = None

    fc_path = os.path.join(assets_dir, "fold_change.png")
    try:
        plots['fold_change'] = plot_ddct_bar(ddct_df, fc_path)
    except Exception:
        plots['fold_change'] = None

    ddct_path = os.path.join(assets_dir, "ddct_values.png")
    try:
        plots['ddct_bars'] = plot_ddct_values(ddct_df, ddct_path)
    except Exception:
        plots['ddct_bars'] = None

    melt_dir = os.path.join(assets_dir, "melt_examples")
    try:
        plots['melt_examples'] = plot_melt_examples(
            melt_data or {}, melt_dir, max_examples=6)
    except Exception:
        plots['melt_examples'] = []

    return plots
