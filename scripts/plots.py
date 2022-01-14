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
	from peaks import find_peaks
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
	frame["std_minus_y0"] = frame["roll_y0"] - frame["std_y0"] * std_coefficient
	frame["std_minus_y0_flip"] = -(frame["std_minus_y0"]) + 200

	horizontal_peaks = find_peaks(frame["std_plus_x0"], high=True)
	print(len(horizontal_peaks))

	vertical_peaks = find_peaks(frame["std_plus_y0"], high=True)
	print(len(vertical_peaks))

	vertical_peaks_low = find_peaks(frame["std_plus_y0"], high=False)
	print(len(vertical_peaks_low))



	fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
	ax1.plot(frame["x0"], linewidth=0.5, label='Raw Data', color="black")
	ax1.plot(frame["std_plus_x0"], color='teal', label='Rolling STD')
	ax1.plot(horizontal_peaks, frame["std_plus_x0"][horizontal_peaks], "o", color="mediumvioletred", alpha=0.5)
	ax1.set_title('Horizontal Movements')
	ax1.legend()

	ax2.plot(frame["y0"], linewidth = 0.5, label = 'Raw Data', color = 'black')
	ax2.plot(frame["std_plus_y0"], color='teal', label='Rolling STD')
	ax2.plot(vertical_peaks, frame["std_plus_y0"][vertical_peaks], "o", color="mediumvioletred", alpha=0.5)
	ax2.plot(vertical_peaks_low, frame["std_plus_y0"][vertical_peaks_low], "o", color="mediumvioletred", alpha=0.5)
	ax2.set_title('Vertical Movements')
	fig.text(0.06, 0.5, 'Pixels', ha='center', va='center', rotation='vertical')
	ax2.legend()

	ax3.plot(frame["ellipse_area"], linewidth = 0.5, label = 'Raw Data', color = 'black')
	ax3.plot(frame["roll_ellipse_area"], color='teal', label='Rolling Mean')
	ax3.set_title('Pupil Area')
	ax3.set_xlabel('Frames')
	ax3.legend()
	plt.show()


if __name__ == "__main__":
	main()
