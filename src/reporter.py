import os
from datetime import datetime
from pathlib import Path
import shutil
import subprocess

# -----------------------
# YAML BLOCK HELPERS
# -----------------------


def _yaml_block(key: str, value):
    """Render Python types (list/dict/string) into YAML-friendly blocks."""
    out = []
    if isinstance(value, list):
        out.append(f"{key}:")
        if not value:
            out.append("  []")
        else:
            for v in value:
                out.append(f"  - \"{str(v).replace('\"', '\\\"')}\"")
    elif isinstance(value, dict):
        out.append(f"{key}:")
        if not value:
            out.append("  {}")
        else:
            for k, v in value.items():
                out.append(f"  {k}: \"{str(v).replace('\"', '\\\"')}\"")
    else:
        s = str(value)
        out.append(f"{key}: |")
        for line in s.splitlines():
            out.append("  " + line)
    return "\n".join(out)


# -----------------------
# MARKDOWN RENDERING
# -----------------------

def render_report_md(output_md_path: str, context: dict) -> str:
    """Generate markdown with YAML front-matter from structured context."""
    out_path = os.path.abspath(output_md_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    meta = {
        "title": context.get("experiment_name", "Auto qPCR run"),
        "experiment_name": context.get("experiment_name", "Auto qPCR run"),
        "date": context.get("date", datetime.now().strftime("%Y-%m-%d")),
        "analyst": context.get("analyst", "Auto-analyst"),
        "logo": context.get("logo", "logo.png"),
    }

    # ----- YAML FRONT MATTER -----
    fm = ["---"]
    for k, v in meta.items():
        fm.append(f"{k}: \"{str(v).replace('\"', '\\\"')}\"")

    # structured blocks
    if "summary" in context:
        fm.append(_yaml_block("summary", context["summary"]))
    if "qc_table_md" in context:
        fm.append(_yaml_block("qc_table_md", context["qc_table_md"]))
    if "ct_table" in context:
        fm.append(_yaml_block("ct_table", context["ct_table"]))
    if "ddct_table" in context:
        fm.append(_yaml_block("ddct_table", context["ddct_table"]))
    if "interpretation" in context:
        fm.append(_yaml_block("interpretation", context["interpretation"]))
    if "plots" in context:
        fm.append(_yaml_block("plots", context["plots"]))

    fm.append("---\n")

    # ----- BODY -----
    body = []
    body.append(f"# {meta['title']}\n")
    body.append(f"**Experiment:** {meta['experiment_name']}")
    body.append(f"**Date:** {meta['date']}")
    body.append(f"**Analyst:** {meta['analyst']}\n")

    body.append("## Summary of Results\n")
    for s in context.get("summary", []):
        body.append(f"- {s}")

    body.append("\n## QC Summary\n")
    body.append(context.get("qc_table_md", "_No QC info._"))

    body.append("\n## Cleaned CT Table\n")
    body.append(context.get("ct_table", "_No CT table._"))

    body.append("\n## ΔCT / ΔΔCT Analysis\n")
    body.append(context.get("ddct_table", "_No ΔΔCT table._"))

    body.append("\n## Plots\n")
    for name, p in context.get("plots", {}).items():
        body.append(f"![{name}]({p})\n")

    body.append("\n## Interpretation\n")
    body.append(context.get("interpretation", "_No interpretation._"))

    # write final
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(fm + body))

    return out_path


# -----------------------
# PROGRAM LOCATOR
# -----------------------

def _which_windows_fallback(name, fallbacks):
    p = shutil.which(name)
    if p:
        return p
    for fb in fallbacks:
        if Path(fb).exists():
            return str(Path(fb))
    return None


# -----------------------
# PDF GENERATION
# -----------------------

def md_to_pdf(md_path: str, pdf_path: str,
              template="templates/report_template.html",
              css="templates/report_style.css") -> str:

    md_path = str(Path(md_path).resolve())
    pdf_path = str(Path(pdf_path).resolve())
    md_dir = str(Path(md_path).parent)

    # ----- FIND PANDOC -----
    pandoc = _which_windows_fallback("pandoc", [
        r"C:\Program Files\Pandoc\pandoc.exe",
        r"C:\Program Files (x86)\Pandoc\pandoc.exe"
    ])
    if not pandoc:
        raise RuntimeError("Pandoc not found.")

    # ----- STEP 1: MD → FULL HTML -----
    html_path = os.path.join(md_dir, "report.full.html")
    pandoc_cmd = [
        pandoc, md_path,
        "--from", "markdown",
        "--to", "html5",
        "--standalone",
        "--template", template,
        "--css", css,
        "-o", html_path,
    ]
    subprocess.check_call(pandoc_cmd)

    # ----- FIND WKHTMLTOPDF -----
    wkhtml = _which_windows_fallback("wkhtmltopdf", [
        r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
        r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
    ])

    if wkhtml:
        # ----- STEP 2: HTML → PDF -----
        wk_cmd = [
            wkhtml,
            "--enable-local-file-access",
            "--margin-top", "20mm",
            "--margin-bottom", "20mm",
            "--margin-left", "15mm",
            "--margin-right", "15mm",
            html_path,
            pdf_path
        ]
        subprocess.check_call(wk_cmd)
        return pdf_path

    # ----- FALLBACK -----
    subprocess.check_call([pandoc, html_path, "-o", pdf_path])
    return pdf_path
