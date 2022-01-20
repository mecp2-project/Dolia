#!/usr/bin/env python3

import os
import argparse
import coloredlogs, logging
from pathlib import Path
import yaml
import numpy as np

HORIZONTAL_TAG = "x0"
VERTICAL_TAG = "y0"
HIGH_TYPE = "high"
LOW_TYPE = "low"

logger = logging.getLogger(__name__)
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


def _tag(tag, type):
	"""A helper to construct the key from tag and type (e.g. x0_high)"""
	return f"{tag}_{type}"


def parse_cli():

	# https://stackoverflow.com/a/11541450/1644554
	def is_valid_file(parser, arg):
		if not os.path.exists(arg):
			parser.error("The file %s does not exist!" % arg)
		else:
			return arg

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

	def peaks_to_segments(highs, lows):

		# short circuit if one of the lists is empty (no segments can exist)
		if len(highs) == 0 or len(lows) == 0:
			return []

		# attach the origin to a peak value
		highs = list(map(lambda x: {"value": x, "tag": HIGH_TYPE}, highs))
		lows = list(map(lambda x: {"value": x, "tag": LOW_TYPE}, lows))

		# merge peaks
		both = highs + lows

		# sort by value (but keep origin)
		both.sort(key=lambda x: x["value"])

		segments = []

		# for every two consecutive peaks, if they form a segment, save it
		for i in range(len(both)):
			if i != 0:
				if both[i - 1]["tag"] == HIGH_TYPE and both[i]["tag"] == LOW_TYPE:
					segments += [[both[i - 1]["value"], both[i]["value"]]]

		return segments

	horizontal_segments = peaks_to_segments(peaks[_tag(HORIZONTAL_TAG, HIGH_TYPE)], peaks[_tag(HORIZONTAL_TAG, LOW_TYPE)])
	vertical_segments = peaks_to_segments(peaks[_tag(VERTICAL_TAG, HIGH_TYPE)], peaks[_tag(VERTICAL_TAG, LOW_TYPE)])

	logger.info(len(horizontal_segments))
	logger.info(len(vertical_segments))

	if len(peaks[_tag(HORIZONTAL_TAG, HIGH_TYPE)]) + len(peaks[_tag(HORIZONTAL_TAG, LOW_TYPE)]) + len(peaks[_tag(VERTICAL_TAG, HIGH_TYPE)]) + len(peaks[_tag(VERTICAL_TAG, LOW_TYPE)]) > (len(horizontal_segments) + len(vertical_segments)) * 2:
		logger.critical("Single peaks detected!")


def main():
	import pandas as pd

	data_file, peaks_file, rolling = parse_cli()

	frame = pd.read_csv(data_file)
	compute_segments(peaks_file)


if __name__ == "__main__":
	main()
