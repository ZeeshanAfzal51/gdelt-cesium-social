import streamlit as st
import json
from utils import fetch_gdelt_events, get_social_activity_curve

st.set_page_config(page_title="🌍 GeoSentience", layout="wide")
st.title("🌍 GeoSentience — Social Activity vs Conflict Events")

# Sidebar filters
st.sidebar.header("Filter Events")
keyword = st.sidebar.text_input("Keyword (optional):", "")

with st.spinner("Fetching the latest global events..."):
    events = fetch_gdelt_events(keyword=keyword)

if not events:
    st.error("❌ No events found. Try again later.")
else:
    cesium_html = open("cesium_globe.html").read()
    st.components.v1.html(
        cesium_html.replace("EVENT_DATA_PLACEHOLDER", json.dumps(events)), height=700
    )

    selected = st.selectbox("Choose an event to analyze:", [e["title"] for e in events])
    event = next(e for e in events if e["title"] == selected)

    st.markdown(f"### 🗺️ {event['title']}")
    st.write(f"**Date:** {event['date']} | **Location:** {event['location']}")

    st.subheader("📈 Social Media Activity (24h before incident)")
    chart = get_social_activity_curve(event["lat"], event["lon"])
    st.line_chart(chart)

