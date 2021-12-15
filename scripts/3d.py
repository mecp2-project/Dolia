#!/usr/bin/env python3

import os
import logging

# change directory to that of the script file
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


def parse_cli():
	import argparse

	# https://stackoverflow.com/a/11541450/1644554
	def is_valid_file(parser, arg):
		if not os.path.exists(arg):
			parser.error("The file %s does not exist!" % arg)
		else:
			return arg

	# All input that is needed
	parser = argparse.ArgumentParser(description="Plot 3D")
	parser.add_argument("--file", dest="file", type=lambda x: is_valid_file(parser, x), required=True, help="CSV file to read.")
	parser.add_argument("--from", dest="_from", type=int, default=0, help="Frame from which to plot.")
	parser.add_argument("--to", dest="_to", type=int, default=500, help="Frame to which to plot.")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	args = parser.parse_args()

	if args._from >= args._to:
		parser.error(f"--to (given {args._to}) must be after --from (given {args._from})")

	logging.basicConfig(
		level=logging.DEBUG if args.verbose else logging.INFO,
		format="%(asctime)s %(levelname)-8s %(message)s",
		datefmt="%a, %d %b %Y %H:%M:%S",
	)

	return args.file, args._from, args._to


def main():
	import pandas as pd
	from mpl_toolkits import mplot3d
	import matplotlib.pyplot as plt

	file, _from, _to = parse_cli()

	frame = pd.read_csv(file, skiprows=range(1, _from + 1), nrows=(_to - _from + 1))

	plt.figure()
	ax = plt.axes(projection="3d")
	ax.plot3D(frame["roll_x0"], frame["roll_y0"], range(_from, _to + 1), "blue")
	ax.set_xlabel("x")
	ax.set_ylabel("y")
	ax.set_zlabel("frame")

	plt.show()


if __name__ == "__main__":
	main()