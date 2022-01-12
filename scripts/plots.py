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

	rolling = parse_cli()

	frame = pd.read_csv('clean.csv')

	std_coefficient = 2

	frame["roll_x0"] = frame["x0"].rolling(20).mean()  # rolling mean to smooth the plot
	frame["std_x0"] = frame["roll_x0"].rolling(5).std()  # rolling mean to smooth the plot
	frame["std_plus_x0"] = frame["std_x0"] * std_coefficient + frame["roll_x0"]

	peaks, _ = find_peaks(frame["std_plus_x0"], height=2, distance=200, prominence=2)
	print(len(peaks))

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

	print(len(new_peaks))

	fig, (ax1, ax2) = plt.subplots(2, sharex=True)
	ax1.plot(frame["x0"], linewidth=0.5, label='Raw Data', color="green")
	# ax1.plot(frame["roll_x0"], color='red', label='Rolling Mean')
	ax1.plot(frame["std_plus_x0"], color='blue', label='Rolling STD')
	ax1.plot(new_peaks, frame["std_plus_x0"][new_peaks], "o", color="red", alpha=0.5)
	#ax1.plot(peaks, frame["std_plus_x0"][peaks], "x", color="yellow")
	ax1.set_title('Horizontal Movements')
	ax1.legend()

	ax2.plot(frame["y0"], linewidth = 0.5, label = 'Raw Data', color = "green")
	#ax1.plot(frame["std_plus_y0"], color='blue', label='Rolling STD')
	#ax1.plot(new_peaks, frame["std_plus_y0"][new_peaks], "o", color="red", alpha=0.5)
	ax2.plot(frame["roll_y0"],color = 'red', label = 'Rolling Mean')
	ax2.set_title('Vertical Movements')
	ax2.set_xlabel('Frames')
	fig.text(0.06, 0.5, 'Pixels', ha='center', va='center', rotation='vertical')
	ax2.legend()
	plt.show()


if __name__ == "__main__":
	main()