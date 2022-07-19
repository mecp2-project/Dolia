#!/usr/bin/env python3
"""
The script takes Category File and computes the duration of each epoch (Patten(P), Component (C) or Break (B))
							 
Inputs:
	1. Category file
Output:
	1. Duration of P, C and B
	2. Percentile of P, C and B
"""

import argparse
import coloredlogs, logging
from pathlib import Path
import pandas as pd
from utility import logger, is_valid_file
import matplotlib.pyplot as plt


def parse_cli():

	# All input that is needed
	parser = argparse.ArgumentParser(description="Histograms -- plot a single or double histogram")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")
	parser.add_argument("--category-file", dest="category_file", type=str, required=True, help="path to a CSV categories file")
	
	

	args = parser.parse_args()

	# enable colored logs
	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return  Path(args.category_file)

def main():

	category_file = parse_cli()
	categories_frame = pd.read_csv(category_file, usecols=["0", "1"])

	p_duration = 0
	c_duration = 0
	b_duration = 0
	duration = 0

	for _, row in categories_frame.iterrows():
		duration += row["1"]
		if row["0"] == "P":
			p_duration += row["1"]
		elif row ["0"] == "C":
			c_duration += row["1"]
		else:
			b_duration += row["1"]
	
	logger.info(f"Number of Switches including Breaks {categories_frame.shape[0]- 1}")
	logger.info("-------------------------")
	logger.info(f"Whole Eye Movements Duration is: {int(duration)}")
	logger.info(f"Pattern Duration is: {int(p_duration)}")
	logger.info(f"Component Duration is: {int(c_duration)}")
	logger.info(f"Brake Duration is: {int(b_duration)}")
	logger.info("-------------------------")
	logger.info(f"Pattern share is: {(int(p_duration) / int(duration))* 100 :.2f}%")
	logger.info(f"Component share is: {(int(c_duration) / int(duration))* 100 :.2f}%")
	logger.info(f"Brake share is: {(int(b_duration) / int(duration))* 100 :.2f}%")

if __name__ == "__main__":
	main()
