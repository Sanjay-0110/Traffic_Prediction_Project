import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import numpy as np
import requests
import datetime
import time
import folium
from streamlit_folium import folium_static

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import API_KEY

# Set page config
st.set_page_config(page_title="🚦 Traffic Flow Dashboard", page_icon="🚗", layout="wide")

st.sidebar.title("Navigation")
st.sidebar.page_link("webapp.py", label="🚗 Traffic Prediction")
st.sidebar.page_link("Pages/accurary.py", label="📊 Model Accuracy & Findings")

# TomTom API Key
API_key = API_KEY

# Title
st.title("🚦 Traffic Flow Dashboard - Interstate 94")

# Load dataset
@st.cache_data
def load_data():
    df = pd.read_csv("Data/Metro_Interstate_Traffic_Volume.csv", engine="python")  # Replace with actual path
    return df
# Function to get live traffic flow
def get_traffic_flow(lat, lon):
    url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    params = {"key": API_key, "point": f"{lat},{lon}"}
    response = requests.get(url, params=params)
    return response.json()

# Function to get travel time
def get_travel_time(start_lat, start_lon, end_lat, end_lon):
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{start_lat},{start_lon}:{end_lat},{end_lon}/json"
    params = {"key": API_KEY}
    response = requests.get(url, params=params)
    return response.json()

# Function to get traffic incidents
def get_traffic_incidents(bounding_box):
    url = "https://api.tomtom.com/traffic/services/5/incidentDetails"
    params = {"key": API_KEY, "bbox": bounding_box, "language": "en-US"}
    response = requests.get(url, params=params)
    return response.json()

