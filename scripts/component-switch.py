#!/usr/bin/env python3
"""
The script takes Category File and computes the duration of each Component (C1 and C2)
USE SPLIT FILE
							 
Inputs:
	1. Category file
Output:
	1. Duration of C1 and C2
	2. Percentile of C1 and C2
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
	categories_frame = pd.read_csv(category_file, usecols=["category", "length"])

	c1_duration = 0
	c2_duration = 0
	b_duration = 0
	p_duration = 0
	duration = 0
	switches = 0
	category_switches = 0
	current_category = ""

	for _, [category, length] in categories_frame.iterrows():
		#if category == "B":
		#	continue
		if current_category != category:
			switches += 1
			if (current_category == "C1" and category == "C2") or (current_category == "C2" and category == "C1"):
				category_switches +=1
			current_category = category
		duration += length
		if category == "C1":
			c1_duration += length
		elif category == "C2":
			c2_duration += length
		elif category == "B":
			b_duration += length
		elif category == "P":
			p_duration += length		


	logger.info("-------------------------")
	logger.info(f"Number of All Switches {switches}")
	logger.info(f"Number of C1-C2 Switches {category_switches}")
	logger.info(f"Pattern Duration is: {int(p_duration)}")
	logger.info(f"Component 1 Duration is: {int(c1_duration)}")
	logger.info(f"Component 2 Durationis: {int(c2_duration)}")
	logger.info(f"Break Durationis: {int(b_duration)}")
	logger.info(f"Pattern share is: {(int(p_duration) / int(duration))* 100 :.2f}%")
	logger.info(f"Component 1 share is: {(int(c1_duration) / int(duration))* 100 :.2f}%")
	logger.info(f"Component 2 share is: {(int(c2_duration) / int(duration))* 100 :.2f}%")
	logger.info(f"Break share is: {(int(b_duration) / int(duration))* 100 :.2f}%")
	

if __name__ == "__main__":
	main()
