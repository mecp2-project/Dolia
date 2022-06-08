#!/usr/bin/env python3

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
from utility import HORIZONTAL_TAG, VERTICAL_TAG, AREA_TAG, RATIO_TAG, HIGH_TYPE, LOW_TYPE, logger, _tag, is_valid_file, peaks_to_segments

# Constants
KEY_CLOSE = "q"
KEY_RIGHT = "right"
KEY_LEFT = "left"
KEY_ZOOM_IN = "i"
KEY_ZOOM_OUT = "o"
KEY_UNDO = "z"
KEY_HOLD_NOT_SNAP = "alt"
BUTTON_LEFT = 8
BUTTON_RIGHT = 9

# when hovering with mouse, the algorithm will look at this many frames to find something to snap to (e.g. existing peak)
PEAK_SEARCH_DISTANCE = 50
# the lag of the moving average
MOVING_AVG = 10
# initial view window size in frames
INITIAL_WINDOW = 1000



def parse_cli():
	"""Parse command line arguments and return them as values"""

	parser = argparse.ArgumentParser(
		description="Interactive plots that let user semi-manually select peaks",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=textwrap.dedent(f"""\
			Example:
				./interactive.py --data-file ./clean.csv --peaks-file ./peaks.yaml -v

				./interactive.py --data-file ./clean.csv --peaks-file ./peaks.yaml -v --view-area
				./interactive.py --data-file ./clean.csv --peaks-file ./peaks.yaml -v --view-ratio

			Keys:
				"{KEY_CLOSE}" : close the window, save all peaks
				"{KEY_LEFT}"/"{KEY_RIGHT}" : move zoom window left and right
				"{KEY_ZOOM_IN}"/"{KEY_ZOOM_OUT}" : zoom in and out (2x)
				Hold "{KEY_HOLD_NOT_SNAP}" : while holding, current peak selection (red dot) will NOT snap to suggested peaks
				LEFT click to add/remove HIGH peak on the currently selected frame (red dot)
				RIGHT click to add/remove LOW peak on the currently selected frame (red dot)
				"{KEY_UNDO}" : to add/remove last removed/added peak

			Notes:
				At most one of --view-area and --view-ratio can be set
				If --view-* is set, interactive marking of segments is disabled
		"""),
	)
	parser.add_argument("--data-file", dest="data_file", type=lambda x: is_valid_file(parser, x), required=True, help="path to CSV data file to read")
	parser.add_argument("--peaks-file", dest="peaks_file", type=str, required=True, help="path to YAML peaks file; if exists, will read, else will create")
	parser.add_argument("--plus-std", dest="plus_std", type=float, default=None, help="Highest peak plus 2 standard deviations")
	parser.add_argument("--minus-std", dest="minus_std", type=float, default=None, help="Highest peak minus 2 standard deviations")
	parser.add_argument("--view-area", dest="view_area", default=False, help="show pupil radius as a third plot; will disable marking functionality, but not zooming and walking;", action="store_true")
	parser.add_argument("--view-ratio", dest="view_ratio", default=False, help="show pupil radii ratio as a third plot; will disable marking functionality, but not zooming and walking;", action="store_true")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	args = parser.parse_args()

	# enable colored logs
	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return args.data_file, args.peaks_file, args.view_area, args.view_ratio, args.plus_std, args.minus_std


def update_peaks_file(peaks, peaks_file_path):
	"""
	Write current peaks to the file given by the path.
	Will overwrite the file if exists.
	"""

	peaks_path = Path(peaks_file_path)

	peaks_as_lists = {}
	for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
		for type in [HIGH_TYPE, LOW_TYPE]:
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
					for type in [HIGH_TYPE, LOW_TYPE]:
						# what we read is list, but we expect numpy array in the rest of the script
						peaks[_tag(tag, type)] = np.array(content[_tag(tag, type)])
			except yaml.YAMLError as exception:
				logger.critical(exception)
	else:
		for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
			for type in [HIGH_TYPE, LOW_TYPE]:
				peaks[_tag(tag, type)] = find_peaks(frame[f"mavg_{MOVING_AVG}_{tag}"], type == HIGH_TYPE)
		update_peaks_file(peaks, peaks_file_path)

	for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
		for type in [HIGH_TYPE, LOW_TYPE]:
			logger.info(f"Found {len(peaks[f'{tag}_{type}'])} peaks for {f'{tag}_{type}'}")

	return peaks

