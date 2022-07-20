#!/usr/bin/env python3
"""
The script takes Angles file and based on the Angle and the brackets determines which category (Component (C) or Pattern (P)) it belongs to.
If the distance between two eye movements is greater that 300 frames (Defined as MAX_INTERVAL, can be changed if needed), this period will be considered a break (B).

Merge Epochs:
			 Component 1 and Cmponent 2 will be considered the same epoch ===> Component (C).
Split Epochs:
			Component 1 (Value smaller than MEAN - STD) will be marked as C1
			Component 2 (Value Greater than MEAN + STD) will be marked as C2							 

Inputs:
	1. Angles file
	2. Plus/ Minust Std
	3. Name of Category file
Output:
	1. CSV File that contains Categories and Lengthes of these categories
"""

import argparse
import coloredlogs, logging
from pathlib import Path
import pandas as pd
from utility import logger, is_valid_file
import matplotlib.pyplot as plt

MAX_INTERVAL = 300

def parse_cli():

	# All input that is needed
	parser = argparse.ArgumentParser(description="Histograms -- plot a single or double histogram")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")
	parser.add_argument("--bins", dest="bins", type=int, default=20, help="The number of bins for the histogram.")
	parser.add_argument("--angles-file", dest="angles_file", type=lambda x: is_valid_file(parser, x), required=True, help="path to Angles CSV file to read (if supplied, will plot the distribution of pursuit durations).")
	parser.add_argument("--category-file", dest="category_file", type=str, required=True, help="path to a CSV categories file to write.")
	parser.add_argument("--plus-std", dest="plus_std", type=float, required=True, help="Highest peak plus standard deviation")
	parser.add_argument("--minus-std", dest="minus_std", type=float, required=True, help="Highest peak minus standard deviation")
	

	args = parser.parse_args()

	# enable colored logs
	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return Path(args.angles_file), Path(args.category_file), args.bins, args.plus_std, args.minus_std 


def compute_epochs(angles_frame, plus_std, minus_std, get_category):
	current_category = ""
	current_epoch_length = 0
	epochs = []
	for _, row in angles_frame.iterrows():
		category = get_category(row["angle"], plus_std, minus_std)
		if current_category == category and row["interval"] < MAX_INTERVAL:
			current_epoch_length += int(row["length"])
		else:
			if current_category != "":
				epochs += [[current_category, current_epoch_length]]
			if row["interval"] >= MAX_INTERVAL:
				epochs += [["B", row["interval"]]]
			current_epoch_length = int(row["length"])
			current_category = category

	epochs += [[current_category, current_epoch_length]]
	return epochs


def split_components(angle, plus_std, minus_std):
	if angle > plus_std:
		return "C2"
	if angle < minus_std:
		return "C1"	
	return "P "


def merge_components(angle, plus_std, minus_std):
	if angle > plus_std or angle < minus_std:
		return "C"
	return "P"


def main():

	angles_file, category_file, bins, plus_std, minus_std  = parse_cli()

	angles_frame = pd.read_csv(angles_file, usecols=["length", "angle", "interval"])

	split_epochs = compute_epochs(
		angles_frame,
		plus_std,
		minus_std,
		split_components,
	)

	logger.info("-------------------------")

	merge_epochs = compute_epochs(
		angles_frame,
		plus_std,
		minus_std,
		merge_components,
	)

	for category, length in merge_epochs:
		logger.info(f"{category}: {length}")

	
	category_frame = pd.DataFrame(merge_epochs)
	category_frame.to_csv(category_file)

	logger.info(category_frame)
	logger.info(f"Categories computed and written to {category_file}")
	logger.info(f" Number of Switches including Breaks {category_frame.shape[0]- 1}")


	#plt.hist(
	#	list(map(lambda x: x[1], split_epochs)),
	#	bins=bins,
	#)
	#plt.show()

if __name__ == "__main__":
	main()
