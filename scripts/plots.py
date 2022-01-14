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

	fig, (ax_horizontal, ax_vertical, ax3) = plt.subplots(3, sharex=True)

	def plot_peaks(column_name, plot_name, ax):
		rolling_mean = frame[column_name].rolling(20).mean()  # rolling mean to smooth the plot

		peaks = find_peaks(rolling_mean, high=True)
		print(len(peaks))

		peaks_low = find_peaks(rolling_mean, high=False)
		print(len(peaks_low))

		ax.set_title(f"{plot_name} Movements")
		ax.plot(frame[column_name], linewidth=0.5, label='Raw Data', color="black")
		ax.plot(rolling_mean, color='teal', label='Rolling Mean')
		ax.plot(peaks, rolling_mean[peaks], "o", color="mediumvioletred", alpha=0.5)
		ax.plot(peaks_low, rolling_mean[peaks_low], "o", color="orange", alpha=0.5)
		ax.legend()

	plot_peaks("x0", "Horizontal", ax_horizontal)
	plot_peaks("y0", "Vertical", ax_vertical)

	ax3.plot(frame["ellipse_area"], linewidth=0.5, label='Raw Data', color='black')
	ax3.plot(frame["roll_ellipse_area"], color='teal', label='Rolling Mean')
	ax3.set_title('Pupil Area')
	ax3.set_xlabel('Frames')
	ax3.legend()
	plt.show()


if __name__ == "__main__":
	main()
