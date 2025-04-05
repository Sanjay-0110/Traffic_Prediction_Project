import networkx as nx
import folium
from streamlit_folium import folium_static
import streamlit as st
from geopy.distance import geodesic
import sys
import os
import requests
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import API_KEY

print(API_KEY)

# TomTom API Key (  Replace with your actual API key)
TOMTOM_API_KEY = API_KEY

# Define key locations along I-94 in Minnesota (latitude, longitude)
nodes = {
    "Minneapolis": (44.9778, -93.2650),
    "St. Paul": (44.9537, -93.0900),
    "Alt Route 1": (44.9700, -93.2000),  # Example alternative point
    "Alt Route 2": (44.9600, -93.1500),  # Example alternative point
}

# Function to get real-time traffic volume from TomTom API
def get_traffic_volume(origin, destination):
    origin_coords = f"{nodes[origin][0]},{nodes[origin][1]}"
    destination_coords = f"{nodes[destination][0]},{nodes[destination][1]}"

    url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin_coords}:{destination_coords}/json"
    params = {
        "key": TOMTOM_API_KEY,
        "traffic": "true",  # Use real-time traffic
        "computeTravelTimeFor": "all",
        "routeType": "fastest"
    }
    response = requests.get(url, params=params).json()

    if "routes" in response and response["routes"]:
        return response["routes"][0]["summary"].get("trafficDelayInSeconds", 0) // 60  # Convert to minutes
    return None

# Define edges with real-time traffic volume values
edge_traffic = {}
for edge in [("Minneapolis", "St. Paul"), ("Minneapolis", "Alt Route 1"),
             ("Alt Route 1", "Alt Route 2"), ("Alt Route 2", "St. Paul")]:
    traffic_volume = get_traffic_volume(edge[0], edge[1])
    print(edge[0], edge[1], traffic_volume)
    edge_traffic[edge] = traffic_volume if traffic_volume is not None else 9999  # Default high value if no data

# Create a directed graph
G = nx.DiGraph()
for node, coords in nodes.items():
    G.add_node(node, pos=coords)
for edge, traffic in edge_traffic.items():
    G.add_edge(edge[0], edge[1], weight=traffic)

# Find the route with the least total traffic volume
shortest_path = nx.shortest_path(G, source="Minneapolis", target="St. Paul", weight="weight")
shortest_path_edges = [(shortest_path[i], shortest_path[i+1]) for i in range(len(shortest_path)-1)]

# Create a Folium map centered around Minnesota
m = folium.Map(location=[44.96, -93.15], zoom_start=11)

# Add only the selected route nodes to the map
for node in shortest_path:
    lat, lon = nodes[node]
    folium.Marker([lat, lon], popup=node, icon=folium.Icon(color='blue')).add_to(m)

# Add only the selected route edges to the map
for edge in shortest_path_edges:
    loc1, loc2 = edge
    coords1, coords2 = nodes[loc1], nodes[loc2]
    distance = geodesic(coords1, coords2).miles  # Calculate distance in miles
    folium.PolyLine([coords1, coords2], color="red", weight=5,
                    popup=f"Distance: {distance:.2f} miles\nTraffic: {edge_traffic[edge]} min").add_to(m)

# Display the map in Streamlit
st.title("Interstate 94 (I-94) Minneapolis-St. Paul Traffic-Based Route Selection")
folium_static(m)
