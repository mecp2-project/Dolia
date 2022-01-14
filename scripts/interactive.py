#!/usr/bin/env python3

import os
import argparse
import coloredlogs, logging
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path
import textwrap
import yaml
from peaks import find_peaks

# change directory to that of the script file;
# this way, the relative paths will work as expected
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

logger = logging.getLogger(__name__)

# Constants
KEY_CLOSE = "q"
KEY_RIGHT = "right"
KEY_LEFT = "left"
KEY_ZOOM_IN = "i"
KEY_ZOOM_OUT = "o"
KEY_HOLD_NOT_SNAP = "alt"

HORIZONTAL_TAG = "x0"
VERTICAL_TAG = "y0"
HIGH_TAG = "high"
LOW_TAG = "low"

# the number of STD's to add to moving average
STD_COEFFICIENT = 2
# when hovering with mouse, the algorithm will look at this many frames to find something to snap to (e.g. existing peak)
PEAK_SEARCH_DISTANCE = 50
# the lag of the moving average
MOVING_AVG = 10
# initial view window size in frames
INITIAL_WINDOW = 1000


def _tag(tag, type):
	"""A helper to construct the key from tag and type (e.g. x0_high)"""
	return f"{tag}_{type}"


def parse_cli():
	"""Parse command line arguments and return them as values"""

	# https://stackoverflow.com/a/11541450/1644554
	def is_valid_file(parser, arg):
		if not os.path.exists(arg):
			parser.error("The file %s does not exist!" % arg)
		else:
			return arg

	parser = argparse.ArgumentParser(
		description="Interactive plots that let user semi-manually select peaks",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=textwrap.dedent(f"""\
			Example:
				./interactive.py --data-file ./clean.csv --peaks-file ./peaks.yaml -v

			Keys:
				"{KEY_CLOSE}" : close the window, save all peaks
				"{KEY_LEFT}"/"{KEY_RIGHT}" : move zoom window left and right
				"{KEY_ZOOM_IN}"/"{KEY_ZOOM_OUT}" : zoom in and out (2x)
				Hold "{KEY_HOLD_NOT_SNAP}" : while holding, current peak selection (red dot) will NOT snap to suggested peaks
				LEFT click to add/remove HIGH peak on the currently selected frame (red dot)
				RIGHT click to add/remove LOW peak on the currently selected frame (red dot)
		"""),
	)
	parser.add_argument("--data-file", dest="data_file", type=lambda x: is_valid_file(parser, x), required=True, help="path to CSV data file to read.")
	parser.add_argument("--peaks-file", dest="peaks_file", type=str, required=True, help="path to YAML peaks file; if exists, will read, else will create.")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	args = parser.parse_args()

	# enable colored logs
	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return args.data_file, args.peaks_file


def update_peaks_file(peaks, peaks_file_path):
	"""
	Write current peaks to the file given by the path.
	Will overwrite the file if exists.
	"""

	peaks_path = Path(peaks_file_path)

	peaks_as_lists = {}
	for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
		for type in [HIGH_TAG, LOW_TAG]:
			# need to convert numpy array to list, or it will put internal structure in the file
			peaks_as_lists[_tag(tag, type)] = peaks[_tag(tag, type)].tolist()

	with open(peaks_path, "w", encoding="utf8") as peaks_file:
		yaml.dump(peaks_as_lists, peaks_file, default_flow_style=False, allow_unicode=True)


def read_or_compute_peaks(frame, peaks_file_path):
	"""
	Try to read peaks from file, and if file does not exist, compute them from the data.

	The file is expected to be a YAML created by this script.
	The algorithm to find the peaks from data is in a separate file.
	Once peaks are computed, they are written in the newly created file.
	"""

	peaks = {}

	peaks_path = Path(peaks_file_path)
	if peaks_path.exists():
		with open(peaks_path, "r") as peaks_file:
			try:
				content = yaml.safe_load(peaks_file)
				for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
					for type in [HIGH_TAG, LOW_TAG]:
						# what we read is list, but we expect numpy array in the rest of the script
						peaks[_tag(tag, type)] = np.array(content[_tag(tag, type)])
			except yaml.YAMLError as exception:
				logger.critical(exception)
	else:
		for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
			for type in [HIGH_TAG, LOW_TAG]:
				peaks[_tag(tag, type)] = find_peaks(frame[f"std_plus_{tag}"], type == HIGH_TAG)
		update_peaks_file(peaks, peaks_file_path)

	for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
		for type in [HIGH_TAG, LOW_TAG]:
			logger.info(f"Found {len(peaks[f'{tag}_{type}'])} peaks for {f'{tag}_{type}'}")

	return peaks


