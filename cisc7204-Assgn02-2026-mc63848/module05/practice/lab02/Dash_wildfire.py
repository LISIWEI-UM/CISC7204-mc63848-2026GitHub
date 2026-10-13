# -*- coding: utf-8 -*-
"""Module05 Practice Part2 - Australia wildfire dashboard, mc63848 LI SIWEI."""
from pathlib import Path
import argparse
import calendar
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / 'data' / 'Historical_Wildfires.csv'
if not DATA_PATH.exists():
    DATA_PATH = HERE.parents[2] / 'data' / 'Historical_Wildfires.csv'
df = pd.read_csv(DATA_PATH)
dates = pd.to_datetime(df['Date'], format='%m/%d/%Y')
df['Year'], df['Month'] = dates.dt.year, dates.dt.month
MONTHS = list(calendar.month_name)[1:]
REGIONS = {'NSW': 'New South Wales', 'NT': 'Northern Territory', 'QL': 'Queensland',
           'SA': 'South Australia', 'TA': 'Tasmania', 'VI': 'Victoria', 'WA': 'Western Australia'}
app = Dash(__name__)
app.title = 'Australia Wildfire Dashboard'
# TASK 2.1-2.3: title, two input controls, two output divisions.
app.layout = html.Div([
    html.H1('Australia Wildfire Dashboard',
            style={'textAlign': 'center', 'color': '#503D36', 'fontSize': 26}),
    html.Div([
        html.H2('Select Region:'),
        dcc.RadioItems([{'label': label, 'value': code} for code, label in REGIONS.items()],
                       value='NSW', id='region', inline=True,
                       labelStyle={'marginRight': '16px'}),
        html.H2('Select Year:'),
        dcc.Dropdown([{'label': y, 'value': y} for y in range(2005, 2021)],
                     value=2005, id='year', clearable=False, style={'width': '300px'}),
    ]),
    html.P('Monthly means of available daily records. Pie slices compare monthly mean fire area.'),
    html.Div([html.Div(id='plot1', style={'width': '50%'}),
              html.Div(id='plot2', style={'width': '50%'})], style={'display': 'flex'}),
], style={'maxWidth': '1180px', 'margin': 'auto', 'fontFamily': 'Arial', 'padding': '12px'})

def monthly_summary(region, year):
    """Keep numerical month order; do not alphabetically sort month names."""
    if region not in REGIONS or year not in range(2005, 2021):
        return pd.DataFrame(columns=['Month', 'Estimated_fire_area', 'Count'])
    subset = df[(df.Region == region) & (df.Year == year)]
    result = subset.groupby('Month', as_index=False)[['Estimated_fire_area', 'Count']].mean()
    result['Month'] = result['Month'].map(lambda m: calendar.month_name[int(m)])
    return result

# TASK 2.4-2.5: both controls update both charts.
@app.callback([Output('plot1', 'children'), Output('plot2', 'children')],
              [Input('region', 'value'), Input('year', 'value')])
def reg_year_display(input_region, input_year):
    summary = monthly_summary(input_region, input_year)
    fig1 = px.pie(summary, values='Estimated_fire_area', names='Month',
                  title=f'{input_region}: Monthly Average Estimated Fire Area<br>in year {input_year}')
    fig2 = px.bar(summary, x='Month', y='Count', category_orders={'Month': MONTHS},
                  title=f'{input_region}: Average Count of Pixels for<br>Presumed Vegetation Fires in year {input_year}',
                  labels={'Count': 'Average Daily Fire Pixel Count'})
    for figure in [fig1, fig2]:
        figure.update_layout(height=440, margin={'l': 50, 'r': 20, 't': 80, 'b': 60},
                             title_font_size=16)
    return [dcc.Graph(id='fire-area-chart', figure=fig1),
            dcc.Graph(id='fire-pixels-chart', figure=fig2)]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8058)
    args = parser.parse_args()
    app.run(host='127.0.0.1', port=args.port, debug=False)
