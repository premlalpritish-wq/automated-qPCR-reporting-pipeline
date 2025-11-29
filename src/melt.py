import numpy as np
from scipy.signal import find_peaks


def detect_melt_peaks(temp: np.ndarray, fluo: np.ndarray, prominence=0.2):
    # temp, fluo: same-length arrays
    # normalize fluorescence to [0,1] to set relative prominence default
    fluo_norm = (fluo - fluo.min()) / (fluo.max() - fluo.min() + 1e-9)
    peaks, props = find_peaks(fluo_norm, prominence=prominence)
    peak_temps = temp[peaks]
    peak_prominences = props.get('prominences', [])
    return list(zip(peak_temps.tolist(), peak_prominences.tolist()))
