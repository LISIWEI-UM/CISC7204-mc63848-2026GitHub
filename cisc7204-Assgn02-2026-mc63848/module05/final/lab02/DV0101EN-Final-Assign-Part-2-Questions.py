# -*- coding: utf-8 -*-
"""Module05 Final Part2 - automobile sales dashboard, mc63848 LI SIWEI."""
from pathlib import Path
import argparse
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / 'data' / 'automobile-sales.csv'
if not DATA_PATH.exists():
    DATA_PATH = HERE.parents[2] / 'data' / 'automobile-sales.csv'
data = pd.read_csv(DATA_PATH)
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
# Use the actual 1980-2023 dataset and the task's range(1980, 2024) hint.
year_list = list(range(1980, 2024))
dropdown_options = [{'label': name, 'value': name} for name in
                    ['Yearly Statistics', 'Recession Period Statistics']]
app = Dash(__name__)
app.title = 'Automobile Sales Statistics Dashboard'
# TASK 2.1-2.3: heading, report/year controls and named output container.
app.layout = html.Div([
    html.H1('Automobile Sales Statistics Dashboard',
            style={'textAlign': 'center', 'color': '#503D36', 'fontSize': 24}),
    html.Div([html.Label('Select Statistics:'),
              dcc.Dropdown(id='dropdown-statistics', options=dropdown_options,
                           value='Select Statistics', placeholder='Select a report type',
                           clearable=False, style={'width': '80%', 'padding': '3px',
                                                   'fontSize': 20, 'textAlignLast': 'center'})]),
    html.Div([html.Label('Select Year:'),
              dcc.Dropdown(id='select-year', options=[{'label': y, 'value': y} for y in year_list],
                           value='Select-year', placeholder='Select-year', clearable=False,
                           disabled=True, style={'width': '300px'})]),
    html.Div(id='output-container', className='chart-grid',
             style={'display': 'flex', 'flexDirection': 'column'}),
], style={'maxWidth': '1180px', 'margin': 'auto', 'fontFamily': 'Arial', 'padding': '12px'})

# TASK 2.4: disabled=False enables the year control.
@app.callback(Output('select-year', 'disabled'), Input('dropdown-statistics', 'value'))
def update_input_container(selected_statistics):
    return selected_statistics != 'Yearly Statistics'

def report_figures(selected_statistics, input_year):
    """Return the four figures, using means/sums exactly as specified."""
    if selected_statistics == 'Recession Period Statistics':
        recession_data = data[data.Recession == 1]
        # TASK 2.5: four recession statistics.
        yearly_rec = recession_data.groupby('Year', as_index=False)['Automobile_Sales'].mean()
        average_sales = recession_data.groupby('Vehicle_Type', as_index=False)['Automobile_Sales'].mean()
        exp_rec = recession_data.groupby('Vehicle_Type', as_index=False)['Advertising_Expenditure'].sum()
        unemp_data = recession_data.groupby(['unemployment_rate', 'Vehicle_Type'],
                                            as_index=False)['Automobile_Sales'].mean()
        figures = [
            px.line(yearly_rec, x='Year', y='Automobile_Sales', markers=True,
                    title='Average Automobile Sales during Recessions'),
            px.bar(average_sales, x='Vehicle_Type', y='Automobile_Sales',
                   title='Average Vehicles Sold by Type during Recessions'),
            px.pie(exp_rec, values='Advertising_Expenditure', names='Vehicle_Type',
                   title='Advertising Expenditure Share during Recessions'),
            px.bar(unemp_data, x='unemployment_rate', y='Automobile_Sales', color='Vehicle_Type',
                   barmode='group', title='Unemployment Rate, Vehicle Type and Sales',
                   labels={'unemployment_rate': 'Unemployment Rate (%)',
                           'Automobile_Sales': 'Average Automobile Sales'}),
        ]
    elif selected_statistics == 'Yearly Statistics' and input_year in year_list:
        # TASK 2.6: whole-period mean; selected-year monthly total, type mean, ad total.
        yearly_data = data[data.Year == input_year]
        yas = data.groupby('Year', as_index=False)['Automobile_Sales'].mean()
        mas = yearly_data.groupby('Month', as_index=False)['Automobile_Sales'].sum()
        avr_vdata = yearly_data.groupby('Vehicle_Type', as_index=False)['Automobile_Sales'].mean()
        exp_data = yearly_data.groupby('Vehicle_Type', as_index=False)['Advertising_Expenditure'].sum()
        figures = [
            px.line(yas, x='Year', y='Automobile_Sales', markers=True,
                    title='Average Yearly Automobile Sales - Whole Period'),
            px.line(mas.assign(Month=pd.Categorical(mas.Month, categories=MONTHS, ordered=True))
                    .sort_values('Month'), x='Month', y='Automobile_Sales', markers=True,
                    title=f'Total Monthly Automobile Sales - {input_year}'),
            px.bar(avr_vdata, x='Vehicle_Type', y='Automobile_Sales',
                   title=f'Average Vehicles Sold by Type - {input_year}'),
            px.pie(exp_data, values='Advertising_Expenditure', names='Vehicle_Type',
                   title=f'Total Advertising Expenditure by Vehicle - {input_year}'),
        ]
    else:
        return []
    for fig in figures:
        fig.update_layout(height=370, margin={'l': 55, 'r': 20, 't': 65, 'b': 75},
                          title_font_size=15, legend_font_size=10)
    return figures

@app.callback(Output('output-container', 'children'),
              [Input('dropdown-statistics', 'value'), Input('select-year', 'value')])
def update_output_container(selected_statistics, input_year):
    figures = report_figures(selected_statistics, input_year)
    if not figures:
        return html.P('Select a report type and, for yearly statistics, a year.')
    graphs = [dcc.Graph(id=f'report-chart-{i+1}', figure=fig) for i, fig in enumerate(figures)]
    return [html.Div([html.Div(graph, style={'width': '50%'}) for graph in graphs[i:i+2]],
                     className='chart-item', style={'display': 'flex'}) for i in [0, 2]]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8059)
    args = parser.parse_args()
    app.run(host='127.0.0.1', port=args.port, debug=False)