# Function to get historical traffic trends
def get_traffic_trends():
    hourly_data = {"Hour": list(range(24)), "Traffic Volume": [abs(50 - i) + 20 for i in range(24)]}
    daily_data = {"Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "Traffic Volume": [70, 75, 80, 85, 90, 60, 50]}
    return pd.DataFrame(hourly_data), pd.DataFrame(daily_data)

# Function to get current date and time
def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

df = load_data()

st.header('Real-Time Traffic Flow Insight')
# Date & Real-Time Display
col1, col2 = st.columns(2)
with col1:
    st.subheader("📅 Date")
    st.info(datetime.datetime.now().strftime("%A, %B %d, %Y"))

with col2:
    st.subheader("⏰ Real-Time")
    time_placeholder = st.empty()

# Auto-refreshing time
time_placeholder.info(get_current_time())

st.divider()
# Traffic Overview
st.subheader("Live Traffic Overview")
traffic_data = get_traffic_flow(44.9778, -93.2650)  # Minneapolis center
if traffic_data and "flowSegmentData" in traffic_data:
    traffic_info = traffic_data["flowSegmentData"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🚗 Current Speed (km/h)", value=traffic_info.get("currentSpeed", "N/A"))
        st.metric(label="🔄 Free Flow Speed (km/h)", value=traffic_info.get("freeFlowSpeed", "N/A"))

    with col2:
        st.metric(label="⏳ Traffic Delay (seconds)",
                  value=traffic_info.get("currentTravelTime", "N/A") - traffic_info.get("freeFlowTravelTime", "N/A"))
        st.metric(label="🛑 Road Closed?", value="Yes" if traffic_info.get("roadClosure", False) else "No")

    with col3:
        st.metric(label="📊 Confidence Level (%)", value=traffic_info.get("confidence", "N/A"))
        st.metric(label="🚦 Traffic Density Level", value=traffic_info.get("trafficDensity", "N/A"))
else:
    st.warning("Traffic data unavailable")

st.divider()
# Travel Time Analysis
st.subheader("Travel Time Analysis")
# Get travel time for the main route
travel_times = get_travel_time(44.9778, -93.2650, 44.9537, -93.0900)  # Minneapolis to St. Paul

if travel_times and "routes" in travel_times:
    route_info = travel_times["routes"][0]["summary"]
    travel_time_value = route_info.get("travelTimeInSeconds", 0) / 60  # Convert to minutes
    free_flow_time = route_info.get("trafficDelayInSeconds", 0) / 60  # Convert to minutes
    total_delay = travel_time_value - free_flow_time  # Calculate traffic delay

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🚗 Estimated Travel Time (minutes)", value=round(travel_time_value, 2))

    with col2:
        st.metric(label="⏳ Traffic Delay (minutes)", value=round(total_delay, 2))

    with col3:
        st.metric(label="🚦 Free Flow Travel Time (minutes)", value=round(free_flow_time, 2))

    # Check for alternative routes
    if len(travel_times["routes"]) > 1:
        alternative_route_time = travel_times["routes"][1]["summary"]["travelTimeInSeconds"] / 60
        st.info(f"🛤 Alternative Route Available: Estimated Time - {round(alternative_route_time, 2)} min")

else:
    st.warning("Travel time data unavailable")

st.divider()
# Geospatial Insights
st.subheader("Traffic Hotspots")
hotspot_data = get_traffic_flow(44.9778, -93.2650)  # Using traffic flow as a proxy for hotspots
if hotspot_data:
    hotspot_map = folium.Map(location=[44.9778, -93.2650], zoom_start=12)
    folium.Marker([44.9778, -93.2650], popup="Traffic Hotspot", icon=folium.Icon(color="red")).add_to(hotspot_map)
    folium_static(hotspot_map)
else:
    st.warning("No traffic hotspots detected")

st.divider()
# Live Alerts & Notifications
st.subheader("Live Alerts & Notifications")
alerts = get_traffic_incidents("44.90,-93.30,45.00,-93.00")  # Bounding box for Minneapolis-St. Paul
if alerts:
    for alert in alerts.get("incidents", []):
        st.error(f"🚨 {alert['type']}: {alert['description']} at {alert['location']['point']['latitude']}, {alert['location']['point']['longitude']}")
else:
    st.write("No Active Alerts Detected")
    st.success("No active alerts")
st.write("No Active Alerts Detected")
st.divider()
# Hourly & Daily Traffic Trends
st.subheader("📊 Real Time Hourly & Daily Traffic Trends")
hourly_df, daily_df = get_traffic_trends()
col1, col2 = st.columns(2)
with col1:
    fig_hourly = px.line(hourly_df, x="Hour", y="Traffic Volume", title="Hourly Traffic Trends")
    st.plotly_chart(fig_hourly, use_container_width=True)
with col2:
    fig_daily = px.bar(daily_df, x="Day", y="Traffic Volume", title="Daily Traffic Trends")
    st.plotly_chart(fig_daily, use_container_width=True)

st.divider()

st.header("EDA on Metro Interstate Traffic Volume dataset")
# Traffic Volume Analysis
st.subheader("📊 Traffic Volume Distribution")
fig1 = px.histogram(df, x="traffic_volume", nbins=50, title="Traffic Volume Distribution")
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# Weather vs. Traffic Volume
st.subheader("🌦️ Weather Impact on Traffic")
fig2 = px.scatter(df, x="temp", y="traffic_volume", color="weather_description",
                  title="Temperature vs. Traffic Volume")
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# Time-based Analysis
st.subheader("⏳ Hourly Traffic Trends")
df["hour"] = pd.to_datetime(df["date_time"]).dt.hour
# Create two columns
col1, col2 = st.columns(2)

# Line Chart
with col1:
    fig3 = px.line(df.groupby("hour")["traffic_volume"].mean().reset_index(),
                   x="hour", y="traffic_volume", title="Average Traffic Volume by Hour")
    st.plotly_chart(fig3, use_container_width=True)

# Bar Chart
with col2:
    fig_bar = px.bar(df.groupby("hour")["traffic_volume"].mean().reset_index(),
                     x="hour", y="traffic_volume", title="Average Traffic Volume by Hour")
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# Holiday Impact
st.subheader("🎉 Holiday vs. Regular Days Traffic")
fig4 = px.box(df, x="holiday", y="traffic_volume", title="Traffic Volume on Holidays vs. Regular Days")
st.plotly_chart(fig4, use_container_width=True)

fig_bar = px.bar(df.groupby("holiday")["traffic_volume"].mean().reset_index(),
                 x="holiday", y="traffic_volume", title="Average Traffic Volume on Holidays vs. Regular Days",
                 color="holiday")
st.plotly_chart(fig_bar, use_container_width=True)


st.divider()
# Second Row for Line Charts
col3, col4 = st.columns(2)

# Line Chart (Overall Holiday vs. Regular Trends)
with col3:
    fig_line = px.line(df.groupby(["holiday", "date_time"])["traffic_volume"].mean().reset_index(),
                       x="date_time", y="traffic_volume", color="holiday",
                       title="Traffic Volume Trends on Holidays vs. Regular Days")
    st.plotly_chart(fig_line, use_container_width=True, key="line_chart_overall")

# Holiday Selection & Filtered Line Chart
with col4:
    # Extract unique holidays
    unique_holidays = df["holiday"].unique()

    # Streamlit dropdown for filtering with a unique key
    selected_holiday = st.selectbox("Select a Holiday", unique_holidays, key="holiday_selectbox")

    # Filter the dataset
    df_filtered = df[df["holiday"] == selected_holiday]

    # Aggregate data by day
    df_filtered["date"] = pd.to_datetime(df_filtered["date_time"]).dt.date
    df_daily_filtered = df_filtered.groupby("date")["traffic_volume"].mean().reset_index()

    # Line chart for selected holiday
    fig_filtered = px.line(df_daily_filtered, x="date", y="traffic_volume",
                           title=f"Traffic Volume Trend on {selected_holiday}")
    st.plotly_chart(fig_filtered, use_container_width=True, key="line_chart_filtered")

st.divider()

df_weather = df.groupby("weather_main")["traffic_volume"].mean().reset_index()

# Sort by traffic volume (descending)
df_weather = df_weather.sort_values(by="traffic_volume", ascending=False)

# Horizontal bar chart
fig1 = px.bar(df_weather,
             x="traffic_volume",
             y="weather_main",
             orientation="h",  # Horizontal bars
             title="🚦 Traffic Volume in Different Weather Conditions",
             text_auto=True,  # Display values
             color="traffic_volume",
             color_continuous_scale="oranges")  # Match color theme

# Display in Streamlit
#st.subheader("🚦 Traffic Volume in Different Weather Conditions")
#st.plotly_chart(fig1, use_container_width=True)

#st.divider()

# Extract year from datetime
df["year"] = pd.to_datetime(df["date_time"]).dt.year

# Aggregate traffic volume by weather type and year
df_weather_year = df.groupby(["weather_main", "year"])["traffic_volume"].mean().reset_index()

# Create grouped bar chart
fig2 = px.bar(df_weather_year,
             x="weather_main",
             y="traffic_volume",
             color="year",  # Different colors for each year
             barmode="group",  # Grouped bars
             title="🚦 Traffic Volume by Weather Type and Year")

# Display in Streamlit
#st.subheader("🚦 Traffic Volume by Weather Type and Year")
#st.plotly_chart(fig2, use_container_width=True)

#st.divider()

# Display Side by Side
st.subheader('Weather Type Distribution')
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚦 Traffic Volume in Different Weather Conditions")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("🚦 Traffic Volume by Weather Type and Year")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

st.subheader("Holiday Traffic Volume")

# Filter only holidays
df_holiday = df[df["holiday"] != "None"]  # Remove non-holiday records

# Aggregate traffic volume for each holiday
df_holiday_grouped = df_holiday.groupby("holiday")["traffic_volume"].sum().reset_index()

# Convert to percentage
df_holiday_grouped["percentage"] = (df_holiday_grouped["traffic_volume"] / df_holiday_grouped["traffic_volume"].sum()) * 100

# Generate random positions for bubbles
np.random.seed(42)  # Ensures consistent positioning
df_holiday_grouped["x"] = np.random.uniform(-10, 10, df_holiday_grouped.shape[0])
df_holiday_grouped["y"] = np.random.uniform(-10, 10, df_holiday_grouped.shape[0])

# Bubble Chart
fig = px.scatter(df_holiday_grouped,
                 x='x',
                 y='y',
                 size="percentage",
                 text="holiday",
                 color="holiday",
                 title="🚦 Traffic Volume on National Holidays",
                 size_max=80,  # Control max bubble size
                 labels={"holiday": "Holiday", "percentage": "Traffic Share (%)"},
                 hover_data={"percentage": ":.2f"})  # Show percentage on hover

fig.update_traces(textposition='middle center')

# Hide axes
fig.update_xaxes(visible=False)
fig.update_yaxes(visible=False)

# Display in Streamlit
st.subheader("🚦 Traffic Volume on National Holidays")
st.plotly_chart(fig, use_container_width=True)

