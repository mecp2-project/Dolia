#!/usr/bin/env python3
"""
Looking for Horizontal and Vertical segments
If Vertical does not have corresponding Horizontal --- taking Vertical
If corresponding segment exists --- taking Horizontal

Foolproof (todo):
	Plot calculated segments (in case something is missed)

Inputs:
	1. Clean.CSV
	2. peaks file
Output:
	1. Angles file
"""

import argparse
import coloredlogs, logging
from pathlib import Path
import yaml
import numpy as np
import pandas as pd
from utility import HORIZONTAL_TAG, VERTICAL_TAG, HIGH_TYPE, LOW_TYPE, logger, _tag, is_valid_file, peaks_to_segments


def parse_cli():

	# All input that is needed
	parser = argparse.ArgumentParser(description="Angles -- processes data na peak files for one experiment extracting segment info including angles")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")
	parser.add_argument("--data-file", dest="data_file", type=lambda x: is_valid_file(parser, x), required=True, help="path to a CSV data file to read.")
	parser.add_argument("--peaks-file", dest="peaks_file", type=lambda x: is_valid_file(parser, x), required=True, help="path to a YAML peaks file to read.")
	parser.add_argument("--angles-file", dest="angles_file", type=str, required=True, help="path to a CSV angles file to write.")

	args = parser.parse_args()

	# enable colored logs
	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return Path(args.data_file), Path(args.peaks_file), Path(args.angles_file)


def find_single_peaks(peaks, horizontal_segments, vertical_segments):
	"""
	Returns the frame numbers of all detected single peaks split into horizontal and vertical.

	It first creates the sets (unordered collection with no duplicates) of original peaks and peaks derived from segment endpoints.
	It then simply take the set difference and reports it for both horizontal and vertical data.
	"""

	single_peaks = {}
	for segments, tag in [(horizontal_segments, HORIZONTAL_TAG), (vertical_segments, VERTICAL_TAG)]:
		peaks_set = set.union(
			set(peaks[_tag(tag, HIGH_TYPE)]),
			set(peaks[_tag(tag, LOW_TYPE)]),
		)
		segment_endpoints_set = set([item for sublist in segments for item in sublist])
		single_peaks[tag] = peaks_set.difference(segment_endpoints_set)

	return single_peaks


def compute_segments(peaks_path):
	peaks = {}
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
		single_peaks = find_single_peaks(peaks, horizontal_segments, vertical_segments)
		for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
			if len(single_peaks[tag]) > 0:
				logger.critical(f"{tag} single peak frames: {single_peaks[tag]}")
		exit(1)

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

	data_file_path, peaks_file_path, angles_file_path = parse_cli()

	data_frame = pd.read_csv(data_file_path)
	segments = compute_segments(peaks_file_path)
	angles = []
	for segment in segments:
		x0 = data_frame["x0"][segment[0]]
		y0 = data_frame["y0"][segment[0]]
		x1 = data_frame["x0"][segment[1]]
		y1 = data_frame["y0"][segment[1]]
		segment_info = {}
		segment_info["start"] = segment[0]
		segment_info["end"] = segment[1]
		segment_info["length"] = segment[1] - segment[0]
		segment_info["delta_x"] = x1 - x0
		segment_info["delta_y"] = y1 - y0
		segment_info["angle"] = np.degrees(np.arctan((y1 - y0) / (x1 - x0))) 

		angles += [segment_info]

	angles_frame = pd.DataFrame(angles)

	angles_frame.to_csv(angles_file_path)

	logger.info(f"Angles computed and written to {angles_file_path}")

if __name__ == "__main__":
	main()
