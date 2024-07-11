import sqlite3
import pandas as pd
import dash
from dash import dcc, html
from utils import DatabaseHandler
from dash.dependencies import Output, Input
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from typing import Dict, Any
from threading import Thread
import config

db_handler = DatabaseHandler('mqtt_data.db', config.topics)
problem = ""
solution = ""
db_topics = ['iot/sensor/temperature',
          'iot/sensor/airquality', 
          'iot/sensor/presence',
          "iot/sensor/luminosity"]

soln_topics = ['iot/aiplanning/problem',
               'iot/aiplanning/solution']
# Create a Dash app
app = dash.Dash(__name__,suppress_callback_exceptions=True)

app.layout = html.Div([
    html.H1("MQTT Messages"),
    html.Div(id='live-update-text1'),
    html.Div(id='live-update-text2'),
    html.Div(id='max-values', style={'display': 'flex', 'marginBottom': '20px'}),
    html.Div(id='graphs', style={'display': 'flex', 'flexWrap': 'wrap'}),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,  # Update every second
        n_intervals=0
    ),
])

# app.layout = html.Div([
#     dcc.Interval(id='interval-component', interval=2*1000, n_intervals=0),
#     html.Div(id='max-values', style={'display': 'flex', 'marginBottom': '20px'}),
#     html.Div(id='graphs', style={'display': 'flex', 'flexWrap': 'wrap'})
# ])

@app.callback(
    [Output('graphs', 'children'), Output('max-values', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n):
    df = db_handler.read_from_db()

    graphs = []
    max_values = []
    for topic in config.sensor_topics:
        topic_ = topic.split('/')[2]

        if topic_ in df.columns:
            fig = px.line(df, x='timestamp', y=topic_, title=f'{topic} over Time')
            graphs.append(html.Div(dcc.Graph(figure=fig), style={'width': '48%', 'display': 'inline-block'}))
            max_value = df[topic_].max()
            max_values.append(html.Div(f'Max {topic}: {max_value}', style={'fontSize': 20, 'margin': '10px'}))

    return graphs, max_values


@app.callback(Output('live-update-text1', 'children'),
              Input('interval-component', 'n_intervals'))
def update_message1(n):
    return f"Message from topic/test1: {problem}"

@app.callback(Output('live-update-text2', 'children'),
              Input('interval-component', 'n_intervals'))
def update_message2(n):
    return f"Message from topic/test2: {solution}"

if __name__ == '__main__':
    app.run_server(debug=True)

