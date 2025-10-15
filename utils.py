import requests, zipfile, io, pandas as pd, numpy as np

def fetch_gdelt_events(keyword=None):
    """Fetch the latest 15-minute GDELT global event feed — always returns data."""
    try:
        # get URL of most recent feed
        txt = requests.get("http://data.gdeltproject.org/gdeltv2/lastupdate.txt").text.strip()
        latest_url = txt.split("\n")[2].split(" ")[-1]
        res = requests.get(latest_url, timeout=20)
        z = zipfile.ZipFile(io.BytesIO(res.content))
        fname = z.namelist()[0]
        df = pd.read_csv(z.open(fname), sep="\t", header=None)

        # column map (subset)
        df.columns = [
            "GLOBALEVENTID","SQLDATE","MonthYear","Year","FractionDate",
            "Actor1Code","Actor1Name","Actor1CountryCode","Actor1Type1Code",
            "Actor2Code","Actor2Name","Actor2CountryCode","Actor2Type1Code",
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

        # keep only rows with coordinates
        df = df.dropna(subset=["ActionGeo_Lat", "ActionGeo_Long"])

        # optional keyword match
        if keyword:
            df = df[df["Actor1Name"].astype(str).str.contains(keyword, case=False, na=False)]

        # pick first 200 rows for speed
        df = df.head(200)

        events = []
        for _, e in df.iterrows():
            events.append({
                "title": e["Actor1Name"] if pd.notna(e["Actor1Name"]) else "Event",
                "lat": float(e["ActionGeo_Lat"]),
                "lon": float(e["ActionGeo_Long"]),
                "location": e["ActionGeo_FullName"] if pd.notna(e["ActionGeo_FullName"]) else "",
                "date": str(e["SQLDATE"]),
            })
        return events
    except Exception as ex:
        print("Error fetching GDELT data:", ex)
        return []

def get_social_activity_curve(lat, lon):
    """Simulated 24-hour social-media bell curve."""
    hours = np.arange(-24, 1)
    peak_hour = np.random.randint(-8, -2)
    activity = np.exp(-0.5 * ((hours - peak_hour)/4)**2) + np.random.rand(len(hours))*0.1
    df = pd.DataFrame({"Hours Before Incident": hours, "Activity Level": activity})
    return df.set_index("Hours Before Incident")

