# tests/test_parser.py
import io
import pandas as pd
import tempfile
import os
import pytest
from src import read_raw_csv, CT_UNDETERMINED

SAMPLE_CSV = """Well,Sample,Target,CT,Replicate,Plate
A1,Control_1,GAPDH,18.4,1,Plate1
A2,Control_2,GAPDH,18.6,2,Plate1
B1,ExpA_1,GAPDH,19.1,1,Plate1
B2,ExpA_2,GAPDH,19.4,2,Plate1
C1,Control_1,TargetX,22.0,1,Plate1
C2,Control_2,TargetX,22.5,2,Plate1
D1,ExpA_1,TargetX,19.3,1,Plate1
D2,ExpA_2,TargetX,19.7,2,Plate1
E1,NTC,TargetX,Undetermined,1,Plate1
"""


def test_read_raw_csv_tmpfile(tmp_path):
    p = tmp_path / "example.csv"
    p.write_text(SAMPLE_CSV)
    df = read_raw_csv(str(p))
    assert 'Well' in df.columns
    assert 'Sample' in df.columns
    assert 'Target' in df.columns
    assert 'CT' in df.columns
    # Check Undetermined becomes NaN
    ntc_row = df[(df['Sample'].str.contains("NTC"))
                 & (df['Target'] == "TargetX")]
    assert ntc_row.shape[0] == 1
    assert pd.isna(ntc_row.iloc[0]['CT'])


def test_infer_replicates_if_missing(tmp_path):
    # remove Replicate column to test inference
    data = SAMPLE_CSV.replace(",1,Plate1", ",,Plate1").replace(
        ",2,Plate1", ",,Plate1")
    p = tmp_path / "no_reps.csv"
    p.write_text(data)
    df = read_raw_csv(str(p))
    # replicate column created and is numeric and >=1
    assert 'Replicate' in df.columns
    assert df['Replicate'].min() >= 1


def test_non_numeric_ct_handled(tmp_path):
    bad_csv = """Well,Sample,Target,CT
A1,S1,GAPDH,18.5
A2,S1,GAPDH,abc
A3,S2,TargetX,Undetermined
"""
    p = tmp_path / "bad.csv"
    p.write_text(bad_csv)
    df = read_raw_csv(str(p))
    assert df.shape[0] == 3
    assert pd.isna(df.loc[df['Well'] == 'A2', 'CT'].iloc[0])
    assert pd.isna(df.loc[df['Well'] == 'A3', 'CT'].iloc[0])
