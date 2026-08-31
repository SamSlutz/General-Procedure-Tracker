# General-Procedure-Tracker
A configurable desktop app for tracking recurring procedures for a list of people or items, built with Python and Tkinter.


> **Disclaimer:** This software is provided for demonstration and general record-tracking purposes. Do not use it to store sensitive personal or regulated information (e.g. real medical, financial, or otherwise legally protected data) without independently evaluating the applicable legal, privacy, and security requirements. Ships with synthetic/demo data only.

## Why this exists

I built this to practice desktop app architecture, data modeling, and turning a narrow, domain-specific tool into a genuinely reusable one. It started as a single-purpose tracker for a specific use case with two hardcoded procedure types on a fixed schedule; I refactored it into a generic version where both the labels and the underlying scheduling rule are configuration, not code.

Some of the scaffolding was AI-assisted. The scheduling algorithm below was not: an AI tool's first attempt at the recurrence got it wrong, so I derived the closed-form version myself and verified it against the original hardcoded behavior before generalizing it.

## Features

- **Track two recurring procedure types per person**, plus a separate registry/enrollment date
- **Fully relabelable at runtime:** rename "Process 1" / "Process 2" to whatever your use case needs from the in-app Settings panel; every button, header, and list updates instantly
- **Configurable due-date schedule** via three parameters (Starting Ratio, Change Point, Following Ratio). See [How the scheduling works](#how-the-scheduling-works) below
- **Automatic status flags** (color-coded) showing who's currently due for their next procedure, and whether someone's registry enrollment has lapsed
- **CSV-backed storage:** human-readable, portable, easy to inspect or edit by hand
- **Editable history per person:** add, remove, or correct individual dates after the fact
- Packagable as a standalone desktop app (macOS/Windows) via PyInstaller

## Windows and Mac screenshots

![Appscreenshot](assets/General_Procedure_micro.png)
![Appscreenshot](assets/General_tracker_mac.png)

## Getting started

**Requirements:** Python 3.11+, [pandas](https://pypi.org/project/pandas/)

```bash
git clone https://github.com/<your-username>/general-procedure-tracker.git
cd general-procedure-tracker
pip install pandas
python tracker_gui_tk.py
```

On first launch, the app looks for a `people.csv` file in the project root. This repo includes a blank template and a file of synthetic demo data; rename whichever one you want to start with to `people.csv`.

## Usage

1. **Type a name** and press Enter (or click away). This loads an existing person or creates a new one.
2. **Add Process 1 / Add Process 2 / Add Registry:** each opens a small dialog pre-filled with today's date. Press Enter to accept it, or type a different date to backdate an entry.
3. **Remove Selected / Edit Selected:** select an entry in either history list to correct or delete it.
4. **Settings panel** (bottom of the window): relabel the two procedure types, and tune the schedule that drives the status flag (see below). Click **Apply Settings** to save; this also retroactively recalculates every existing person's flag under the new rule.

Settings persist across runs in a small `tracker_config.json` file saved next to `people.csv`.

## How the scheduling works

The app tracks a "Flag" per person: whether they're currently due for their next Process 1, driven by three numbers:

| Parameter | Meaning |
|---|---|
| **Starting Ratio** | How many Process 2 entries occur between Process 1 entries at the start |
| **Change Point** | How many Process 1 occurrences the starting ratio applies to, before the schedule changes |
| **Following Ratio** | How many Process 2 entries occur between Process 1 entries after the change point |

For example, `Starting Ratio = 1, Change Point = 4, Following Ratio = 3` alternates 1:1 for the first four Process 1 occurrences, then settles into one Process 1 per three Process 2 occurrences after that, producing this pattern:

```
P1, P2, P1, P2, P1, P2, P1, P2, P2, P2, P1, P2, P2, P2, P1, ...
```

This generalizes to a closed-form recurrence. The cumulative Process 2 count at which the *n*th Process 1 becomes due is:

```
if n <= change_point:
    due_at(n) = (n - 1) * starting_ratio
else:
    due_at(n) = (change_point - 1) * starting_ratio + (n - change_point) * following_ratio
```

Any combination of the three parameters produces a valid, consistent schedule. This isn't hardcoded to the 1/4/3 example above.

The only remaining hardcoded value in the app is the registry lapse window, fixed at 6 months (see [Known limitations](#known-limitations)).

## Using your own data

The included `people.csv` files use the header row the app expects:

```
Name,Registry,Registry Date,Process 1,Process 1 Date,Process 2,Process 2 Date,Flag,Registration Flag
```

To point the app at your own dataset, reshape your CSV to match this header row exactly (column order doesn't matter, but the names do). The in-app Settings panel only changes what's displayed in the GUI; the actual CSV column names stay fixed unless you also edit the `kwargs.get(...)` calls and `to_dict()` method in `builds/tracker.py`'s `Person` class to match different header names.

## Project structure

```
.
├── tracker_gui_tk.py     # Tkinter GUI, main entry point
├── builds/
│   ├── __init__.py
│   └── tracker.py        # Data model (Person class), scheduling logic, CSV I/O, CLI mode
├── people.csv             # Your data (not committed, see .gitignore)
└── tracker_config.json    # Saved labels + schedule settings (auto-created on first run)
```

`tracker.py` also works standalone as a command-line version of the same tool. Run `python builds/tracker.py` for a terminal-based menu with the same feature set.

## Building a standalone app

The project can be packaged into a double-clickable app with [PyInstaller](https://pyinstaller.org/):

```bash
pip install pyinstaller
pyinstaller --windowed tracker_gui_tk.py
```

Place `people.csv` next to the built executable/`.app` bundle so the app can find it. See `macbuild.py` for a scripted version of this step.

## Adding a screenshot

1. Take a screenshot of the app running.
2. Save it into the repo, for example as `assets/screenshot.png`.
3. Reference it in this README using markdown image syntax: `![App screenshot](assets/screenshot.png)`.
4. Commit and push both the image file and this README together. GitHub only renders images that actually exist in the repo, not local-only file paths.

## Known limitations

This is a portfolio-scale project, not a production system:

- One flat table per data file
- Single-user, single-file access
- No authentication, encryption, or audit trail
- Local CSV storage only
- Registry lapse window is hardcoded to 6 months

## License

[MIT](LICENSE). Free to use, modify, and distribute.

## Acknowledgments

Built with general-purpose AI coding assistants for scaffolding and refactoring. The core scheduling algorithm was independently derived and verified against the original hardcoded behavior before being generalized.
