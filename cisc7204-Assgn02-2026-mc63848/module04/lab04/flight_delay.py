"""Five delay-category figures updated together by one year callback."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash,dcc,html,Input,Output
HERE=Path(__file__).resolve().parent
DATA_PATH=HERE/'data/airline_data.csv'
if not DATA_PATH.exists(): DATA_PATH=HERE.parents[1]/'data/airline_data.csv'
airline_data=pd.read_csv(DATA_PATH,encoding='ISO-8859-1',
    dtype={'Div1Airport':str,'Div1TailNum':str,'Div2Airport':str,'Div2TailNum':str})
METRICS=['CarrierDelay','WeatherDelay','NASDelay','SecurityDelay','LateAircraftDelay']
GRAPH_IDS=['carrier-plot','weather-plot','nas-plot','security-plot','late-plot']
TITLES=['Carrier delay','Weather delay','NAS delay','Security delay','Late aircraft delay']
def compute_info(data,entered_year):
    df=data.loc[data.Year==int(entered_year)]
    return tuple(df.groupby(['Month','Reporting_Airline'])[metric].mean().reset_index()
                 for metric in METRICS)
def get_graph(entered_year):
    try:
        number=float(entered_year)
        year=int(number) if number.is_integer() and 2010<=number<=2020 else None
    except (TypeError,ValueError,OverflowError): year=None
    figures=[]
    tables=compute_info(airline_data,year) if year is not None else [None]*5
    for table,metric,title in zip(tables,METRICS,TITLES):
        if year is None:
            fig=go.Figure()
            fig.add_annotation(text='Enter a whole year from 2010 to 2020.',showarrow=False)
        else:
            fig=px.line(table,x='Month',y=metric,color='Reporting_Airline',
                title=f'{title} — {year}',labels={metric:'Mean delay (minutes)'})
        fig.update_layout(template='plotly_white',height=300,font={'size':11},
            margin={'l':55,'r':20,'t':45,'b':45},legend_title_text='Airline')
        fig.update_xaxes(dtick=1,range=[0.5,12.5])
        figures.append(fig)
    return figures
def create_app(practice=False):
    app=Dash(__name__)
    title='Flight Details Statistics Dashboard' if practice else 'Flight Delay Time Statistics'
    panel=lambda graph_id:html.Div(dcc.Graph(id=graph_id),style={'width':'50%','minWidth':0})
    app.layout=html.Div([
        html.H1(title,style={'textAlign':'center','color':'#503D36','fontSize':35 if practice else 30}),
        html.Div([html.Label('Input Year: ',htmlFor='input-year'),
            dcc.Input(id='input-year',value=2010,type='number',min=2010,max=2020,step=1,
                debounce=True,style={'height':'35px','fontSize':30,'width':'150px'})],style={'fontSize':30}),
        html.P('Monthly mean recorded delay by airline (minutes); missing values are excluded.'),
        html.Div([panel('carrier-plot'),panel('weather-plot')],style={'display':'flex'}),
        html.Div([panel('nas-plot'),panel('security-plot')],style={'display':'flex'}),
        html.Div(dcc.Graph(id='late-plot'),style={'width':'65%'})
    ],style={'fontFamily':'Arial, sans-serif','maxWidth':'1180px','margin':'15px auto'})
    app.callback([Output(graph_id,'figure') for graph_id in GRAPH_IDS],Input('input-year','value'))(get_graph)
    return app
app=create_app()
if __name__=='__main__': app.run(host='127.0.0.1',port=8056,debug=False)
