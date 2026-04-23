import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

# -----------------------------
# Mock data
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
            "rating": np.random.randint(1, 6),
            "likes": np.random.randint(0, 500)   # ⭐ NEW
        })
    return pd.DataFrame(data)

df = generate_posts()

# -----------------------------
# Session state
# -----------------------------
if "center_lat" not in st.session_state:
    st.session_state.center_lat = 38.7223
    st.session_state.center_lon = -9.1393
    st.session_state.center_set = False

# -----------------------------
# UI
# -----------------------------
st.title("📍 DartMap Prototype")

radius_km = st.slider("Radius (km)", 1, 100, 20)

st.write(f"📍 Center: {st.session_state.center_lat:.4f}, {st.session_state.center_lon:.4f}")

# -----------------------------
# Distance function
# -----------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

# -----------------------------
# Compute nearby ONLY after click
# -----------------------------
nearby = pd.DataFrame()

if st.session_state.center_set:
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
# MAP
# -----------------------------
m = folium.Map(
    location=[st.session_state.center_lat, st.session_state.center_lon],
    zoom_start=7
)

# center marker only after click
if st.session_state.center_set:
    folium.Marker(
        [st.session_state.center_lat, st.session_state.center_lon],
        tooltip="Center",
        icon=folium.Icon(color="blue")
    ).add_to(m)

    # ONLY nearby markers
    for _, row in nearby.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=6,
            color="red",
            fill=True,
            fill_opacity=0.7,

            # ⭐ HOVER INFO
            tooltip=folium.Tooltip(
                f"""
                <b>{row['city']}</b><br>
                ❤️ Likes: {row['likes']}<br>
                ⭐ Rating: {row['rating']}<br>
                📍 Distance: {row['distance']:.1f} km
                """
            ),

            popup=f"{row['review']}"
        ).add_to(m)
else:
    st.info("Click anywhere on the map to load nearby posts")

# -----------------------------
# CLICK HANDLING
# -----------------------------
map_data = st_folium(m, height=500, width=700)

if map_data and map_data.get("last_clicked"):
    st.session_state.center_lat = map_data["last_clicked"]["lat"]
    st.session_state.center_lon = map_data["last_clicked"]["lng"]
    st.session_state.center_set = True
    st.rerun()

# -----------------------------
# TABLE (only after click)
# -----------------------------
if st.session_state.center_set:
    st.subheader("🔥 Nearby Posts")
    st.dataframe(nearby[["city", "review", "rating", "distance"]])