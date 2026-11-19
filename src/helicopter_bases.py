"""Helicopter base selection for Castilla y León (heuristic + coverage check).

Pipeline per province (El Bierzo counts as its own unit, 10 units in total):
  1. Population-weighted centroid of the municipalities (optionally damping the
     provincial capital by a factor, 0.4 in the original report).
  2. Choice of the base (manual, see UNITS) and check against the existing helipads.
  3. For the base finally chosen: flight time to every municipality
     (haversine distance, 250 km/h) and check of the 30-minute limit.

Input data (not redistributed, see README): data/<PROVINCE>.csv with columns
municipio, provincia, población, latitud, longitud; data/helipuertos.csv;
data/limites_cyl_autonomia.shp (IDECyL).
"""
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
OUT = Path("results")
SPEED_KM_MIN = 250 / 60       # 250 km/h
LIMIT_MIN = 30                # maximum response time
CAPITAL_FACTOR = 0.4

# unit -> (csv file, capital municipality, chosen base name, lat, lon)
UNITS = {
    "Ávila": ("AVILA2", "avila", "Aldea del Rey Niño (new)", 40.59121025212638, -4.744046789099592),
    "El Bierzo": ("BIERZO2", "ponferrada", "Hospital El Bierzo", 42.570759, -6.644009),
    "Burgos": ("BURGOS2", "burgos", "Hospital Universitario de Burgos", 42.361637, -3.683733),
    "León": ("LEON3", "leon", "Hospital Universitario de León", 42.619475, -5.571511),
    "Palencia": ("PALENCIA2", "palencia", "Villaldavín (new)", 42.16053935587521, -4.573186388760666),
    "Salamanca": ("SALAMANCA2", "salamanca", "Otero de Vaciadores (new)", 40.88021054363704, -5.765183288959207),
    "Segovia": ("SEGOVIA2", "segovia", "Parador de Segovia", 40.96059, -4.10915),
    "Soria": ("SORIA2", "soria", "Villaciervitos (new)", 41.7540331684373, -2.6415659499109343),
    "Valladolid": ("VALLADOLID2", "valladolid", "Centro Municipal de Acústica", 41.61524, -4.77196),
    "Zamora": ("ZAMORA2", "zamora", "Montamarta (new)", 41.65046612693046, -5.802912674910756),
}


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def norm(s):
    s = str(s).encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn").strip()


def load_municipalities(stem):
    df = pd.read_csv(DATA / f"{stem}.csv", encoding="latin1")
    df.columns = [norm(c) for c in df.columns]
    df = df.rename(columns={"poblacion": "pop", "poblaci": "pop"})
    popcol = [c for c in df.columns if c.startswith("poblaci")][0] if "pop" not in df else "pop"
    df["pop"] = pd.to_numeric(df[popcol].astype(str).str.replace(" ", ""), errors="coerce")
    df["name"] = df["municipio"].map(norm)
    return df


def centroid(df, capital, factor):
    w = df["pop"].astype(float).copy()
    w[df["name"] == capital] *= factor
    return (df["latitud"] * w).sum() / w.sum(), (df["longitud"] * w).sum() / w.sum()


def existing_helipads():
    h = pd.read_csv(DATA / "helipuertos.csv", sep=";", encoding="latin1")
    for c in ("latitud", "longitud"):
        h[c] = pd.to_numeric(h[c].astype(str).str.replace(",", "."), errors="coerce")
    return h.dropna(subset=["latitud", "longitud"])


def main():
    heli = existing_helipads()
    rows = []
    for unit, (stem, capital, base, blat, blon) in UNITS.items():
        df = load_municipalities(stem)
        assert (df["name"] == capital).sum() == 1, f"capital {capital} not found in {stem}"
        lat0, lon0 = centroid(df, capital, 1.0)
        lat4, lon4 = centroid(df, capital, CAPITAL_FACTOR)
        d_shift = haversine(lat0, lon0, lat4, lon4)
        dist = haversine(blat, blon, df["latitud"].values, df["longitud"].values)
        far = df.assign(d=dist).sort_values("d").iloc[-1]
        rows.append({
            "unit": unit, "municipalities": len(df), "population": int(df["pop"].sum()),
            "centroid_plain": f"{lat0:.4f}, {lon0:.4f}",
            "centroid_capital_x0.4": f"{lat4:.4f}, {lon4:.4f}",
            "shift_km": round(d_shift, 1),
            "base": base,
            "farthest_municipality": far["municipio"].encode("latin1", errors="ignore").decode("utf-8", errors="ignore"),
            "farthest_km": round(far["d"], 1),
            "farthest_min": round(far["d"] / SPEED_KM_MIN, 1),
            "municipalities_over_30min": int((dist / SPEED_KM_MIN > LIMIT_MIN).sum()),
        })
    res = pd.DataFrame(rows)
    OUT.joinpath("tables").mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT / "tables" / "coverage_summary.csv", index=False)
    print(res.to_string(index=False))
    make_map()


def make_map():
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from shapely.geometry import Point

    shp = DATA / "limites_cyl_autonomia.shp"
    if not shp.exists():
        return
    cyl = gpd.read_file(shp).to_crs(25830)
    bases = gpd.GeoDataFrame(
        {"name": [v[2] for v in UNITS.values()]},
        geometry=[Point(v[4], v[3]) for v in UNITS.values()], crs=4326).to_crs(25830)
    fig, ax = plt.subplots(figsize=(8, 8))
    cyl.plot(ax=ax, color="white", edgecolor="black")
    bases.assign(geometry=bases.buffer(125_000)).plot(ax=ax, color="tab:blue", alpha=0.1, edgecolor="tab:blue")
    bases.plot(ax=ax, color="red", markersize=30)
    ax.set_title("Chosen helicopter bases and 125 km radius (30 min at 250 km/h)")
    ax.set_xlabel("Easting (m, EPSG:25830)")
    ax.set_ylabel("Northing (m)")
    plt.tight_layout()
    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT / "figures" / "bases_125km.png", dpi=60)


if __name__ == "__main__":
    main()
