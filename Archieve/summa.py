import streamlit as st
import numpy as np
import math
import random
from tensorflow.keras.saving import load_model
from sklearn.preprocessing import MinMaxScaler
import folium
from streamlit_folium import folium_static
import requests

# Load the trained LSTM model
model = load_model("MyLSTM_1.keras")

# Set Streamlit page config
st.set_page_config(page_title="Traffic Volume Prediction", page_icon="🚦", layout="wide")

# Initialize session state
if "last_prediction" not in st.session_state:
    st.session_state.last_prediction = None
if "last_map" not in st.session_state:
    st.session_state.last_map = None

# App Title
st.title("🚦 Traffic Volume Prediction App")
st.subheader("Between Minneapolis and St. Paul")

# TomTom API Request
minneapolis_coords = "44.9778,-93.2650"
st_paul_coords = "44.9537,-93.0900"

# TomTom API Key
TOMTOM_API_KEY = "3nVe88xLTd0ma3Yum5CG6uqB1HivAGfp"

# Function to get all possible routes from TomTom API
def get_routes():
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{minneapolis_coords}:{st_paul_coords}/json"
    params = {
        "key": TOMTOM_API_KEY,
        "traffic": "true",
        "maxAlternatives": 2,  # Get alternative routes
        "travelMode": "car"
    }
    response = requests.get(url, params=params).json()
    return response.get("routes", [])

# Function to calculate traffic volume
def calculate_traffic_volume(travel_time, traffic_delay):
    free_flow_time = travel_time - traffic_delay
    congestion_factor = traffic_delay / free_flow_time if free_flow_time > 0 else 0
    traffic_volume = congestion_factor * 1000  # Scaled estimate
    return round(traffic_volume, 2)

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
random.randint(500, 900)
past_hours = [max(day_of_hour - i, 0) for i in range(6)]
input_sequence = np.array([[
    math.sin(2 * math.pi * day / 31), math.cos(2 * math.pi * day / 31),
    math.sin(2 * math.pi * (year - 2012) / 13), math.cos(2 * math.pi * (year - 2012) / 13),
    temp, clouds_all, rain_1h, snow_1h, int(is_weekend), int(is_holiday),
    *weather_encoded, ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(day_of_week),
    month, year, hour, day, random.randint(100, 1900)
] for hour in past_hours])

st.write(input_sequence)

# Scale features
feature_min = np.array([-1, -1, -1, -1, -30, 0, 0, 0, 0, 0] + [0] * 11 + [0, 1, 2012, 0, 1, 1000])
feature_max = np.array([1, 1, 1, 1, 50, 100, 50, 50, 1, 1] + [1] * 11 + [6, 12, 2025, 23, 31, 2000])
scaler = MinMaxScaler()
scaler.fit(np.vstack([feature_min, feature_max]))
input_sequence = scaler.transform(input_sequence).reshape(1, 6, 27)
real_prediction = 0

# Predict Traffic Volume
if st.button("🚗 Predict Traffic Volume"):
    with st.spinner("🔄 Predicting Traffic Volume..."):
        prediction = model.predict(input_sequence)[0]
        real_prediction = int(prediction * (2000 - 1000) + 1000)
        print(real_prediction)
        st.session_state.last_prediction = real_prediction

        # Define route color
        route_color = "green" if real_prediction < 1200 else "orange" if real_prediction < 1700 else "red"


        # Fetch routes from TomTom API
        routes = get_routes()

        # Store traffic volume and route details
        traffic_data = []
        for i, route in enumerate(routes):
            travel_time = route["summary"]["travelTimeInSeconds"]
            traffic_delay = random.randint(50, 300)  # Simulated traffic delay in seconds
            distance_km = route['summary']['lengthInMeters'] // 1000
            traffic_volume = calculate_traffic_volume(travel_time, traffic_delay)

            traffic_data.append({
                "index": i,
                "travel_time": travel_time,
                "traffic_delay": traffic_delay,
                "traffic_volume": traffic_volume,
                "distance": distance_km,
                "route": route
            })

        # Determine if all routes have traffic volume below the threshold
        all_below_threshold = all(data["traffic_volume"] <= real_prediction for data in traffic_data)

        # If all routes are below the threshold, choose the most efficient route (least traffic volume)
        if all_below_threshold:
            best_route = min(traffic_data, key=lambda x: (x['distance'], x["traffic_volume"]))
            best_route_index = best_route["index"]
        else:
            best_route_index = None  # No specific best route, highlight all below threshold

        # Create a Folium map
        m = folium.Map(location=[44.9650, -93.1775], zoom_start=12)

        # Define colors
        default_colors = ["grey"]
        highlight_color = "green"  # Most efficient route color

        # Add routes to the map
        for data in traffic_data:
            polyline = [(point["latitude"], point["longitude"]) for point in data["route"]["legs"][0]["points"]]
            popup_text = (
                f"Route {data['index'] + 1}<br>"
                f"Travel Time: {data['travel_time'] // 60} min {data['travel_time'] % 60} sec<br>"
                f"Traffic Delay: {data['traffic_delay']} sec<br>"
                #f"Traffic Volume: {data['traffic_volume']}<br>"
                f"Distance: {data['distance']} km"
            )

            # If all routes are below threshold, highlight the most efficient route
            if all_below_threshold and data["index"] == best_route_index:
                color = highlight_color
            else:
                color = default_colors[data["index"] % len(default_colors)]

            folium.PolyLine(polyline, color=color, weight=5, popup=popup_text).add_to(m)

        # Add markers
        folium.Marker((44.9778, -93.2650), popup="Minneapolis", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker((44.9537, -93.0900), popup="St. Paul", icon=folium.Icon(color="red")).add_to(m)

        # Store the map in session state
        st.session_state.last_map = m

# Display Prediction
if st.session_state.last_prediction:
    st.markdown(
        f"""
               <div style="
                   background-color: white;
                   padding: 20px;
                   border-radius: 10px;
                   border-left: 10px solid {route_color};
                   text-align: center;">
                   <h3 style="color: black;">Predicted Traffic Volume</h3>
                   <h1 style="color: black;">{real_prediction} vehicles/hour</h1>
               </div>
               """,
        unsafe_allow_html=True
    )

# Display Map
if st.session_state.last_map:
    folium_static(st.session_state.last_map)
