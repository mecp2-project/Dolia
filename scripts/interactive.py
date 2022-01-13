#!/usr/bin/env python3

import os
import logging
import argparse
import coloredlogs, logging
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import textwrap
import numpy as np
from pathlib import Path
import yaml
from scipy.signal import find_peaks

# change directory to that of the script file
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

logger = logging.getLogger(__name__)

KEY_CLOSE = "q"
KEY_START = "a"
KEY_RIGHT = "right"
KEY_LEFT = "left"
KEY_ZOOM_IN = "+"
KEY_ZOOM_OUT = "-"
KEY_HOLD_NOT_SNAP = "alt"

HORIZONTAL_TAG = "x0"
VERTICAL_TAG = "y0"

STD_COEFFICIENT = 2
PEAK_SEARCH_DISTANCE = 50


def parse_cli():

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
			Keys:
				{KEY_CLOSE} : close the window, save all peaks
				{KEY_START} : start the selection, zoom to the first window, redraw
				{KEY_LEFT}/{KEY_RIGHT} : move zoom window left and right
				{KEY_ZOOM_IN}/{KEY_ZOOM_OUT} : zoom in and out (2x)
				Hold {KEY_HOLD_NOT_SNAP} : while holding, current peak selection (red dot) will NOT snap to suggested peaks
		"""),
	)
	parser.add_argument("--data-file", dest="data_file", type=lambda x: is_valid_file(parser, x), required=True, help="CSV data file to read.")
	parser.add_argument("--peaks-file", dest="peaks_file", type=str, required=True, help="YAML peaks file. If exists, will read, else will create.")
	parser.add_argument("--window", dest="window", type=int, default=1000, help="Length of zoom window in frames.")
	parser.add_argument("--moving-avg", dest="moving_avg", type=int, default=10, help="Moving average lag")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	args = parser.parse_args()

	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return args.data_file, args.peaks_file, args.moving_avg, args.window


def update_peaks_file(peaks, peaks_file_path):
	peaks_path = Path(peaks_file_path)

	peaks_as_lists = {}
	for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
		peaks_as_lists[tag] = peaks[tag].tolist()

	with open(peaks_path, "w", encoding="utf8") as peaks_file:
		yaml.dump(peaks_as_lists, peaks_file, default_flow_style=False, allow_unicode=True)


def read_or_compute_peaks(frame, peaks_file_path):
	peaks = {}

	peaks_path = Path(peaks_file_path)
	if peaks_path.exists():
		with open(peaks_path, "r") as peaks_file:
			try:
				content = yaml.safe_load(peaks_file)
				for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
					peaks[tag] = np.array(content[tag])
			except yaml.YAMLError as exception:
				logger.critical(exception)
	else:
		for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
			peaks[tag] = find_peaks(frame[f"std_plus_{tag}"], height=2, distance=200)[0]
		update_peaks_file(peaks, peaks_file_path)

	for tag in [HORIZONTAL_TAG, VERTICAL_TAG]:
		logger.info(f"Found {len(peaks[tag])} peaks for {tag}")

	return peaks


def main():

	current_left_window_endpoint = 0
	peak_selection = 0

	background = None
	active_peak_plots = {}
	current_pressed_keys = []
	current_mouse_x = 0

	data_file, peaks_file, moving_avg, window = parse_cli()

	frame = pd.read_csv(data_file)

	matplotlib.use("Qt5Agg")

	figure, (subplot_horizontal, subplot_vertical) = plt.subplots(2)

	for tag, title in [[HORIZONTAL_TAG, "Horizontal"], [VERTICAL_TAG, "Vertical"]]:
		frame[f"mavg_{moving_avg}_{tag}"] = frame[tag].rolling(moving_avg).mean()

		frame[f"std_{tag}"] = frame[f"mavg_{moving_avg}_{tag}"].rolling(moving_avg).std()
		frame[f"std_plus_{tag}"] = frame[f"std_{tag}"] * STD_COEFFICIENT + frame[f"mavg_{moving_avg}_{tag}"]

	peaks = read_or_compute_peaks(frame, peaks_file)

	subplot_vertical.set_xlabel("Frames")
	figure.text(0.06, 0.5, "Pixels", ha="center", va="center", rotation="vertical")

	def redraw():
		nonlocal background
		nonlocal active_peak_plots

		for tag, subplot in [[HORIZONTAL_TAG, subplot_horizontal], [VERTICAL_TAG, subplot_vertical]]:
			subplot.cla()

			left_endpoint = max(0, current_left_window_endpoint - int(0.5 * window))
			right_endpoint = min(len(frame.index), current_left_window_endpoint + window + int(0.5 * window))
			peaks_in_range = peaks[tag][(peaks[tag] >= left_endpoint) & (peaks[tag] <= right_endpoint)]

			subplot.plot(frame[tag][left_endpoint:right_endpoint], linewidth=0.5, label="Original Sanitized Series", color="darkslategray")
			subplot.plot(frame[f"std_plus_{tag}"][left_endpoint:right_endpoint], label=f"{STD_COEFFICIENT} STD from {moving_avg} moving average", color="teal")
			subplot.plot(peaks_in_range, frame[f"std_plus_{tag}"][peaks_in_range], "o", color="orange", alpha=0.5)

			(active_peak_plots[tag], ) = subplot.plot([], [], marker="o", color="red", alpha=0.75, animated=True)

			subplot.set_xlim(current_left_window_endpoint, current_left_window_endpoint + window)
			subplot.set_ylim(frame[tag][current_left_window_endpoint:current_left_window_endpoint + window].min() * 0.9, frame[tag][current_left_window_endpoint:current_left_window_endpoint + window].max() * 1.1)

			subplot.set_title(f"{title} Movements")
			subplot.legend()

		figure.canvas.draw()
		background = figure.canvas.copy_from_bbox(figure.bbox)

	def key_release_handler(event):
		if event.key in current_pressed_keys:
			current_pressed_keys.remove(event.key)

	def key_press_handler(event):
		nonlocal current_left_window_endpoint
		nonlocal window
		nonlocal current_pressed_keys

		logger.debug(f"key pressed: {event.key}")
		current_pressed_keys += [event.key]

		if event.key == KEY_START:
			current_left_window_endpoint = 0
		elif event.key == KEY_RIGHT:
			current_left_window_endpoint += int(window * 0.8)
			current_left_window_endpoint = min(current_left_window_endpoint, len(frame.index) - 1)
		elif event.key == KEY_LEFT:
			current_left_window_endpoint -= int(window * 0.8)
			current_left_window_endpoint = max(current_left_window_endpoint, 0)
		elif event.key == KEY_ZOOM_IN:
			window = int(window / 2)
		elif event.key == KEY_ZOOM_OUT:
			window = int(window * 2)
		redraw()

	def motion_notify_handler(event):
		nonlocal current_mouse_x
		nonlocal peak_selection

		def compute_nearest_peak(tag, current):
			peak = current
			if KEY_HOLD_NOT_SNAP in current_pressed_keys:
				return peak

			points = frame[f"std_plus_{tag}"][current:min(len(frame.index), current + PEAK_SEARCH_DISTANCE)].tolist()
			for x in range(0, len(points) - 2):
				peak = x + current
				if peak in peaks[tag]:
					return peak

			for x in range(0, len(points) - 2):
				peak = x + current
				if points[x] >= points[x + 1] or peak in peaks[tag]:
					return peak

			return peak

		for tag, subplot in [[HORIZONTAL_TAG, subplot_horizontal], [VERTICAL_TAG, subplot_vertical]]:
			if event.inaxes == subplot:
				if current_mouse_x != event.xdata:
					current_mouse_x = event.xdata
					peak_selection = compute_nearest_peak(tag, int(event.xdata))

					active_peak_plots[tag].set_data([peak_selection], [frame[f"std_plus_{tag}"][peak_selection]])
					if peak_selection in peaks[tag]:
						active_peak_plots[tag].set(marker="x")
					else:
						active_peak_plots[tag].set(marker="o")

					figure.canvas.restore_region(background)
					figure.draw_artist(active_peak_plots[tag])
					figure.canvas.blit(figure.bbox)

					figure.canvas.flush_events()

				break

	def on_click_handler(event):
		if not event.dblclick and event.button == 1:
			for tag, subplot in [[HORIZONTAL_TAG, subplot_horizontal], [VERTICAL_TAG, subplot_vertical]]:
				if event.inaxes == subplot:
					if peak_selection in peaks[tag]:
						peaks[tag] = np.delete(peaks[tag], peaks[tag] == peak_selection)
						logger.debug(f"Removed peak: {peak_selection}")
					else:
						peaks[tag] = np.append(peaks[tag], peak_selection)
						logger.debug(f"Added peak: {peak_selection}")
					update_peaks_file(peaks, peaks_file)
					redraw()
					break

	figure.canvas.mpl_connect("motion_notify_event", motion_notify_handler)
	figure.canvas.mpl_connect("key_press_event", key_press_handler)
	figure.canvas.mpl_connect("key_release_event", key_release_handler)
	figure.canvas.mpl_connect("button_press_event", on_click_handler)
	figure.canvas.mpl_connect("resize_event", lambda event: redraw())

	redraw()

	plt.show()


if __name__ == "__main__":
	main()
