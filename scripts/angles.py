#!/usr/bin/env python3
"""
Looking for Horizontal and Vertical segments
If Vertical does not have corresponding Horizontal --- taking Vertical
If corresponding segment exists --- taking Horizontal

Foolproof:
	Plot calculated segments (in case something is missed)

Inputs:
	1. Clean.csv
	2. peaks file
	3. Moving average value (default = 10)
Output:
	1. Angles file
	2. Histogram of angle distribution
"""

import argparse
import coloredlogs, logging
from pathlib import Path
import yaml
import numpy as np
import pandas as pd
from utility import HORIZONTAL_TAG, VERTICAL_TAG, HIGH_TYPE, LOW_TYPE, logger, _tag, is_valid_file, peaks_to_segments
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.ticker import PercentFormatter
import scipy.stats as st
from scipy.stats import norm
import statistics


def parse_cli():

	# All input that is needed
	parser = argparse.ArgumentParser(description="Angles (Plots the distribution of angles)")
	parser.add_argument("--rolling", dest="rolling", type=int, default=10, help="Rolling mean value")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")
	parser.add_argument("--data-file", dest="data_file", type=lambda x: is_valid_file(parser, x), required=True, help="path to CSV data file to read.")
	parser.add_argument("--peaks-file", dest="peaks_file", type=lambda x: is_valid_file(parser, x), required=True, help="path to YAML peaks file.")

	args = parser.parse_args()

	# enable colored logs
	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return args.data_file, args.peaks_file, args.rolling


def compute_segments(peaks_file_path):
	peaks = {}
	peaks_path = Path(peaks_file_path)
	with open(peaks_path, "r") as peaks_file:
		try:
			content = yaml.safe_load(peaks_file)
			for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
				for type in [HIGH_TYPE, LOW_TYPE]:
					# what we read is list, but we expect numpy array in the rest of the script
					peaks[_tag(tag, type)] = np.array(content[_tag(tag, type)])
		except yaml.YAMLError as exception:
			logger.critical(exception)

	horizontal_segments = peaks_to_segments(peaks[_tag(HORIZONTAL_TAG, HIGH_TYPE)], peaks[_tag(HORIZONTAL_TAG, LOW_TYPE)])
	vertical_segments = peaks_to_segments(peaks[_tag(VERTICAL_TAG, HIGH_TYPE)], peaks[_tag(VERTICAL_TAG, LOW_TYPE)])

	logger.info(f"Original horizontal segments: {len(horizontal_segments)}")
	logger.info(f"Original vertical segments: {len(vertical_segments)}")

	peak_sum = 0
	for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
		for type in [HIGH_TYPE, LOW_TYPE]:
			peak_sum = peak_sum + len(peaks[_tag(tag, type)])
	if peak_sum > (len(horizontal_segments) + len(vertical_segments)) * 2:
		logger.critical("Single peaks detected!")

	horizontal_intervals = pd.arrays.IntervalArray.from_tuples(horizontal_segments)
	vertical_intervals = pd.arrays.IntervalArray.from_tuples(vertical_segments)

	segments = list(map(lambda interval: (interval.left, interval.right), horizontal_intervals))

	for vertical_interval in vertical_intervals:
		if not np.any(horizontal_intervals.overlaps(vertical_interval)):
			segments += [(vertical_interval.left, vertical_interval.right)]

	segments.sort(key=lambda x: x[0])

	logger.info(f"Resulting segments: {len(segments)}")

	return segments


def main():

	data_file, peaks_file, rolling = parse_cli()

	frame = pd.read_csv(data_file)
	segments = compute_segments(peaks_file)

	angles = []
	for segment in segments:
		x0 = frame["x0"][segment[0]]
		y0 = frame["y0"][segment[0]]
		x1 = frame["x0"][segment[1]]
		y1 = frame["y0"][segment[1]]
		rad_angle = np.arctan((x0 - x1) / (y0 - y1))
		angle = np.degrees(rad_angle)
		angles += [angle]
		#df = pd.DataFrame(angles)
		#df.to_csv('auto-2/angle-l.csv')

	#	logger.info(f"Angle is {angle}")

	mu, std = norm.fit(angles)

	plt.hist(angles, bins=40, density=True)
	xmin, xmax = plt.xlim()
	x = np.linspace(xmin, xmax)
	p = norm.pdf(x, mu, std)
	plt.plot(x, p, 'k', linewidth=2)
	plt.plot(x, p, 'k', linewidth=2)
	title = "Fit Values: {:.2f} and {:.2f}".format(mu, std)
	plt.title(title)
	plt.ylabel('N')
	plt.xlabel('Angles');
	plt.show()




if __name__ == "__main__":
	main()
