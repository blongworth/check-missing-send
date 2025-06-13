import requests
from bs4 import BeautifulSoup
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import time

url = "https://gems.whoi.edu/LECS_data/?timestamp="
start_date = datetime.strptime("2025-06-01", "%Y-%m-%d")


def get_table_rows(base_url, start_date=None):
    """
    Fetch LECS data from web page based on date
    Args:
        start_date: datetime or None (defaults to today)
        base_url: string or None (defaults to LECS data URL)
    Returns:
        a list of strings representing rows in the table
    """
    if start_date is None:
        start_date = datetime.now()
    if base_url is None:
        base_url = "https://gems.whoi.edu/LECS_data/?timestamp="

    query_url = base_url + start_date.strftime("%Y%m%d%H")
    
    while True:
        try:
            print(f"Fetching data from: {query_url}")
            response = requests.get(query_url)
            response.raise_for_status()  # Raise an exception for bad status codes
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table")
            if table:
                return [row.get_text().strip() for row in table.find_all("tr")]
            return []
        except (requests.ConnectionError, requests.RequestException) as e:
            print(f"Connection error: {e}")
            print("Retrying in 30 seconds...")
            time.sleep(30)
            continue


def parse_table_rows(rows):
    """
    Parse rows with format [-1]T:2025-06-08T12:00:25Z,52.14 into tuples of (timestamp, temperature)
    """
    parsed_data = []
    for row in rows:
        # Only process rows that start with "[0]T:"
        if re.match(r"^\[\d+\]T:", row):
            # Split on "T:" and take the second part
            _, data = row.split("T:", 1)
            # Split timestamp and temperature on comma
            timestamp, temp = data.split(",")
            # Convert temperature to float
            temp = float(temp)
            parsed_data.append((timestamp, temp))
    return parsed_data


def plot_temperature_data(parsed_data):
    """
    Create a plot of temperature vs time using plotly
    """
    times = [datetime.fromisoformat(t.replace("Z", "+00:00")) for t, _ in parsed_data]
    temps = [temp for _, temp in parsed_data]

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
    fig.show()


def check_missing_intervals(parsed_data, expected_interval_minutes=10):
    """
    Check for missing intervals in timestamp data
    Args:
        parsed_data: list of (timestamp, temperature) tuples
        expected_interval_minutes: expected minutes between readings
    Returns:
        list of gaps as (start_time, end_time) tuples
    """
    if not parsed_data:
        return []
    
    times = [datetime.fromisoformat(t.replace("Z", "+00:00")).replace(second=0)
            for t, _ in parsed_data]
    times.sort()
    
    gaps = []
    for i in range(len(times) - 1):
        diff = (times[i + 1] - times[i]).total_seconds() / 60
        if diff > expected_interval_minutes:
            gaps.append((times[i], times[i + 1]))
            
    return gaps


def update_plot(fig, parsed_data):
    """
    Update the plot with new data
    """
    times = [datetime.fromisoformat(t.replace("Z", "+00:00")) for t, _ in parsed_data]
    temps = [temp for _, temp in parsed_data]
    
    fig.data[0].x = times
    fig.data[0].y = temps
    fig.show()


def main():
    try:
        # Create initial empty figure
        fig = go.Figure(data=[go.Scatter(
            x=[],
            y=[],
            mode='lines',
            name='Temperature'
        )])
        
        fig.update_layout(
            title='Temperature vs Time',
            xaxis_title='Time',
            yaxis_title='Temperature (°C)',
            template='plotly_white'
        )

        while True:
            data = get_table_rows(url, start_date)
            if data:
                parsed_data = parse_table_rows(data)
                checked_gaps = check_missing_intervals(parsed_data)
                if checked_gaps:
                    print("\nMissing intervals found:")
                    for start, end in checked_gaps:
                        print(f"Missing from {start} to {end}")
                update_plot(fig, parsed_data)
            time.sleep(600)  # Wait 10 minutes
    except KeyboardInterrupt:
        print("\nExiting program...")


if __name__ == "__main__":
    main()
