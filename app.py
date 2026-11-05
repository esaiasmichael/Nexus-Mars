"""NEXUS-Mars v0.4 | Mission Control — historical MY29 observation interface."""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "cloudspotting_centroids_MY29.csv"
IMAGES = ROOT / "images"
MARS_TEXTURE = IMAGES / "mars_surface.jpg"
st.set_page_config(page_title="NEXUS | Mars Mission Control", page_icon="🪐", layout="wide", initial_sidebar_state="expanded")
css = ROOT / "assets" / "styles.css"
if css.is_file():
    st.markdown("<style>" + css.read_text(encoding="utf-8") + "</style>", unsafe_allow_html=True)

@st.cache_data(show_spinner="Loading historical MCS catalogue...")
def load_data(path):
    return pd.read_csv(path, parse_dates=["UTC"])

@st.cache_data(show_spinner="Preparing planetary surface...")
def load_mars_texture(path):
    with Image.open(path) as image:
        rgb = image.convert("RGB").resize((360, 180), Image.Resampling.LANCZOS)
        quantized = rgb.quantize(colors=256)
        indices = np.asarray(quantized, dtype=np.uint8)
        palette = quantized.getpalette()
    scale = [[i / 255, f"rgb({palette[3*i]},{palette[3*i+1]},{palette[3*i+2]})"] for i in range(256)]
    return indices, scale

if not DATA.is_file():
    st.error(f"Missing observation catalogue: {DATA}. Copy the data folder from your working v0.3 project.")
    st.stop()
df = load_data(str(DATA))
required = {"Channel", "Altitude", "L_sub_s", "Scene_lat", "Scene_lon", "UTC"}
if required - set(df.columns):
    st.error(f"Missing catalogue columns: {sorted(required - set(df.columns))}")
    st.stop()

with st.sidebar:
    st.markdown('<div class="side-mark">⌁</div><div class="side-title">N E X U S</div><div class="side-subtitle">MARS DIGITAL TWIN</div>', unsafe_allow_html=True)
    page = st.radio("NAVIGATION", ["Overview", "Mars Explorer", "Data Explorer", "Analysis", "Research & Sources"], label_visibility="collapsed")
    st.divider()
    st.markdown('<div class="side-footer">MCS / MARS YEAR 29<br>HISTORICAL OBSERVATION DATA<br><span>RESEARCH PROTOTYPE · V0.4</span></div>', unsafe_allow_html=True)

st.markdown("""<div class="topline"><span class="topword">N E X U S</span><span class="topmeta">MARS DIGITAL TWIN <b>V0.4</b></span><span class="preview">● &nbsp; RESEARCH PREVIEW</span></div>""", unsafe_allow_html=True)

available_channels = sorted(df["Channel"].dropna().unique().tolist())
alt_min, alt_max = float(df["Altitude"].min()), float(df["Altitude"].max())
if alt_min == alt_max: alt_max = alt_min + 0.01

# The controls live on the right of the hero on Overview, and in a filter panel elsewhere.
def controls():
    st.markdown('<div class="panel-label">⌁ &nbsp; VIEW CONTROLS</div>', unsafe_allow_html=True)
    view = st.segmented_control("Display", ["Globe", "Map"], default="Globe", label_visibility="collapsed", key="view")
    show_obs = st.checkbox("Show observations", value=True, key="show_obs")
    channels = st.multiselect("Instrument channels", available_channels, default=available_channels, key="channels")
    season = st.slider("Solar longitude (Ls °)", 0.0, 360.0, (0.0, 360.0), key="season")
    altitude = st.slider("Centroid altitude (dataset units)", alt_min, alt_max, (alt_min, alt_max), key="altitude")
    latitude = st.slider("Latitude (°)", -90, 90, (-90, 90), key="latitude")
    sample_size = st.select_slider("Render sample", options=[1000, 3000, 6000, 10000, 15000, 20000], value=6000, key="sample")
    return view, show_obs, channels, season, altitude, latitude, sample_size

def subset(channels, season, altitude, latitude):
    return df.loc[df["Channel"].isin(channels) & df["L_sub_s"].between(*season) & df["Altitude"].between(*altitude) & df["Scene_lat"].between(*latitude)].copy()

