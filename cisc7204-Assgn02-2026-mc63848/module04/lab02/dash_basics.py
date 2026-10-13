"""Dash Basics: H1, P and Graph, including the requested title exercise."""
from pathlib import Path
import argparse
import pandas as pd
import plotly.express as px
from dash import Dash,dcc,html
HERE=Path(__file__).resolve().parent
DATA_PATH=HERE/'data/airline_data.csv'
if not DATA_PATH.exists(): DATA_PATH=HERE.parents[1]/'data/airline_data.csv'
airline_data=pd.read_csv(DATA_PATH,encoding='ISO-8859-1',
    dtype={'Div1Airport':str,'Div1TailNum':str,'Div2Airport':str,'Div2TailNum':str})
data=airline_data.sample(n=500,random_state=42)
fig=px.pie(data,values='Flights',names='DistanceGroup',title='Distance group proportion by flights')
fig.update_layout(template='plotly_white',height=430)
def create_app(practice=True):
    app=Dash(__name__)
    title='Airline On-time Performance Dashboard' if practice else 'Airline Dashboard'
    app.layout=html.Div([
        html.H1(title,style={'textAlign':'center','color':'#503D36','fontSize':50 if practice else 40}),
        html.P('Proportion of distance group (250 mile distance interval group) by flights.',
            style={'textAlign':'center','color':'#F57241'}),
        dcc.Graph(id='distance-pie',figure=fig)
    ],style={'fontFamily':'Arial, sans-serif','maxWidth':'1180px','margin':'20px auto'})
    return app
app=create_app()
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--original',action='store_true',help='Show initial 40px title')
    parser.add_argument('--port',type=int,default=8052)
    args=parser.parse_args()
    print('Rows:',len(airline_data),'| sample:',len(data),'| stop with Ctrl+C',flush=True)
    create_app(practice=not args.original).run(host='127.0.0.1',port=args.port,debug=False)
