#!/usr/bin/env python3
"""
Inputs:
		1. .CSV file;
		2. Threshold of the likelihood for all points;
		3. Maximum percentile for datapoints of interest. Anything ABOVE this percentile will be dropped;
		4. Verbosity for debugging.

What it does:
		This function reads CSV file, detects points with low likelihood, marks them as NaN (not a number) and gets them removed.
		Cuts the CSV file to 15 minutes (where the visual stimulus stops)
		Next, it detects left and right paw and plots the movement
		Write CSV File
"""

import os
import logging
from pathlib import Path
from tqdm import tqdm
from utility import is_valid_file
import matplotlib.pyplot as plt

FRAME_RATE = 60
KEEP_SECONDS = 900

C_LEFT_PAW_X = 1
C_LEFT_LIKELIHOOD = 3
C_RIGHT_PAW_X = 7
C_RIGHT_LIKELIHOOD = 9

LIKELIHOOD_THRESHOLD = 0.99
X_PERCENTILE = 0.99

WINDOW = 100
INCREMENT = 1
DIFF_THRESHOLD = 50


# parse command-line options
def parse_cli():
	import argparse

	def is_valid_percentile(parser, arg):
		if not arg.isnumeric():
			parser.error(f"Invalid value {arg}, is not a number")
		a = int(arg)
		if a > 100 or a < 0:
			parser.error(f"Invalid value {a}")
		else:
			return a

	# All input that is needed
	parser = argparse.ArgumentParser(description="Sanitizer (drop low likelihood and high percentile, crop CSV, calculate locomotion")
	parser.add_argument("--file", dest="file", type=lambda x: is_valid_file(parser, x), required=True, help="CSV file to read.")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	args = parser.parse_args()

	logging.basicConfig(
		level=logging.DEBUG if args.verbose else logging.INFO,
		format='%(asctime)s %(levelname)-8s %(message)s',
		datefmt='%a, %d %b %Y %H:%M:%S',
	)

	return args.file


def main():
	import pandas as pd
	import numpy as np

	file = parse_cli()

	frame = pd.read_csv(file, header=2)

	logging.info(f"Parsed CSV (n = {len(frame.index)})")

	frame = frame.truncate(after=KEEP_SECONDS * FRAME_RATE)

	logging.info(f"Truncated frame (n = {len(frame.index)})")

	for c_likelihood, c_paw_x in [(C_LEFT_LIKELIHOOD, C_LEFT_PAW_X), (C_RIGHT_LIKELIHOOD, C_RIGHT_PAW_X)]:

		frame.iloc[(frame.iloc[:, c_likelihood] < LIKELIHOOD_THRESHOLD), c_paw_x] = np.nan

		frame.iloc[(frame.iloc[:, c_paw_x] > frame.iloc[:, c_paw_x].quantile(X_PERCENTILE)), c_paw_x] = np.nan

	frame.interpolate(inplace=True)

	movements = []

	current = 0
	movement_start = None
	with tqdm(total=len(frame.index)) as pbar:
		while current + WINDOW < len(frame.index):
			subframe = frame.iloc[current:current + WINDOW, :]

			diff_left = subframe.iloc[:, C_LEFT_PAW_X].max() - subframe.iloc[:, C_LEFT_PAW_X].min()
			diff_right = subframe.iloc[:, C_RIGHT_PAW_X].max() - subframe.iloc[:, C_RIGHT_PAW_X].min()

			if diff_left >= DIFF_THRESHOLD or diff_right >= DIFF_THRESHOLD:
				logging.debug(f"Window [{current} : {current+WINDOW}] MOVEMENT")
				if movement_start is None:
					movement_start = current
			else:
				if movement_start is not None:
					movements += [(movement_start, current)]
					movement_start = None

			current += INCREMENT
			pbar.update(INCREMENT)

	logging.info(f"Found {len(movements)} movement windows")

	total_frames = 0

	for start, end in movements:
		logging.info(f"Movement [{start} : {end}] {end - start} frames")
		total_frames += end - start

	logging.info(f"Total frames where mouse walks: {total_frames}")

	ax = frame.iloc[:, C_LEFT_PAW_X].plot(label="Left Paw")
	frame.iloc[:, C_RIGHT_PAW_X].plot(ax=ax, label="Right Paw")
	plt.xlabel("Frames")
	plt.ylabel("Pixels")
	plt.legend()
	
	plt.show()



	print(frame.iloc[:, [C_LEFT_PAW_X, C_LEFT_LIKELIHOOD, C_RIGHT_PAW_X, C_RIGHT_LIKELIHOOD]])


if __name__ == "__main__":
	main()
