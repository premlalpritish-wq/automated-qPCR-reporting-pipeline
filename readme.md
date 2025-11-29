Automated qPCR Reporting Pipeline
End-to-end scientific workflow automation for real-world lab data

This project demonstrates a complete raw-data → QC → analysis → report automation pipeline for qPCR experiments. It showcases how repetitive scientific workflows can be converted into fully automated, reproducible, and auditable reporting systems — the same principles used to automate business, R&D, and operational workflows across industries.

Although built around qPCR data, the design reflects a general pattern for robust workflow automation:
structured ingestion → validation → transformation → analysis → standardized output.

🔍 Overview

This automation takes a raw qPCR CSV file and produces a publication-style PDF report containing:

sample name normalization

QC checks (NTC, replicate variance, housekeeping stability)

ΔCT / ΔΔCT analysis

fold-change calculations

automatically generated plots

a clean, styled final PDF report

It is built as a modular, testable Python pipeline, serving as a technical portfolio piece demonstrating depth in:

engineering clean, reusable automation components

structuring complex data workflows

reproducible scientific computation

automated reporting and visualization

⚠️ Data Quality Note (Important)

The example dataset intentionally contains single-replicate measurements and one missing housekeeping gene, to demonstrate how the system handles real-world, imperfect lab data.

The pipeline performs QC checks and marks affected fold-changes as low confidence.
This project showcases workflow automation, not validated biological conclusions.

✨ Key Features
1. Automated QC

NTC contamination detection

Replicate variance scoring

Housekeeping gene consistency checks

Automatic low-confidence annotations

2. Automated Analysis

CT mean aggregation

ΔCT and ΔΔCT calculations

Fold-change computation

Optional bootstrap confidence estimation

3. Automated Visualization

replicate CT distribution plots

ΔΔCT bar plots

fold-change charts

optional melt-curve visuals

4. Automated Reporting

A complete report is generated via:

Markdown → HTML → PDF


with:

consistent formatting

embedded plots

QC tables

interpretation section

optional provenance metadata (config + file hash + git commit)

🧱 Architecture

This pipeline follows a clean, extensible structure:

Raw CSV
   ↓
Parser (src/parser.py)
   ↓
Cleaner (src/cleaner.py)
   ↓
QC Engine (src/qc.py)
   ↓
Analysis Core (src/analysis.py)
   ↓
Plot Generator (src/plots.py)
   ↓
Report Builder (src/reporter.py)
   ↓
Final PDF


Each module is independent and testable, enabling reuse across other automation projects (e.g., ELISA reporting, NGS QC, business analytics pipelines, Excel automations, invoice extraction, etc.).

📂 Repository Structure
.
├── data/
│   └── example_raw.csv
├── reports/
│   └── run_*/      # auto-generated report folders
├── src/
│   ├── cli.py
│   ├── parser.py
│   ├── cleaner.py
│   ├── qc.py
│   ├── analysis.py
│   ├── plots.py
│   ├── reporter.py
│   └── interpretation.py
├── templates/
│   ├── report_template.html
│   └── report_style.css
└── README.md

🚀 Usage
python src/cli.py \
    --input data/example_raw.csv \
    --config config.yml \
    --output-md report.md \
    --output-pdf report.pdf


Outputs:

report.md – intermediate markdown

report.full.html – full HTML version

report.pdf – the final styled report

reports/run_<timestamp>/assets/ – generated plots

💡 Why This Project Matters

Labs and technical teams lose hours weekly to:

manual spreadsheet cleanup

repeated ΔCT / ΔΔCT calculations

inconsistent QC checks

manual plot generation

formatting reports for publication

This pipeline makes those workflows:

stable

repeatable

error-resistant

automated

The same engineering patterns used here apply directly to:

business reporting automations

PDF → structured data extraction

email → CRM routing

automated dashboards

AI-assisted support workflows

any repetitive data→report pipeline

This is why this project is used as a technical depth signal in the broader automation consulting roadmap.

🔭 Roadmap

melt-curve extraction

template selector (academic / clinical / industry)

web dashboard (upload → PDF)

API-ready service

LIMS / CRM integration

versioned workflows

🔒 Disclaimer

This project is an engineering demonstration.
It is not a diagnostic tool and should be validated before use in regulated workflows.