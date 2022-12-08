# Automation

Here what the project is.

Put here a nice screenshot from interactive.

BioRXiv Link: https://www.biorxiv.org/content/10.1101/2022.09.23.509144v1

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

❯ ./scripts/interactive.py -h 
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
   <img
  src="/images/interactive-example.png"
  alt="Interactive"
  title="Semi-Automated peaks selection"
  style="display: inline-block; margin: 0 auto; max-width: 300px">

### Angles

The script will calculate the angles of mice's eye movements.

We expect input from `Sanitizer.py`. Clean data in a .CSV format
And Peaks data in .YAML format from `interactive.py`

The Output will be Angles file in .CSV format

```
❯ ./scripts/angles.py -h  
usage: angles.py [-h] [-v] --data-file DATA_FILE --peaks-file PEAKS_FILE --angles-file ANGLES_FILE

Angles -- processes data na peak files for one experiment extracting segment info including angles

optional arguments:
  -h, --help            show this help message and exit
  -v                    increase output verbosity
  --data-file DATA_FILE
                        path to a CSV data file to read.
  --peaks-file PEAKS_FILE
                        path to a YAML peaks file to read.
  --angles-file ANGLES_FILE
                        path to a CSV angles file to write.

```
Here is an example of running this script:

```
 ❯ ./scripts/angles.py --data-file ./clean/file-name-clean.csv --peaks-file ./peaks/file-name-peaks.yaml --angles-file ./angles/filename-angles.csv
 		INFO Original horizontal segments: 89
        INFO Original vertical segments: 30
        INFO Resulting segments: 94
        INFO Angles computed and written to angles/file-name-angles.csv
```
### Categories

The script takes Angles file and based on the Angle and the brackets determines which category (Component (C) or Pattern (P)) it belongs to.
If the distance between two eye movements is greater than 300 frames (defined as MAX_INTERVAL, can be changed if needed), this period will be considered a break (B).

There are two possible modes of running the script: 
You can either `Merge Epochs`--- this way Component 1 and Component 2 will be considered the same epoch ===> Component (C).

You can also use `Split Epochs` and consider Component 1 (Value smaller than MEAN - STD) and Component 2 (Value Greater than MEAN + STD) separate epochs.

We expect the following input:

	1. Angles file in .CSV Format
	2. Calculated standard deviation (Plus / Minus Std)
	3. Name of Category file

The output will be File in .CSV Format that contains Categories and Lengths of these categories.

```
❯ ./scripts/categories.py -h                                                                                                                        13:56:19
usage: categories.py [-h] [-v] [--bins BINS] --mode MODE --angles-file ANGLES_FILE --category-file CATEGORY_FILE --plus-std PLUS_STD --minus-std MINUS_STD

Histograms -- plot a single or double histogram

optional arguments:
  -h, --help            show this help message and exit
  -v                    increase output verbosity
  --bins BINS           The number of bins for the histogram.
  --mode MODE           The mode: 'merge' or 'split'.
  --angles-file ANGLES_FILE
                        path to Angles CSV file to read (if supplied, will plot the distribution of pursuit durations).
  --category-file CATEGORY_FILE
                        path to a CSV categories file to write.
  --plus-std PLUS_STD   Highest peak plus standard deviation
  --minus-std MINUS_STD
                        Highest peak minus standard deviation
```		
Here is an example of running this script:

MERGE OPTION 
```
❯ ./scripts/categories.py --angles-file ./angles/file-name-angles/file-name-angles.csv --plus-std  31.14  --minus-std -10.66 --category-file ./categories/file-name-merge.csv --mode merge

   category   start   length
0         B     420    420.0
1         P     420   2821.0
2         B    4337    821.0
3         P    4337    734.0
4         C    5181     47.0
..      ...     ...      ...
69        P  215072   3873.0
70        B  227875   8930.0
71        P  227875   3153.0
72        B  242648  11620.0
73        P  242648   6333.0

[74 rows x 3 columns]
INFO Categories computed and written to categories/file-name-category/merge/file-name-merge.csv
```
SPLIT OPTION 
```
❯ ./scripts/categories.py --angles-file ./angles/file-name-angles.csv --plus-std  31.14  --minus-std -10.66 --category-file ./categories/file-name-category/split/file-name-split.csv --mode split

   category   start  length
0         B     409   409.0
1        C2     409   137.0
2         P     574  7688.0
3         B    9786   363.0
4        C1    9786    86.0
..      ...     ...     ...
79       C2  260639   341.0
80        P  261056  5486.0
81       C1  267204   337.0
82       C2  267610  1320.0
83        P  269029  1380.0

[84 rows x 3 columns]
INFO Categories computed and written to categories/file-name-category/split/file-name-split.csv
```

### Histograms

A script to plot histograms based on the angles.
Helps visualize your data as well as calculates some basic statistics

The input needed is the Angles file in a .CSV format.
You can also upload second angles file and compare two histograms (WT and MECP2 Duplication mice in our case).

Output is and .SVG file showing histogram and gives statistical values such as mean, median, local maxima/minima and KDE

```
❯ ./scripts/histograms.py -h                                                                                                                     14:07:28
usage: histograms.py [-h] [-v] [--bins BINS] [--highest_peak HIGHEST_PEAK] --angles-file ANGLES_FILE [--secondary-file SECONDARY_FILE] [--svg]

Histograms -- plot a single or double histogram

optional arguments:
  -h, --help            show this help message and exit
  -v                    increase output verbosity
  --bins BINS           The number of bins for the histogram.
  --highest_peak HIGHEST_PEAK
                        Highest peak of the set. If supplied, program will compute switches using standard deviation.
  --angles-file ANGLES_FILE
                        path to a CSV angles file to read.
  --secondary-file SECONDARY_FILE
                        path to a secondary CSV angles file to read (if supplied, will plot double histogram).
  --svg                 save to SVG (double-histogram.svg in your current directory) instead of showing in a window
```
Here is an example of running this script:

```
❯ ./scripts/histograms.py --angles-file ./angles/file-name-angles/file-name-angles.csv          
INFO Read 356 Primary segments
INFO Median is 12.32
INFO Mean is 12.99
```

Slava Ukraini! 