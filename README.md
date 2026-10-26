# NEXUS — Mars Cloud Observatory (v0.1)

An **observation-driven digital-twin prototype** exploring Mars Year 29 cloud-centroid detections from the Cloudspotting on Mars citizen-science project.

## Run locally

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens in a browser, usually at `http://localhost:8501`.

## Included

- Original 127,473-row / 17-variable dataset (`data/cloudspotting_centroids_MY29.csv`)
- Filtering by channel, latitude, altitude, and solar longitude
- Interactive, sampled orthographic location plot
- Altitude and solar-longitude distributions
- Filtered observation table and CSV export

## What this is not

This is **not** a complete physical atmospheric digital twin, live Mars weather, a forecast, or an estimate of true cloud occurrence probability. Observation coverage is not normalised. The globe's illustrative land shading is not a Martian terrain basemap. Confirm field units and dataset reuse terms against JPL metadata before external release.

## Provenance

Slipski, M. et al. (2023). *Replication Data for Cloudspotting on Mars Citizen Science Cloud Centroids for Mars Year 29*, JPL Open Repository, v1.2. DOI: https://doi.org/10.48577/jpl.UXMDDK

## Next milestone

Replace illustrative globe with a Mars-specific basemap, add coverage-aware aggregation, metadata validation, and a reproducible quality-control report.
