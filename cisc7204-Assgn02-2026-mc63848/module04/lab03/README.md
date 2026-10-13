# Module 04 Lab03 — Year Input and Callbacks

Student: mc63848, LI SIWEI. Tested with Python 3.10 in CISC7204.

From this extracted project folder:

```sh
python -m pip install -r requirements.txt
python dash_interactivity.py
```

Open http://127.0.0.1:8053 for the required monthly mean arrival-delay line chart. Enter a whole year from 2010 to 2020, then press Enter or move focus to update it. Missing arrival delays are excluded from means. Clear/invalid values show an explanatory message.

The separate practice exercise is complete:

```sh
python dash_interactivity_barplot.py
```

Open http://127.0.0.1:8054. The callback filters the selected year, groups by DestState and Reporting_Airline, and sums Flights; colors identify the airline. Its H1 title, input-year and bar-plot component ids match the exercise requirements.

Stop either app with **Ctrl+C**. Both scripts and their shared import are included, together with data/airline_data.csv. The provided 2020 sample covers only months 1–3; the apps do not invent later observations.
