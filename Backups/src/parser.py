import pandas as pd
import numpy as np
from typing import Tuple

CT_UNDETERMINED = "Undetermined"


def read_raw_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    # normalize column names
    df.columns = [c.strip() for c in df.columns]
    # ensure required columns exist
    required = {"Well", "Sample", "Target", "CT"}
    if not required.issubset(set(df.columns)):
        raise ValueError(
            f"Missing required columns: {required - set(df.columns)}")
    # coerce CT: convert 'Undetermined' and non-numeric to NaN

    def parse_ct(x):
        if pd.isna(x):
            return np.nan
        s = str(x).strip()
        if s.lower() in {"undetermined", "nd", ""}:
            return np.nan
        try:
            return float(s)
        except:
            return np.nan
    df['CT'] = df['CT'].apply(parse_ct)
    # Replicate handling
    if 'Replicate' not in df.columns:
        # infer replicate by counting occurrences per Sample/Target
        df['Replicate'] = df.groupby(['Sample', 'Target']).cumcount()+1
    else:
        df['Replicate'] = pd.to_numeric(
            df['Replicate'], errors='coerce').fillna(1).astype(int)
    return df
