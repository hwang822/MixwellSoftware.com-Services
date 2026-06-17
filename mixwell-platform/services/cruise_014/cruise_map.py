import os
import json
import time
import pandas as pd
import folium

from geopy.geocoders import Nominatim

# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_FILE = os.path.join(BASE_DIR, "data", "itinerary.csv")
CACHE_DIR = os.path.join(BASE_DIR, "cache")

ITINERARY_JSON = os.path.join(CACHE_DIR, "itinerary.json")
PORT_CACHE_JSON = os.path.join(CACHE_DIR, "ports.json")

os.makedirs(CACHE_DIR, exist_ok=True)

# --------------------------------------------------
# Load CSV
# --------------------------------------------------

df = pd.read_csv(
    CSV_FILE,
    skiprows=1,
    encoding="cp1252"
)

# --------------------------------------------------
# Geocoder
# --------------------------------------------------

geo = Nominatim(user_agent="cruise_map_v1")

# --------------------------------------------------
# Load cache
# --------------------------------------------------

if os.path.exists(PORT_CACHE_JSON):
    ports_cache = json.load(open(PORT_CACHE_JSON, "r", encoding="utf-8"))
else:
    ports_cache = {}

# --------------------------------------------------
# Build itinerary list (merge duplicates = stays)
# --------------------------------------------------

itinerary = []

last_port = None
last_country = None
start_date = None

def save_cache():
    with open(PORT_CACHE_JSON, "w", encoding="utf-8") as f:
        json.dump(ports_cache, f, indent=2)

def geocode(port, country):

    key = f"{port}|{country}"

    if key in ports_cache:
        return ports_cache[key]

    try:
        time.sleep(1)  # avoid 429

        loc = geo.geocode(f"{port}, {country}", timeout=10)

        if loc:
            result = {
                "lat": loc.latitude,
                "lon": loc.longitude
            }
        else:
            result = None

    except Exception:
        result = None

    ports_cache[key] = result
    save_cache()

    return result

# --------------------------------------------------
# Process rows
# --------------------------------------------------

for _, row in df.iterrows():

    port = str(row.get("Port", "")).strip()
    country = str(row.get("Country", "")).strip()
    date = str(row.get("Date", "")).strip()
    segment = str(row.get("Segment", "")).strip()

    if not port:
        continue

    # skip sea
    if "sea" in port.lower():
        continue

    if "nan" == port: 
        continue

    if "nan" == country: 
        continue

    # merge consecutive same port (stay logic)
    if port == last_port and country == last_country:
        continue

    loc = geocode(port, country)

    google_link = (
        f"https://www.google.com/maps/search/?api=1&query="
        f"{port}+{country}"
    )

    itinerary.append({
        "seq": len(itinerary) + 1,
        "segment": segment,
        "port": port,
        "country": country,
        "date": date,
        "lat": loc["lat"] if loc else None,
        "lon": loc["lon"] if loc else None,
        "google": google_link
    })

    last_port = port
    last_country = country

# --------------------------------------------------
# Save itinerary JSON
# --------------------------------------------------

with open(ITINERARY_JSON, "w", encoding="utf-8") as f:
    json.dump(itinerary, f, indent=2)

# --------------------------------------------------
# Build map
# --------------------------------------------------

m = folium.Map(location=[0, 0], zoom_start=2)

points = []

for p in itinerary:

    if p["lat"] is not None and p["lon"] is not None:

        points.append([p["lat"], p["lon"]])

        #folium.Marker(
        #    [p["lat"], p["lon"]],
        #    popup=f"{p['seq']} {p['port']}<br>{p['date']}"
        #).add_to(m)

        google_url = (
            "https://www.google.com/maps/search/?api=1&query="
            f"{p['port']} {p['country']}"
        )

        popup_html = f"""
        <b>{p['seq']}. {p['port']}</b><br>
        {p['country']}<br>
        {p['date']}<br><br>

        <a href="{google_url}" target="_blank">
            Open in Google Maps
        </a>
        """

        folium.Marker(
            [p["lat"], p["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=p["port"]
        ).add_to(m)

#if len(points) > 1:
#    points = fix_dateline(points)
#    folium.PolyLine(points, weight=3).add_to(m)

segments = []
current = []

for i, pt in enumerate(points):

    if i == 0:
        current.append(pt)
        continue

    prev = points[i - 1]

    lon_prev = prev[1]
    lon_curr = pt[1]

    # Crossing the International Date Line?
    if abs(lon_curr - lon_prev) > 180:

        # Finish current segment
        if len(current) > 1:
            segments.append(current)

        # Start a new segment
        current = [pt]

    else:
        current.append(pt)

# Add the last segment
if len(current) > 1:
    segments.append(current)

# Draw all segments
for seg in segments:
    folium.PolyLine(
        seg,
        weight=3,
        color="blue"
    ).add_to(m)



# --------------------------------------------------
# SAVE HTML (THIS IS THE ONLY OUTPUT)
# --------------------------------------------------

output_file = os.path.join(BASE_DIR, "cruise_map.html")

m.save(output_file)

print("DONE:", output_file)