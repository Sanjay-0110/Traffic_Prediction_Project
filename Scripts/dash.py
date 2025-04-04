import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static
import datetime
import time

# TomTom API Key
API_KEY = "rPL3ekmb1C0IxwN1fkVaOyrQ85DZgk4p"

# Function to get live traffic flow
def get_traffic_flow(lat, lon):
    url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    params = {"key": API_KEY, "point": f"{lat},{lon}"}
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

# Streamlit page setup
st.set_page_config(page_title="Minneapolis-St. Paul Traffic Dashboard", layout="wide")
st.title("🚦 Minneapolis-St. Paul Traffic Dashboard")

# Date & Real-Time Display
col1, col2 = st.columns(2)
with col1:
    st.subheader("📅 Date")
    st.info(datetime.datetime.now().strftime("%A, %B %d, %Y"))

with col2:
    st.subheader("⏰ Real-Time")
    time_placeholder = st.empty()

while True:
    time_placeholder.info(get_current_time())
    time.sleep(1)  # Update every second

# Sidebar: User Inputs
st.sidebar.header("Settings")
refresh_rate = st.sidebar.slider("Auto-refresh rate (seconds)", 10, 300, 60)

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

# Geospatial Insights
st.subheader("Traffic Hotspots")
hotspot_data = get_traffic_flow(44.9778, -93.2650)  # Using traffic flow as a proxy for hotspots
if hotspot_data:
    hotspot_map = folium.Map(location=[44.9778, -93.2650], zoom_start=12)
    folium.Marker([44.9778, -93.2650], popup="Traffic Hotspot", icon=folium.Icon(color="red")).add_to(hotspot_map)
    folium_static(hotspot_map)
else:
    st.warning("No traffic hotspots detected")

# Live Alerts & Notifications
st.subheader("Live Alerts & Notifications")
alerts = get_traffic_incidents("44.90,-93.30,45.00,-93.00")  # Bounding box for Minneapolis-St. Paul
if alerts:
    for alert in alerts.get("incidents", []):
        st.error(f"🚨 {alert['type']}: {alert['description']} at {alert['location']['point']['latitude']}, {alert['location']['point']['longitude']}")
else:
    st.success("No active alerts")

# Hourly & Daily Traffic Trends
st.subheader("📊 Hourly & Daily Traffic Trends")
hourly_df, daily_df = get_traffic_trends()
col1, col2 = st.columns(2)
with col1:
    fig_hourly = px.line(hourly_df, x="Hour", y="Traffic Volume", title="Hourly Traffic Trends")
    st.plotly_chart(fig_hourly, use_container_width=True)
with col2:
    fig_daily = px.bar(daily_df, x="Day", y="Traffic Volume", title="Daily Traffic Trends")
    st.plotly_chart(fig_daily, use_container_width=True)

# Auto-refresh logic (simulated)
st.sidebar.text(f"Dashboard updates every {refresh_rate} seconds")