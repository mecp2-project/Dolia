#!/usr/bin/env python3

from enum import unique
import os
import logging
import argparse
import coloredlogs, logging
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import textwrap
import numpy as np
from scipy.signal import find_peaks

matplotlib.use('Qt5Agg')

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
KEY_NEXT_PEAK = "up"
KEY_PREV_PEAK = "down"
KEY_CONF_PEAK = "control"


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
				{KEY_START} : start the selection, zoom to the first window
		"""),
	)
	parser.add_argument("--file", dest="file", type=lambda x: is_valid_file(parser, x), required=True, help="CSV file to read.")
	parser.add_argument("--window", dest="window", type=int, default=1000, help="Length of zoom windown in frames.")
	parser.add_argument("--moving-avg", dest="moving_avg", type=int, default=10, help="Moving average lag")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	args = parser.parse_args()

	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return args.file, args.moving_avg, args.window


def main():

	file, moving_avg, window = parse_cli()

	frame = pd.read_csv(file)

	horizontal = "x0"
	vertical = "y0"
	std_coefficient = 2
	peak_search_distance = 100

	figure, (subplot_horizontal, subplot_vertical) = plt.subplots(2)

	for tag, title in [[horizontal, "Horizontal"], [vertical, "Vertical"]]:
		frame[f"mavg_{moving_avg}_{tag}"] = frame[tag].rolling(moving_avg).mean()

		frame[f"std_{tag}"] = frame[f"mavg_{moving_avg}_{tag}"].rolling(moving_avg).std()
		frame[f"std_plus_{tag}"] = frame[f"std_{tag}"] * std_coefficient + frame[f"mavg_{moving_avg}_{tag}"]

	peaks = {}
	for tag in [horizontal, vertical]:
		peaks[tag] = find_peaks(frame[f"std_plus_{tag}"], height=2, distance=200)[0]
		logger.info(f"Found {len(peaks)} peaks for {tag}")

	subplot_vertical.set_xlabel("Frames")
	figure.text(0.06, 0.5, "Pixels", ha="center", va="center", rotation="vertical")

	current = 0
	peak = 0
	peak_index = 0
	peak_plots = {}
	confirmed_peaks = []
	confirmed_peaks_plots = {}

	background = None
	active_peak_plots = {}

	def redraw():
		nonlocal confirmed_peaks_plots
		nonlocal background
		nonlocal active_peak_plots

		for tag, subplot in [[horizontal, subplot_horizontal], [vertical, subplot_vertical]]:
			subplot.cla()

			left_endpoint = max(0, current - int(0.5 * window))
			right_endpoint = min(len(frame.index), current + window + int(0.5 * window))
			peaks_in_range = peaks[tag][(peaks[tag] >= left_endpoint) & (peaks[tag] <= right_endpoint)]

			subplot.plot(frame[tag][left_endpoint:right_endpoint], linewidth=0.5, label="Original Sanitized Series", color="darkslategray")
			subplot.plot(frame[f"std_plus_{tag}"][left_endpoint:right_endpoint], label=f"{std_coefficient} STD from {moving_avg} moving average", color="teal")
			subplot.plot(peaks_in_range, frame[f"std_plus_{tag}"][peaks_in_range], "o", color="orange", alpha=0.5)

			(active_peak_plots[tag], ) = subplot.plot([], [], marker="o", color="red", alpha=1, animated=True)

			subplot.set_xlim(current, current + window)
			subplot.set_ylim(frame[tag][current:current + window].min() * 0.9, frame[tag][current:current + window].max() * 1.1)

			subplot.set_title(f"{title} Movements")
			subplot.legend()

			# if tag in confirmed_peaks_plots:
			# 	confirmed_plot = confirmed_peaks_plots[tag].pop(0)
			# 	confirmed_plot.remove()
			# confirmed_peaks_plots[tag] = subplot.plot(confirmed_peaks, frame[f"std_plus_{tag}"][confirmed_peaks], "o", color="green", alpha=1)

		figure.canvas.draw()
		background = figure.canvas.copy_from_bbox(figure.bbox)

	redraw()

	def key_press_handler(event):
		nonlocal current
		nonlocal window
		nonlocal peak_index
		nonlocal confirmed_peaks

		logger.debug(f"key pressed: {event.key}")

		if event.key == KEY_START:
			current = 0
		elif event.key == KEY_RIGHT:
			current += int(window * 0.8)
			current = min(current, len(frame.index) - 1)
		elif event.key == KEY_LEFT:
			current -= int(window * 0.8)
			current = max(current, 0)
		elif event.key == KEY_ZOOM_IN:
			window = int(window / 2)
		elif event.key == KEY_ZOOM_OUT:
			window = int(window * 2)
		redraw()

	current_mouse_x = 0

	def motion_notify_handler(event):
		nonlocal current_mouse_x
		nonlocal peak

		def compute_nearest_peak(tag, current):
			nonlocal peak

			points = frame[f"std_plus_{tag}"][current:min(len(frame.index), current + peak_search_distance)].tolist()
			peak = current
			for x in range(0, len(points) - 2):
				peak = x + current
				if points[x] >= points[x + 1]:
					break
			return peak

		for tag, subplot in [[horizontal, subplot_horizontal], [vertical, subplot_vertical]]:
			if event.inaxes == subplot:
				if current_mouse_x != event.xdata:
					current_mouse_x = event.xdata
					peak = compute_nearest_peak(tag, int(event.xdata))
					logger.debug(f"Current peak: {peak}")

					active_peak_plots[tag].set_data([peak], [frame[f"std_plus_{tag}"][peak]])

					figure.canvas.restore_region(background)
					figure.draw_artist(active_peak_plots[tag])
					figure.canvas.blit(figure.bbox)

					figure.canvas.flush_events()

				break

	def on_click_handler(event):
		if not event.dblclick and event.button == 1:
			for tag, subplot in [[horizontal, subplot_horizontal], [vertical, subplot_vertical]]:
				if event.inaxes == subplot:
					if peak in peaks[tag]:
						peaks[tag] = np.delete(peaks[tag], peaks[tag] == peak)
						logger.debug(f"Unconfirmed peak: {peak}")
					else:
						peaks[tag] = np.append(peaks[tag], peak)
						logger.debug(f"Confirmed peak: {peak}")
					redraw()
					break

	figure.canvas.mpl_connect("motion_notify_event", motion_notify_handler)
	figure.canvas.mpl_connect("key_press_event", key_press_handler)
	figure.canvas.mpl_connect('button_press_event', on_click_handler)

	plt.show()


if __name__ == "__main__":
	main()
