#!/usr/bin/env python3

import os

# change directory to that of the script file
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


# parse command-line options
def parse_cli():
	import argparse

	# https://stackoverflow.com/a/11541450/1644554
	def is_valid_file(parser, arg):
		if not os.path.exists(arg):
			parser.error("The file %s does not exist!" % arg)
		else:
			return arg

	parser = argparse.ArgumentParser(description="Basic Plot")
	parser.add_argument("--file", dest="file", metavar="file", type=lambda x: is_valid_file(parser, x), required=True, help=f"CSV file to read.")
	parser.add_argument("-c", dest="column", metavar="column", type=int, required=True, default="1", help=f"The column to plot (start with 0, where 0 is the record number).")
	parser.add_argument("-l", dest="likelihood", metavar="likelihood-column", type=int, required=False, default="3", help=f"The column that corresponds to likelihood of the target column.")
	parser.add_argument("-n", dest="points", metavar="points-number", type=int, required=False, default="9999999", help=f"Number of points to read from CSV (default read all).")
	parser.add_argument("-r", dest="rolling", metavar="rolling-value", type=int, required=False, default="5", help=f"the value of rolling mean.")

	args = parser.parse_args()

	return args.file, args.column, args.points, args.rolling, args.likelihood


def main():
	import pandas as pd
	from bokeh.plotting import figure, show
	from bokeh.models import Range1d
	import numpy as np

	file, column, points, rolling, likelihood = parse_cli()

	df = pd.read_csv(file, usecols=[column, likelihood], header=2, nrows=points)
	df.columns = ["Target", "Likelihood"]

	df["Target"] = np.where((df.Likelihood <= 0.95), 0, df.Target)

	rolling = df["Target"].rolling(window=rolling).mean()

	plot = figure(title=f"Column {column}", x_axis_label='frame', y_axis_label='coordinate', plot_width=1800)
	plot.y_range = Range1d(50, 150)

	plot.line([x for x in range(0, len(df))], df["Target"].values.tolist(), legend_label="Line", line_width=2)
	plot.line([x for x in range(0, len(df))], rolling.values.tolist(), legend_label="Moving Average", line_width=2, color="red")

	show(plot)


if __name__ == "__main__":
	main()
