"""Selected year -> monthly mean arrival-delay line plot."""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from dash import Dash,dcc,html,Input,Output
HERE=Path(__file__).resolve().parent
DATA_PATH=HERE/'data/airline_data.csv'
if not DATA_PATH.exists(): DATA_PATH=HERE.parents[1]/'data/airline_data.csv'
airline_data=pd.read_csv(DATA_PATH,encoding='ISO-8859-1',
    dtype={'Div1Airport':str,'Div1TailNum':str,'Div2Airport':str,'Div2TailNum':str})
def selected_year(value):
    try:
        number=float(value)
        return int(number) if number.is_integer() and 2010<=number<=2020 else None
    except (TypeError,ValueError,OverflowError): return None
app=Dash(__name__)
app.layout=html.Div([
    html.H1('Airline Performance Dashboard',style={'textAlign':'center','color':'#503D36','fontSize':40}),
    html.Div([html.Label('Input Year: ',htmlFor='input-year'),
        dcc.Input(id='input-year',value=2010,type='number',min=2010,max=2020,step=1,
            debounce=True,style={'height':'50px','fontSize':35,'width':'160px'})],style={'fontSize':40}),
    html.P('Monthly mean arrival delay in minutes. Missing delays are excluded.'),
    dcc.Graph(id='line-plot')
],style={'fontFamily':'Arial, sans-serif','maxWidth':'1180px','margin':'20px auto'})
@app.callback(Output('line-plot','figure'),Input('input-year','value'))
def get_graph(entered_year):
    year=selected_year(entered_year)
    fig=go.Figure()
    if year is None:
        fig.add_annotation(text='Enter a whole year from 2010 to 2020.',showarrow=False)
    else:
        df=airline_data.loc[airline_data.Year==year]
        line_data=df.groupby('Month')['ArrDelay'].mean().reset_index()
        fig.add_trace(go.Scatter(x=line_data.Month,y=line_data.ArrDelay,
            mode='lines',line={'color':'green'},name=str(year)))
    fig.update_layout(title='Month vs Average Flight Delay Time'+(f' — {year}' if year else ''),
        xaxis_title='Month',yaxis_title='ArrDelay (minutes)',template='plotly_white',height=430)
    fig.update_xaxes(dtick=1,range=[0.5,12.5])
    return fig
if __name__=='__main__':
    print('Year callback: 2010–2020; stop with Ctrl+C',flush=True)
    app.run(host='127.0.0.1',port=8053,debug=False)
