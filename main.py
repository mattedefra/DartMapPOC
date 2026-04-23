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
            "likes": np.random.randint(0, 500)
        })
    return pd.DataFrame(data)

# -----------------------------
# SESSION STATE (acts like DB)
# -----------------------------
if "df" not in st.session_state:
    st.session_state.df = generate_posts()

df = st.session_state.df

if "center_lat" not in st.session_state:
    st.session_state.center_lat = 38.7223
    st.session_state.center_lon = -9.1393
    st.session_state.center_set = False

# store clicked position for posting
if "pending_lat" not in st.session_state:
    st.session_state.pending_lat = None
    st.session_state.pending_lon = None

# -----------------------------
# UI
# -----------------------------
st.title("📍 DartMap Prototype (with Posting)")

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
# MAP
# -----------------------------
m = folium.Map(
    location=[st.session_state.center_lat, st.session_state.center_lon],
    zoom_start=7
)

# show center
if st.session_state.center_set:
    folium.Marker(
        [st.session_state.center_lat, st.session_state.center_lon],
        tooltip="Center",
        icon=folium.Icon(color="blue")
    ).add_to(m)

# compute nearby only if active
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

    # draw ONLY nearby
    for _, row in nearby.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=6,
            color="red",
            fill=True,
            fill_opacity=0.7,
            tooltip=folium.Tooltip(
                f"""
                <b>{row['city']}</b><br>
                ❤️ Likes: {row['likes']}<br>
                ⭐ Rating: {row['rating']}<br>
                📍 {row['distance']:.1f} km
                """
            ),
            popup=row["review"]
        ).add_to(m)
else:
    st.info("Click on the map to set a location and unlock posts")

# -----------------------------
# CLICK HANDLING
# -----------------------------
map_data = st_folium(m, height=500, width=700)

if map_data and map_data.get("last_clicked"):
    st.session_state.center_lat = map_data["last_clicked"]["lat"]
    st.session_state.center_lon = map_data["last_clicked"]["lng"]
    st.session_state.center_set = True

    # store for posting
    st.session_state.pending_lat = st.session_state.center_lat
    st.session_state.pending_lon = st.session_state.center_lon

    st.rerun()

# -----------------------------
# POSTING UI (UNDER MAP)
# -----------------------------
st.subheader("✍️ Add Your Experience")

if st.session_state.pending_lat is None:
    st.warning("Click on the map first to choose a location")
else:
    review = st.text_area("Your experience")
    rating = st.slider("Rating", 1, 5, 3)

    if st.button("Publish"):
        new_post = {
            "post_id": len(st.session_state.df),
            "city": "User Post",
            "lat": st.session_state.pending_lat,
            "lon": st.session_state.pending_lon,
            "review": review,
            "rating": rating,
            "likes": 0
        }

        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([new_post])],
            ignore_index=True
        )

        st.success("Posted successfully! 🎉")
        st.rerun()

# -----------------------------
# TABLE
# -----------------------------
if st.session_state.center_set:
    st.subheader("🔥 Nearby Posts")
    st.dataframe(nearby[["city", "review", "rating", "distance"]])