def build_globe(filtered, sample_size, show_obs):
    if filtered.empty:
        st.warning("No observations match these filters. The surface remains available.")
    sampled = filtered.sample(n=min(sample_size, len(filtered)), random_state=42) if not filtered.empty else filtered
    # --------------------------------------------------------
    # 7.1 Construct Mars sphere
    # --------------------------------------------------------

    if MARS_TEXTURE.is_file():

        surface_indices, mars_colorscale = load_mars_texture(
            str(MARS_TEXTURE)
        )

        texture_height, texture_width = surface_indices.shape

        # Equirectangular surface coordinates.
        latitudes = np.linspace(
            90,
            -90,
            texture_height,
        )

        longitudes = np.linspace(
            -180,
            180,
            texture_width,
        )

        lon_grid, lat_grid = np.meshgrid(
            longitudes,
            latitudes,
        )

        lat_r = np.radians(lat_grid)
        lon_r = np.radians(lon_grid)

        surface_x = np.cos(lat_r) * np.cos(lon_r)
        surface_y = np.cos(lat_r) * np.sin(lon_r)
        surface_z = np.sin(lat_r)

        fig = go.Figure()

        # Realistic Mars surface
        fig.add_trace(
            go.Surface(
                x=surface_x,
                y=surface_y,
                z=surface_z,
                surfacecolor=surface_indices,
                colorscale=mars_colorscale,
                cmin=0,
                cmax=255,
                showscale=False,
                hoverinfo="skip",
                lighting=dict(
                    ambient=0.85,
                    diffuse=0.65,
                    specular=0.03,
                ),
                name="Mars surface",
            )
        )

        surface_type = "NASA Mars surface imagery"

    else:

        st.warning(
            "Mars surface texture not found. "
            "Using the original illustrative sphere. "
            f"Expected file: {MARS_TEXTURE}"
        )

        lat_grid, lon_grid = np.meshgrid(
            np.linspace(-90, 90, 37),
            np.linspace(-180, 180, 73),
            indexing="ij",
        )

        lat_r = np.radians(lat_grid)
        lon_r = np.radians(lon_grid)

        surface_x = np.cos(lat_r) * np.cos(lon_r)
        surface_y = np.cos(lat_r) * np.sin(lon_r)
        surface_z = np.sin(lat_r)

        fig = go.Figure()

        fig.add_trace(
            go.Surface(
                x=surface_x,
                y=surface_y,
                z=surface_z,
                surfacecolor=np.ones_like(surface_x),
                colorscale=[
                    [0, "#A84432"],
                    [1, "#A84432"],
                ],
                showscale=False,
                hoverinfo="skip",
                lighting=dict(
                    ambient=0.65,
                    diffuse=0.85,
                    specular=0.08,
                ),
                name="Illustrative Mars sphere",
            )
        )

        surface_type = "Illustrative Mars sphere"

    # --------------------------------------------------------
    # 7.2 Plot cloud-centroid observations
    # --------------------------------------------------------

    if show_obs and not sampled.empty:
        valid = sampled.dropna(
            subset=[
                "Scene_lat",
                "Scene_lon",
                "Altitude",
            ]
        )

        cloud_lat = np.radians(
            valid["Scene_lat"].to_numpy()
        )

        cloud_lon = np.radians(
            valid["Scene_lon"].to_numpy()
        )

        # Slightly above surface so markers remain visible.
        radius = 1.018

        cloud_x = (
            radius
            * np.cos(cloud_lat)
            * np.cos(cloud_lon)
        )

        cloud_y = (
            radius
            * np.cos(cloud_lat)
            * np.sin(cloud_lon)
        )

        cloud_z = radius * np.sin(cloud_lat)

        fig.add_trace(
            go.Scatter3d(
                x=cloud_x,
                y=cloud_y,
                z=cloud_z,
                mode="markers",
                marker=dict(
                    size=2.1,
                    color=valid["Altitude"],
                    colorscale="Cividis",
                    opacity=0.76,
                    colorbar=dict(
                        title="Altitude"
                    ),
                ),
                customdata=np.column_stack([
                    valid["Scene_lat"].to_numpy(),
                    valid["Scene_lon"].to_numpy(),
                    valid["Altitude"].to_numpy(),
                ]),
                hovertemplate=(
                    "Latitude: %{customdata[0]:.2f}°"
                    "<br>Longitude: %{customdata[1]:.2f}°"
                    "<br>Altitude: %{customdata[2]:.2f}"
                    "<extra></extra>"
                ),
                name="Cloud detections",
            )
        )

    # --------------------------------------------------------
    # 7.3 Configure interactive globe
    # --------------------------------------------------------

    fig.update_layout(
        height=540,
        paper_bgcolor="#08090B",
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0,
        ),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="cube",
            bgcolor="#08090B",
            camera=dict(
                eye=dict(
                    x=1.7,
                    y=1.6,
                    z=1.1,
                )
            ),
        ),
        showlegend=False,
    )

    return fig

