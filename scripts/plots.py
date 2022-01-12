#!/usr/bin/env python3

import os
import logging

# change directory to that of the script file
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


def parse_cli():
	import argparse

	# All input that is needed
	parser = argparse.ArgumentParser(description="Plot (Plots sanitized data)")
	parser.add_argument("--rolling", dest="rolling", type=int, default=10, help="Rolling mead value")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	args = parser.parse_args()

	logging.basicConfig(
		level=logging.DEBUG if args.verbose else logging.INFO,
		format='%(asctime)s %(levelname)-8s %(message)s',
		datefmt='%a, %d %b %Y %H:%M:%S',
	)

	return args.rolling


def main():
	import pandas as pd
	import matplotlib.pyplot as plt
	from scipy.signal import find_peaks
	import matplotlib.colors as mcolors


	rolling = parse_cli()

	frame = pd.read_csv('clean.csv')

	std_coefficient = 2

	frame["roll_x0"] = frame["x0"].rolling(20).mean()  # rolling mean to smooth the plot
	frame["std_x0"] = frame["roll_x0"].rolling(5).std()  # rolling mean to smooth the plot
	frame["std_plus_x0"] = frame["std_x0"] * std_coefficient + frame["roll_x0"]
	frame["roll_y0"] = frame["y0"].rolling(20).mean()  # rolling mean to smooth the plot
	frame["std_y0"] = frame["roll_y0"].rolling(5).std()  # rolling mean to smooth the plot
	frame["std_plus_y0"] = frame["std_y0"] * std_coefficient + frame["roll_y0"]
	frame["std_plus_y0_flip"] = -(frame["std_plus_y0"]) + 200

	peaks, _ = find_peaks(frame["std_plus_x0"], height=2, distance=200, prominence=2)
	print(len(peaks))

	peaks_y, _ = find_peaks(frame["std_plus_y0"], height=2, distance=200, prominence=2)
	print(len(peaks_y))

	peaks_y_flip, _ = find_peaks(frame["std_plus_y0_flip"], height=2, distance=200, prominence=2)
	print(len(peaks_y_flip))

	new_peaks = []
	for peak in peaks:
		if peak < 50 or peak > len(frame.index) - 50:
			new_peaks += [peak]
			continue
		left_mean = frame["std_plus_x0"][peak - 50 : peak].mean()
		right_mean = frame["std_plus_x0"][peak : peak + 50 ].mean()
		# print(f"Left mean = {left_mean}", f"Right mean = {right_mean}", f"Peak = {peak}", f"keep = {right_mean > left_mean}")
		if right_mean > left_mean:
			new_peaks += [peak]

	new_peaks_y = []
	for peak in peaks_y:
		if peak < 50 or peak > len(frame.index) - 50:
			new_peaks_y += [peak]
			continue
		left_mean = frame["std_plus_y0"][peak - 50 : peak].mean()
		right_mean = frame["std_plus_y0"][peak : peak + 50 ].mean()
		if right_mean > left_mean:
			new_peaks_y += [peak]

	for peak in peaks_y_flip:
		if peak < 50 or peak > len(frame.index) - 50:
			new_peaks_y += [peak]
			continue
		left_mean = frame["std_plus_y0_flip"][peak - 50 : peak].mean()
		right_mean = frame["std_plus_y0_flip"][peak : peak + 50 ].mean()
		if right_mean > left_mean:
			new_peaks_y += [peak]					

	

	fig, (ax1, ax2) = plt.subplots(2, sharex=True)
	ax1.plot(frame["x0"], linewidth=0.5, label='Raw Data', color="darkslategray")
	ax1.plot(frame["std_plus_x0"], color='teal', label='Rolling STD')
	ax1.plot(new_peaks, frame["std_plus_x0"][new_peaks], "o", color="mediumvioletred", alpha=0.5)
	ax1.set_title('Horizontal Movements')
	ax1.legend()

	ax2.plot(frame["y0"], linewidth = 0.5, label = 'Raw Data', color = 'navy')
	ax2.plot(frame["std_plus_y0"], color='cornflowerblue', label='Rolling STD')
	ax2.plot(new_peaks_y, frame["std_plus_y0"][new_peaks_y], "o", color="darkmagenta", alpha=0.5)
	ax2.set_title('Vertical Movements')
	ax2.set_xlabel('Frames')
	fig.text(0.06, 0.5, 'Pixels', ha='center', va='center', rotation='vertical')
	ax2.legend()
	plt.show()


if __name__ == "__main__":
	main()