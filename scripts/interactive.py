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
import matplotlib.colors as mcolors

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
	parser.add_argument("--moving-avgs", dest="moving_avgs", nargs="*", type=int, default=[10], help="Moving average lags (may provide multiple, space separated")
	parser.add_argument("-v", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	args = parser.parse_args()

	coloredlogs.install(level=logging.DEBUG if args.verbose else logging.INFO, logger=logger)

	return args.file, args.moving_avgs, args.window


def main():

	file, moving_avgs, window = parse_cli()

	if len(moving_avgs) == 0:
		logger.critical("Need to provide at least one moving average")

	frame = pd.read_csv(file)

	horizontal = "x0"
	vertical = "y0"
	std_coefficient = 2

	figure, (subplot_horizontal, subplot_vertical) = plt.subplots(2)

	for tag, subplot, title in [[horizontal, subplot_horizontal, "Horizontal"], [vertical, subplot_vertical, "Vertical"]]:
		subplot.plot(frame[tag], linewidth=0.5, label="Raw Data", color="darkslategray")

		for moving_avg in moving_avgs:
			frame[f"mavg_{moving_avg}_{tag}"] = frame[tag].rolling(moving_avg).mean()
			subplot.plot(frame[f"mavg_{moving_avg}_{tag}"], label=f"Moving Average {moving_avg}", color="steelblue")

		frame[f"std_{tag}"] = frame[f"mavg_{moving_avgs[0]}_{tag}"].rolling(5).std()
		frame[f"std_plus_{tag}"] = frame[f"std_{tag}"] * std_coefficient + frame[f"mavg_{moving_avgs[0]}_{tag}"]
		subplot.plot(frame[f"std_plus_{tag}"], label=f"{std_coefficient} STD from {moving_avgs[0]} moving average", color="teal")

		subplot.set_title(f"{title} Movements")
		subplot.legend()

	all_peaks = np.array([])
	for tag in [horizontal, vertical]:
		peaks, _ = find_peaks(frame[f"std_plus_{tag}"], height=2, distance=200)
		logger.info(f"Found {len(peaks)} peaks in {tag}")
		all_peaks = np.concatenate((all_peaks, peaks), axis=None)
	all_peaks = np.unique(all_peaks)
	logger.info(f"Found total of {len(all_peaks)}")

	for tag, subplot in [[horizontal, subplot_horizontal], [vertical, subplot_vertical]]:
		subplot.plot(all_peaks, frame[f"std_plus_{tag}"][all_peaks], "o", color="orange", alpha=0.5)

	subplot_vertical.set_xlabel("Frames")
	figure.text(0.06, 0.5, "Pixels", ha="center", va="center", rotation="vertical")

	current = 0
	peak_index = 0
	peak_plots = {}
	confirmed_peaks = []
	confirmed_peaks_plots = {}

	logger.debug(f"First peak: {int(all_peaks[peak_index])}")

	def redraw():
		nonlocal confirmed_peaks_plots

		for tag, subplot in [[horizontal, subplot_horizontal], [vertical, subplot_vertical]]:

			subplot.set_xlim(current, current + window)
			subplot.set_ylim(frame[tag][current:current + window].min() * 0.8, frame[tag][current:current + window].max() * 1.2)

			if tag in confirmed_peaks_plots:
				# confirmed_peaks_plot.pop(0).remove()
				confirmed_plot = confirmed_peaks_plots[tag].pop(0)
				confirmed_plot.remove()
			confirmed_peaks_plots[tag] = subplot.plot(confirmed_peaks, frame[f"std_plus_{tag}"][confirmed_peaks], "o", color="green", alpha=1)

			if tag in peak_plots:
				peak_plot = peak_plots[tag].pop(0)
				peak_plot.remove()
			peak_plots[tag] = subplot.plot([all_peaks[peak_index]], frame[f"std_plus_{tag}"][[all_peaks[peak_index]]], "o", color="red", alpha=1)

		figure.canvas.draw()

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
		elif event.key == KEY_NEXT_PEAK:
			if peak_index != len(all_peaks) - 1:
				peak_index += 1
		elif event.key == KEY_PREV_PEAK:
			if peak_index != 0:
				peak_index -= 1
		elif event.key == KEY_CONF_PEAK:
			peak = all_peaks[peak_index]
			if peak in confirmed_peaks:
				confirmed_peaks.remove(peak)
				logger.debug(f"Unconfirmed peak: {int(all_peaks[peak_index])}")
			else:
				confirmed_peaks += [peak]
				logger.debug(f"Confirmed peak: {int(all_peaks[peak_index])}")
		redraw()

	figure.canvas.mpl_connect("key_press_event", key_press_handler)

	plt.show()


if __name__ == "__main__":
	main()
