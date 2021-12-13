#!/usr/bin/env python3

import os
import logging

# change directory to that of the script file
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

def parse_cli():
	import argparse

	# All input that is needed
	parser = argparse.ArgumentParser(description="Plot (Plots sanitized data)")
	parser.add_argument("--rolling", dest="rolling", type=int, default=10, help="Rolling mead value")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	args = parser.parse_args()

	logging.basicConfig(
		level=logging.DEBUG if args.verbose else logging.INFO,
		format='%(asctime)s %(levelname)-8s %(message)s',
		datefmt='%a, %d %b %Y %H:%M:%S',
	)

	return args.rolling

def main():
	import pandas as pd
	import matplotlib.pyplot as plt

	rolling = parse_cli()
	
	frame = pd.read_csv('clean.csv')

	#plt.plot(frame["roll_x0"], color = 'red', label = f'Rolling Mean {rolling}')
		
	#plt.plot(frame["x0"], linewidth = 0.5, label = 'Raw Data')
	#plt.ylabel('Pixels')
	#plt.xlabel('Frames')
	#plt.legend()
	#plt.show()

	fig, (ax1, ax2) = plt.subplots(2)
	ax1.plot(frame["x0"], linewidth = 0.5, label = 'Raw Data')
	ax1.plot(frame["roll_x0"],color = 'red', label = 'Rolling Mean')
	ax1.set_title('Horizontal Movements')
	ax1.legend()
	ax2.plot(frame["y0"], linewidth = 0.5, label = 'Raw Data')
	ax2.plot(frame["roll_y0"],color = 'red', label = 'Rolling Mean')
	ax2.set_title('Vertical Movements')
	ax2.set_xlabel('Frames')
	fig.text(0.06, 0.5, 'Pixels', ha='center', va='center', rotation='vertical')
	ax2.legend()
	plt.show()


if __name__ == "__main__":
	main()