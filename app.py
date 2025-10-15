import streamlit as st
import requests
import plotly.graph_objs as go
import streamlit.components.v1 as components
import random
import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="GeoSocial Intelligence", layout="wide")
st.markdown("<h1 style='text-align:center;'>🌍 GeoSocial Intelligence Dashboard</h1>", unsafe_allow_html=True)
st.write("Analyze social media activity patterns around real-world events in 3D.")

# --- LOAD CESIUM GLOBE ---
with open("cesium_component.html", "r") as f:
    html_string = f.read()
components.html(html_string, height=600)

# --- GDELT QUERY FUNCTION ---
def fetch_gdelt_events():
    url = "https://api.gdeltproject.org/api/v2/events/query"
    params = {
        "query": "conflict OR protest OR crisis",
        "format": "json",
        "maxrecords": 20,
        "sort": "datedesc"
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        if "events" in data:
            return data["events"]
    return []

events = fetch_gdelt_events()
if not events:
    st.warning("No recent events found. Try again later.")
else:
    st.success(f"Loaded {len(events)} recent events from GDELT.")

# --- DISPLAY EVENT TABLE ---
selected_event = None
for i, event in enumerate(events):
    if st.button(f"{event['EventRootCode']}: {event['EventBaseCode']} | {event['Actor1Name']} in {event['ActionGeo_FullName']}"):
        selected_event = event

# --- SIMULATE SOCIAL MEDIA ACTIVITY ---
if selected_event:
    st.markdown(f"### 📍 Selected Event: {selected_event['ActionGeo_FullName']}")
    st.write(f"**Summary:** {selected_event['SOURCEURL']}")
    st.write(f"**Date:** {selected_event['Day']} | **Tone:** {selected_event['AvgTone']}")

    # Generate fake “social activity index” (as we can’t access Twitter API)
    times = [datetime.datetime.now() - datetime.timedelta(hours=i) for i in range(24)][::-1]
    activity = [random.uniform(0.8, 1.2) for _ in range(24)]
    spike_index = random.randint(10, 20)
    for j in range(spike_index, 24):
        activity[j] += random.uniform(0.3, 0.9)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=activity, mode='lines+markers', name='Activity Index'))
    fig.update_layout(
        title="📈 Social Media Activity (Simulated 24h Before Event)",
        xaxis_title="Time (hours before event)",
        yaxis_title="Activity Index",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)
