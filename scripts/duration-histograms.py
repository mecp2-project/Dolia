#!/usr/bin/env python3
"""
Plotting the histogram of the duration of pursuits

Inputs:
	1. Angles File
Output:
	1. Histogram with duration distribution
"""

import argparse
import coloredlogs, logging
from pathlib import Path
import numpy as np
import pandas as pd
from utility import logger, is_valid_file
import matplotlib.pyplot as plt
import statsmodels.api as sm
import scipy.signal as signal
import statistics


def parse_cli():

	# All input that is needed
	parser = argparse.ArgumentParser(description="Histograms -- plot a single or double histogram")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")
	parser.add_argument("--bins", dest="bins", type=int, default=20, help="The number of bins for the histogram.")
	parser.add_argument("--angles-file", dest="angles_file", type=lambda x: is_valid_file(parser, x), required=True, help="path to Angles CSV file to read (if supplied, will plot the distribution of pursuit durations).")

	args = parser.parse_args()

	# enable colored logs
	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return Path(args.angles_file), args.bins


def main():

	angles_file, bins = parse_cli()

	angles_frame = pd.read_csv(angles_file, usecols=['length'])
	plt.hist(
		angles_frame['length'],
		bins=bins,
		density=True,
		label=[
			"Probability of the pursuit duration",
			],
	)
	plt.show()


if __name__ == "__main__":
	main()
