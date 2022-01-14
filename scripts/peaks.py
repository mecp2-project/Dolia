# designed to be included in other programs

import scipy.signal as signal
import numpy as np


def find_peaks(series, high=True):
	if not high:
		series = -series + 200

	peaks = signal.find_peaks(series, height=2, distance=200, prominence = 2)[0]

	new_peaks = []
	for peak in peaks:
		if peak < 50 or peak > len(series) - 50:
			new_peaks += [peak]
			continue
		left_mean = series[peak - 50 : peak].mean()
		right_mean = series[peak : peak + 50 ].mean()
		if right_mean > left_mean:
			new_peaks += [peak]

	return new_peaks
