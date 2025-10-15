import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def fetch_events(hours=6, keyword="conflict"):
    """Fetch recent global events from GDELT"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    query = (
        f"https://api.gdeltproject.org/api/v2/events/query?"
        f"query={keyword}&mode=EventOnly&format=json"
        f"&startdatetime={start_time.strftime('%Y%m%d%H%M%S')}"
        f"&enddatetime={end_time.strftime('%Y%m%d%H%M%S')}"
    )

    try:
        res = requests.get(query, timeout=10)
        data = res.json()
        if "events" not in data or not data["events"]:
            return []

        events = []
        for e in data["events"]:
            if not e.get("Actor1Geo_Lat") or not e.get("Actor1Geo_Long"):
                continue
            events.append({
                "title": e.get("Actor1Name", "Unknown Event"),
                "lat": float(e["Actor1Geo_Lat"]),
                "lon": float(e["Actor1Geo_Long"]),
                "location": e.get("Actor1Geo_FullName", "Unknown"),
                "date": e.get("SQLDATE")
            })
        return events[:50]
    except Exception:
        return []

def get_social_activity_curve(lat, lon):
    """Mock up social activity (bell curve)"""
    hours = np.arange(-24, 1)
    # simulate some abnormality
    peak_hour = np.random.randint(-8, -2)
    activity = np.exp(-0.5 * ((hours - peak_hour)/4)**2)
    activity = activity + np.random.rand(len(hours))*0.1
    df = pd.DataFrame({"Hours Before Incident": hours, "Activity Level": activity})
    return df.set_index("Hours Before Incident")
