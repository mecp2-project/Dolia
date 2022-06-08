#!/usr/bin/env python3

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
	parser.add_argument("--clean-file", dest="clean_file", type=lambda x: is_valid_file(parser, x), required=True, help="path to a Clean CSV file to read (if supplied, will plot pupils area).")

	args = parser.parse_args()

	# enable colored logs
	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return Path(args.clean_file), args.bins


def main():

	clean_file, bins = parse_cli()

	clean_frame = pd.read_csv(clean_file, usecols=['roll_ellipse_area'])
	plt.hist(
		clean_frame['roll_ellipse_area'],
		bins=bins,
		density=True,
		label=[
			"Pupil area distribution probability",
			],
	)
	plt.show()


if __name__ == "__main__":
	main()
