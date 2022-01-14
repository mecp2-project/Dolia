# designed to be included in other programs

import scipy.signal as signal
import numpy as np

STD_COEFFICIENT = 2


def find_peaks(series, high=True):
	"""
	Takes:
		series: numpy array of points (floats), already smoothed with moving average
		high: whether to compute high or low peaks
	Returns:
		a numpy array with indices of found peaks (may be empty)
	"""

	if high:
		std_series = series + series.rolling(5).std() * STD_COEFFICIENT
	else:
		std_series = 200 - (series - series.rolling(5).std() * STD_COEFFICIENT)

	peaks = signal.find_peaks(std_series, height=2, distance=200, prominence=2)[0]

	new_peaks = []
	for peak in peaks:
		if peak < 50 or peak > len(std_series) - 50:
			new_peaks += [peak]
			continue
		left_mean = std_series[peak - 50:peak].mean()
		right_mean = std_series[peak:peak + 50].mean()
		if right_mean > left_mean:
			new_peaks += [peak]

	return np.array(new_peaks)
