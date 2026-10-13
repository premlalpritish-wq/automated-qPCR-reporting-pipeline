# tests/test_analysis.py
import pandas as pd
import pytest

from src.analysis import compute_mean_ct, compute_delta_ct, compute_ddct


# A small, fully hand-checkable dataset.
#
#   Control_1  GAPDH   18.4, 18.6  -> mean 18.5
#   Control_1  TargetX 22.0, 22.2  -> mean 22.1
#   Control_2  GAPDH   19.0        -> mean 19.0
#   Control_2  TargetX 23.0        -> mean 23.0
#   ExpA_1     GAPDH   19.5        -> mean 19.5
#   ExpA_1     TargetX 19.7        -> mean 19.7
#
# DeltaCT against GAPDH is therefore 3.6, 4.0 and 0.2, and the mean
# control DeltaCT is (3.6 + 4.0) / 2 = 3.8.
RAW = pd.DataFrame([
    {"Sample": "Control_1", "Target": "GAPDH", "CT": 18.4},
    {"Sample": "Control_1", "Target": "GAPDH", "CT": 18.6},
    {"Sample": "Control_1", "Target": "TargetX", "CT": 22.0},
    {"Sample": "Control_1", "Target": "TargetX", "CT": 22.2},
    {"Sample": "Control_2", "Target": "GAPDH", "CT": 19.0},
    {"Sample": "Control_2", "Target": "TargetX", "CT": 23.0},
    {"Sample": "ExpA_1", "Target": "GAPDH", "CT": 19.5},
    {"Sample": "ExpA_1", "Target": "TargetX", "CT": 19.7},
])


def _delta_ct():
    return compute_delta_ct(compute_mean_ct(RAW), housekeeping="GAPDH")


# --------------------------------------------------------------- mean CT

def test_compute_mean_ct_averages_replicates():
    summary = compute_mean_ct(RAW)
    got = {(r.Sample, r.Target): r.CT_mean for r in summary.itertuples()}
    assert got[("Control_1", "GAPDH")] == pytest.approx(18.5)
    assert got[("Control_1", "TargetX")] == pytest.approx(22.1)
    assert got[("Control_2", "GAPDH")] == pytest.approx(19.0)
    assert got[("ExpA_1", "TargetX")] == pytest.approx(19.7)


def test_compute_mean_ct_counts_replicates():
    summary = compute_mean_ct(RAW).set_index(["Sample", "Target"])
    assert summary.loc[("Control_1", "GAPDH"), "n_rep"] == 2
    assert summary.loc[("Control_2", "GAPDH"), "n_rep"] == 1


def test_compute_mean_ct_sd_is_nan_for_a_single_replicate():
    summary = compute_mean_ct(RAW).set_index(["Sample", "Target"])
    assert pd.isna(summary.loc[("Control_2", "GAPDH"), "CT_sd"])
    assert not pd.isna(summary.loc[("Control_1", "GAPDH"), "CT_sd"])


def test_compute_mean_ct_columns():
    assert list(compute_mean_ct(RAW).columns) == [
        "Sample", "Target", "CT_mean", "n_rep", "CT_sd"]


# ------------------------------------------------------------- delta CT

def test_compute_delta_ct_subtracts_housekeeping():
    delta = _delta_ct().set_index("Sample")["DeltaCT"]
    assert delta["Control_1"] == pytest.approx(3.6)
    assert delta["Control_2"] == pytest.approx(4.0)
    assert delta["ExpA_1"] == pytest.approx(0.2)


def test_compute_delta_ct_drops_the_housekeeping_column():
    assert "GAPDH" not in set(_delta_ct()["Target"])


def test_compute_delta_ct_long_form_columns():
    assert list(_delta_ct().columns) == ["Sample", "Target", "DeltaCT"]


def test_compute_delta_ct_requires_the_housekeeping_gene():
    with pytest.raises(KeyError):
        compute_delta_ct(compute_mean_ct(RAW), housekeeping="ACTB")


# --------------------------------------------------------- delta delta CT

