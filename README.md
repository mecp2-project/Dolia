# Automation

1. Use `sanitizer.py` to convert raw CSV to x/y coordinates of eye for all frames
Example: `./sanitizer.py --file ~/Desktop/Code_daria/E1_plaid.csv -n 5000`

2. Use `plots.py` to plot the horizontal and vertical movements of the eye center.
Example: `./plots.py`

## Dependencies

To install Python packages, use `requirements.txt`

```bash
/usr/bin/env python3 -m pip install -r requirements.txt
```

To install Qt Python driver on Mac

```bash
brew install pyqt
```
