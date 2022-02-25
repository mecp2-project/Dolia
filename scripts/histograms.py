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


def parse_cli():

	# All input that is needed
	parser = argparse.ArgumentParser(description="Histograms -- plot a single or double histogram")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")
	parser.add_argument("--bins", dest="bins", type=int, default=30, help="The number of bins for the histogram.")
	parser.add_argument("--angles-file", dest="angles_file", type=lambda x: is_valid_file(parser, x), required=True, help="path to a CSV angles file to read.")
	parser.add_argument("--secondary-file", dest="secondary_file", type=lambda x: is_valid_file(parser, x), required=False, help="path to a secondary CSV angles file to read (if supplied, will plot double histogram).")
	parser.add_argument("--svg", dest="svg", default=False, help="save to SVG (double-histogram.svg in your current directory) instead of showing in a wondow", action="store_true")

	args = parser.parse_args()

	# enable colored logs
	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return Path(args.angles_file), Path(args.secondary_file) if args.secondary_file else None, args.bins, args.svg


def main():

	angles_file_path, secondary_file_path, bins, svg = parse_cli()

	grid = np.linspace(-90, 90, 1000)
	bar_colors = ["forestgreen", "firebrick"]
	line_colors = ["limegreen", "orangered"]
	tick_colors = ["lime", "red"]

	if svg:
		plt.figure(figsize=[10, 6])

	angles_list = []
	for file_path, primary in [(angles_file_path, True), (secondary_file_path, False)]:
		if file_path:

			angles_frame = pd.read_csv(file_path)
			logger.info(f"Read {len(angles_frame.index)} {'Primary' if primary else 'secondary'} segments")

			angles = np.array(angles_frame["angle"])
			angles_list += [angles]

			kde_distribution = sm.nonparametric.KDEMultivariate([angles], var_type="c", bw="normal_reference")

			pdf = kde_distribution.pdf(grid)
			peaks = signal.find_peaks(pdf)[0]

			plt.plot(grid, pdf, lw=3, color=line_colors[0 if primary else 1], label=f"{'Non-MECP2' if primary else 'MECP2'} KDE with normal reference bandwidth")
			plt.plot(grid[peaks], pdf[peaks], "o", color="orange")

			plt.plot(angles, [0 for i in range(len(angles))], "|", color=tick_colors[0 if primary else 1])

	plt.hist(
		angles_list,
		bins=bins,
		density=True,
		color=bar_colors if secondary_file_path else bar_colors[0],
		label=[
			"Non-MECP2 angle probability distribution",
			"MECP2 angle probability distribution",
		],
	)

	plt.ylabel("Probability")
	plt.xlabel("Angle (degrees)")
	plt.title("Non-MECP2 vs MECP2 by angle distribution")
	plt.legend()

	if svg:
		plt.savefig("double-histogram.svg", format="svg")
		logger.info("Saved to SVG file: double-histogram.svg")
	else:
		plt.show()


if __name__ == "__main__":
	main()
