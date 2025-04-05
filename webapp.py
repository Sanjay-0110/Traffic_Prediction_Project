import streamlit as st
import numpy as np
import pandas as pd
import math
import random
from tensorflow.keras.saving import load_model
from sklearn.preprocessing import MinMaxScaler
import folium
from streamlit_folium import folium_static
import requests
from streamlit_extras.metric_cards import style_metric_cards
from geopy.distance import geodesic
import networkx as nx

# Load the trained LSTM model
model = load_model("Models/MyLSTM_1.keras")

# Set Streamlit page config
st.set_page_config(page_title="Traffic Volume Prediction", page_icon="🚦", layout="wide")

st.sidebar.title("Navigation")
st.sidebar.page_link("webapp.py", label="🚗 Traffic Prediction")
st.sidebar.page_link("Pages/accurary.py", label="📊 Model Accuracy & Findings")
st.sidebar.page_link("Pages/Traffic_flow_dashboard.py", label="🔲 Dashboard Page")

# Custom CSS for styling
st.markdown("""
    <style>
    .stTitle {
        font-size: 32px !important;
        text-align: center;
        font-weight: bold;
        color: #FF5733;
    }
    .stText, .stSubheader {
        text-align: center;
    }
    .stSidebar .css-1d391kg {
        background-color: #f0f2f6;
    }
    .stButton>button {
        background-color: #FF5733;
        color: white;
        border-radius: 8px;
        font-size: 16px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Title of the web app
st.markdown("<h1 class='stTitle'>Traffic Volume Prediction App 🚦</h1>", unsafe_allow_html=True)
st.subheader("Between Minneapolis and St. Paul")
st.text("This app predicts Traffic Volume using a trained LSTM model between Minneapolis and St. Paul.")

# Sidebar Inputs
st.sidebar.header("📊 Enter Traffic Conditions")
day = st.sidebar.slider("📅 Day of the Month", 1, 31, 15)
month = st.sidebar.slider("📆 Month", 1, 12, 6)
year = st.sidebar.slider("🗓️ Year", 2012, 2025, 2023)
day_of_week = st.sidebar.selectbox("📌 Day of the Week",
                                   ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
day_of_hour = st.sidebar.slider("⏰ Hour of the Day", 0, 23, 12)
temp = st.sidebar.number_input("🌡️ Temperature (°C)", min_value=-30.0, max_value=50.0, value=20.0)
clouds_all = st.sidebar.slider("☁️ Cloud Cover (%)", 0, 100, 50)
rain_1h = st.sidebar.number_input("🌧️ Rainfall (mm in last 1h)", min_value=0.0, max_value=50.0, value=0.0)
snow_1h = st.sidebar.number_input("❄️ Snowfall (mm in last 1h)", min_value=0.0, max_value=50.0, value=0.0)
is_holiday = st.sidebar.selectbox("🎉 Holiday Status", ["No", "Yes"]) == "Yes"
is_weekend = day_of_week in ["Saturday", "Sunday"]

# Weather condition one-hot encoding
weather_conditions = ["Clear", "Clouds", "Drizzle", "Fog", "Haze", "Mist", "Rain", "Smoke", "Snow", "Squall",
                      "Thunderstorm"]
selected_weather = st.sidebar.selectbox("🌦️ Weather Condition", weather_conditions)
weather_encoded = [1 if selected_weather == w else 0 for w in weather_conditions]

# Generate past 6 hours for LSTM input
random_traffic_volume = random.randint(1000, 2000)
past_hours = [max(day_of_hour - i, 0) for i in range(6)]
input_sequence = np.array([[
    math.sin(2 * math.pi * day / 31), math.cos(2 * math.pi * day / 31),
    math.sin(2 * math.pi * (year - 2012) / 13), math.cos(2 * math.pi * (year - 2012) / 13),
    temp, clouds_all, rain_1h, snow_1h, int(is_weekend), int(is_holiday),
    *weather_encoded, ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(day_of_week),
    month, year, hour, day, random.randint(100, 2000)
] for hour in past_hours])

# Scale features
feature_min = np.array([-1, -1, -1, -1, -30, 0, 0, 0, 0, 0] + [0] * 11 + [0, 1, 2012, 0, 1, 1000])
feature_max = np.array([1, 1, 1, 1, 50, 100, 50, 50, 1, 1] + [1] * 11 + [6, 12, 2025, 23, 31, 2000])
scaler = MinMaxScaler()
scaler.fit(np.vstack([feature_min, feature_max]))
input_sequence = scaler.transform(input_sequence).reshape(1, 6, 27)
real_prediction = 0

# Predict Traffic Volume (New Update code)
if st.button("🚗 Predict Traffic Volume"):
    with st.spinner("🔄 Predicting Traffic Volume..."):
        prediction = model.predict(input_sequence)[0]
        real_prediction = int(prediction * (2000 - 1000) + 1000)

    # Define the color for styling but not for delta_color
    color = "green" if real_prediction < 1200 else "red"  # No orange allowed in delta_color

    #st.metric(label="Predicted Traffic Volume", value=f"{real_prediction} vehicles/hour", delta_color="normal")
    # Display Prediction with better visibility
    st.markdown(
        f"""
           <div style="
               background-color: white;
               padding: 20px;
               border-radius: 10px;
               border-left: 10px solid {color};
               text-align: center;">
               <h3 style="color: black;">Predicted Traffic Volume</h3>
               <h1 style="color: black;">{real_prediction} vehicles/hour</h1>
           </div>
           """,
        unsafe_allow_html=True
    )

    # Apply custom styling to metric cards
    style_metric_cards(border_left_color="green" if real_prediction < 1200 else "orange" if real_prediction < 1700 else "red")


# Map Visualization
minneapolis_coords = (44.9778, -93.2650)
st_paul_coords = (44.9537, -93.0900)
m = folium.Map(location=[44.9650, -93.1775], zoom_start=12)

''''# Fetch route from OSRM API
route_url = f"https://router.project-osrm.org/route/v1/driving/{minneapolis_coords[1]},{minneapolis_coords[0]};{st_paul_coords[1]},{st_paul_coords[0]}?overview=full&geometries=geojson"
response = requests.get(route_url)
data = response.json()

if 'routes' in data:
    route_coords = [(lat, lon) for lon, lat in data['routes'][0]['geometry']['coordinates']]
    route_color = "green" if real_prediction < 1200 else "orange" if real_prediction < 1700 else "red"
    folium.PolyLine(route_coords, color=route_color, weight=6, opacity=0.9).add_to(m)

folium.Marker(minneapolis_coords, popup="Minneapolis", icon=folium.Icon(color="green")).add_to(m)
folium.Marker(st_paul_coords, popup="St. Paul", icon=folium.Icon(color="red")).add_to(m)

st.title("🗺️ Traffic Route Visualization")
st.write("This map shows the route between Minneapolis and St. Paul with traffic color coding.")
folium_static(m)

st.divider()
'''
st.subheader("The Optimal Route to Travel")
# Define key locations along I-94 in Minnesota (latitude, longitude)
nodes = {
    "Minneapolis": (44.9778, -93.2650),
    "St. Paul": (44.9537, -93.0900),
    "Alt Route 1": (44.9700, -93.2000),  # Example alternative point
    "Alt Route 2": (44.9600, -93.1500),  # Example alternative point
}

# Define edges between the locations (representing I-94 highway segments and alternative routes)
main_route = [("Minneapolis", "St. Paul")]
alternative_route = [
    ("Minneapolis", "Alt Route 1"),
    ("Alt Route 1", "Alt Route 2"),
    ("Alt Route 2", "St. Paul"),
]

traffic_volume = real_prediction

# Choose route based on traffic volume
if traffic_volume < 1350:
    edges = main_route
    visible_nodes = {"Minneapolis", "St. Paul"}  # Hide alternative route markers
else:
    edges = alternative_route
    visible_nodes = set(nodes.keys())  # Show all markers

# Create a directed graph
G = nx.DiGraph()
for node, coords in nodes.items():
    G.add_node(node, pos=coords)
for edge in edges:
    G.add_edge(*edge)

# Create a Folium map centered around Minnesota
m = folium.Map(location=[44.96, -93.15], zoom_start=11)

# Add nodes to the map (only visible nodes)
for node, (lat, lon) in nodes.items():
    if node in visible_nodes:
        folium.Marker([lat, lon], popup=node, icon=folium.Icon(color='blue')).add_to(m)

# Add edges to the map with distances
for edge in edges:
    loc1, loc2 = edge
    coords1, coords2 = nodes[loc1], nodes[loc2]
    distance = geodesic(coords1, coords2).miles  # Calculate distance in miles
    color = "red" if edge in main_route else "green"
    folium.PolyLine([coords1, coords2], color=color, weight=5,
                    popup=f"Distance: {distance:.2f} miles").add_to(m)

# Display the map in Streamlit
st.title("Interstate 94 (I-94) Minneapolis-St. Paul Traffic-Based Route Selection")
folium_static(m)
