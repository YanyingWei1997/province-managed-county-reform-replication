"""
Fetch county-level centroids from DataV Aliyun for the 22 provinces in our sample.
Output: data/processed/county_centroids.csv with columns county_code, lon, lat, name.
"""
import json
import pathlib
import time
import urllib.request
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "processed" / "county_centroids.csv"

# Read the GRF analytical sample
grf = pd.read_csv(ROOT / "data" / "processed" / "grf_input.csv")
codes = grf["county_code"].astype(int).astype(str).str.zfill(6)
city_codes = sorted(set([c[:4] + "00" for c in codes]))
print(f"Need to fetch {len(city_codes)} city-level files for county centroids")

records = []
fail_cities = []
for i, city in enumerate(city_codes):
    url = f"https://geo.datav.aliyun.com/areas_v3/bound/{city}_full.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
        for feat in data["features"]:
            p = feat["properties"]
            adcode = p.get("adcode")
            center = p.get("center")
            if adcode and center and len(center) == 2:
                records.append({
                    "county_code": int(adcode),
                    "lon": float(center[0]),
                    "lat": float(center[1]),
                    "name": p.get("name", ""),
                    "level": p.get("level", ""),
                })
        time.sleep(0.05)
        if (i + 1) % 30 == 0:
            print(f"  fetched {i+1}/{len(city_codes)}")
    except Exception as e:
        fail_cities.append(city)
        print(f"  FAIL city {city}: {e}")

df = pd.DataFrame(records).drop_duplicates(subset=["county_code"])
print(f"Total county-level records: {len(df)}")
df.to_csv(OUT, index=False)
print(f"Saved to {OUT}")
if fail_cities:
    print(f"Failed cities ({len(fail_cities)}): {fail_cities[:10]}...")

# Match to our sample
matched = df[df["county_code"].isin(grf["county_code"].astype(int))]
print(f"Match with GRF sample: {len(matched)} / {len(grf)}")
unmatched = set(grf["county_code"].astype(int)) - set(df["county_code"])
print(f"Unmatched county_codes: {len(unmatched)}")
if unmatched:
    print(f"First 10 unmatched: {sorted(unmatched)[:10]}")
