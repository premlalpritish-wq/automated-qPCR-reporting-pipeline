import pandas as pd
from src.analysis import compute_mean_ct, compute_delta_ct, compute_ddct

def test_delta_ddct():
    data = pd.DataFrame([
        {"Sample":"Control","Target":"GAPDH","CT_mean":18.0},
        {"Sample":"Control","Target":"TargetX","CT_mean":22.0},
        {"Sample":"Exp","Target":"GAPDH","CT_mean":19.0},
        {"Sample":"Exp","Target":"TargetX","CT_mean":19.0},
    ])
    # compute delta ct expects the summary form used in code; adapt accordingly in tests