def render_globe(filtered, sample_size, show_obs, view):
    if view == "Map":
        pts = filtered.dropna(subset=["Scene_lat", "Scene_lon"])
        pts = pts.sample(n=min(sample_size, len(pts)), random_state=42) if len(pts) else pts
        fig = px.scatter_geo(pts if show_obs else pts.head(0), lat="Scene_lat", lon="Scene_lon", color="Altitude", projection="equirectangular", color_continuous_scale="Cividis")
        fig.update_geos(showcoastlines=False, showland=False, showocean=False, showcountries=False, showframe=True, bgcolor="#08090B", projection_bgcolor="#08090B", lataxis_range=[-90,90], lonaxis_range=[-180,180])
        fig.update_layout(height=540, paper_bgcolor="#08090B", font_color="#D9DDE1", margin=dict(l=5,r=5,t=5,b=5), coloraxis_colorbar=dict(title="Altitude"))
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
        st.caption("Coordinate scatter map; not a textured surface map. Longitude positive east, latitude planetocentric.")
    else:
        fig = build_globe(filtered, sample_size, show_obs)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "scrollZoom": True})
        st.caption("Spherical surface with sampled historical cloud centroids. Marker elevation is illustrative, not physical cloud altitude; texture alignment remains provisional.")

def observation_gallery():
    cards = [
        ("mars-clouds.jpg", "MARTIAN ATMOSPHERIC CLOUDS", "NASA cloud research", "https://science.nasa.gov/citizen-science/cloudspotting/"),
        ("cloudspotting-results.jpg", "CLOUDSPOTTING FINDINGS", "Citizen-science detections", "https://science.nasa.gov/get-involved/citizen-science/new-patterns-in-marss-clouds-revealed-by-volunteers/"),
        ("mars-dust-storm.jpg", "ATMOSPHERIC DUST & CLOUDS", "Atmospheric context", "https://science.nasa.gov/science-research/planetary-science/cloudspotting-on-mars-project-extended/"),
    ]
    cols = st.columns(3, gap="small")
    for col, (filename, title, desc, url) in zip(cols, cards):
        with col:
            path = IMAGES / filename
            if path.is_file(): st.image(str(path), use_container_width=True)
            else: st.markdown('<div class="missing-photo">IMAGE ASSET NOT FOUND</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-title">{title}</div><div class="card-desc">{desc}</div>', unsafe_allow_html=True)
            st.link_button("NASA SOURCE ↗", url, use_container_width=True)

