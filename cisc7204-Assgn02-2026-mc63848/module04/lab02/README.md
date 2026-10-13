# Module 04 Lab02 — Dash Basics

Student: mc63848, LI SIWEI. Tested with Python 3.10 in CISC7204.

From this extracted project folder:

```sh
python -m pip install -r requirements.txt
python dash_basics.py
```

Open http://127.0.0.1:8052. The practice title is **Airline On-time Performance Dashboard**, font size 50px. The chart uses a deterministic 500-row sample, random_state=42, and Flights as the pie weight.

To view the initial title (Airline Dashboard, 40px):

```sh
python dash_basics.py --original --port 8057
```

Practice answers: change the H1 title/fontSize, save the file, stop the previous app with **Ctrl+C**, and run it again. Ctrl+C is the requested keyboard command to stop the running application. The command-line switch preserves both versions for comparison.

The included data/airline_data.csv is the supplied course dataset. The program resolves the path from its script, so it also works when launched from a different directory. In the working assignment checkout it can fall back to the shared data directory.