def compute_segments(highs, lows):
	"""
	Derive full segments from the lists of high and low peaks.

	A segment is a pair of peaks such that the first one is high, the second is low, and there are no other peaks in between.
	"""

	# short circuit if one of the lists is empty (no segments can exist)
	if len(highs) == 0 or len(lows) == 0:
		return []

	# attach the origin to a peak value
	highs = list(map(lambda x: {"value": x, "tag": HIGH_TAG}, highs))
	lows = list(map(lambda x: {"value": x, "tag": LOW_TAG}, lows))

	# merge peaks
	both = highs + lows

	# sort by value (but keep origin)
	both.sort(key=lambda x: x["value"])

	segments = []

	# for every two consecutive peaks, if they form a segment, save it
	for i in range(len(both)):
		if i != 0:
			if both[i - 1]["tag"] == HIGH_TAG and both[i]["tag"] == LOW_TAG:
				segments += [[both[i - 1]["value"], both[i]["value"]]]

	return segments


def main():
	"""
	Main event loop.

	The structure is roughly as follows.
	First, the data is read from CSV file, and the peaks are read or computed.
	Second, we define a redraw function that plots current viewpoint given selected peaks.
	Third, we define event handlers that are called on keys presses, mouse clicks and mouse hover.
	Finally, we run the plot until user exits the program.
	"""

	# current viewpoint window size in frames
	window = INITIAL_WINDOW
	# current leftmost visible point
	current_left_window_endpoint = 0
	# current selected frame (to add/remove a peak)
	peak_selection = 0

	# a variable to store a snapshot of rendered UI to be able to restore without redrawing
	background = None
	# a plot per tag, holds plots of actively selected frame (red dot)
	active_peak_plots = {}
	# a list of currently pressed keys (to track KEY_HOLD_NOT_SNAP)
	current_pressed_keys = []
	# current mouse x-position (need to trigger new red dot only when actual frame changes)
	current_mouse_x = 0

	data_file, peaks_file = parse_cli()

	frame = pd.read_csv(data_file)

	# this is important, we need a capable backend that can redraw and do bliting
	matplotlib.use("Qt5Agg")

	figure, (subplot_horizontal, subplot_vertical) = plt.subplots(2)

	# compute moving average, rolling STD and average + coefficient STD series
	for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
		frame[f"mavg_{MOVING_AVG}_{tag}"] = frame[tag].rolling(MOVING_AVG).mean()

		frame[f"std_{tag}"] = frame[f"mavg_{MOVING_AVG}_{tag}"].rolling(MOVING_AVG).std()
		frame[f"std_plus_{tag}"] = frame[f"std_{tag}"] * STD_COEFFICIENT + frame[f"mavg_{MOVING_AVG}_{tag}"]

	# get all peaks
	peaks = read_or_compute_peaks(frame, peaks_file)

	subplot_vertical.set_xlabel("Frames")
	figure.text(0.06, 0.5, "Pixels", ha="center", va="center", rotation="vertical")

	def redraw():
		"""
		Recreate a plot in the viewframe.

		For both directions (horizontal and vertical), do this.
		Extract data for the viewable window plus wide margins.
		Plot original data and STD series, high/low peaks, segments and currently selected frame marker (red dot).
		"""

		nonlocal background
		nonlocal active_peak_plots

		for tag, subplot, title in [[HORIZONTAL_TAG, subplot_horizontal, "Horizontal"], [VERTICAL_TAG, subplot_vertical, "Vertical"]]:
			subplot.cla()

			# compute margins for frames to plot
			left_endpoint = max(0, current_left_window_endpoint - int(1.5 * window))
			right_endpoint = min(len(frame.index), current_left_window_endpoint + window + int(1.5 * window))

			# plot original data and STD series
			subplot.plot(frame[tag][left_endpoint:right_endpoint], linewidth=0.5, label="Original Sanitized Data", color="darkslategray")
			subplot.plot(frame[f"std_plus_{tag}"][left_endpoint:right_endpoint], label=f"{STD_COEFFICIENT} STD from {MOVING_AVG} moving average", color="teal")

			# plot current peaks, high and low
			peaks_in_range = {}
			for type, color in [[HIGH_TAG, "orange"], [LOW_TAG, "blue"]]:
				peaks_in_range[type] = peaks[_tag(tag, type)][(peaks[_tag(tag, type)] >= left_endpoint) & (peaks[_tag(tag, type)] <= right_endpoint)]
				subplot.plot(peaks_in_range[type], frame[f"std_plus_{tag}"][peaks_in_range[type]], "o", color=color, alpha=0.5)

			# compute segments for current window and plot them
			segments = compute_segments(peaks_in_range[HIGH_TAG].tolist(), peaks_in_range[LOW_TAG].tolist())
			for start, end in segments:
				subplot.axvspan(start, end, color='green', alpha=0.3)

			# create empty plot for current frame (to be red dot)
			(active_peak_plots[tag], ) = subplot.plot([], [], marker="o", color="red", alpha=0.75, animated=True)

			# set viewframe
			subplot.set_xlim(current_left_window_endpoint, current_left_window_endpoint + window)
			subplot.set_ylim(frame[f"std_plus_{tag}"][current_left_window_endpoint:current_left_window_endpoint + window].min() * 0.9, frame[f"std_plus_{tag}"][current_left_window_endpoint:current_left_window_endpoint + window].max() * 1.1)

			subplot.set_title(f"{title} Movements")
			subplot.legend()

		# draw and save rendered UI into variable
		figure.canvas.draw()
		background = figure.canvas.copy_from_bbox(figure.bbox)

	# remove key from pressed array on release
	def key_release_handler(event):
		if event.key in current_pressed_keys:
			current_pressed_keys.remove(event.key)

	# invoke on keyboard key press
	def key_press_handler(event):
		nonlocal current_left_window_endpoint
		nonlocal window
		nonlocal current_pressed_keys

		logger.debug(f"key pressed: {event.key}")
		current_pressed_keys += [event.key]

		if event.key == KEY_RIGHT:
			# shift window right
			current_left_window_endpoint += int(window * 0.8)
			current_left_window_endpoint = min(current_left_window_endpoint, len(frame.index) - 1)
		elif event.key == KEY_LEFT:
			# shift window left
			current_left_window_endpoint -= int(window * 0.8)
			current_left_window_endpoint = max(current_left_window_endpoint, 0)
		elif event.key == KEY_ZOOM_IN:
			# shrink window
			window = int(window / 2)
		elif event.key == KEY_ZOOM_OUT:
			# expand window
			window = int(window * 2)
		redraw()

	# invoke on mouse movement
	def motion_notify_handler(event):
		nonlocal current_mouse_x
		nonlocal peak_selection

		def compute_nearest_peak(tag, current):
			"""
			Return the active frame for the location.

			Go right PEAK_SEARCH_DISTANCE until either peak found, or a downturn.
			"""

			peak = current
			# don't snap if KEY_HOLD_NOT_SNAP is pressed
			if KEY_HOLD_NOT_SNAP in current_pressed_keys:
				return peak

			# get next PEAK_SEARCH_DISTANCE points
			points = frame[f"std_plus_{tag}"][current:min(len(frame.index), current + PEAK_SEARCH_DISTANCE)].tolist()

			# if found peak, snap to it
			for x in range(0, len(points) - 2):
				peak = x + current
				if peak in peaks[_tag(tag, HIGH_TAG)] or peak in peaks[_tag(tag, LOW_TAG)]:
					return peak

			# if found downturn, snap to it
			for x in range(0, len(points) - 2):
				peak = x + current
				if points[x] >= points[x + 1]:
					return peak

			return peak

		for tag, subplot in [[HORIZONTAL_TAG, subplot_horizontal], [VERTICAL_TAG, subplot_vertical]]:
			# if mouse is within plot canvas
			if event.inaxes == subplot:
				# don't trigger if frame not changed
				if int(current_mouse_x) != int(event.xdata):

					# set new frame
					current_mouse_x = event.xdata
					# set new selection
					peak_selection = compute_nearest_peak(tag, int(event.xdata))

					# modify existing peak selection plot, set marker
					active_peak_plots[tag].set_data([peak_selection], [frame[f"std_plus_{tag}"][peak_selection]])
					if peak_selection in peaks[_tag(tag, HIGH_TAG)] or peak_selection in peaks[_tag(tag, LOW_TAG)]:
						active_peak_plots[tag].set(marker="x")
					else:
						active_peak_plots[tag].set(marker="o")

					# restore (not re-render) UI, put peak selection manually, do bliting
					figure.canvas.restore_region(background)
					figure.draw_artist(active_peak_plots[tag])
					figure.canvas.blit(figure.bbox)

					figure.canvas.flush_events()

				break

	# invoke on mouse click
	def on_click_handler(event):
		# do nothing for double click
		if not event.dblclick:
			for type, button in [[HIGH_TAG, 1], [LOW_TAG, 3]]:
				# only trigger for left and right buttons
				if event.button == button:
					for tag, subplot in [[HORIZONTAL_TAG, subplot_horizontal], [VERTICAL_TAG, subplot_vertical]]:
						# if mouse is within the plot canvas
						if event.inaxes == subplot:
							# if existing peak selected, remove it, otherwise, add
							if peak_selection in peaks[_tag(tag, type)]:
								peaks[_tag(tag, type)] = np.delete(peaks[_tag(tag, type)], peaks[_tag(tag, type)] == peak_selection)
								logger.debug(f"Removed {type} peak: {peak_selection}")
							else:
								peaks[_tag(tag, type)] = np.append(peaks[_tag(tag, type)], peak_selection)
								logger.debug(f"Added {type} peak: {peak_selection}")
							# modify peaks file immediately
							update_peaks_file(peaks, peaks_file)
							redraw()
							break

	# register event listeners
	figure.canvas.mpl_connect("motion_notify_event", motion_notify_handler)
	figure.canvas.mpl_connect("key_press_event", key_press_handler)
	figure.canvas.mpl_connect("key_release_event", key_release_handler)
	figure.canvas.mpl_connect("button_press_event", on_click_handler)
	figure.canvas.mpl_connect("resize_event", lambda event: redraw())

	redraw()

	plt.show()


if __name__ == "__main__":
	main()
