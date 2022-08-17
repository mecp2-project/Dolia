#!/usr/bin/env python3
"""
The script takes Category File and computes the duration of each epoch (Patten (P), Component (C) or Break (B))
USE MERGE FILE
							 
Inputs:
	1. Category file
Output:
	WHEN BREAKS ARE CONSIDERED CATEGORIES
	1. Number of Switches
	2. Duration of Eye Movements 
	3. Pattern Duration
	4. Break Duration
	5. Component Duration
	6. Pattern Share (in %)
	7. Component Share (in %)
	8. Break Share (in %)

	WHEN BREAKS ARE NOT CONSIDERED CATEGORIES
	1. Number of Switches
	2. Duration of Eye Movements 
	3. Pattern Duration
	4. Component Duration
	5. Pattern Share (in %)
	6. Component Share (in %)
	
	
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

	p_duration = 0
	c_duration = 0
	b_duration = 0
	duration = 0

	for _, [category, length] in categories_frame.iterrows():
		duration += length
		if category == "P":
			p_duration += length
		elif category == "C":
			c_duration += length
		else:
			b_duration += length
	
	logger.info(f"Number of Switches including Breaks {categories_frame.shape[0]- 1}")
	logger.info("-------------------------")
	logger.info(f"Whole Eye Movements Duration is: {int(duration)}")
	logger.info(f"Pattern Duration is: {int(p_duration)}")
	logger.info(f"Component Duration is: {int(c_duration)}")
	logger.info(f"Break Duration is: {int(b_duration)}")
	logger.info("-------------------------")
	logger.info(f"Pattern share is: {(int(p_duration) / int(duration))* 100 :.2f}%")
	logger.info(f"Component share is: {(int(c_duration) / int(duration))* 100 :.2f}%")
	logger.info(f"Break share is: {(int(b_duration) / int(duration))* 100 :.2f}%")

	switches = 0
	c_duration = 0
	p_duration = 0
	duration = 0
	current_category = ""
	
	for _, [category, length] in categories_frame.iterrows():
		if category == "B":
			continue
		if current_category != category:
			switches += 1
			current_category = category
		duration += length
		if category == "P":
			p_duration += length
		elif category == "C":
			c_duration += length

	logger.info("-------------------------")
	logger.info("WITHOUT BREAKS")
	logger.info("-------------------------")
	logger.info(f"Number of Switches EXCLUDING Breaks {switches}")
	logger.info("-------------------------")
	logger.info(f"Whole Eye Movements Duration is: {int(duration)}")
	logger.info(f"Pattern Duration is: {int(p_duration)}")
	logger.info(f"Component Duration is: {int(c_duration)}")
	logger.info("-------------------------")
	logger.info(f"Pattern share is: {(int(p_duration) / int(duration))* 100 :.2f}%")
	logger.info(f"Component share is: {(int(c_duration) / int(duration))* 100 :.2f}%")
	



if __name__ == "__main__":
	main()
