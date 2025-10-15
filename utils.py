import requests, zipfile, io, pandas as pd, numpy as np
from datetime import datetime

def fetch_gdelt_events(keyword="protest"):
    """Fetch latest GDELT events from the CSV feed."""
    try:
        # Step 1: Get link to latest update
        txt = requests.get("http://data.gdeltproject.org/gdeltv2/lastupdate.txt").text.strip()
        latest_url = txt.split("\n")[2].split(" ")[-1]  # URL of the latest .zip
        res = requests.get(latest_url)
        z = zipfile.ZipFile(io.BytesIO(res.content))
        fname = z.namelist()[0]
        df = pd.read_csv(z.open(fname), sep="\t", header=None)

        # GDELT column map (from documentation)
        df.columns = [
            "GLOBALEVENTID","SQLDATE","MonthYear","Year","FractionDate",
            "Actor1Code","Actor1Name","Actor1CountryCode","Actor1KnownGroupCode",
            "Actor1EthnicCode","Actor1Religion1Code","Actor1Religion2Code",
            "Actor1Type1Code","Actor1Type2Code","Actor1Type3Code",
            "Actor2Code","Actor2Name","Actor2CountryCode","Actor2KnownGroupCode",
            "Actor2EthnicCode","Actor2Religion1Code","Actor2Religion2Code",
            "Actor2Type1Code","Actor2Type2Code","Actor2Type3Code",
            "IsRootEvent","EventCode","EventBaseCode","EventRootCode",
            "QuadClass","GoldsteinScale","NumMentions","NumSources","NumArticles",
            "AvgTone","Actor1Geo_Type","Actor1Geo_FullName","Actor1Geo_CountryCode",
            "Actor1Geo_ADM1Code","Actor1Geo_Lat","Actor1Geo_Long","Actor1Geo_FeatureID",
            "Actor2Geo_Type","Actor2Geo_FullName","Actor2Geo_CountryCode",
            "Actor2Geo_ADM1Code","Actor2Geo_Lat","Actor2Geo_Long","Actor2Geo_FeatureID",
            "ActionGeo_Type","ActionGeo_FullName","ActionGeo_CountryCode",
            "ActionGeo_ADM1Code","ActionGeo_Lat","ActionGeo_Long","ActionGeo_FeatureID",
            "DATEADDED","SOURCEURL"
        ]

        # Step 2: Filter conflict/protest events
        mask = df["EventRootCode"].astype(str).str.startswith(("14", "18", "19"))
        df = df[mask].dropna(subset=["ActionGeo_Lat", "ActionGeo_Long"])

        # Step 3: Filter by keyword
        df = df[df["Actor1Name"].astype(str).str.contains(keyword, case=False, na=False)]

        # Step 4: Build event list
        events = []
        for _, e in df.head(100).iterrows():
            events.append({
                "title": e["Actor1Name"] if pd.notna(e["Actor1Name"]) else "Unknown",
                "lat": float(e["ActionGeo_Lat"]),
                "lon": float(e["ActionGeo_Long"]),
                "location": e["ActionGeo_FullName"],
                "date": str(e["SQLDATE"]),
            })
        return events
    except Exception as ex:
        print("Error fetching GDELT data:", ex)
        return []

def get_social_activity_curve(lat, lon):
    """Simulate bell curve of social media activity."""
    hours = np.arange(-24, 1)
    peak_hour = np.random.randint(-8, -2)
    activity = np.exp(-0.5 * ((hours - peak_hour)/4)**2)
    activity = activity + np.random.rand(len(hours))*0.1
    df = pd.DataFrame({"Hours Before Incident": hours, "Activity Level": activity})
    return df.set_index("Hours Before Incident")

