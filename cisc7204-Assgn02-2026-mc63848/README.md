# CISC7204 Assignment 02 — Data Visualization Portfolio

**LI SIWEI · mc63848 · University of Macau · 2026**

This portfolio contains my completed personal labs for CISC7204 Assignment 02:
10 executed Jupyter notebooks, 5 Dash project ZIPs, editable Python sources and
98 selected screenshots documenting code and actual execution results.
Course-provided lab templates and datasets are acknowledged below. The work covers
Pandas, Matplotlib, Seaborn, WordCloud, PyWaffle, Folium, Plotly and Dash.

## Modules

| Module | Content | Labs | Screenshots |
|---|---|---:|---:|
| 01 | [Pandas preprocessing and line plots](module01/README.md) | 2 | 9 |
| 02 | [Matplotlib basic and specialized plots](module02/README.md) | 3 | 18 |
| 03 | [Waffle charts, word clouds, regression and Folium maps](module03/README.md) | 2 | 16 |
| 04 | [Plotly charts and airline Dash applications](module04/README.md) | 4 | 22 |
| 05 | [Australian wildfire and automobile-sales projects](module05/README.md) | 4 | 33 |

Module 05 includes both Practice and Final projects. The ZIPs preserve the required
submission filenames and contain independently runnable Dash projects. The two
required Final dashboard images are named `RecessionReportgraphs.png` and
`YearlyReportgraphs.png`.

## Run locally

Tested with **Python 3.10**. From this assignment folder:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m notebook
```

Open a notebook in its existing module folder and trust it to view saved interactive
outputs. Keep the `data/` directory in place. Saved notebooks include executed
outputs; interactive maps need an internet connection for their external assets.

For Dash applications, run a Python entry point below, then open the printed local URL.
Use **Ctrl+C** to stop. Each project folder contains further instructions.

| Project | Entry point (relative to this folder) | Port |
|---|---|---:|
| Module04 Lab02 | `module04/lab02/dash_basics.py` | 8052 |
| Module04 Lab03 | `module04/lab03/dash_interactivity.py` | 8053 |
| Module04 Lab03 exercise | `module04/lab03/dash_interactivity_barplot.py` | 8054 |
| Module04 Lab04 original | `module04/lab04/flight_delay.py` | 8056 |
| Module04 Lab04 exercise | `module04/lab04/flight_details.py` | 8055 |
| Module05 Practice Lab02 | `module05/practice/lab02/Dash_wildfire.py` | 8058 |
| Module05 Final Lab02 | `module05/final/lab02/DV0101EN-Final-Assign-Part-2-Questions.py` | 8059 |

For example:

```sh
python module05/final/lab02/DV0101EN-Final-Assign-Part-2-Questions.py
```

### Module03 CARTO basemaps

The lab's CARTO light/dark basemaps use a local tile proxy so credentials are not
embedded in the notebooks. Obtain your own CARTO key, create
`.runtime/carto_api_key.txt` in this assignment folder, put your key in that file,
and run `python start_map_tiles.py` before opening Module03 Lab02 maps.
The proxy listens on `127.0.0.1:8894`. The private key and runtime folder are ignored
by Git. The original notebook outputs and static screenshots are retained.

## Data and interpretation notes

- Local datasets are supplied with the course labs and retained for reproducibility.
- The automobile dataset spans **1980–2023**, following the supplied data and the
  task's `range(1980, 2024)` instruction.
- The 2020 airline data in the provided file includes January–March only.
- Dash callbacks use the means or sums specified by each exercise. Final yearly
  and recession reports contain four figures in a two-by-two layout.

## Acknowledgements

Course lab templates, assignment instructions and supplied data are from University
of Macau CISC7204 and the IBM Skills Network Data Visualization with Python labs.
The lab materials contain their original attribution and source links. The Alice
text/mask, Canada immigration data, San Francisco incident data, geographic JSON
files, airline data and project datasets retain their course-provided contents.
Third-party materials remain subject to their respective terms; this repository
does not grant a new license to them.
