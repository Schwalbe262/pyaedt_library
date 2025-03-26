import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt

class PostProcessing:

    def __init__(self, design) :

        self.design = design
        a = 1
        
    def detect_peak(self, freq=None, data=None) :

        peaks_prom, properties = find_peaks(data, prominence=10)

        if freq is not None :
            peak_freqs_prom = freq[peaks_prom].values
            peak_vals_prom = data[peaks_prom].values
            return peak_freqs_prom, peak_vals_prom
        
        elif freq is None :
            peak_vals_prom = data[peaks_prom].values
            return peak_vals_prom
