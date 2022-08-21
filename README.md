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

### Sanitize raw inputs

We expect raw inputs from DeepLabCut in CSV format.
The script below parses these raw data and does the following:
- Trims data
    - trims low likellihood
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
❯ ./scripts/sanitizer.py --file ./sorted-videos/q118-rr/OKN_plaid_eye_0001DLC_resnet50_MassiveEyeOct27shuffle1_1030000.csv
Sun, 21 Aug 2022 18:01:14 INFO     Parsed CSV (n = 542488)
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 542488/542488 [00:38<00:00, 14028.94it/s]
Sun, 21 Aug 2022 18:01:53 INFO     Converted to ellipses
Sun, 21 Aug 2022 18:01:53 INFO     Removed Radius Ratio Outliers
Sun, 21 Aug 2022 18:01:54 INFO     Removed X Y Outliers
Sun, 21 Aug 2022 18:01:54 INFO     Smoothed the plot
Sun, 21 Aug 2022 18:01:54 INFO     Pupil area calculated and smoothed
Sun, 21 Aug 2022 18:01:57 INFO     Written to CSV: /Users/daria/Desktop/auto-2/scripts/../clean/OKN_plaid_eye_0001DLC_resnet50_MassiveEyeOct27shuffle1_1030000_clean.csv
```

### For each script

### For each script
