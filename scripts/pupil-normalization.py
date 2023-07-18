#!/usr/bin/env python3
"""
Inputs:
    1. .CSV file;
    2. The area of the pupil aka ellipse_area
    4. Verbosity for debugging.

What it does:
    This function reads CSV file, 
    Finds minimum and maximum value for the area of pupils
    Removes bottom (top if needed) outliers using IQR
    Interpolates the values
    Normalizes the values in the column from 0 to 1
    Write CSV File
"""

import os
import logging
from pathlib import Path
from tqdm import tqdm
from utility import is_valid_file
import matplotlib.pyplot as plt


# parse command-line options
def parse_cli():
    import argparse

    # All input that is needed
    parser = argparse.ArgumentParser(description="Sanitizer (drop low likelihood and high percentile, crop CSV, calculate locomotion)")
    parser.add_argument("--file", dest="file", type=lambda x: is_valid_file(parser, x), required=True, help="CSV file to read.")
    parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
    )

    return args.file


# This is the main function of the script. It loads and processes the data from the CSV file, 
# normalizes the area of the pupil from 0 to 1
def main():
    import pandas as pd
    import numpy as np

    # Parse the CSV file.
    file = parse_cli()
    
    pupil_frame = pd.read_csv(file, header=0)

    logging.info(f"Parsed CSV (n = {len(pupil_frame.index)})")

    # Calculate the interquartile range (IQR)
    Q1 = pupil_frame["ellipse_area"].quantile(0.25)
    Q3 = pupil_frame["ellipse_area"].quantile(0.75)
    IQR = Q3 - Q1

    # Define the upper and lower bounds for outliers
    lower_bound = Q1 - 1.5 * IQR
    #upper_bound = Q3 + 1.5 * IQR																if needed, uncomment to remove top outliers

    # Interpolate outliers within the upper and lower bounds
    pupil_frame.loc[pupil_frame["ellipse_area"] < lower_bound, "ellipse_area"] = np.nan
    #pupil_frame.loc[pupil_frame["ellipse_area"] > upper_bound, "ellipse_area"] = np.nan		if needed, uncomment to remove top outliers
    pupil_frame["ellipse_area"].interpolate(inplace=True)

    # Normalize the interpolated values from 0 to 1
    min_value = pupil_frame["ellipse_area"].min()
    max_value = pupil_frame["ellipse_area"].max()
    normalized_pupil_frame = (pupil_frame["ellipse_area"] - min_value) / (max_value - min_value)
    
    # Create a DataFrame to hold the normalized values
    df_normalized = pd.DataFrame({"normalized_pupil_area": normalized_pupil_frame})

    logging.info(f"Normalized pupil area:\n{df_normalized}")

    # Save the DataFrame to a new CSV file
    df_normalized.to_csv('normalized_pupil_area.csv', index=False)
 
if __name__ == "__main__":
    main()
