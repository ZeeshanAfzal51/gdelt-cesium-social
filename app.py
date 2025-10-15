import streamlit as st
import requests
import json
from datetime import datetime, timedelta
from utils import fetch_events, get_social_activity_curve

st.set_page_config(page_title="GeoSentience", layout="wide")

st.title("🌍 GeoSentience — Social Activity vs Conflict Events")

# Sidebar options
st.sidebar.header("Filter Events")
hours = st.sidebar.slider("Look back (hours):", 1, 48, 6)
keyword = st.sidebar.text_input("Keyword (optional):", "conflict")

# Fetch events
with st.spinner("Fetching latest global events..."):
    events = fetch_events(hours=hours, keyword=keyword)

if not events:
    st.warning("⚠️ No recent events found. Expanding time window...")
    events = fetch_events(hours=24, keyword=keyword)

if not events:
    st.error("❌ Still no events found. Try again later.")
else:
    # Display Cesium globe
    cesium_html = open("cesium_globe.html").read()
    st.components.v1.html(cesium_html.replace("EVENT_DATA_PLACEHOLDER", json.dumps(events)), height=700)

    # Sidebar event picker
    selected = st.selectbox("Choose an event to analyze:", [e['title'] for e in events])
    event = next(e for e in events if e['title'] == selected)

    st.markdown(f"### 🗺️ {event['title']}")
    st.write(f"**Date:** {event['date']} | **Location:** {event['location']}")

    # Social activity simulation
    st.subheader("📈 Social Media Activity (24h before incident)")
    chart = get_social_activity_curve(event['lat'], event['lon'])
    st.line_chart(chart)

