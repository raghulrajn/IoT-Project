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
import paho.mqtt.client as mqtt
import config

mqtt_client = mqtt.Client()
db_handler = DatabaseHandler('mqtt_data.db', config.topics,"mqtt")
planner_handler = DatabaseHandler('planner_data.db', config.planning_topics,"planning")
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
    plan_df = planner_handler.read_from_db()
    print(len(plan_df))
    for topic in config.planning_topics:
        topic_ = topic.split('/')[2]
        if "problem" in plan_df.columns:
            problem_ = plan_df["problem"].iloc[-1]
    return f"Problem: {problem_}"

@app.callback(Output('live-update-text2', 'children'),
              Input('interval-component', 'n_intervals'))
def update_message2(n):
    plan_df = planner_handler.read_from_db()
    for topic in config.planning_topics:
        topic_ = topic.split('/')[2]
        if "solution" in plan_df.columns:
            solution = plan_df["solution"].iloc[-1]
    return f"solution: {solution}"

# def on_connect(client, userdata, flags, rc):
#     print(f"Connected with result code {rc}")
#     client.subscribe("iot/aiplanning/problem")
#     client.subscribe("iot/aiplanning/solution")

# def on_message(client, userdata, msg):
#     global problem, solution
#     if msg.topic == "iot/aiplanning/problem":
#         problem = msg.payload.decode()
#     elif msg.topic == "iot/aiplanning/solution":
#         solution = msg.payload.decode()



# def mqtt_loop():
#     mqtt_client.connect("127.0.0.1", 1883, 60)
#     mqtt_client.on_connect = on_connect
#     mqtt_client.on_message = on_message
#     mqtt_client.loop_start()

# Start the MQTT client in a separate thread
# mqtt_thread = Thread(target=mqtt_loop)
# mqtt_thread.start()
# mqtt_thread.join()

if __name__ == '__main__':
    app.run_server(debug=True)

