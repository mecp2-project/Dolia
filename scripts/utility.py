import logging
import os

HORIZONTAL_TAG = "x0"
VERTICAL_TAG = "y0"
AREA_TAG = "ellipse_area"
RATIO_TAG = "radius_ratio"
HIGH_TYPE = "high"
LOW_TYPE = "low"

logger = logging.getLogger(__name__)


def _tag(tag, type):
	"""A helper to construct the key from tag and type (e.g. x0_high)"""
	return f"{tag}_{type}"


# https://stackoverflow.com/a/11541450/1644554
def is_valid_file(parser, arg):
	if not os.path.exists(arg):
		parser.error("The file %s does not exist!" % arg)
	else:
		return arg


def peaks_to_segments(highs, lows):
	"""
	Derive full segments from the lists of high and low peaks.

	A segment is a pair of peaks such that the first one is high, the second is low, and there are no other peaks in between.

	The output is a tuple of lists of tuples representing segments.
	"""

	# short circuit if one of the lists is empty (no segments can exist)
	if len(highs) == 0 or len(lows) == 0:
		return []

	# attach the origin to a peak value
	highs = list(map(lambda x: {"value": x, "tag": HIGH_TYPE}, highs))
	lows = list(map(lambda x: {"value": x, "tag": LOW_TYPE}, lows))

	# merge peaks
	both = highs + lows

	# sort by value (but keep origin)
	both.sort(key=lambda x: x["value"])

	segments = []

	# for every two consecutive peaks, if they form a segment, save it
	for i in range(len(both)):
		if i != 0:
			if both[i - 1]["tag"] == HIGH_TYPE and both[i]["tag"] == LOW_TYPE:
				segments += [(both[i - 1]["value"], both[i]["value"])]

	return segments
