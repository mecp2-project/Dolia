#!/usr/bin/env python3

import os
import logging

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

    def is_valid_percentile(parser, arg):
        if not arg.isnumeric():
            parser.error(f"Invalid value {arg}, is not a number")
        a = float(arg)
        if a > 1 or a < 0:
            parser.error(f"Invalid value {a}")
        else:
            return arg

    parser = argparse.ArgumentParser(description="Sanitizer")
    parser.add_argument(
        # CLI parameter
        "--file",
        # the name of the argument in Python (i.e. args.VARIABLE_NAME)
        dest="file",
        # either the Python native type (int, float, str) or a function that validates the input
        type=lambda x: is_valid_file(parser, x),
        # will not run if required argument is not given
        required=True,
        # help message to be displayed in -h
        help="CSV file to read.",
    )

    parser.add_argument(
        "--likelihood",
        dest="likelihood",
        type=lambda x: is_valid_percentile(parser, x),
        default=0.9,
        help="Likelihood threshold. Datapoints below this will be dropped.",
    )
    parser.add_argument(
        "--min-percentile",
        dest="min_percentile",
        type=lambda x: is_valid_percentile(parser, x),
        default=0.15,
        help=
        "Min. percentile. Datapoints below this percentile will be dropped.",
    )
    parser.add_argument(
        "--max-percentile",
        dest="max_percentile",
        type=lambda x: is_valid_percentile(parser, x),
        default=0.95,
        help=
        "Max. percentile. Datapoints above this percentile will be dropped.",
    )
    parser.add_argument(
        "--eyeblink",
        dest="eyeblink",
        type=int,
        default=50,
        help=
        "Number of pixels between top and bottom lid. Datapoints below this value will be dropped.",
    )
    parser.add_argument(
        "--points-to-plot",
        dest="p",
        type=int,
        default=0,
        help="Number of points to plot. Not plotting in default",
    )
    parser.add_argument(
        "-v",
        dest="verbose",
        default=False,
        help="increase output verbosity",
        action="store_true",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
    )

    return args.file, args.likelihood, args.min_percentile, args.max_percentile, args.eyeblink, args.p


def main():
    file, likelihood, min_percentile, max_percentile, eyeblink, p = parse_cli()
    logging.debug("%s, %f, %f, %f, %d, %d", file, likelihood, min_percentile,
                  max_percentile, eyeblink, p)
    logging.info(f"File: {file}")


if __name__ == "__main__":
    main()
