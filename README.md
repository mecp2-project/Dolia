# Automation

Here what the project is.

Put here a nice screenshot from interactive.

Later put a link to bioarxiv.

## Dependencies

- python3
- packages from requirement.txt (`/usr/bin/env python3 -m pip install -r requirements.txt`)
- Qt plugin (`brew install pyqt@5`)
- etc

## How to run

### Sanitize raw inputs (Sanitizer.py)

We expect raw inputs from DeepLabCut in CSV format.
The script below parses these raw data and does the following:
- Trims data
    - trims low likelihood
    - trims data outside of percentiles
    - computes radii and areas of pupils and trims the outliers
- Computes and outputs for each frame
    - x and y coordinates of center
    - radii of pupil ellipse
    - TODO

```
❯ ./scripts/sanitizer.py -h
usage: sanitizer.py [-h] --file FILE [--likelihood LIKELIHOOD] [--min-percentile MIN_PERCENTILE] [--max-percentile MAX_PERCENTILE]
                    [--radius-max-percentile RADIUS_MAX_PERCENTILE] [--radius-min-percentile RADIUS_MIN_PERCENTILE] [--eyeblink EYEBLINK] [-n N]
                    [--window WINDOW] [--rolling ROLLING] [-v]

Sanitizer (drop low likelihood, compute ellipses, interpolate radius ratio outliers and center coordinates)

optional arguments:
  -h, --help            show this help message and exit
  --file FILE           CSV file to read.
  --likelihood LIKELIHOOD
                        Likelihood threshold. Datapoints below this will be dropped.
  --min-percentile MIN_PERCENTILE
                        Min. percentile. Datapoints below this percentile will be dropped.
  --max-percentile MAX_PERCENTILE
                        Max. percentile. Datapoints above this percentile will be dropped.
  --radius-max-percentile RADIUS_MAX_PERCENTILE
                        Max. percentile of a RADIUS. Datapoints above this percentile will be dropped.
  --radius-min-percentile RADIUS_MIN_PERCENTILE
                        Min. percentile of a RADIUS. Datapoints below this percentile will be dropped.
  --eyeblink EYEBLINK   Number of pixels between top and bottom lid. Datapoints below this value will be dropped.
  -n N                  Number of points to plot. Not plotting in default
  --window WINDOW       Window size in frames
  --rolling ROLLING     Rolling mead value
  -v                    increase output verbosity
```

Here is an example of running the script:

```
❯ ./scripts/sanitizer.py --file ./raw-videos/folder/raw-file-name.csv
Sun, 21 Aug 2022 18:01:14 INFO     Parsed CSV (n = 542488)
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 542488/542488 [00:38<00:00, 14028.94it/s]
Sun, 21 Aug 2022 18:01:53 INFO     Converted to ellipses
Sun, 21 Aug 2022 18:01:53 INFO     Removed Radius Ratio Outliers
Sun, 21 Aug 2022 18:01:54 INFO     Removed X Y Outliers
Sun, 21 Aug 2022 18:01:54 INFO     Smoothed the plot
Sun, 21 Aug 2022 18:01:54 INFO     Pupil area calculated and smoothed
Sun, 21 Aug 2022 18:01:57 INFO     Written to CSV: /Users/Desktop/scripts/../clean/file-name_clean.csv 
```

### Interactive

```
Interactive plots that let user semi-manually select peaks

optional arguments:
  -h, --help            show this help message and exit
  --data-file DATA_FILE
                        path to CSV data file to read
  --peaks-file PEAKS_FILE
                        path to YAML peaks file; if exists, will read, else will create
  --plus-std PLUS_STD   Highest peak plus 2 standard deviations
  --minus-std MINUS_STD
                        Highest peak minus 2 standard deviations
  --view-area           show pupil radius as a third plot; will disable marking functionality, but not zooming and walking;
  --view-ratio          show pupil radii ratio as a third plot; will disable marking functionality, but not zooming and walking;
  -v                    increase output verbosity

Example:
        ./interactive.py --data-file ./clean.csv --peaks-file ./peaks.yaml -v

        ./interactive.py --data-file ./clean.csv --peaks-file ./peaks.yaml -v --view-area
        ./interactive.py --data-file ./clean.csv --peaks-file ./peaks.yaml -v --view-ratio

Keys:
        "q" : close the window, save all peaks
        "left"/"right" : move zoom window left and right
        "i"/"o" : zoom in and out (2x)
        Hold "alt" : while holding, current peak selection (red dot) will NOT snap to suggested peaks
        LEFT click to add/remove HIGH peak on the currently selected frame (red dot)
        RIGHT click to add/remove LOW peak on the currently selected frame (red dot)
        "z" : to add/remove last removed/added peak

Notes:
        At most one of --view-area and --view-ratio can be set
        If --view-* is set, interactive marking of segments is disabled
```
Here is an example of running the script:
    ![plot](./auto-2/scripts/interactive-example.png)


### For each script
