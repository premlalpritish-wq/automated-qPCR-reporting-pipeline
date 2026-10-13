"""Verify that every QC finding survives into each regenerated output format.

Run from the repository root:
    python evidence/verify_qc_findings.py

Exits non-zero if any of the nine flagged sample|target pairs is missing
from the Markdown, the rendered HTML or the PDF.
"""
import pathlib
import re
import sys

EXPECTED = [
    ("Control_1", "GAPDH"), ("Control_1", "TargetX"),
    ("Control_2", "GAPDH"), ("Control_2", "TargetX"),
    ("ExpA_1", "GAPDH"), ("ExpA_1", "TargetX"),
    ("ExpA_2", "GAPDH"), ("ExpA_2", "TargetX"),
    ("NTC", "TargetX"),
]
MD = pathlib.Path("evidence/regen_report.md")
HTML = pathlib.Path("evidence/report.full.html")
PDF = pathlib.Path("evidence/regen_report.pdf")


def check(label, text):
    missing = [f"{s}|{t}" for s, t in EXPECTED if f"{s}|{t}" not in text]
    found = len(EXPECTED) - len(missing)
    print(f"  {label:22} {found}/{len(EXPECTED)} findings"
          + (f"   MISSING: {missing}" if missing else "   OK"))
    return not missing


ok = True

md = MD.read_text(encoding="utf-8")
ok &= check("regen_report.md", md.replace(r"\|", "|"))

rows = re.findall(
    r"<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>",
    HTML.read_text(encoding="utf-8"), re.S)
qc = {re.sub("<[^>]+>", "", r[0]).strip(): re.sub("<[^>]+>", "", r[2]).strip()
      for r in rows}
print("\n  rendered QC table:")
for k, v in qc.items():
    print(f"    {k:<20} {v}")
ok &= check("report.full.html", " ".join(qc.values()))

try:
    from pypdf import PdfReader
except ImportError:
    print("  report.pdf              SKIPPED - pip install pypdf")
else:
    reader = PdfReader(PDF)
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    print(f"\n  PDF: {len(reader.pages)} pages, {len(text)} characters extracted")
    ok &= check("regen_report.pdf", text)

print("\n  RESULT:", "all nine findings present in every format"
      if ok else "FAILURE - findings were dropped")
sys.exit(0 if ok else 1)
