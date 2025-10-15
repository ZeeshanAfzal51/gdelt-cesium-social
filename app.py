import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from urllib.parse import quote

# Page configuration
st.set_page_config(
    page_title="Global Conflict Monitor",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for aesthetic design
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }
    h1 {
        color: #ffffff;
        text-align: center;
        font-size: 3em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        padding: 20px;
    }
    h2, h3 {
        color: #e0e0e0;
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 15px 30px;
        font-size: 18px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.4);
    }
    .metric-card {
        background: rgba(255,255,255,0.1);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

# Cesium Ion API Token
CESIUM_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIyYmZjMGU3OS0wYjE5LTQwYzItYThmNC04Y2NlODZjYTA1ZjciLCJpZCI6MzUwNjQ1LCJpYXQiOjE3NjA1MDg3NDB9.m3BFiquwA4LnItl6sBbr-vr1RXhQGu65NMx6g5MiUGs"

@st.cache_data(ttl=3600)
def fetch_gdelt_events(days_back=7):
    """
    Fetch recent conflict events from GDELT using the GKG API
    """
    try:
        # Use GDELT 2.0 GKG API for recent events
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Format dates for GDELT (YYYYMMDDHHMMSS)
        start_str = start_date.strftime("%Y%m%d%H%M%S")
        end_str = end_date.strftime("%Y%m%d%H%M%S")
        
        # GDELT GKG API endpoint - search for conflict-related themes
        base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        
        # Search for conflict-related keywords
        keywords = ["conflict", "violence", "protest", "attack", "military", "war"]
        
        events_data = []
        
        for keyword in keywords[:2]:  # Limit to avoid rate limits
            query = f'"{keyword}"'
            params = {
                'query': query,
                'mode': 'artlist',
                'maxrecords': 50,
                'format': 'json',
                'startdatetime': start_str,
                'enddatetime': end_str
            }
            
            url = f"{base_url}?{'&'.join([f'{k}={quote(str(v))}' for k, v in params.items()])}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'articles' in data:
                        for article in data['articles'][:20]:  # Limit per keyword
                            if 'sourcelang' in article and article['sourcelang'] == 'English':
                                events_data.append({
                                    'title': article.get('title', 'Unknown'),
                                    'url': article.get('url', ''),
                                    'domain': article.get('domain', ''),
                                    'date': article.get('seendate', ''),
                                    'language': article.get('language', ''),
                                    'lat': None,
                                    'lon': None
                                })
                except:
                    continue
        
        if events_data:
            return pd.DataFrame(events_data)
        
        # Fallback to ACLED API if GDELT doesn't return results
        return fetch_acled_events()
        
    except Exception as e:
        st.error(f"GDELT Error: {str(e)}")
        return fetch_acled_events()

def fetch_acled_events():
    """
    Fetch conflict events from ACLED API (free tier)
    """
    try:
        # ACLED free API endpoint
        url = "https://api.acleddata.com/acled/read"
        
        # Get data from last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        params = {
            'limit': 100,
            'event_date': f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
            'event_date_where': 'BETWEEN'
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                events = []
                for event in data['data']:
                    events.append({
                        'title': event.get('event_type', 'Conflict Event'),
                        'location': event.get('location', 'Unknown'),
                        'country': event.get('country', 'Unknown'),
                        'date': event.get('event_date', ''),
                        'lat': float(event.get('latitude', 0)),
                        'lon': float(event.get('longitude', 0)),
                        'fatalities': event.get('fatalities', 0),
                        'notes': event.get('notes', '')[:200]
                    })
                
                return pd.DataFrame(events)
        
        # If ACLED also fails, return sample geopolitical hotspots
        return get_fallback_hotspots()
        
    except Exception as e:
        st.warning(f"ACLED Error: {str(e)}. Using fallback data.")
        return get_fallback_hotspots()

def get_fallback_hotspots():
    """
    Returns known geopolitical hotspots when APIs fail
    """
    hotspots = [
        {'title': 'Ukraine Conflict Zone', 'location': 'Eastern Ukraine', 'country': 'Ukraine', 
         'lat': 48.5, 'lon': 37.5, 'date': datetime.now().strftime('%Y-%m-%d'), 'fatalities': 'Unknown'},
        {'title': 'Gaza Strip Tensions', 'location': 'Gaza', 'country': 'Palestine', 
         'lat': 31.5, 'lon': 34.45, 'date': datetime.now().strftime('%Y-%m-%d'), 'fatalities': 'Unknown'},
        {'title': 'Myanmar Civil Unrest', 'location': 'Yangon', 'country': 'Myanmar', 
         'lat': 16.8, 'lon': 96.2, 'date': datetime.now().strftime('%Y-%m-%d'), 'fatalities': 'Unknown'},
        {'title': 'Syrian Border Region', 'location': 'Aleppo', 'country': 'Syria', 
         'lat': 36.2, 'lon': 37.1, 'date': datetime.now().strftime('%Y-%m-%d'), 'fatalities': 'Unknown'},
        {'title': 'Sahel Region Instability', 'location': 'Mali', 'country': 'Mali', 
         'lat': 17.5, 'lon': -4.0, 'date': datetime.now().strftime('%Y-%m-%d'), 'fatalities': 'Unknown'},
    ]
    
    return pd.DataFrame(hotspots)

def generate_social_media_bell_curve(event_lat, event_lon, event_title):
    """
    Generate a simulated bell curve of social media activity
    In a real implementation, this would fetch actual social media data
    """
    import numpy as np
    
    # Time points (24 hours before event)
    hours = np.linspace(-24, 0, 100)
    
    # Generate bell curve with some randomness
    # Peak activity happens 2-4 hours before the event
    peak_time = np.random.uniform(-4, -2)
    std_dev = np.random.uniform(2, 4)
    
    # Normal distribution centered at peak_time
    activity = 100 * np.exp(-0.5 * ((hours - peak_time) / std_dev) ** 2)
    
    # Add baseline noise
    baseline = np.random.uniform(10, 30)
    activity = activity + baseline + np.random.normal(0, 5, len(hours))
    
    # Ensure non-negative
    activity = np.maximum(activity, 0)
    
    # Create plot
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hours,
        y=activity,
        mode='lines',
        name='Social Media Activity',
        line=dict(color='#667eea', width=3),
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.3)'
    ))
    
    # Add vertical line at event time
    fig.add_vline(x=0, line_dash="dash", line_color="red", 
                  annotation_text="Event Time", annotation_position="top")
    
    # Mark peak activity
    peak_idx = np.argmax(activity)
    fig.add_trace(go.Scatter(
        x=[hours[peak_idx]],
        y=[activity[peak_idx]],
        mode='markers',
        name='Peak Activity',
        marker=dict(color='red', size=12, symbol='star')
    ))
    
    fig.update_layout(
        title=f'Social Media Activity Pattern: {event_title}',
        xaxis_title='Hours Before Event',
        yaxis_title='Activity Index',
        plot_bgcolor='rgba(0,0,0,0.1)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=12),
        height=400,
        showlegend=True,
        hovermode='x unified'
    )
    
    return fig

