# Air-ambulance bases in Castilla y León

University of León, Mathematical Modelling I (course 2025-26). Group project (6 students).

Where should the 10 helicopters of a new air-ambulance fleet be based (one per province plus one for the El Bierzo district) so that every municipality is reachable in at most 30 minutes? The group's approach is a **heuristic, not an exact optimisation**: a population-weighted centre of gravity per province, a choice of base near it, and a coverage check. The formal model (location-allocation with binary variables) is written down in the report but it is not solved as an integer program.

## Method

1. **Centroid.** For each province, the centre of gravity of its municipalities weighted by population.
2. **Base.** A base is chosen close to the centroid. An existing helipad is reused when there is one nearby; a new one is proposed otherwise (only Ávila, whose centroid is more than 10 km from any existing helipad).
3. **Coverage.** Haversine distance from the base to every municipality, flight time at 250 km/h, and a check against the 30-minute limit (125 km radius).

Data: municipalities and helipads from IDECyL (Junta de Castilla y León) and the regional boundary shapefile. They are not redistributed here; place them in `data/` (see the docstring of `src/helicopter_bases.py` for the expected files).

## Results

All 10 bases reach every municipality of their province within 30 minutes. The most distant municipality takes at most 26.5 minutes (Salamanca).

| Unit | Municipalities | Base | Farthest municipality | Time (min) |
|---|---|---|---|---|
| Ávila | 248 | Aldea del Rey Niño (new) | Puerto Castilla | 20.0 |
| El Bierzo | 38 | Hospital El Bierzo | Palacios del Sil | 9.4 |
| Burgos | 371 | Hospital Universitario de Burgos | Fuentenebro | 22.8 |
| León | 173 | Hospital Universitario de León | Encinedo | 23.1 |
| Palencia | 191 | Villaldavín | La Pernía | 22.5 |
| Salamanca | 362 | Otero de Vaciadores | Navasfrías | 26.5 |
| Segovia | 209 | Parador de Segovia | Languilla | 19.1 |
| Soria | 183 | Villaciervitos | Castillejo de Robledo | 17.8 |
| Valladolid | 225 | Centro Municipal de Acústica | Monasterio de Vega | 18.9 |
| Zamora | 248 | Montamarta | Pías | 26.1 |

Full table: `results/tables/coverage_summary.csv`. Running the script also draws a map of the bases and their 125 km radius (`results/figures/bases_125km.png`) when the boundary shapefile is available.

## A note on the capital correction

The report describes damping the weight of the provincial capital by a factor of 0.4, so that the centroid does not collapse onto the capital. In the delivered notebook this correction was **never applied**: the capital was looked up by an unaccented lowercase name that did not match the data, so the centroids used are plain population-weighted ones. `src/helicopter_bases.py` fixes the matching and reports both versions; the damped centroid moves between 1.8 km (León) and 8.1 km (Palencia) from the plain one. The chosen bases, and therefore the coverage results, are those of the delivered work and do not depend on this correction.

## Run

```
pip install pandas numpy matplotlib geopandas
python src/helicopter_bases.py data
```
