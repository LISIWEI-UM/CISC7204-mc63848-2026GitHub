"""Practice exercise: flights by destination state and reporting airline."""
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash,dcc,html,Input,Output
from dash_interactivity import airline_data,selected_year
app=Dash(__name__)
app.layout=html.Div([
    html.H1('Total number of flights to the destination state split by reporting airline',
        style={'textAlign':'center','color':'#503D36','fontSize':40}),
    html.Div([html.Label('Input Year: ',htmlFor='input-year'),
        dcc.Input(id='input-year',value=2010,type='number',min=2010,max=2020,step=1,
            debounce=True,style={'height':'50px','fontSize':35,'width':'160px'})],style={'fontSize':40}),
    dcc.Graph(id='bar-plot')
],style={'fontFamily':'Arial, sans-serif','maxWidth':'1180px','margin':'20px auto'})
@app.callback(Output('bar-plot','figure'),Input('input-year','value'))
def get_graph(entered_year):
    year=selected_year(entered_year)
    if year is None:
        fig=go.Figure()
        fig.add_annotation(text='Enter a whole year from 2010 to 2020.',showarrow=False)
    else:
        df=airline_data.loc[airline_data.Year==year]
        bar_data=df.groupby(['DestState','Reporting_Airline'])['Flights'].sum().reset_index()
        fig=px.bar(bar_data,x='DestState',y='Flights',color='Reporting_Airline',
            title=f'Flights by destination state and reporting airline — {year}',
            labels={'DestState':'Destination state','Flights':'Number of flights'})
        fig.update_xaxes(categoryorder='category ascending')
    fig.update_layout(template='plotly_white',height=470,legend_title_text='Reporting airline')
    return fig
if __name__=='__main__': app.run(host='127.0.0.1',port=8054,debug=False)
