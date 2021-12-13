#!/usr/bin/env python3
"""
Inputs:
		1. .CSV file;
		2. Threshold of the likelihood for all points;
		3. Minimum percentile for datapoints of interest. Anything BELOW this percentile will be dropped;
		4. Maximum percentile for datapoints of interest. Anything ABOVE this percentile will be dropped;
		5. Minimum percentile for Radius. Anything BELOW this percentile will be dropped;
		6. Maximum percentile for Radius. Anything ABOVE this percentile will be dropped;
		7. Threshold that is considered an eyeblink. Anything BELOW this value will be dropped;
		8. Number of points you want to plot (it is 0 by default). If you want to print everything, type -n 0;
		9. Size of the sliding window;
		10. Verbosity for debugging.

What it does:
		This function reads CSV file, detects points with low likelihood, marks them as NaN (not a number) and gets them removed. 
		Next, it tries to fit an ellipse (ellipse.py).
		If ellipse is found -- data is written into table, If ellipse not found data are aremoved.
		Ratios of radii that are not within threshold range get removed.
		Sliding window removes last outliers.
		Plotting.		
"""

import os
import logging

# change directory to that of the script file
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


# parse command-line options
def parse_cli():
	"""
    sdds
    """
	import argparse

	# https://stackoverflow.com/a/11541450/1644554
	def is_valid_file(parser, arg):
		if not os.path.exists(arg):
			parser.error("The file %s does not exist!" % arg)
		else:
			return arg

	def is_valid_percentile(parser, arg):
		if not arg.isnumeric():
			parser.error(f"Invalid value {arg}, is not a number")
		a = int(arg)
		if a > 100 or a < 0:
			parser.error(f"Invalid value {a}")
		else:
			return a
	# All input that is needed
	parser = argparse.ArgumentParser(description="Sanitizer (drop low likelihood, compute ellipses, interpolate radius ratio outliers and center coordinates)")
	parser.add_argument("--file", dest="file", type=lambda x: is_valid_file(parser, x), required=True, help="CSV file to read.")
	parser.add_argument("--likelihood", dest="likelihood", type=lambda x: is_valid_percentile(parser, x), default=0.9, help="Likelihood threshold. Datapoints below this will be dropped.")
	parser.add_argument("--min-percentile", dest="min_percentile", type=lambda x: is_valid_percentile(parser, x), default= 1, help="Min. percentile. Datapoints below this percentile will be dropped.")
	parser.add_argument("--max-percentile", dest="max_percentile", type=lambda x: is_valid_percentile(parser, x), default= 99, help="Max. percentile. Datapoints above this percentile will be dropped.")
	parser.add_argument("--radius-max-percentile", dest="radius_max_percentile", type=lambda x: is_valid_percentile(parser, x), default= 99, help="Max. percentile of a RADIUS. Datapoints above this percentile will be dropped.")
	parser.add_argument("--radius-min-percentile", dest="radius_min_percentile", type=lambda x: is_valid_percentile(parser, x), default=1, help="Min. percentile of a RADIUS. Datapoints below this percentile will be dropped.")
	parser.add_argument("--eyeblink", dest="eyeblink", type=int, default=50, help="Number of pixels between top and bottom lid. Datapoints below this value will be dropped.")
	parser.add_argument("-n", dest="n", type=int, default=0, help="Number of points to plot. Not plotting in default")
	parser.add_argument("--window", dest="window", type=int, default=500, help="Window size in frames")
	parser.add_argument("--rolling", dest="rolling", type=int, default=10, help="Rolling mead value")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	args = parser.parse_args()

	logging.basicConfig(
		level=logging.DEBUG if args.verbose else logging.INFO,
		format='%(asctime)s %(levelname)-8s %(message)s',
		datefmt='%a, %d %b %Y %H:%M:%S',
	)

	return args.file, args.likelihood, args.min_percentile, args.max_percentile, args.radius_max_percentile, args.radius_min_percentile, args.eyeblink, args.n, args.window, args.rolling


def main():
	import pandas as pd
	import numpy as np
	from ellipse import ellipse_fit

	file, likelihood, min_percentile, max_percentile, radius_max_percentile, radius_min_percentile, eyeblink, n, window, rolling = parse_cli()


	input = pd.read_csv(file, header=2, nrows=None if n == 0 else n)

	likelihood_columns = [3, 6, 9, 12, 15, 18, 21, 24]

	initial_data = []

	for index, row in input.iterrows(): 
		low_likelihood = False
		for column in likelihood_columns:
			if row[column] < likelihood:
				low_likelihood = True		# find low likelihood
				break
		if low_likelihood:
			initial_data += [[np.nan, np.nan, np.nan, np.nan, np.nan]]	# if not within normal range --- remove
		else:
			status, ellipse = ellipse_fit(
				np.array([row["x"], row["x.1"], row["x.2"], row["x.3"], row["x.4"], row["x.5"], row["x.6"], row["x.7"]]), #ellipse.py fit the ellipse
				np.array([row["y"], row["y.1"], row["y.2"], row["y.3"], row["y.4"], row["y.5"], row["y.6"], row["y.7"]]),
			)
			if status:
				initial_data += [[
					ellipse["X0_in"],
					ellipse["Y0_in"],
					ellipse["b"],
					ellipse["a"],
					ellipse["a"] / ellipse["b"], #ellipse is found
				]]
			else:
				initial_data += [[np.nan, np.nan, np.nan, np.nan, np.nan]] #ellipse is not found, 

	frame = pd.DataFrame(initial_data, columns=['x0', 'y0', 'rlong', 'rshort', 'radius_ratio'])

	# Removes outliers with unacceptable ratio of radii
	frame[frame.radius_ratio > frame.radius_ratio.quantile(radius_max_percentile/100.0)] = np.nan 
	frame[frame.radius_ratio < frame.radius_ratio.quantile(radius_min_percentile/100.0)] = np.nan

	#Sliding Window. Removes outliers
	current = 0 #first position
	while current < len(frame.index):
		current_window = min(window, len(frame.index) - current)
		current_frame = frame[current:current + current_window].copy()

		x0_max_percentile = current_frame.x0.quantile(max_percentile/100.0)
		x0_min_percentile = current_frame.x0.quantile(min_percentile/100.0)
		y0_max_percentile = current_frame.y0.quantile(max_percentile/100.0)
		y0_min_percentile = current_frame.y0.quantile(min_percentile/100.0)

		current_frame.loc[current_frame.x0 > x0_max_percentile, "x0"] = x0_max_percentile
		current_frame.loc[current_frame.x0 < x0_min_percentile, "x0"] = x0_min_percentile

		current_frame.loc[current_frame.y0 > y0_max_percentile, "y0"] = y0_max_percentile
		current_frame.loc[current_frame.y0 < y0_min_percentile, "y0"] = y0_min_percentile

		frame[current:current + current_window] = current_frame.copy()
		current += window

	frame.interpolate(inplace=True) #interpolation

	frame["roll_x0"] = frame["x0"].rolling(rolling).mean() #rolling mean to smooth the plot
	
	import matplotlib.pyplot as plt

	plt.plot(frame["roll_x0"], color = 'red', label = f'Rolling Mean {rolling}')
	
	plt.plot(frame["x0"], linewidth = 0.5, label = 'Raw Data')
	plt.ylabel('Pixels')
	plt.xlabel('Frames')
	plt.legend()
	plt.show()
	


if __name__ == "__main__":
	main()
