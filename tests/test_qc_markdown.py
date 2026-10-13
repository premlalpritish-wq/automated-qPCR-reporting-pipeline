# tests/test_qc_markdown.py
"""Regression tests for Markdown table rendering of the QC summary.

Defect: QC notes join findings as ``sample|target``. Written into a Markdown
table unescaped, every ``|`` splits the cell into extra columns and all but the
first finding silently disappears from the rendered report.
"""
import re

import pytest

from cli import qc_summary_to_markdown, _md_cell


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def parse_qc_rows(md: str):
    """Parse the QC markdown table into a list of (test, status, notes).

    Mirrors what a Markdown renderer does, which is the point of the exercise:
    a cell split by an unescaped pipe shows up here as extra columns.
    """
    lines = [ln for ln in md.strip().splitlines() if ln.strip()]
    assert lines, "table is empty"
    assert lines[0].strip() == "| Test | Status | Notes |", lines[0]
    assert re.fullmatch(r"\|(?:-+\|){3}", lines[1].strip()), lines[1]

    rows = []
    for ln in lines[2:]:
        cells = _split_row(ln)
        assert len(cells) == 3, f"expected 3 columns, got {len(cells)}: {ln!r}"
        rows.append(tuple(c.strip() for c in cells))
    return rows


def _split_row(line: str):
    """Split a Markdown table row, honouring ``\\|`` as a literal pipe."""
    body = line.strip()
    assert body.startswith("|") and body.endswith("|")
    body = body[1:-1]

    cells, buf, i = [], [], 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body) and body[i + 1] == "|":
            buf.append("|")
            i += 2
            continue
        if ch == "|":
            cells.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    cells.append("".join(buf))
    return cells


def rep(sample, target, status="warn"):
    return {"sample": sample, "target": target, "status": status, "notes": []}


# ---------------------------------------------------------------------------
# unit: _md_cell
# ---------------------------------------------------------------------------

def test_md_cell_escapes_pipes():
    assert _md_cell("a|b") == r"a\|b"
    assert _md_cell("a|b|c") == r"a\|b\|c"


def test_md_cell_collapses_line_breaks():
    assert _md_cell("a\nb") == "a b"
    assert _md_cell("a\r\nb") == "a b"
    assert _md_cell("a\rb") == "a b"


def test_md_cell_handles_none_and_empty():
    assert _md_cell(None) == ""
    assert _md_cell("") == ""


# ---------------------------------------------------------------------------
# regression: multiple QC findings in one report
# ---------------------------------------------------------------------------

def test_all_replicate_findings_survive():
    """The defect: 9 findings rendered as 1. All 9 must survive."""
    qc_reps = [
        rep("Control_1", "GAPDH"),
        rep("Control_1", "TargetX"),
        rep("Control_2", "GAPDH"),
        rep("Control_2", "TargetX"),
        rep("ExpA_1", "GAPDH"),
        rep("ExpA_1", "TargetX"),
        rep("ExpA_2", "GAPDH"),
        rep("ExpA_2", "TargetX"),
        rep("NTC", "TargetX"),
    ]
    qc_ntc = {"TargetX": {"status": "pass", "notes": "No amplification in NTC"}}
    qc_hk = {
        "GAPDH": {"status": "fail", "mean_ct": 18.5, "sd": 0.9},
        "ACTB": {"status": "missing", "mean_ct": None, "sd": None},
    }

    md = qc_summary_to_markdown(qc_ntc, qc_reps, qc_hk)
    rows = parse_qc_rows(md)

    rep_row = next(r for r in rows if r[0] == "Replicate variance")
    notes = rep_row[2]

    # every flagged sample|target pair is present and readable
    for sample, target in [
        ("Control_1", "GAPDH"), ("Control_1", "TargetX"),
        ("Control_2", "GAPDH"), ("Control_2", "TargetX"),
        ("ExpA_1", "GAPDH"), ("ExpA_1", "TargetX"),
        ("ExpA_2", "GAPDH"), ("ExpA_2", "TargetX"),
        ("NTC", "TargetX"),
    ]:
        assert f"{sample}|{target}" in notes, f"{sample}|{target} missing from {notes!r}"

    assert notes.count("|") == 9, notes
    assert rep_row[1] == "Warn"