def create_cesium_html(events_df):
    """
    Create HTML page with Cesium globe and event markers
    """
    
    # Prepare event markers data
    events_json = []
    for idx, row in events_df.iterrows():
        if pd.notna(row['lat']) and pd.notna(row['lon']):
            events_json.append({
                'id': idx,
                'title': row['title'],
                'lat': float(row['lat']),
                'lon': float(row['lon']),
                'location': row.get('location', 'Unknown'),
                'date': str(row.get('date', '')),
                'fatalities': str(row.get('fatalities', 'Unknown'))
            })
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <script src="https://cesium.com/downloads/cesiumjs/releases/1.95/Build/Cesium/Cesium.js"></script>
        <link href="https://cesium.com/downloads/cesiumjs/releases/1.95/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
        <style>
            html, body, #cesiumContainer {{
                width: 100%;
                height: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden;
                background: #000;
            }}
            .event-tooltip {{
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-family: Arial, sans-serif;
            }}
        </style>
    </head>
    <body>
        <div id="cesiumContainer"></div>
        <script>
            Cesium.Ion.defaultAccessToken = '{CESIUM_TOKEN}';
            
            const viewer = new Cesium.Viewer('cesiumContainer', {{
                terrainProvider: Cesium.createWorldTerrain(),
                baseLayerPicker: true,
                animation: false,
                timeline: false,
                geocoder: false,
                homeButton: true,
                navigationHelpButton: false,
                sceneModePicker: true,
                imageryProvider: new Cesium.IonImageryProvider({{ assetId: 3954 }})
            }});
            
            viewer.scene.globe.enableLighting = true;
            
            const events = {json.dumps(events_json)};
            
            events.forEach(event => {{
                const entity = viewer.entities.add({{
                    position: Cesium.Cartesian3.fromDegrees(event.lon, event.lat),
                    point: {{
                        pixelSize: 15,
                        color: Cesium.Color.RED.withAlpha(0.8),
                        outlineColor: Cesium.Color.WHITE,
                        outlineWidth: 2,
                        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
                    }},
                    label: {{
                        text: event.title,
                        font: '14pt sans-serif',
                        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                        outlineWidth: 2,
                        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                        pixelOffset: new Cesium.Cartesian2(0, -20),
                        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    }},
                    description: `
                        <div class="event-tooltip">
                            <h3>${{event.title}}</h3>
                            <p><strong>Location:</strong> ${{event.location}}</p>
                            <p><strong>Date:</strong> ${{event.date}}</p>
                            <p><strong>Fatalities:</strong> ${{event.fatalities}}</p>
                            <p><strong>Coordinates:</strong> ${{event.lat.toFixed(2)}}, ${{event.lon.toFixed(2)}}</p>
                        </div>
                    `,
                    eventId: event.id
                }});
            }});
            
            // Store selected event in parent window
            viewer.selectedEntityChanged.addEventListener(function(entity) {{
                if (entity && entity.eventId !== undefined) {{
                    window.parent.postMessage({{
                        type: 'eventSelected',
                        eventId: entity.eventId
                    }}, '*');
                }}
            }});
            
            // Fly to a good starting view
            viewer.camera.flyTo({{
                destination: Cesium.Cartesian3.fromDegrees(20, 30, 15000000)
            }});
        </script>
    </body>
    </html>
    """
    
    return html_content

# Main Application
def main():
    st.markdown("<h1>🌍 Global Conflict Monitor & Social Media Analysis</h1>", unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Globe_icon.svg/240px-Globe_icon.svg.png", width=150)
        st.markdown("## 📊 Controls")
        
        days_back = st.slider("Days of data to fetch", 1, 30, 7)
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### About")
        st.info("""
        This application visualizes global conflict events in real-time using:
        - **Cesium Ion**: 3D globe visualization
        - **GDELT/ACLED**: Conflict event data
        - **Social Media Analysis**: Activity patterns before events
        """)
    
    # Fetch events
    with st.spinner("🔍 Fetching real-time conflict data..."):
        events_df = fetch_gdelt_events(days_back)
    
    if events_df is not None and not events_df.empty:
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Events", len(events_df))
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            unique_countries = events_df['country'].nunique() if 'country' in events_df.columns else 0
            st.metric("Countries Affected", unique_countries)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            total_fatalities = events_df['fatalities'].sum() if 'fatalities' in events_df.columns else 0
            st.metric("Total Fatalities", total_fatalities if pd.notna(total_fatalities) else "N/A")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Create two columns for globe and details
        col_globe, col_details = st.columns([2, 1])
        
        with col_globe:
            st.markdown("### 🌐 Interactive 3D Globe")
            
            # Create and display Cesium globe
            cesium_html = create_cesium_html(events_df)
            st.components.v1.html(cesium_html, height=600, scrolling=False)
        
        with col_details:
            st.markdown("### 📋 Recent Events")
            
            # Display event list
            for idx, row in events_df.head(10).iterrows():
                with st.expander(f"📍 {row['title'][:50]}..."):
                    st.write(f"**Location:** {row.get('location', 'Unknown')}")
                    st.write(f"**Date:** {row.get('date', 'N/A')}")
                    if 'fatalities' in row:
                        st.write(f"**Fatalities:** {row['fatalities']}")
                    
                    if st.button(f"Analyze Social Media", key=f"btn_{idx}"):
                        st.session_state['selected_event'] = idx
        
        # Social Media Analysis Section
        if 'selected_event' in st.session_state:
            st.markdown("---")
            st.markdown("## 📈 Social Media Activity Analysis")
            
            selected_idx = st.session_state['selected_event']
            if selected_idx < len(events_df):
                event = events_df.iloc[selected_idx]
                
                st.markdown(f"### Analyzing: {event['title']}")
                
                # Generate and display bell curve
                fig = generate_social_media_bell_curve(
                    event.get('lat', 0),
                    event.get('lon', 0),
                    event['title']
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Analysis insights
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown("#### 🔍 Key Insights")
                    st.write("- Peak activity detected 2-4 hours before event")
                    st.write("- Activity spike indicates heightened social awareness")
                    st.write("- Pattern suggests predictive potential")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown("#### ⚠️ Note")
                    st.warning("""
                    This is a simulated analysis. In production:
                    - Connect to Twitter/X API
                    - Use Reddit/News APIs
                    - Implement ML models for anomaly detection
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        st.error("❌ No conflict events found. Please try adjusting the date range or check your internet connection.")
        st.info("💡 The application is attempting to fetch data from multiple sources. Please wait and try refreshing.")

if __name__ == "__main__":
    main()
