# tests/test_qc.py
import tempfile
import pandas as pd
import pytest
from src import ntc_check, replicate_variance_check, housekeeping_consistency, read_raw_csv
from io import StringIO

CSV_SIMPLE = """Well,Sample,Target,CT,Replicate
A1,NTC,TargetX,Undetermined,1
A2,NTC,TargetX,Undetermined,2
B1,Control,GAPDH,18.0,1
B2,Control,GAPDH,18.1,2
C1,Exp,GAPDH,18.5,1
C2,Exp,GAPDH,18.6,2
D1,Control,TargetX,22.0,1
D2,Control,TargetX,22.1,2
E1,Exp,TargetX,19.0,1
E2,Exp,TargetX,25.0,2
"""

def make_df():
    return pd.read_csv(StringIO(CSV_SIMPLE), dtype=str).assign(
        CT=lambda d: d['CT'].apply(lambda x: float(x) if x not in ("Undetermined","") else float("nan")),
        Replicate=lambda d: d['Replicate'].astype(int)
    )

def test_ntc_check_pass():
    df = make_df()
    res = ntc_check(df, ntc_name="NTC", ntc_threshold=35.0)
    assert 'TargetX' in res
    assert res['TargetX']['status'] == "pass"

def test_replicate_variance_check_flags():
    df = make_df()
    rep_res = replicate_variance_check(df, variance_limit=0.3)
    # find Exp/TargetX entry which has a big range (19.0 and 25.0)
    fails = [r for r in rep_res if r['sample']=="Exp" and r['target']=="TargetX"]
    assert len(fails) == 1
    assert fails[0]['status'] == "fail"
    assert fails[0]['range'] >= 6.0

def test_housekeeping_consistency():
    df = make_df()
    # housekeeping list contains GAPDH
    hk = housekeeping_consistency(df, hk_genes=["GAPDH"], var_limit=0.5)
    assert 'GAPDH' in hk
    # GAPDH sd should be small and pass for given numbers
    assert hk['GAPDH']['status'] == "pass"