def test_single_finding_unaffected():
    qc_reps = [rep("ExpA_1", "TargetX")]
    md = qc_summary_to_markdown({}, qc_reps, {})
    # raw markdown carries the escape...
    assert r"ExpA_1\|TargetX" in md
    # ...and a renderer reads it back as the literal pair
    rows = parse_qc_rows(md)
    rep_row = next(r for r in rows if r[0] == "Replicate variance")
    assert rep_row[2] == "ExpA_1|TargetX"
    assert rep_row[1] == "Warn"


def test_no_findings_reports_ok():
    qc_reps = [rep("Control_1", "GAPDH", status="pass")]
    md = qc_summary_to_markdown({}, qc_reps, {})
    rows = parse_qc_rows(md)
    rep_row = next(r for r in rows if r[0] == "Replicate variance")
    assert rep_row[2] == "All replicates OK"
    assert rep_row[1] == "Pass"


def test_pipe_in_other_note_columns_also_escaped():
    """Any cell, not just Replicate variance, must be escaped."""
    qc_ntc = {"TargetX": {"status": "fail", "notes": "NTC|amplified"}}
    qc_hk = {"GAPDH": {"status": "fail", "mean_ct": 18.5, "sd": 0.9}}
    md = qc_summary_to_markdown(qc_ntc, [], qc_hk)
    assert r"NTC\|amplified" in md
    rows = parse_qc_rows(md)
    ntc_row = next(r for r in rows if r[0] == "NTC")
    assert ntc_row[2] == "NTC|amplified"
    assert len(rows) == 3


def test_multiline_note_does_not_break_table():
    qc_ntc = {"TargetX": {"status": "fail", "notes": "line one\nline two\r\nline three"}}
    md = qc_summary_to_markdown(qc_ntc, [], {})
    rows = parse_qc_rows(md)
    ntc_row = next(r for r in rows if r[0] == "NTC")
    assert ntc_row[2] == "line one line two line three"
    assert len(rows) == 3  # header rules not split into extra rows


def test_housekeeping_notes_preserved():
    qc_hk = {
        "GAPDH": {"status": "fail", "mean_ct": 18.5, "sd": 0.9},
        "ACTB": {"status": "missing", "mean_ct": None, "sd": None},
    }
    md = qc_summary_to_markdown({}, [], qc_hk)
    rows = parse_qc_rows(md)
    hk = next(r for r in rows if r[0] == "Housekeeping")
    assert hk[1] == "Warn"
    assert "GAPDH: mean=18.50, SD=0.90 (fail)" in hk[2]
    assert "ACTB: missing" in hk[2]


def test_table_shape_is_always_three_columns():
    """Whatever the input, every data row must stay at 3 columns."""
    qc_ntc = {"T|A": {"status": "pa|ss", "notes": "a|b\nc|d"}}
    qc_reps = [rep("S|1", "T|1"), rep("S|2", "T|2")]
    qc_hk = {"G|1": {"status": "fail", "mean_ct": 1.0, "sd": 0.1}}
    md = qc_summary_to_markdown(qc_ntc, qc_reps, qc_hk)
    rows = parse_qc_rows(md)
    assert len(rows) == 3
    for row in rows:
        assert len(row) == 3


def test_header_and_separator_unchanged():
    """Existing formatting must be preserved."""
    md = qc_summary_to_markdown({}, [], {})
    lines = md.strip().splitlines()
    assert lines[0] == "| Test | Status | Notes |"
    assert lines[1] == "|---|---|---|"
    assert [r[0] for r in parse_qc_rows(md)] == [
        "NTC", "Replicate variance", "Housekeeping"
    ]