def charts(filtered):
    if filtered.empty:
        st.info("Adjust the observation filters to display analytics.")
        return
    left, right = st.columns(2)
    with left:
        fig = px.histogram(filtered, x="Altitude", nbins=55, color_discrete_sequence=["#BB7459"])
        fig.update_layout(title="CLOUD-CENTROID ALTITUDE", xaxis_title="Altitude (dataset units)", yaxis_title="Detected centroids")
        style_chart(fig)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        seasonal = filtered.assign(Ls_bin=(filtered["L_sub_s"] // 10 * 10).astype(int)).groupby("Ls_bin", as_index=False).size()
        fig = px.bar(seasonal, x="Ls_bin", y="size", color_discrete_sequence=["#9AA8B3"])
        fig.update_layout(title="DETECTIONS BY SOLAR LONGITUDE", xaxis_title="Ls (10° bins)", yaxis_title="Detected centroids")
        style_chart(fig)
        st.plotly_chart(fig, use_container_width=True)
    st.caption("Raw detection counts are not normalised for observation coverage or sensitivity.")

def style_chart(fig):
    fig.update_layout(height=330, paper_bgcolor="#0D0F12", plot_bgcolor="#0D0F12", font=dict(color="#CDD0D3", family="Arial", size=11), margin=dict(l=10,r=10,t=45,b=20), title_font=dict(size=12), xaxis=dict(gridcolor="#272B31"), yaxis=dict(gridcolor="#272B31"))

def provenance():
    with st.expander("SCIENTIFIC PROVENANCE & LIMITATIONS"):
        st.markdown("""**Source:** Slipski et al. (2023), *Replication Data for Cloudspotting on Mars Citizen Science Cloud Centroids for Mars Year 29*, JPL Open Repository, v1.2. DOI: `10.48577/jpl.UXMDDK`.

**Instrument:** Mars Climate Sounder (MCS), Mars Reconnaissance Orbiter. Historical MY29 cloud-centroid catalogue, not live telemetry, a forecast, or a physics-based simulation.

**Coordinates:** planetocentric latitude and east-positive longitude (confirmed by researcher correspondence). The texture's precise georeferencing has not been independently validated.

**Interpretation:** marker distance from the globe is illustrative, not scaled to measured cloud altitude. Counts are not normalised for sampling coverage or detection sensitivity. Dataset altitude units remain labelled as source units pending confirmation.

**Imagery:** Gallery imagery is scientific context, not the selected filtered observations. Verify image-specific NASA/JPL credits and reuse conditions before public release.""")

if page == "Overview":
    left, center, right = st.columns([1.05, 1.8, 1.12], gap="medium")
    with right:
        with st.container(border=True):
            view, show_obs, channels, season, altitude, latitude, sample_size = controls()
        filtered = subset(channels, season, altitude, latitude)
        with st.container(border=True):
            st.markdown('<div class="panel-label">⌁ &nbsp; CURRENT CONTEXT</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="context-row"><span>Selected centroids</span><strong>{len(filtered):,}</strong></div><div class="context-row"><span>Instrument channels</span><strong>{filtered["Channel"].nunique()}</strong></div><div class="context-row"><span>Rendered sample</span><strong>{min(sample_size,len(filtered)):,}</strong></div><div class="context-row"><span>Mars year</span><strong>MY29</strong></div>', unsafe_allow_html=True)
    with left:
        st.markdown('<div class="hero-copy"><div class="hero-title">MARS<br>DIGITAL TWIN</div><div class="hero-kicker">OBSERVE &nbsp; / &nbsp; ANALYSE &nbsp; / &nbsp; EXPLORE</div><p>Explore historical Martian atmospheric cloud detections through an interactive planetary observatory.</p><div class="hero-rule"></div></div>', unsafe_allow_html=True)
        a,b=st.columns(2)
        a.metric("SELECTED CENTROIDS", f"{len(filtered):,}")
        b.metric("CATALOGUE RECORDS", f"{len(df):,}")
        st.caption("MCS / MY29 · NASA/JPL RESEARCH DATA")
    with center:
        st.markdown('<div class="planet-heading">MARS / GLOBAL OBSERVATION</div>', unsafe_allow_html=True)
        render_globe(filtered, sample_size, show_obs, view)
    st.markdown('<div class="section-heading">01 &nbsp; / &nbsp; FEATURED RESEARCH</div>', unsafe_allow_html=True)
    observation_gallery()
    st.markdown('<div class="section-heading">02 &nbsp; / &nbsp; ATMOSPHERIC ANALYTICS</div>', unsafe_allow_html=True)
    charts(filtered)
    provenance()
else:
    st.markdown(f'<div class="inner-heading">{page.upper()}</div>', unsafe_allow_html=True)
    with st.expander("OBSERVATION FILTERS", expanded=True):
        view, show_obs, channels, season, altitude, latitude, sample_size = controls()
    filtered = subset(channels, season, altitude, latitude)
    if page == "Mars Explorer":
        render_globe(filtered, sample_size, show_obs, view)
    elif page == "Data Explorer":
        a,b,c=st.columns(3)
        a.metric("Selected centroids",f"{len(filtered):,}")
        b.metric("Catalogue records",f"{len(df):,}")
        c.metric("Channels represented",filtered["Channel"].nunique())
        st.dataframe(filtered.head(1000), use_container_width=True, hide_index=True)
        st.download_button("DOWNLOAD FILTERED CSV", filtered.to_csv(index=False).encode("utf-8"), "nexus_mars_filtered.csv", "text/csv", disabled=filtered.empty)
    elif page == "Analysis":
        charts(filtered)
    elif page == "Research & Sources":
        observation_gallery()
        provenance()

st.markdown('<div class="footnote">NEXUS / MARS DIGITAL TWIN &nbsp; · &nbsp; RESEARCH PROTOTYPE &nbsp; · &nbsp; HISTORICAL MY29 OBSERVATIONS</div>', unsafe_allow_html=True)
