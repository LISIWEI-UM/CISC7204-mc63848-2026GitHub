# Module 04 Lab04 — Flight Delay Time Statistics

Student: mc63848, LI SIWEI. Tested with Python 3.10 in CISC7204.

From this extracted project folder:

```sh
python -m pip install -r requirements.txt
python flight_delay.py
```

Open http://127.0.0.1:8056 for the original title (Flight Delay Time Statistics, 30px).

Practice answers: the renamed entry point is flight_details.py, and its H1 title is **Flight Details Statistics Dashboard**, font size 35px:

```sh
python flight_details.py
```

Open http://127.0.0.1:8055. Save/relaunch after changing the title; stop the running app with **Ctrl+C**.

The selected year feeds one callback with five figure outputs. Each figure uses Month and Reporting_Airline groups to compute mean CarrierDelay, WeatherDelay, NASDelay, SecurityDelay or LateAircraftDelay, in minutes. The layout keeps two paired rows and a last graph at 65% width. Missing delay values are excluded from means, not treated as zeros.

Input years are 2010–2020. Enter or blur the field to update all five figures together. Invalid/empty input shows a message. The supplied 2020 sample contains only months 1–3. Both Python files and data/airline_data.csv are included; no other assignment folders are required after extraction.
