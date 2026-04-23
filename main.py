import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

# -----------------------------
# Mock data (Portugal-focused)
# -----------------------------
np.random.seed(42)

PLACES = [
    ("Lisbon", 38.7223, -9.1393),
    ("Porto", 41.1579, -8.6291),
    ("Coimbra", 40.2033, -8.4103),
    ("Faro", 37.0194, -7.9304),
    ("Braga", 41.5454, -8.4265),
]

def generate_posts(n=30):
    data = []
    for i in range(n):
        city, lat, lon = PLACES[np.random.randint(0, len(PLACES))]

        lat += np.random.normal(0, 0.05)
        lon += np.random.normal(0, 0.05)

        data.append({
            "post_id": i,
            "city": city,
            "lat": lat,
            "lon": lon,
            "review": f"Experience in {city} #{i}",
            "rating": np.random.randint(1, 6)
        })

    return pd.DataFrame(data)

df = generate_posts()

# -----------------------------
# Session state (center point)
# -----------------------------
if "center_lat" not in st.session_state:
    st.session_state.center_lat = 38.7223  # Lisbon default
    st.session_state.center_lon = -9.1393

# -----------------------------
# UI
# -----------------------------
st.title("📍 DartMap Prototype (Click to Set Center)")

radius_km = st.slider("Radius (km)", 1, 100, 20)

st.write(
    f"📍 Current center: "
    f"{st.session_state.center_lat:.4f}, {st.session_state.center_lon:.4f}"
)

# -----------------------------
# Haversine distance
# -----------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

# -----------------------------
# MAP (Folium)
# -----------------------------
m = folium.Map(
    location=[st.session_state.center_lat, st.session_state.center_lon],
    zoom_start=7
)

# center marker
folium.Marker(
    [st.session_state.center_lat, st.session_state.center_lon],
    tooltip="Center",
    icon=folium.Icon(color="blue")
).add_to(m)

# posts markers
for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=5,
        color="red",
        fill=True,
        fill_opacity=0.6,
        popup=f"{row['city']} | Rating: {row['rating']}"
    ).add_to(m)

# CLICK HANDLING
map_data = st_folium(m, height=500, width=700)

if map_data and map_data.get("last_clicked"):
    st.session_state.center_lat = map_data["last_clicked"]["lat"]
    st.session_state.center_lon = map_data["last_clicked"]["lng"]
    st.rerun()

# -----------------------------
# Filtering
# -----------------------------
df["distance"] = df.apply(
    lambda r: haversine(
        st.session_state.center_lat,
        st.session_state.center_lon,
        r["lat"],
        r["lon"]
    ),
    axis=1
)

nearby = df[df["distance"] <= radius_km]

# -----------------------------
# Results
# -----------------------------
st.subheader("🔥 Nearby Posts")
st.dataframe(nearby[["city", "review", "rating", "distance"]])