def test_compute_ddct_uses_the_mean_of_keyword_matched_controls():
    """No sample is literally called "Control", so both controls are averaged."""
    out = compute_ddct(_delta_ct(), "Control").set_index("Sample")
    assert out.loc["Control_1", "DeltaDeltaCT"] == pytest.approx(3.6 - 3.8)
    assert out.loc["Control_2", "DeltaDeltaCT"] == pytest.approx(4.0 - 3.8)
    assert out.loc["ExpA_1", "DeltaDeltaCT"] == pytest.approx(0.2 - 3.8)


def test_compute_ddct_keyword_match_is_case_insensitive():
    out = compute_ddct(_delta_ct(), "CONTROL").set_index("Sample")
    assert out.loc["ExpA_1", "DeltaDeltaCT"] == pytest.approx(0.2 - 3.8)


def test_compute_ddct_fold_change_is_two_to_the_minus_delta_delta():
    out = compute_ddct(_delta_ct(), "Control").set_index("Sample")
    assert out.loc["ExpA_1", "FoldChange"] == pytest.approx(2 ** 3.6)
    assert out.loc["Control_2", "FoldChange"] == pytest.approx(2 ** -0.2)
    assert out.loc["Control_2", "FoldChange"] < 1.0
    assert out.loc["ExpA_1", "FoldChange"] > 1.0


def test_compute_ddct_prefers_an_exact_control_sample_name():
    """An exact name wins over the keyword path."""
    out = compute_ddct(_delta_ct(), "Control_1").set_index("Sample")
    # against Control_1 alone (3.6) rather than the mean of both (3.8)
    assert out.loc["Control_2", "DeltaDeltaCT"] == pytest.approx(4.0 - 3.6)
    assert out.loc["ExpA_1", "DeltaDeltaCT"] == pytest.approx(0.2 - 3.6)


def test_compute_ddct_no_control_yields_nan():
    out = compute_ddct(_delta_ct(), "NoSuchSample")
    assert out["DeltaDeltaCT"].isna().all()
    assert out["FoldChange"].isna().all()


def test_compute_ddct_requires_the_expected_columns():
    with pytest.raises(KeyError):
        compute_ddct(pd.DataFrame([{"Sample": "a", "Target": "b"}]), "Control")


def test_compute_ddct_keeps_the_input_columns():
    out = compute_ddct(_delta_ct(), "Control")
    for col in ("Sample", "Target", "DeltaCT", "DeltaDeltaCT", "FoldChange"):
        assert col in out.columns


# ------------------------------------------------- against the shipped run

def test_matches_the_published_example_output():
    """The bundled run must reproduce the published figures exactly.

    The example run's mean control DeltaCT is (3.6 + 3.9) / 2 = 3.75,
    which is where the published -0.15, -3.55 and -3.45 come from.
    """
    summary = pd.DataFrame([
        {"Sample": "Control_1", "Target": "GAPDH", "CT_mean": 18.4},
        {"Sample": "Control_1", "Target": "TargetX", "CT_mean": 22.0},
        {"Sample": "Control_2", "Target": "GAPDH", "CT_mean": 18.6},
        {"Sample": "Control_2", "Target": "TargetX", "CT_mean": 22.5},
        {"Sample": "ExpA_1", "Target": "GAPDH", "CT_mean": 19.1},
        {"Sample": "ExpA_1", "Target": "TargetX", "CT_mean": 19.3},
        {"Sample": "ExpA_2", "Target": "GAPDH", "CT_mean": 19.4},
        {"Sample": "ExpA_2", "Target": "TargetX", "CT_mean": 19.7},
    ])
    out = compute_ddct(
        compute_delta_ct(summary, housekeeping="GAPDH"), "Control"
    ).set_index("Sample")

    assert out.loc["Control_1", "FoldChange"] == pytest.approx(1.10957, abs=1e-5)
    assert out.loc["Control_2", "FoldChange"] == pytest.approx(0.90125, abs=1e-5)
    assert out.loc["ExpA_1", "FoldChange"] == pytest.approx(11.7127, abs=1e-4)
    assert out.loc["ExpA_2", "FoldChange"] == pytest.approx(10.9283, abs=1e-4)
