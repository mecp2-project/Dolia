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
	1. Category file
Output:
	1. CSV File that contains Categories and Lengthes of these categories
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
	parser.add_argument("--bins", dest="bins", type=int, default=20, help="The number of bins for the histogram.")
	parser.add_argument("--category-file", dest="category_file", type=str, required=True, help="path to a CSV categories file")
	
	

	args = parser.parse_args()

	# enable colored logs
	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return  Path(args.category_file), args.bins, 

def main():

    category_file, bins  = parse_cli()
    categories_frame = pd.read_csv(category_file, usecols=["0", "1"])

    p_duration = 0
    c_duration = 0
    b_duration = 0

    for _, row in categories_frame.iterrows():
        if row["0"] == "P":
            p_duration += row["1"]
        elif row ["0"] == "C":
             c_duration += row["1"] 
        else:
            b_duration += row["1"]        
	
    logger.info(f"Pattern Duration is: {p_duration}")
    logger.info(f"Component Duration is: {c_duration}")
    logger.info(f"Brake Duration is: {b_duration}")

if __name__ == "__main__":
	main()
