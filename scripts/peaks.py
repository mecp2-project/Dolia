# designed to be included in other programs

import scipy.signal as signal
import numpy as np


def find_peaks(series, high=True):
	if high:
		return signal.find_peaks(series, height=2, distance=200)[0]
	else:
		return np.array([])
