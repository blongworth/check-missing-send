from flask import Flask, render_template
from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
from main import get_table_rows, parse_table_rows, check_missing_intervals, url, start_date

app = Flask(__name__)
dash_app = Dash(__name__, server=app, url_base_pathname='/dash/')

# Initialize empty data
data_store = {
    'parsed_data': [],
    'gaps': [],
    'last_reading': None
}

# Create the layout
dash_app.layout = html.Div([
    html.H1('Temperature Monitoring Dashboard'),
    html.Div([
        html.H3('Latest Reading'),
        html.Div(id='last-reading')
    ]),
    dcc.Graph(id='temperature-plot'),
    html.Div([
        html.H3('Missing Intervals'),
        html.Div(id='missing-intervals', style={'maxHeight': '300px', 'overflow': 'auto'})
    ]),
    dcc.Interval(
        id='interval-component',
        interval=600*1000,  # 10 minutes in milliseconds
        n_intervals=0
    )
])

@dash_app.callback(
    [Output('temperature-plot', 'figure'),
     Output('last-reading', 'children'),
     Output('missing-intervals', 'children')],
    Input('interval-component', 'n_intervals')
)
def update_dashboard(n):
    # Fetch and process data
    data = get_table_rows(url, start_date)
    if data:
        data_store['parsed_data'] = parse_table_rows(data)
        data_store['gaps'] = check_missing_intervals(data_store['parsed_data'])
        if data_store['parsed_data']:
            data_store['last_reading'] = data_store['parsed_data'][-1]

    # Create plot
    times = [datetime.fromisoformat(t.replace("Z", "+00:00")) for t, _ in data_store['parsed_data']]
    temps = [temp for _, temp in data_store['parsed_data']]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times,
        y=temps,
        mode='lines',
        name='Temperature'
    ))
    fig.update_layout(
        title='Temperature vs Time',
        xaxis_title='Time',
        yaxis_title='Temperature (°C)',
        template='plotly_white'
    )

    # Format last reading
    last_reading_html = "No data available"
    if data_store['last_reading']:
        timestamp, temp = data_store['last_reading']
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        last_reading_html = html.Div([
            html.P(f"Time: {dt.strftime('%Y-%m-%d %H:%M:%S')} UTC"),
            html.P(f"Temperature: {temp:.2f}°C")
        ])

    # Format missing intervals
    missing_intervals_html = []
    for start, end in data_store['gaps']:
        missing_intervals_html.append(
            html.Div(f"Gap from {start} to {end}", 
                    style={'padding': '5px', 'borderBottom': '1px solid #ddd'})
        )
    if not missing_intervals_html:
        missing_intervals_html = [html.Div("No missing intervals detected")]

    return fig, last_reading_html, missing_intervals_html

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)