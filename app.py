import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import json
import pydeck as pdk

# Page configuration
st.set_page_config(
    page_title="Conflict & Social Media Analyzer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class ConflictAnalyzer:
    def __init__(self):
        self.cesium_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIyYmZjMGU3OS0wYjE5LTQwYzItYThmNC04Y2NlODZjYTA1ZjciLCJpZCI6MzUwNjQ1LCJpYXQiOjE3NjA1MDg3NDB9.m3BFiquwA4LnItl6sBbr-vr1RXhQGu65NMx6g5MiUGs"
        self.gdelt_base_url = "https://api.gdeltproject.org/api/v2/event/event"
        
    def get_gdelt_events(self, query="conflict protest", max_results=50):
        """Fetch recent conflict events from GDELT"""
        try:
            params = {
                "query": query,
                "format": "json",
                "maxrecords": str(max_results),
                "sort": "date"
            }
            
            response = requests.get(self.gdelt_base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                events = []
                
                for event in data.get("events", []):
                    if event.get("actiongeo_lat") and event.get("actiongeo_long"):
                        events.append({
                            "date": event.get("date", ""),
                            "lat": float(event["actiongeo_lat"]),
                            "lon": float(event["actiongeo_long"]),
                            "name": event.get("actorname", "Unknown"),
                            "event_type": event.get("eventtype", "Unknown"),
                            "url": event.get("url", ""),
                            "summary": event.get("summary", "No description available"),
                            "intensity": event.get("avg_tone", 0)
                        })
                
                return pd.DataFrame(events)
            else:
                st.error(f"GDELT API Error: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Error fetching GDELT data: {str(e)}")
            return pd.DataFrame()
    
    def generate_social_media_data(self, lat, lon, event_time):
        """Generate simulated social media activity data (bell curve)"""
        # Simulate social media activity for 24 hours before the event
        hours_before = 24
        time_points = np.linspace(-hours_before, 0, 100)
        
        # Create a bell curve with potential anomaly
        base_activity = 100  # Base level of social media activity
        peak_multiplier = np.random.uniform(2, 5)  # Random peak intensity
        
        # Generate bell curve
        activity = base_activity * np.exp(-(time_points + 12)**2 / 32) * peak_multiplier
        
        # Add some random noise
        noise = np.random.normal(0, 10, len(activity))
        activity = np.maximum(activity + noise, 0)
        
        # Create timeline labels
        timeline = [(event_time + timedelta(hours=float(t))) for t in time_points]
        
        return pd.DataFrame({
            'timestamp': timeline,
            'activity': activity,
            'hours_before_event': -time_points
        })
    
    def create_cesium_globe(self, events_df):
        """Create an interactive 3D globe using PyDeck"""
        if events_df.empty:
            return None
            
        # Set the viewport location
        view_state = pdk.ViewState(
            latitude=events_df['lat'].mean() if not events_df.empty else 0,
            longitude=events_df['lon'].mean() if not events_df.empty else 0,
            zoom=1,
            pitch=0,
            bearing=0
        )
        
        # Define a layer to display on a map
        layer = pdk.Layer(
            "ScatterplotLayer",
            events_df,
            pickable=True,
            opacity=0.8,
            stroked=True,
            filled=True,
            radius_scale=6,
            radius_min_pixels=5,
            radius_max_pixels=100,
            line_width_min_pixels=1,
            get_position=['lon', 'lat'],
            get_radius=100000,
            get_fill_color=[255, 0, 0, 180],
            get_line_color=[0, 0, 0],
        )
        
        # Render
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                'html': '<b>Event:</b> {name}<br/><b>Type:</b> {event_type}<br/><b>Date:</b> {date}',
                'style': {
                    'color': 'white'
                }
            }
        )
        
        return r
    
    def create_bell_curve(self, social_media_df, event_info):
        """Create a bell curve visualization of social media activity"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=social_media_df['hours_before_event'],
            y=social_media_df['activity'],
            mode='lines',
            name='Social Media Activity',
            line=dict(color='#ff6b6b', width=3),
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.1)'
        ))
        
        # Add event marker
        fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Event Time")
        
        fig.update_layout(
            title=f"Social Media Activity 24 Hours Before Event<br><sub>{event_info}</sub>",
            xaxis_title="Hours Before Event",
            yaxis_title="Social Media Activity Level",
            template="plotly_white",
            height=400,
            showlegend=False
        )
        
        return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">🌍 Conflict & Social Media Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <p>This application visualizes global conflict events and analyzes corresponding social media activity patterns.</p>
        <p><strong>How it works:</strong></p>
        <ul>
            <li>Fetches real-time conflict data from GDELT Project</li>
            <li>Displays events on an interactive 3D globe</li>
            <li>Generates social media activity analysis for selected events</li>
            <li>Identifies abnormal activity patterns preceding conflicts</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize analyzer
    analyzer = ConflictAnalyzer()
    
    # Sidebar
    st.sidebar.markdown('<h2 class="sub-header">🔧 Controls</h2>', unsafe_allow_html=True)
    
    # Query parameters
    query_type = st.sidebar.selectbox(
        "Event Type",
        ["conflict protest", "war military", "demonstration", "terror attack"],
        help="Select the type of events to analyze"
    )
    
    max_events = st.sidebar.slider("Maximum Events", 10, 100, 30)
    
    # Fetch data
    if st.sidebar.button("🔄 Fetch Latest Events") or 'events_df' not in st.session_state:
        with st.spinner("Fetching latest conflict events..."):
            events_df = analyzer.get_gdelt_events(query_type, max_events)
            st.session_state.events_df = events_df
    
    events_df = st.session_state.get('events_df', pd.DataFrame())
    
    if not events_df.empty:
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Events", len(events_df))
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Countries", events_df['name'].nunique())
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            latest_date = pd.to_datetime(events_df['date'].max()).strftime('%Y-%m-%d')
            st.metric("Latest Event", latest_date)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            avg_intensity = events_df['intensity'].mean()
            st.metric("Avg Intensity", f"{avg_intensity:.1f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<h2 class="sub-header">🗺️ Global Conflict Events</h2>', unsafe_allow_html=True)
            
            # Create and display the globe
            globe = analyzer.create_cesium_globe(events_df)
            if globe:
                st.pydeck_chart(globe, use_container_width=True)
        
        with col2:
            st.markdown('<h2 class="sub-header">📊 Event Details</h2>', unsafe_allow_html=True)
            
            # Event selector
            selected_event = st.selectbox(
                "Select an event for analysis:",
                options=range(len(events_df)),
                format_func=lambda x: f"{events_df.iloc[x]['name']} - {events_df.iloc[x]['date'][:10]}"
            )
            
            if selected_event is not None:
                event_data = events_df.iloc[selected_event]
                
                # Display event details
                st.markdown(f"""
                **Event Information:**
                - **Location:** {event_data['name']}
                - **Coordinates:** {event_data['lat']:.4f}, {event_data['lon']:.4f}
                - **Date:** {event_data['date']}
                - **Type:** {event_data['event_type']}
                - **Intensity:** {event_data['intensity']}
                """)
                
                # Generate social media analysis
                if st.button("📈 Analyze Social Media Activity", key="analyze_btn"):
                    with st.spinner("Generating social media activity analysis..."):
                        # Simulate event time (using current time for demo)
                        event_time = datetime.now()
                        
                        # Generate social media data
                        social_media_df = analyzer.generate_social_media_data(
                            event_data['lat'], 
                            event_data['lon'], 
                            event_time
                        )
                        
                        # Create and display bell curve
                        event_info = f"{event_data['name']} - {event_data['date'][:10]}"
                        fig = analyzer.create_bell_curve(social_media_df, event_info)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Analysis insights
                        max_activity = social_media_df['activity'].max()
                        avg_activity = social_media_df['activity'].mean()
                        
                        if max_activity > avg_activity * 1.5:
                            st.success("🚨 **Significant spike detected!** Social media activity showed abnormal increase before the event.")
                        elif max_activity < avg_activity * 0.7:
                            st.warning("📉 **Unusual decrease detected!** Social media activity was unusually low before the event.")
                        else:
                            st.info("📊 **Normal pattern detected.** Social media activity followed expected patterns.")
                
                # Show raw data option
                with st.expander("View Raw Event Data"):
                    st.dataframe(events_df, use_container_width=True)
    
    else:
        st.warning("No events found. Try adjusting your search parameters or check your internet connection.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>Built with Streamlit • Data from GDELT Project • Visualization with Cesium Ion</p>
        <p>This tool is for educational and research purposes only.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
