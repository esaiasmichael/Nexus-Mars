"""NEXUS v0.1 — observational Mars cloud explorer."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np
import plotly.graph_objects as go


st.set_page_config(page_title="NEXUS | Mars Cloud Observatory", page_icon="🪐", layout="wide")
st.title("NEXUS · Mars Cloud Observatory")
st.caption("v0.1 | Observational digital-twin prototype · Cloudspotting on Mars · Mars Year 29")

DATA = Path(__file__).parent / "data" / "cloudspotting_centroids_MY29.csv"
@st.cache_data(show_spinner="Loading JPL cloud-centroid catalogue…")
def load():
    df = pd.read_csv(DATA, parse_dates=["UTC"])
    return df

if not DATA.exists():
    st.error("Missing dataset. Put cloudspotting_centroids_MY29.csv in data/.")
    st.stop()
df = load()
with st.sidebar:
    st.header("Observation filters")
    channels = st.multiselect("Instrument channel", sorted(df.Channel.unique()), default=sorted(df.Channel.unique()))
    alt_min, alt_max = float(df.Altitude.min()), float(df.Altitude.max())
    altitude = st.slider("Cloud centroid altitude (dataset units; verify metadata)", alt_min, alt_max, (alt_min, alt_max))
    season = st.slider("Solar longitude Ls (degrees)", 0.0, 360.0, (0.0, 360.0))
    lat = st.slider("Latitude (degrees)", -90, 90, (-90, 90))
    max_points = st.slider("Map sample size", 1000, 20000, 6000, 1000)
    st.info("Points represent detected cloud centroids, not a complete atmospheric state. Sampling coverage varies.")

filtered = df.loc[
    df.Channel.isin(channels)
    & df.Altitude.between(*altitude)
    & df.L_sub_s.between(*season)
    & df.Scene_lat.between(*lat)
].copy()

m1,m2,m3,m4=st.columns(4)
m1.metric("Filtered cloud centroids", f"{len(filtered):,}")
m2.metric("Total catalogue records", f"{len(df):,}")
m3.metric("Channels represented", filtered.Channel.nunique())
m4.metric("Observed date span", f"{(df.UTC.max()-df.UTC.min()).days:,} days")

left,right=st.columns([1.4,1])
with left:
    st.subheader("Cloud centroid geography")
    if filtered.empty:
        st.warning("No observations match these filters.")
    else:
        sampled = filtered.sample(n=min(max_points,len(filtered)),random_state=42)
              #NEXUS v0.1.1 — Low-poly Mars sphere
        lat_edges = np.linspace(-90, 90, 19)
        lon_edges = np.linspace(-180, 180, 37)
        lon_grid, lat_grid = np.meshgrid(lon_edges, lat_edges)

        lat_rad = np.radians(lat_grid)
        lon_rad = np.radians(lon_grid)

        x = np.cos(lat_rad) * np.cos(lon_rad)
        y = np.cos(lat_rad) * np.sin(lon_rad)
        z = np.sin(lat_rad)

        fig = go.Figure()

        fig.add_trace(go.Surface(
            x=x, y=y, z=z,
            surfacecolor=np.ones_like(x),
            colorscale=[[0, "#A84432"], [1, "#A84432"]],
            showscale=False,
            lighting=dict(ambient=0.65, diffuse=0.85, specular=0.08),
            hoverinfo="skip",
            name="Mars"
        ))

        cloud_lat = np.radians(sampled["Scene_lat"].to_numpy())
        cloud_lon = np.radians(sampled["Scene_lon"].to_numpy())

        cloud_x = 1.015 * np.cos(cloud_lat) * np.cos(cloud_lon)
        cloud_y = 1.015 * np.cos(cloud_lat) * np.sin(cloud_lon)
        cloud_z = 1.015 * np.sin(cloud_lat)

        fig.add_trace(go.Scatter3d(
            x=cloud_x, y=cloud_y, z=cloud_z,
            mode="markers",
            marker=dict(
                size=2,
                color=sampled["Altitude"],
                colorscale="Viridis",
                opacity=0.85,
                colorbar=dict(title="Altitude")
            ),
            text=sampled["Channel"].astype(str),
            hovertemplate="Channel: %{text}<extra></extra>",
            name="Cloud centroids"
        ))

        fig.update_layout(
            height=540,
            margin=dict(l=0, r=0, t=0, b=0),
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                aspectmode="cube",
                camera=dict(eye=dict(x=1.6, y=1.6, z=1.1))
            ),
            showlegend=False
        )

        st.plotly_chart(fig, width="stretch")
        st.caption(
            "Illustrative low-poly Mars sphere with sampled cloud centroids. "
            "Altitude is represented by marker colour; terrain is not modelled."
        )
with right:
    st.subheader("Altitude distribution")
    if not filtered.empty:
        hist=px.histogram(filtered,x="Altitude",nbins=55,color_discrete_sequence=["#b86b47"])
        hist.update_layout(height=245,xaxis_title="Altitude (units pending metadata check)",yaxis_title="Detected centroids",margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(hist,use_container_width=True)
        st.subheader("Counts by solar longitude")
        binned=filtered.assign(Ls_bin=(filtered.L_sub_s//10*10).astype(int)).groupby("Ls_bin",as_index=False).size()
        seasonal=px.bar(binned,x="Ls_bin",y="size",color_discrete_sequence=["#547e9d"])
        seasonal.update_layout(height=245,xaxis_title="Ls (10° bins)",yaxis_title="Detected centroids",margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(seasonal,use_container_width=True)
        st.caption("Counts are not cloud occurrence rates: observation effort and detection bias are not normalised.")

st.subheader("Explore the underlying observations")
st.dataframe(filtered.head(1000),use_container_width=True,hide_index=True)
st.download_button("Download filtered observations (CSV)",data=filtered.to_csv(index=False).encode("utf-8"),file_name="nexus_filtered_clouds.csv",mime="text/csv",disabled=filtered.empty)
with st.expander("Scientific provenance and limitations"):
    st.markdown("""**Source:** Slipski et al. (2023), *Replication Data for Cloudspotting on Mars Citizen Science Cloud Centroids for Mars Year 29*, JPL Open Repository, version 1.2. DOI: `10.48577/jpl.UXMDDK`.  
**Scope:** Historical cloud centroid detections. Not a live telemetry feed, atmospheric forecast, physics simulation, or unbiased measure of cloud frequency.  
**Before publication:** Check JPL dataset Terms tab, field units, and coordinate conventions. Plotly globe uses an illustrative Earth-derived landmask rather than a scientifically correct Martian surface.  
**Data handling:** The original 17-column CSV is included unchanged; no imputation. Filtering and plotting are performed in memory.""")
