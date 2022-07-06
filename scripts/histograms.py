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
from scipy.signal import find_peaks


def parse_cli():

	# All input that is needed
	parser = argparse.ArgumentParser(description="Histograms -- plot a single or double histogram")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")
	parser.add_argument("--bins", dest="bins", type=int, default=20, help="The number of bins for the histogram.")
	parser.add_argument("--highest_peak", dest="highest_peak", type=float, default=None, help="Highest peak of the set. If supplied, program will compute switches using standard deviation.")
	parser.add_argument("--angles-file", dest="angles_file", type=lambda x: is_valid_file(parser, x), required=True, help="path to a CSV angles file to read.")
	parser.add_argument("--secondary-file", dest="secondary_file", type=lambda x: is_valid_file(parser, x), required=False, help="path to a secondary CSV angles file to read (if supplied, will plot double histogram).")
	parser.add_argument("--svg", dest="svg", default=False, help="save to SVG (double-histogram.svg in your current directory) instead of showing in a window", action="store_true")

	args = parser.parse_args()

	# enable colored logs
	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return Path(args.angles_file), Path(args.secondary_file) if args.secondary_file else None, args.bins, args.svg, args.highest_peak


def main():

	angles_file_path, secondary_file_path, bins, svg, highest_peak = parse_cli()

	grid = np.linspace(-90, 90, 1000)
	bar_colors = ["steelblue", "palevioletred"]
	line_colors = ["mediumblue", "mediumvioletred"]
	tick_colors = ["mediumblue", "mediumvioletred"]

	if svg:
		plt.figure(figsize=[10, 6])

	# if secondary file supplied and highest peak supplied, then error
	if secondary_file_path is not None and highest_peak is not None:
		logger.critical("Secondary File and Highest peak were supplied. Choose one of them.")
		exit(1)

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

			plt.plot(grid, pdf, lw=3, color=line_colors[0 if primary else 1], label=f"{'WT' if primary else 'MECP2'} KDE with normal reference bandwidth")
			plt.plot(grid[peaks], pdf[peaks], "o", color="orange", label= "highest peak")
			mins, _ =find_peaks(pdf*-1)
			plt.plot(grid[mins], pdf[mins], 'o', color="red")
			plt.axvline(angles.mean(), color='orange', linestyle='dashed', linewidth=1, label= "mean")
			plt.axvline(np.median(angles), color='green', linestyle='dashed', linewidth=2, label= "median")
			plt.plot(angles, [0 for i in range(len(angles))], "|", color=tick_colors[0 if primary else 1])
			logger.info(f"Median is {np.median(angles):.2f}")
			logger.info(f"Mean is {angles.mean():.2f}")
	plt.hist(
		angles_list,
		bins=bins,
		density=True,
		color=bar_colors if secondary_file_path else bar_colors[0],
		label=[
			"WT angle probability distribution",
			"MECP2 angle probability distribution",
		],
	)

	if highest_peak is not None:
		angle_std = statistics.pstdev(angles_list[0])
		plus_std = highest_peak + angle_std
		minus_std = highest_peak - angle_std

		plt.axvline(x=highest_peak, color="green", linewidth=2)
		plt.axvline(x=plus_std, color="red", linewidth=2)
		plt.axvline(x=minus_std, color="red", linewidth=2)

		logger.info(f"Standard Deviation is {angle_std:.2f}")
		logger.info(f"Highest Peak + Standard Deviation is {plus_std:.2f}")
		logger.info(f"Highest Peak - Standard Deviation is {minus_std:.2f}")


	plt.ylabel("Density")
	plt.xlabel("Angle (degrees)")
	plt.title("WT vs MECP2 by angle distribution")
	plt.legend()

	if svg:
		plt.savefig("double-histogram.svg", format="svg")
		logger.info("Saved to SVG file: double-histogram.svg")
	else:
		plt.show()


if __name__ == "__main__":
	main()
