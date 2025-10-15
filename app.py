import streamlit as st
import requests
import plotly.graph_objs as go
import streamlit.components.v1 as components
import datetime
import random
import json

# --- PAGE CONFIG ---
st.set_page_config(page_title="GeoSocial Intelligence", layout="wide")

# --- CUSTOM STYLING ---
st.markdown("""
<style>
body {
    background-color: #0E1117;
    color: #FAFAFA;
}
div.stButton > button {
    background-color: #262730;
    color: white;
    border-radius: 10px;
    border: 1px solid #444;
    padding: 0.5rem 1rem;
    width: 100%;
}
div.stButton > button:hover {
    background-color: #1A1B1F;
    color: #00FFAA;
}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1 style='text-align:center;'>🌍 GeoSocial Intelligence Dashboard</h1>", unsafe_allow_html=True)
st.write("Visualize global conflicts and study simulated social activity around them in 3D.")

# --- CESIUM GLOBE ---
with open("cesium_component.html", "r") as f:
    cesium_html = f.read()
iframe = components.html(cesium_html, height=600)

# --- GDELT FETCH FUNCTION ---
def fetch_gdelt_events():
    url = "https://api.gdeltproject.org/api/v2/events/geojson"
    params = {
        "query": "conflict OR protest OR crisis",
        "maxrecords": 20,
        "sort": "datedesc"
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        if "features" in data:
            events = []
            for feature in data["features"]:
                props = feature["properties"]
                coords = feature["geometry"]["coordinates"]
                events.append({
                    "title": props.get("EventBaseCode", "Unknown Event"),
                    "lat": coords[1],
                    "lon": coords[0],
                    "location": props.get("ActionGeo_FullName", "Unknown"),
                    "date": props.get("SQLDATE", "N/A"),
                    "tone": props.get("AvgTone", 0),
                    "url": props.get("SOURCEURL", "#")
                })
            return events
    return []

# --- FETCH EVENTS ---
st.subheader("🛰 Latest Global Events")
events = fetch_gdelt_events()

if not events:
    st.warning("⚠️ No recent events found. Try again later.")
else:
    st.success(f"Loaded {len(events)} recent events from GDELT.")

# --- SEND EVENTS TO CESIUM ---
if events:
    points = [{"lat": e["lat"], "lon": e["lon"], "title": e["title"], "location": e["location"]} for e in events]
    js_command = f"""
    <script>
        window.parent.postMessage({{"type": "addPoints", "points": {json.dumps(points)}}}, "*");
    </script>
    """
    components.html(js_command, height=0, width=0)

# --- DISPLAY EVENT BUTTONS ---
selected_event = None
cols = st.columns(2)
for i, event in enumerate(events):
    with cols[i % 2]:
        if st.button(f"📍 {event['location']} | Tone: {event['tone']}"):
            selected_event = event

# --- SIMULATED SOCIAL ACTIVITY CURVE ---
if selected_event:
    st.markdown(f"### 🌐 {selected_event['title']} in {selected_event['location']}")
    st.write(f"**Date:** {selected_event['date']} | **Tone:** {selected_event['tone']}")
    if selected_event['url'] != "#":
        st.markdown(f"[📰 Read More]({selected_event['url']})")

    # Simulated "social media activity" trend
    times = [datetime.datetime.now() - datetime.timedelta(hours=i) for i in range(24)][::-1]
    activity = [random.uniform(0.8, 1.2) for _ in range(24)]
    spike_index = random.randint(10, 20)
    for j in range(spike_index, 24):
        activity[j] += random.uniform(0.3, 0.9)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=activity, mode='lines+markers', name='Activity Index'))
    fig.update_layout(
        title="📈 Simulated Social Media Activity (24h Before Event)",
        xaxis_title="Time (hours before event)",
        yaxis_title="Activity Index",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)