def compute_angle_from_segment(start, end, frame):
	x0 = frame["x0"][start]
	y0 = frame["y0"][start]
	x1 = frame["x0"][end]
	y1 = frame["y0"][end]

	angle = np.degrees(np.arctan((y1 - y0) / (x1 - x0)))

	logger.info(f"Segment [{start}, {end}]: angle = {angle}, {x0}, {x1}, {y0}, {y1}")

	return angle

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
	# last added or removed peak (peak frame, tag, type)
	last_peak = None

	# a variable to store a snapshot of rendered UI to be able to restore without redrawing
	background = None
	# a plot per tag, holds plots of actively selected frame (red dot)
	active_peak_plots = {}
	# a list of currently pressed keys (to track KEY_HOLD_NOT_SNAP)
	current_pressed_keys = []
	# current mouse x-position (need to trigger new red dot only when actual frame changes)
	current_mouse_x = 0

	data_file, peaks_file, view_area, view_ratio, plus_std, minus_std = parse_cli()

	if (plus_std is None and minus_std is not None) or (plus_std is not None and minus_std is None):
		logger.critical("Error. Check if Plus STD and Minus STD are given.")
		exit(1)

	if view_area and view_ratio:
		logger.critical("Only one of --view-area and --view-ration can be set")
		exit(1)

	view_extra = view_area or view_ratio
	if view_area:
		EXTRA_TAG = AREA_TAG
		extra_title = "Pupil Area"
		extra_y_label = "Square Pixels"
	if view_ratio:
		EXTRA_TAG = RATIO_TAG
		extra_title = "Pupil Radii Ratio"
		extra_y_label = "Ratio"

	frame = pd.read_csv(data_file)

	# this is important, we need a capable backend that can redraw and do bliting
	matplotlib.use("Qt5Agg")

	if view_extra:
		figure, (subplot_horizontal, subplot_vertical, subplot_extra) = plt.subplots(3)
	else:
		figure, (subplot_horizontal, subplot_vertical) = plt.subplots(2)

	# compute moving averages
	for tag in [HORIZONTAL_TAG, VERTICAL_TAG, AREA_TAG, RATIO_TAG]:
		frame[f"mavg_{MOVING_AVG}_{tag}"] = frame[tag].rolling(MOVING_AVG).mean()
		frame[f"mavg_{MOVING_AVG}_{tag}_shifted"] = frame[f"mavg_{MOVING_AVG}_{tag}"].shift(-int(MOVING_AVG / 2))

	# get all peaks
	peaks = read_or_compute_peaks(frame, peaks_file)

	def redraw():
		"""
		Recreate a plot in the viewframe.

		For both directions (horizontal and vertical), do this.
		Extract data for the viewable window plus wide margins.
		Plot original data and moving average series, high/low peaks, segments and currently selected frame marker (red dot).
		"""

		nonlocal background
		nonlocal active_peak_plots

		subplots = [(HORIZONTAL_TAG, subplot_horizontal, "Horizontal", "Pixels"), (VERTICAL_TAG, subplot_vertical, "Vertical", "Pixels")]
		if view_extra:
			subplots += [(EXTRA_TAG, subplot_extra, extra_title, extra_y_label)]

		for tag, subplot, title, y_label in subplots:
			subplot.cla()

			# compute margins for frames to plot
			left_endpoint = max(0, current_left_window_endpoint - int(1.5 * window))
			right_endpoint = min(len(frame.index), current_left_window_endpoint + window + int(1.5 * window))

			# plot original data and moving average series
			subplot.plot(frame[tag][left_endpoint:right_endpoint], linewidth=0.5, label="Original Sanitized Data", color="darkslategray")
			subplot.plot(frame[f"mavg_{MOVING_AVG}_{tag}_shifted"][left_endpoint:right_endpoint], label=f"{MOVING_AVG} moving average half-shifted", color="teal")

			# set viewframe
			subplot.set_xlim(current_left_window_endpoint, current_left_window_endpoint + window)
			subplot.set_ylim(
				frame[f"mavg_{MOVING_AVG}_{tag}_shifted"][current_left_window_endpoint:current_left_window_endpoint + window].min() * 0.9,
				frame[f"mavg_{MOVING_AVG}_{tag}_shifted"][current_left_window_endpoint:current_left_window_endpoint + window].max() * 1.1,
			)


			subplot.set_title(title)
			subplot.set_ylabel(y_label)
			subplot.legend()

			# shortcut for non vertical and horizontal tags; no need segments for this type;
			if tag not in [HORIZONTAL_TAG, VERTICAL_TAG]:
				continue

			# filter only the peak in the current range
			peaks_in_range = {}
			for type in [HIGH_TYPE, LOW_TYPE]:
				peaks_in_range[type] = peaks[_tag(tag, type)][(peaks[_tag(tag, type)] >= left_endpoint) & (peaks[_tag(tag, type)] <= right_endpoint)]

			# compute segments for current window and plot them
			segments = peaks_to_segments(peaks_in_range[HIGH_TYPE].tolist(), peaks_in_range[LOW_TYPE].tolist())
			for start, end in segments:
				segment_color = "green"
				if plus_std is not None:
					angle = compute_angle_from_segment(start, end, frame)
					if angle < minus_std:
						segment_color = "blue"
					elif angle > plus_std:
						segment_color = "red"
				subplot.axvspan(start, end, color=segment_color, alpha=0.3)

			# plot current peaks, high and low; plot peaks that are a part of a segment differently
			for type, color in [[HIGH_TYPE, "orange"], [LOW_TYPE, "blue"]]:
				# extract only "tag" peaks into segment_peaks
				segment_peaks = list(map(lambda x: x[0 if type == HIGH_TYPE else 1], segments))
				# non_segment_peaks is set difference of all peaks minus segment_peaks
				non_segment_peaks = np.setdiff1d(peaks_in_range[type], segment_peaks, assume_unique=True)
				# plot these two peak types differently
				subplot.plot(segment_peaks, frame[f"mavg_{MOVING_AVG}_{tag}_shifted"][segment_peaks], "o", color=color, alpha=0.5, markersize=10)
				subplot.plot(non_segment_peaks, frame[f"mavg_{MOVING_AVG}_{tag}_shifted"][non_segment_peaks], "X", color=color, alpha=0.8, markersize=10)

			# create empty plot for current frame (to be red dot)
			(active_peak_plots[tag], ) = subplot.plot([], [], marker="o", color="red", alpha=0.75, animated=True, markersize=10)

		# draw and save rendered UI into variable
		figure.canvas.draw()
		background = figure.canvas.copy_from_bbox(figure.bbox)

	def add_or_remove_peak(peak, tag, type):
		"""
		A helper to update the current peaks and update the file.

		Will also remember the last added or removed peak.
		"""
		nonlocal last_peak

		if peak in peaks[_tag(tag, type)]:
			peak_index = np.argwhere(peaks[_tag(tag, type)] == peak)
			peaks[_tag(tag, type)] = np.delete(peaks[_tag(tag, type)], peak_index)
			logger.debug(f"Removed {type} peak: {peak}")
		else:
			peaks[_tag(tag, type)] = np.append(peaks[_tag(tag, type)], peak)
			logger.debug(f"Added {type} peak: {peak}")
		# modify peaks file immediately
		update_peaks_file(peaks, peaks_file)
		last_peak = (peak, tag, type)

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
			window = max(20, window)
		elif event.key == KEY_ZOOM_OUT:
			# expand window
			window = int(window * 2)
			window = min(len(frame.index), window)
		elif event.key == KEY_UNDO:
			add_or_remove_peak(*last_peak)
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
			points = frame[f"mavg_{MOVING_AVG}_{tag}_shifted"][current:min(len(frame.index), current + PEAK_SEARCH_DISTANCE)].tolist()

			# if found peak, snap to it
			for x in range(0, len(points) - 2):
				peak = x + current
				if peak in peaks[_tag(tag, HIGH_TYPE)] or peak in peaks[_tag(tag, LOW_TYPE)]:
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
					active_peak_plots[tag].set_data([peak_selection], [frame[f"mavg_{MOVING_AVG}_{tag}_shifted"][peak_selection]])
					if peak_selection in peaks[_tag(tag, HIGH_TYPE)] or peak_selection in peaks[_tag(tag, LOW_TYPE)]:
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
		nonlocal window
		nonlocal current_left_window_endpoint

		# do nothing for double click
		if not event.dblclick:
			if event.button == 2:
				if KEY_HOLD_NOT_SNAP in current_pressed_keys:
					# expand window
					window = int(window * 2)
					window = min(len(frame.index), window)
				else:
					# shrink window
					window = int(window / 2)
					window = max(20, window)
			if event.button == BUTTON_RIGHT:
				# shift window right
				current_left_window_endpoint += int(window * 0.8)
				current_left_window_endpoint = min(current_left_window_endpoint, len(frame.index) - 1)
			elif event.button == BUTTON_LEFT:
				# shift window left
				current_left_window_endpoint -= int(window * 0.8)
				current_left_window_endpoint = max(current_left_window_endpoint, 0)
			elif event.button == 1 or event.button == 3:
				for type, button in [[HIGH_TYPE, 1], [LOW_TYPE, 3]]:
					# only trigger for left and right buttons
					if event.button == button:
						for tag, subplot in [[HORIZONTAL_TAG, subplot_horizontal], [VERTICAL_TAG, subplot_vertical]]:
							# if mouse is within the plot canvas
							if event.inaxes == subplot:
								# if existing peak selected, remove it, otherwise, add
								add_or_remove_peak(peak_selection, tag, type)
								break
			redraw()

	# register event listeners
	figure.canvas.mpl_connect("key_press_event", key_press_handler)
	figure.canvas.mpl_connect("resize_event", lambda event: redraw())
	if not view_extra:
		figure.canvas.mpl_connect("motion_notify_event", motion_notify_handler)
		figure.canvas.mpl_connect("key_release_event", key_release_handler)
		figure.canvas.mpl_connect("button_press_event", on_click_handler)

	redraw()

	plt.show()


if __name__ == "__main__":
	main()
