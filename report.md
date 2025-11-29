---
title: "Auto qPCR run"
experiment_name: "Auto qPCR run"
date: "2025-11-28"
analyst: "Auto-analyst"
logo: "templates/logo.png"
summary:
  - "TargetX | Control_1: Fold-change 1.11"
  - "TargetX | Control_2: Fold-change 0.90"
  - "TargetX | ExpA_1: Fold-change 11.71"
  - "TargetX | ExpA_2: Fold-change 10.93"
qc_table_md: |
  | Test | Status | Notes |
  |---|---|---|
  | NTC | pass | No amplification in NTC |
  | Replicate variance | Warn | Control_1|GAPDH; Control_1|TargetX; Control_2|GAPDH; Control_2|TargetX; ExpA_1|GAPDH; ExpA_1|TargetX; ExpA_2|GAPDH; ExpA_2|TargetX; NTC|TargetX |
  | Housekeeping | Warn | GAPDH: fail; ACTB: missing |
ct_table: |
  | Sample    | Target   |   CT_mean |   n_rep |   CT_sd |
  |:----------|:---------|----------:|--------:|--------:|
  | Control_1 | GAPDH    |      18.4 |       1 |     nan |
  | Control_1 | TargetX  |      22   |       1 |     nan |
  | Control_2 | GAPDH    |      18.6 |       1 |     nan |
  | Control_2 | TargetX  |      22.5 |       1 |     nan |
  | ExpA_1    | GAPDH    |      19.1 |       1 |     nan |
  | ExpA_1    | TargetX  |      19.3 |       1 |     nan |
  | ExpA_2    | GAPDH    |      19.4 |       1 |     nan |
  | ExpA_2    | TargetX  |      19.7 |       1 |     nan |
  | NTC       | TargetX  |     nan   |       0 |     nan |
ddct_table: |
  | Sample    | Target   |   DeltaCT |   DeltaDeltaCT |   FoldChange |
  |:----------|:---------|----------:|---------------:|-------------:|
  | Control_1 | TargetX  |       3.6 |          -0.15 |      1.10957 |
  | Control_2 | TargetX  |       3.9 |           0.15 |      0.90125 |
  | ExpA_1    | TargetX  |       0.2 |          -3.55 |     11.7127  |
  | ExpA_2    | TargetX  |       0.3 |          -3.45 |     10.9283  |
interpretation: |
  The no-template control (NTC) showed no detectable amplification across targets, indicating no evidence of contamination or widespread primer-dimer artifacts.
  
  Housekeeping QC flags detected (failed: GAPDH; missing: ACTB). Normalization may be unreliable for some comparisons.
  
  Technical replicates showed acceptable variance for most samples/targets.
  
  For **TargetX**, experimental samples show mean ΔΔCT = -3.50, corresponding to a mean fold change ≈ 11.32. This suggests the gene is strongly upregulated.
  
  At least one QC criterion failed or raised warnings; interpret fold-change values with caution and consider repeating critical samples.
plots:
  replicate_distribution: "file:///D:/Pritish/Ideas/specialised%20biotech%20automation%20consultant/Portfolio/Project%201/automated_qpcr/reports/run_20251128T200303/assets/replicate_distribution.png"
  fold_change: "file:///D:/Pritish/Ideas/specialised%20biotech%20automation%20consultant/Portfolio/Project%201/automated_qpcr/reports/run_20251128T200303/assets/fold_change.png"
  ddct_bars: "file:///D:/Pritish/Ideas/specialised%20biotech%20automation%20consultant/Portfolio/Project%201/automated_qpcr/reports/run_20251128T200303/assets/ddct_values.png"
---

# Auto qPCR run

**Experiment:** Auto qPCR run
**Date:** 2025-11-28
**Analyst:** Auto-analyst

## Summary of Results

- TargetX | Control_1: Fold-change 1.11
- TargetX | Control_2: Fold-change 0.90
- TargetX | ExpA_1: Fold-change 11.71
- TargetX | ExpA_2: Fold-change 10.93

## QC Summary

| Test | Status | Notes |
|---|---|---|
| NTC | pass | No amplification in NTC |
| Replicate variance | Warn | Control_1|GAPDH; Control_1|TargetX; Control_2|GAPDH; Control_2|TargetX; ExpA_1|GAPDH; ExpA_1|TargetX; ExpA_2|GAPDH; ExpA_2|TargetX; NTC|TargetX |
| Housekeeping | Warn | GAPDH: fail; ACTB: missing |


## Cleaned CT Table

| Sample    | Target   |   CT_mean |   n_rep |   CT_sd |
|:----------|:---------|----------:|--------:|--------:|
| Control_1 | GAPDH    |      18.4 |       1 |     nan |
| Control_1 | TargetX  |      22   |       1 |     nan |
| Control_2 | GAPDH    |      18.6 |       1 |     nan |
| Control_2 | TargetX  |      22.5 |       1 |     nan |
| ExpA_1    | GAPDH    |      19.1 |       1 |     nan |
| ExpA_1    | TargetX  |      19.3 |       1 |     nan |
| ExpA_2    | GAPDH    |      19.4 |       1 |     nan |
| ExpA_2    | TargetX  |      19.7 |       1 |     nan |
| NTC       | TargetX  |     nan   |       0 |     nan |

## ΔCT / ΔΔCT Analysis

| Sample    | Target   |   DeltaCT |   DeltaDeltaCT |   FoldChange |
|:----------|:---------|----------:|---------------:|-------------:|
| Control_1 | TargetX  |       3.6 |          -0.15 |      1.10957 |
| Control_2 | TargetX  |       3.9 |           0.15 |      0.90125 |
| ExpA_1    | TargetX  |       0.2 |          -3.55 |     11.7127  |
| ExpA_2    | TargetX  |       0.3 |          -3.45 |     10.9283  |

## Plots

![replicate_distribution](file:///D:/Pritish/Ideas/specialised%20biotech%20automation%20consultant/Portfolio/Project%201/automated_qpcr/reports/run_20251128T200303/assets/replicate_distribution.png)

![fold_change](file:///D:/Pritish/Ideas/specialised%20biotech%20automation%20consultant/Portfolio/Project%201/automated_qpcr/reports/run_20251128T200303/assets/fold_change.png)

![ddct_bars](file:///D:/Pritish/Ideas/specialised%20biotech%20automation%20consultant/Portfolio/Project%201/automated_qpcr/reports/run_20251128T200303/assets/ddct_values.png)


## Interpretation

The no-template control (NTC) showed no detectable amplification across targets, indicating no evidence of contamination or widespread primer-dimer artifacts.

Housekeeping QC flags detected (failed: GAPDH; missing: ACTB). Normalization may be unreliable for some comparisons.

Technical replicates showed acceptable variance for most samples/targets.

For **TargetX**, experimental samples show mean ΔΔCT = -3.50, corresponding to a mean fold change ≈ 11.32. This suggests the gene is strongly upregulated.

At least one QC criterion failed or raised warnings; interpret fold-change values with caution and consider repeating critical samples.