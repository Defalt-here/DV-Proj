"""
Renewable Energy Worldwide — Interactive Data Visualisation Dashboard
Run with:  streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).parent / "Data"

st.set_page_config(
    page_title="Renewable Energy Worldwide",
    layout="wide",
    initial_sidebar_state="expanded",
)

SOURCE_COLS = {
    "Wind": "Electricity from wind (TWh)",
    "Hydro": "Electricity from hydro (TWh)",
    "Solar": "Electricity from solar (TWh)",
    "Other (Bio/Geo)": "Other renewables including bioenergy (TWh)",
}
SOURCE_COLORS = {
    "Wind": "#4FC3F7",
    "Hydro": "#1976D2",
    "Solar": "#FFB300",
    "Other (Bio/Geo)": "#66BB6A",
}


@st.cache_data
def load_production() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "03 modern-renewable-prod.csv")
    df = df.rename(columns={c: c for c in df.columns})
    df["Total"] = df[list(SOURCE_COLS.values())].sum(axis=1)
    return df


@st.cache_data
def load_share_electricity() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "04 share-electricity-renewables.csv")


@st.cache_data
def load_share_primary() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "01 renewable-share-energy.csv")


@st.cache_data
def load_solar_capacity() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "13 installed-solar-PV-capacity.csv")


@st.cache_data
def load_wind_capacity() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "09 cumulative-installed-wind-energy-capacity-gigawatts.csv")


def countries_only(df: pd.DataFrame) -> pd.DataFrame:
    """Drop aggregate rows (continents, World, etc.) by requiring an ISO-3 code."""
    return df[df["Code"].notna() & (df["Code"].str.len() == 3) & (df["Code"] != "OWID_WRL")].copy()


prod = load_production()
share_el = load_share_electricity()
share_pri = load_share_primary()
solar_cap = load_solar_capacity()
wind_cap = load_wind_capacity()

prod_c = countries_only(prod)
share_el_c = countries_only(share_el)

# ---------------------------------------------------------------------------
# Sidebar — global filtersasdas
# ---------------------------------------------------------------------------
st.sidebar.title("Filters")

year_min = int(prod_c["Year"].min())
year_max = int(prod_c["Year"].max())

selected_year = st.sidebar.slider(
    "Snapshot year (for maps & rankings)",
    min_value=year_min,
    max_value=year_max,
    value=year_max,
    step=1,
)

year_range = st.sidebar.slider(
    "Year range (for trend charts)",
    min_value=year_min,
    max_value=year_max,
    value=(2000, year_max),
    step=1,
)

selected_sources = st.sidebar.multiselect(
    "Renewable sources",
    options=list(SOURCE_COLS.keys()),
    default=list(SOURCE_COLS.keys()),
)

all_countries = sorted(prod_c["Entity"].unique())
default_countries = [c for c in ["China", "United States", "Germany", "India", "Brazil", "United Kingdom"] if c in all_countries]
selected_countries = st.sidebar.multiselect(
    "Countries to compare (trends, radar)",
    options=all_countries,
    default=default_countries,
)

selected_country_single = st.sidebar.selectbox(
    "Single country (for energy-mix views)",
    options=all_countries,
    index=all_countries.index("China") if "China" in all_countries else 0,
)

st.sidebar.markdown("---")
st.sidebar.caption("Data source: Our World in Data — Renewable Energy. ISO-3 country codes used for the world map.")

active_cols = [SOURCE_COLS[s] for s in selected_sources] or list(SOURCE_COLS.values())

# ---------------------------------------------------------------------------
# Header + KPIs
# ---------------------------------------------------------------------------
st.title("Renewable Energy Worldwide — Interactive Dashboard")
st.markdown(
    f"Exploring global renewable electricity generation **{year_min}–{year_max}**. "
    "Hover any chart for tooltips. Use the sidebar to slice the data."
)

snap = prod_c[prod_c["Year"] == selected_year].copy()
prev = prod_c[prod_c["Year"] == selected_year - 1].copy() if selected_year > year_min else snap

total_now = snap["Total"].sum()
total_prev = prev["Total"].sum() if not prev.empty else total_now
yoy = ((total_now - total_prev) / total_prev * 100) if total_prev else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total renewable generation", f"{total_now:,.0f} TWh", f"{yoy:+.1f}% YoY")
top_country_row = snap.loc[snap["Total"].idxmax()] if not snap.empty else None
if top_country_row is not None:
    k2.metric("Top country", top_country_row["Entity"], f"{top_country_row['Total']:,.0f} TWh")
k3.metric("Wind share", f"{(snap['Electricity from wind (TWh)'].sum() / total_now * 100):.1f}%")
k4.metric("Solar share", f"{(snap['Electricity from solar (TWh)'].sum() / total_now * 100):.1f}%")

st.markdown("---")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tabs = st.tabs([
    "World Map",
    "Trends",
    "Rankings",
    "Energy Mix",
    "Heatmap & Distribution",
    "Capacity vs Production",
    "Multi-source",
])

# ===========================================================================
# TAB 1 — WORLD MAP (the headline)
# ===========================================================================
with tabs[0]:
    st.subheader("Hoverable world map — total renewable electricity generation")

    map_metric = st.radio(
        "Map metric",
        options=["Total renewable generation (TWh)", "Renewable share of electricity (%)", "Selected source only"],
        horizontal=True,
    )

    if map_metric == "Total renewable generation (TWh)":
        map_df = snap.copy()
        map_df["value"] = map_df["Total"]
        color_label = "TWh"
        cscale = "Viridis"
    elif map_metric == "Renewable share of electricity (%)":
        map_df = share_el_c[share_el_c["Year"] == selected_year].copy()
        map_df["value"] = map_df["Renewables (% electricity)"]
        color_label = "% electricity"
        cscale = "YlGn"
    else:
        single_src = st.selectbox("Source", list(SOURCE_COLS.keys()))
        map_df = snap.copy()
        map_df["value"] = map_df[SOURCE_COLS[single_src]]
        color_label = f"{single_src} (TWh)"
        cscale = "Plasma"

    fig_map = px.choropleth(
        map_df,
        locations="Code",
        color="value",
        hover_name="Entity",
        hover_data={
            "Code": False,
            "value": ":.2f",
            "Electricity from wind (TWh)": ":.2f" if "Electricity from wind (TWh)" in map_df.columns else False,
            "Electricity from hydro (TWh)": ":.2f" if "Electricity from hydro (TWh)" in map_df.columns else False,
            "Electricity from solar (TWh)": ":.2f" if "Electricity from solar (TWh)" in map_df.columns else False,
        },
        color_continuous_scale=cscale,
        labels={"value": color_label},
        title=f"{map_metric} — {selected_year}",
    )
    fig_map.update_geos(showframe=False, showcoastlines=True, projection_type="natural earth")
    fig_map.update_layout(height=620, margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("##### Animated choropleth — total generation through time")
    anim_df = prod_c[(prod_c["Year"] >= year_range[0]) & (prod_c["Year"] <= year_range[1])].copy()
    anim_df["Total_log"] = np.log1p(anim_df["Total"])
    fig_anim = px.choropleth(
        anim_df,
        locations="Code",
        color="Total_log",
        hover_name="Entity",
        hover_data={"Total": ":.2f", "Total_log": False, "Code": False},
        animation_frame="Year",
        color_continuous_scale="Turbo",
        labels={"Total_log": "log(TWh+1)"},
        range_color=(0, anim_df["Total_log"].max()),
    )
    fig_anim.update_geos(showframe=False, projection_type="natural earth")
    fig_anim.update_layout(height=560, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_anim, use_container_width=True)

# ===========================================================================
# TAB 2 — TRENDS
# ===========================================================================
with tabs[1]:
    st.subheader("Time-series trends")

    world = prod_c.groupby("Year")[list(SOURCE_COLS.values())].sum().reset_index()
    world = world[(world["Year"] >= year_range[0]) & (world["Year"] <= year_range[1])]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Line chart — global generation by source**")
        long = world.melt("Year", var_name="Source", value_name="TWh")
        long["Source"] = long["Source"].map({v: k for k, v in SOURCE_COLS.items()})
        long = long[long["Source"].isin(selected_sources)]
        fig = px.line(long, x="Year", y="TWh", color="Source",
                      color_discrete_map=SOURCE_COLORS, markers=True)
        fig.update_layout(height=420, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Stacked area chart — global energy mix**")
        fig = px.area(long, x="Year", y="TWh", color="Source",
                      color_discrete_map=SOURCE_COLORS)
        fig.update_layout(height=420, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Country comparison — total renewable generation over time**")
    if selected_countries:
        comp = prod_c[prod_c["Entity"].isin(selected_countries)].copy()
        comp = comp[(comp["Year"] >= year_range[0]) & (comp["Year"] <= year_range[1])]
        fig = px.line(comp, x="Year", y="Total", color="Entity", markers=True,
                      labels={"Total": "Total renewables (TWh)"})
        fig.update_layout(height=460, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select countries in the sidebar to compare.")

    st.markdown("**Renewable share of electricity — selected countries**")
    if selected_countries:
        share = share_el_c[share_el_c["Entity"].isin(selected_countries)].copy()
        share = share[(share["Year"] >= year_range[0]) & (share["Year"] <= year_range[1])]
        fig = px.line(share, x="Year", y="Renewables (% electricity)", color="Entity", markers=True)
        fig.update_layout(height=420, hovermode="x unified", yaxis_ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True)

# ===========================================================================
# TAB 3 — RANKINGS
# ===========================================================================
with tabs[2]:
    st.subheader(f"Country rankings — {selected_year}")

    top_n = st.slider("Top N countries", 5, 30, 15)

    snap_view = snap.copy()
    snap_view["Generation (TWh)"] = snap_view[active_cols].sum(axis=1)
    top = snap_view.nlargest(top_n, "Generation (TWh)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Horizontal bar — total renewable generation**")
        fig = px.bar(top.sort_values("Generation (TWh)"), x="Generation (TWh)", y="Entity",
                     orientation="h", color="Generation (TWh)", color_continuous_scale="Viridis",
                     text_auto=".1f")
        fig.update_layout(height=560)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Stacked bar — energy mix per country**")
        stack_long = top.melt(id_vars=["Entity"], value_vars=active_cols,
                              var_name="Source", value_name="TWh")
        stack_long["Source"] = stack_long["Source"].map({v: k for k, v in SOURCE_COLS.items()})
        fig = px.bar(stack_long, x="Entity", y="TWh", color="Source",
                     color_discrete_map=SOURCE_COLORS)
        fig.update_layout(height=560, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Grouped bar — same data, side-by-side**")
    fig = px.bar(stack_long, x="Entity", y="TWh", color="Source", barmode="group",
                 color_discrete_map=SOURCE_COLORS)
    fig.update_layout(height=440, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# ===========================================================================
# TAB 4 — ENERGY MIX
# ===========================================================================
with tabs[3]:
    st.subheader(f"Energy mix — {selected_country_single}, {selected_year}")

    row = prod_c[(prod_c["Entity"] == selected_country_single) & (prod_c["Year"] == selected_year)]
    if row.empty:
        st.warning("No data for this country/year combination.")
    else:
        mix = pd.DataFrame({
            "Source": list(SOURCE_COLS.keys()),
            "TWh": [row[SOURCE_COLS[k]].iloc[0] for k in SOURCE_COLS],
        })

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Pie chart**")
            fig = px.pie(mix, names="Source", values="TWh",
                         color="Source", color_discrete_map=SOURCE_COLORS)
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Donut chart**")
            fig = px.pie(mix, names="Source", values="TWh", hole=0.55,
                         color="Source", color_discrete_map=SOURCE_COLORS)
            fig.update_traces(textinfo="percent+label")
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Treemap — global generation, top 25 countries (sized by total, colored by mix)**")
    top25 = snap.nlargest(25, "Total")
    tree_long = top25.melt(id_vars=["Entity"], value_vars=list(SOURCE_COLS.values()),
                           var_name="Source", value_name="TWh")
    tree_long["Source"] = tree_long["Source"].map({v: k for k, v in SOURCE_COLS.items()})
    fig = px.treemap(tree_long, path=["Entity", "Source"], values="TWh",
                     color="Source", color_discrete_map=SOURCE_COLORS)
    fig.update_layout(height=560)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Sunburst — drill into any country's mix**")
    fig = px.sunburst(tree_long, path=["Entity", "Source"], values="TWh",
                      color="Source", color_discrete_map=SOURCE_COLORS)
    fig.update_layout(height=620)
    st.plotly_chart(fig, use_container_width=True)

# ===========================================================================
# TAB 5 — HEATMAP & DISTRIBUTIONS
# ===========================================================================
with tabs[4]:
    st.subheader("Heatmap & statistical distributions")

    st.markdown("**Heatmap — top 20 countries × year (total renewable TWh)**")
    top20_names = (prod_c[prod_c["Year"] == selected_year]
                   .nlargest(20, "Total")["Entity"].tolist())
    heat = prod_c[prod_c["Entity"].isin(top20_names)
                  & prod_c["Year"].between(year_range[0], year_range[1])]
    pivot = heat.pivot_table(index="Entity", columns="Year", values="Total", aggfunc="sum")
    pivot = pivot.reindex(top20_names)
    fig = px.imshow(pivot, color_continuous_scale="Viridis", aspect="auto",
                    labels=dict(color="TWh"))
    fig.update_layout(height=540)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    melted = snap.melt(id_vars=["Entity"], value_vars=list(SOURCE_COLS.values()),
                       var_name="Source", value_name="TWh")
    melted["Source"] = melted["Source"].map({v: k for k, v in SOURCE_COLS.items()})
    melted = melted[melted["TWh"] > 0]

    with col1:
        st.markdown("**Box plot — distribution by source (log scale)**")
        fig = px.box(melted, x="Source", y="TWh", color="Source",
                     color_discrete_map=SOURCE_COLORS, points="outliers", log_y=True)
        fig.update_layout(height=460, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Violin plot — distribution shape**")
        fig = px.violin(melted, x="Source", y="TWh", color="Source", box=True,
                        color_discrete_map=SOURCE_COLORS, log_y=True)
        fig.update_layout(height=460, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Histogram — countries by total renewable generation (log)**")
    hist_df = snap[snap["Total"] > 0].copy()
    hist_df["log_total"] = np.log10(hist_df["Total"])
    fig = px.histogram(hist_df, x="log_total", nbins=30,
                       labels={"log_total": "log10(TWh)"})
    fig.update_layout(height=380, bargap=0.05)
    st.plotly_chart(fig, use_container_width=True)

# ===========================================================================
# TAB 6 — CAPACITY vs PRODUCTION
# ===========================================================================
with tabs[5]:
    st.subheader("Installed capacity vs actual generation")

    sc = solar_cap.dropna(subset=["Code"]).copy()
    sc = sc[sc["Code"].str.len() == 3]
    sc = sc.rename(columns={"Solar PV Capacity": "Solar Capacity"}) if "Solar PV Capacity" in sc.columns else sc
    cap_col = [c for c in sc.columns if "apacity" in c][0]
    sc = sc.rename(columns={cap_col: "Solar_Cap_GW"})

    wc = wind_cap.dropna(subset=["Code"]).copy()
    wc = wc[wc["Code"].str.len() == 3]
    wcol = [c for c in wc.columns if "apacity" in c][0]
    wc = wc.rename(columns={wcol: "Wind_Cap_GW"})

    merged = (prod_c[["Entity", "Code", "Year",
                      "Electricity from solar (TWh)", "Electricity from wind (TWh)"]]
              .merge(sc[["Code", "Year", "Solar_Cap_GW"]], on=["Code", "Year"], how="left")
              .merge(wc[["Code", "Year", "Wind_Cap_GW"]], on=["Code", "Year"], how="left"))

    bub = merged[merged["Year"] == selected_year].dropna(subset=["Solar_Cap_GW", "Wind_Cap_GW"])
    bub = bub[(bub["Solar_Cap_GW"] > 0) | (bub["Wind_Cap_GW"] > 0)]

    st.markdown(f"**Bubble chart — solar capacity vs solar generation, sized by wind generation ({selected_year})**")
    if not bub.empty:
        fig = px.scatter(bub, x="Solar_Cap_GW", y="Electricity from solar (TWh)",
                         size="Electricity from wind (TWh)", color="Entity",
                         hover_name="Entity", size_max=50, log_x=True, log_y=True,
                         labels={"Solar_Cap_GW": "Solar capacity (GW, log)",
                                 "Electricity from solar (TWh)": "Solar generation (TWh, log)"})
        fig.update_layout(height=560, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No capacity data for this year.")

    st.markdown("**Animated bubble — solar capacity & generation over the years**")
    anim = merged[(merged["Year"] >= max(year_range[0], 2000))
                  & (merged["Year"] <= year_range[1])
                  & merged["Solar_Cap_GW"].notna()
                  & (merged["Solar_Cap_GW"] > 0)
                  & (merged["Electricity from solar (TWh)"] > 0)].copy()
    if not anim.empty:
        fig = px.scatter(anim, x="Solar_Cap_GW", y="Electricity from solar (TWh)",
                         size="Solar_Cap_GW", color="Entity", hover_name="Entity",
                         animation_frame="Year", size_max=45,
                         log_x=True, log_y=True,
                         range_x=[0.001, anim["Solar_Cap_GW"].max() * 1.5],
                         range_y=[0.001, anim["Electricity from solar (TWh)"].max() * 1.5],
                         labels={"Solar_Cap_GW": "Solar capacity (GW)",
                                 "Electricity from solar (TWh)": "Solar generation (TWh)"})
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ===========================================================================
# TAB 7 — MULTI-SOURCE
# ===========================================================================
with tabs[6]:
    st.subheader("Multi-source comparisons")

    st.markdown("**Radar chart — energy-mix fingerprints**")
    if selected_countries:
        radar_df = prod_c[(prod_c["Entity"].isin(selected_countries))
                          & (prod_c["Year"] == selected_year)]
        fig = go.Figure()
        for _, r in radar_df.iterrows():
            fig.add_trace(go.Scatterpolar(
                r=[r[SOURCE_COLS[s]] for s in SOURCE_COLS],
                theta=list(SOURCE_COLS.keys()),
                fill="toself",
                name=r["Entity"],
            ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, type="log")),
            height=560,
            title=f"Generation by source — log scale (TWh) — {selected_year}",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pick countries in the sidebar to compare.")

    st.markdown("**Parallel coordinates — countries across all four sources**")
    pc_df = snap.nlargest(30, "Total").copy()
    fig = px.parallel_coordinates(
        pc_df,
        dimensions=list(SOURCE_COLS.values()) + ["Total"],
        color="Total", color_continuous_scale="Viridis",
        labels={**{v: k for k, v in SOURCE_COLS.items()}, "Total": "Total"},
    )
    fig.update_layout(height=520)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Sankey — top-15 countries → energy source flow**")
    top15 = snap.nlargest(15, "Total")
    countries = top15["Entity"].tolist()
    sources = list(SOURCE_COLS.keys())
    labels = countries + sources
    src_idx, tgt_idx, vals, link_colors = [], [], [], []
    color_hex = SOURCE_COLORS

    def _hex_to_rgba(h: str, alpha: float = 0.5) -> str:
        h = h.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    for i, c in enumerate(countries):
        for j, s in enumerate(sources):
            v = top15[top15["Entity"] == c][SOURCE_COLS[s]].iloc[0]
            if v > 0:
                src_idx.append(i)
                tgt_idx.append(len(countries) + j)
                vals.append(v)
                link_colors.append(_hex_to_rgba(color_hex[s], 0.5))
    fig = go.Figure(data=[go.Sankey(
        node=dict(label=labels, pad=15, thickness=20,
                  color=["#888"] * len(countries) + [color_hex[s] for s in sources]),
        link=dict(source=src_idx, target=tgt_idx, value=vals, color=link_colors),
    )])
    fig.update_layout(height=620, title=f"Renewable flow — top 15 countries — {selected_year}")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Scatter matrix — pairwise relationships between sources**")
    sm = snap.nlargest(60, "Total")
    fig = px.scatter_matrix(
        sm, dimensions=list(SOURCE_COLS.values()),
        color="Total", color_continuous_scale="Viridis",
        hover_name="Entity",
        labels={v: k for k, v in SOURCE_COLS.items()},
    )
    fig.update_traces(diagonal_visible=False, showupperhalf=False, marker=dict(size=5))
    fig.update_layout(height=620)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption(
    "Built with Streamlit + Plotly. Datasets: Our World in Data (renewable production, share of electricity, "
    "installed solar PV / wind capacity). All charts respond to the sidebar filters; hover for tooltips."
)
