from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import plotly.tools as tls
from dash.dependencies import Input, Output, State

import pandas as pd
import numpy
import datetime as dt 
from dateutil.relativedelta import relativedelta as rel_delt


aggr_dict = {'Week': 'First week day', 'Month': 'Month', 'Quarter': 'Quarter', 'Year': 'Year'}
aggregation_types = list(aggr_dict.keys())

def getQuarterStart(date=dt.date.today()):
    return dt.date(date.year, (date.month - 1) // 3 * 3 + 1, 1)

def cumul_sum_upd(df, col_ref, col_acc, col_date, col_name, month):
    '''Returns cumulative average.
    
    Args:   
    df -- data frame
    col_ref -- reference column for accumulation, can be either DLP or DLA 
    col_acc -- accumulation column, can be eiter Power % or Accuracy %
    col_date -- Start column. 
    col_name -- result column name. Either Average_Power or Average_Accuracy.
    month -- number of month for moving average calculation.   
    '''
    
    uniq_values = df[col_ref].unique()
    cumul_av = []
    
    for un_val in uniq_values:
        df_clice_new = df[df[col_ref] == un_val]
        data_clice = df[df[col_ref] == un_val][col_date]
        for each_date in data_clice:
            past_date = each_date - rel_delt(months=month)            
            df_temp = df_clice_new[(df_clice_new[col_date] <= each_date) & (df_clice_new[col_date] >= past_date)]
            aver = df_temp[col_acc].mean()
            cumul_av.append(aver)
    df[col_name] = cumul_av
    return df

app = Dash(__name__, external_stylesheets=[dbc.themes.JOURNAL])

app.layout = html.Div(children=[

    html.Br(),


    dbc.Row(
        dbc.Col(html.H1("Player progress analysis",
                        className='text-center text-primary mb-4'), width=12, align="end")),

    dbc.Row(children=[
        dbc.Col(width=1),
        dbc.Col(html.Label(['Choose analysis type:'], style={'font-weight': 'bold', "text-align": "right", "offset":1}),
                 width=2),
        dbc.Col(
             dcc.Dropdown( ['Power analysis', 'Accuracy analysis'], 'Power analysis', clearable=False, id='power_accuracy'), width=2, style={"align": "left"}),
        dbc.Col(
                 width=1),
        dbc.Col(html.Label(['Choose aggregation type:'], style={'font-weight': 'bold', "text-align": "center", "offset":1}),
                 width=2),
        dbc.Col(
             dcc.Dropdown(aggregation_types, aggregation_types[1], clearable=False, id='aggragation_type')  , width=2)], 
                        className="g-0"
    ),

    html.Br(),

    dbc.Row(html.Label(['Choose cumulative average constant (Months number)'], style={'font-weight': 'bold', "text-align": "center", "offset":0}),
    
    ),  


    html.Br(),

    dbc.Row(children=[
        dbc.Col(width = 4),
        dbc.Col(dcc.Slider(1, 12, 1, value=3, marks=None, tooltip={"placement": "bottom", "always_visible": True}, id='slider'), width = 4),
        dbc.Col(width = 4)]
    ),   
        
    dbc.Row(children=[
        dbc.Col(width = 2),
        dbc.Col(dcc.Graph(id='graph-output', figure={}), width = 8),
        dbc.Col(width = 2)]
    )

])


@app.callback(
    Output(component_id='graph-output', component_property='figure'),
    [Input(component_id='aggragation_type', component_property='value'),
    Input(component_id='power_accuracy', component_property='value'),
    Input(component_id='slider', component_property='value')]
)
def update_my_graph(aggr_type, pow_acc, slider_val):
    period = aggr_dict[aggr_type]
    
    if pow_acc == 'Power analysis':
        factor = 'DLP'
        yy = "Average_Power"
        yy_1 = 'Power %'

    else:
        factor = 'DLA'
        yy = "Average_Accuracy"
        yy_1 = 'Accuracy %'

    df = pd.read_excel("Player 1 monthly performance.xlsx")
    df['TKicks'] = df['TKicks'] - df['TSleep'] - df['TSkips']
    df.drop(['TSleep', 'TSkips', 'Sleep %', 'Skip %'], axis=1, inplace=True)

    df['Power %'] = round(df['TPower']/df['TKicks'] * 100, 0)
    df['Accuracy %'] = round(df['TAccuracy']/df['TKicks'] * 100, 0)

    date_list = df['Date'].to_list()
    start_list = df['Start'].to_list()
    end_list = df['End'].to_list()

    date_start = []
    date_end = []

    for n in range(len(df['Date'].to_list())):
        new_start = dt.datetime.combine(date_list[n], start_list[n])
        new_end = dt.datetime.combine(date_list[n], end_list[n])
    
        date_start.append(new_start)
        date_end.append(new_end)

    df['Start'] = date_start
    df['End'] = date_end
    dff = df.drop(['TKicks', 'TPower', 'TAccuracy', 'TGoals'], axis=1)

    dff['First week day'] = dff['Date'].apply(lambda x: x - dt.timedelta(days=x.weekday()))
    dff['Month'] = dff['Date'].apply(lambda x: dt.date(x.year, x.month, 1))
    dff['Quarter'] = dff['Date'].apply(lambda x: getQuarterStart(x))#.to_timestamp()
    dff['Year'] = dff['Date'].apply(lambda x: pd.Timestamp(x.year, 1, 1))

    dff['First week day'] = dff['Date'].apply(lambda x: x - dt.timedelta(days=x.weekday()))
    dff['Month'] = dff['Date'].apply(lambda x: dt.date(x.year, x.month, 1))
    dff['Quarter'] = dff['Date'].apply(lambda x: getQuarterStart(x))#.to_timestamp()
    dff['Year'] = dff['Date'].apply(lambda x: pd.Timestamp(x.year, 1, 1))    

    dff = dff.sort_values(by=['DLP', 'Start'])
    dff = dff.reset_index(drop=True)
    dff = cumul_sum_upd(dff, 'DLP', 'Power %', 'Start', 'Average_Power', slider_val)

    dff = dff.sort_values(by=['DLA', 'Start'])
    dff = dff.reset_index(drop=True)
    dff = cumul_sum_upd(dff, 'DLP', 'Accuracy %', 'Start', 'Average_Accuracy', slider_val)

    groupped = dff.groupby(by=[period, factor]).mean()#

    groupped = groupped.reset_index()
    groupped[factor] = groupped[factor].map(int).map(str)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,vertical_spacing=0.09,horizontal_spacing=0.009, subplot_titles=("Cumulative average", "Average"))

    fig['layout']['margin'] = {'l': 10, 'r': 10, 'b': 0, 't': 50}

    bar1 = px.line(groupped.sort_values(by=period), x = period, y = yy, color=factor,  markers=True)
    bar2 = px.line(groupped.sort_values(by=period), x = period, y = yy_1, color=factor,  markers=True)

    for count, trace in enumerate(bar1.data):
        fig.append_trace(trace, 1, 1)
    for trace in bar2.data:
        fig.append_trace(trace, 2, 1)

    fig.update_layout(barmode="stack")      

    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
