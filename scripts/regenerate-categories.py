#!/usr/bin/env python3

import logging
from utility import logger

STD_FILENAME = "mouse-plus-minus-std.tsv"
CMD_FILENAME = "regenerate-categories.sh"


# parse command-line options
def parse_cli():
	import argparse

	# All input that is needed
	parser = argparse.ArgumentParser(description="Walk the directories and regenerate all category files")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	args = parser.parse_args()

	logging.basicConfig(
		level=logging.DEBUG if args.verbose else logging.INFO,
		format='%(asctime)s %(levelname)-8s %(message)s',
		datefmt='%a, %d %b %Y %H:%M:%S',
	)


def main():
	import pandas as pd
	from pathlib import Path

	parse_cli()

	stds = pd.read_csv(STD_FILENAME, sep='\t')

	logger.info(f"Read {len(stds.index)} lines")

	def stds_from_string(string):
		import re

		regexp = re.compile("Plus:\s+(-?\d+.\d+)\s+Minus:\s+(-?\d+.\d+)")
		match = regexp.search(string)
		return match.group(1), match.group(2)

	with open(CMD_FILENAME, "w") as commands:
		commands.write("""
#!/usr/bin/env bash

set -x

# Ensure that the CWD is set to script's location
cd "${0%/*}"
CWD=$(pwd)

""")

		for _, mouse in stds.iterrows():
			plus, minus = stds_from_string(mouse['stds'])
			logger.info(f"Processing mouse '{mouse['name']}' with +STD {plus} and -STD {minus}")

			commands.write(f"# Mouse: '{mouse['name']}' with +STD {plus} and -STD {minus}\n\n")

			tracks = Path(f"./angles/{mouse['name'].lower()}-angles/").glob("*-angles.csv")
			for track in tracks:
				if track.is_file():
					if "OKN_grat" in str(track):
						continue

					for mode in ["merge", "split"]:
						category_file = track.stem.replace("-angles", f"-{mode}")

						arguments = [
							"./scripts/categories.py",
							"--mode",
							mode,
							"--angles-file",
							f"./angles/{mouse['name'].lower()}-angles/{track.stem}.csv",
							"--category-file",
							f"./categories/{mouse['name'].lower()}-category/{mode}/{category_file}.csv",
							"--plus-std",
							plus,
							"--minus-std",
							minus,
						]
						commands.write(" ".join(arguments) + "\n\n")

		commands.write("echo 'Done!'")


if __name__ == "__main__":
	main()
