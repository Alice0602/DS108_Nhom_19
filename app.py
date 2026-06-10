"""Streamlit Dashboard — Steam Games Interactive Dashboard (Home Page)"""
import io

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Steam Games Dashboard", layout="wide", initial_sidebar_state="expanded")

from state import init_state, load_data, apply_filters, genre_cols, genres_list, total_ratings_for
from utils import inject_custom_css, apply_plotly_theme

init_state()
df = load_data()
if df is None:
    st.error("Dataset not found! Expected: data/processed/steam_games_with_genres.csv")
    st.stop()

gcols = genre_cols(df)
gl = genres_list(df)

inject_custom_css()

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Dashboard Filters")

    st.markdown("#### Year")
    yr_select = st.multiselect(
        "Select years",
        sorted(df["year"].dropna().unique().astype(int).tolist()),
        default=sorted(df["year"].dropna().unique().astype(int).tolist()),
        key="year_multiselect",
        help="Filter games by their official release year.",
    )
    st.session_state["dashboard.selected_years"] = list(yr_select)

    st.markdown("#### Price (USD)")
    pr_range = st.slider(
        "Price range", 0.0, float(df["price"].max()), (0.0, float(df["price"].max())),
        step=1.0, key="price_slider", help="Filter games within a specific USD price range.",
    )
    st.session_state["dashboard.price_range"] = pr_range

    st.markdown("#### Genre")
    st.session_state["dashboard.selected_genres"] = st.multiselect(
        "Filter genres", gl, default=[], key="genre_multiselect",
        help="Select one or more genres. Games matching ANY selected genre will be shown.",
    )

    st.markdown("---")
    st.markdown(f"**Total games:** {len(df):,}")
    st.caption(f"Period: 2022-2026 | Genres: {len(gcols)}")

# ── APPLY ALL FILTERS ────────────────────────────────────────────────────────
df_f = apply_filters(df)
df_f = df_f.copy()
df_f["total_ratings"] = total_ratings_for(df_f)

# ── HEADER ───────────────────────────────────────────────────────────────────
st.title("Steam Games Interactive Dashboard")
st.caption(f"DS108 Final Project | Dataset Curation & Validation | {len(df_f):,} games shown after filters")

# ── KPI ──────────────────────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Games", f"{len(df_f):,}")
with k2:
    avg_p = df_f["price"].mean() if len(df_f) else 0
    st.metric("Avg Price", f"${avg_p:.2f}")
with k3:
    avg_w = df_f["wilson_score"].mean() if len(df_f) and "wilson_score" in df_f.columns else 0
    st.metric("Avg Wilson Score", f"{avg_w * 100:.1f}%")
with k4:
    total_r = df_f["total_ratings"].sum() if len(df_f) else 0
    st.metric("Total Ratings", f"{total_r:,}")
st.markdown("</div>", unsafe_allow_html=True)

# ── BAR CHART (year distribution) with on_select ────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.subheader("Games by Year (click a bar to filter)")
year_counts = df_f.groupby("year").size().to_frame("count").reset_index()
bar_fig = px.bar(
    year_counts, x="year", y="count", color="count",
    color_continuous_scale="Blues", labels={"year": "Year", "count": "Games"},
    text_auto=True,
)
bar_fig.update_traces(textposition="outside", marker_line_width=0)
bar_fig.update_layout(xaxis=dict(dtick=1, type="linear"), coloraxis_showscale=False, dragmode=False)
bar_fig = apply_plotly_theme(bar_fig)

st.plotly_chart(
    bar_fig, use_container_width=True, on_select="rerun",
    selection_mode="points", key="bar_chart_sel",
)

# Process selection: read from session_state after rerun
bar_sel = st.session_state.get("bar_chart_sel")
cyf = st.session_state.get("dashboard.chart_year_filter")

if bar_sel and isinstance(bar_sel, dict):
    sel_data = bar_sel.get("selection", {})
    pts = sel_data.get("point_indices", [])
    if pts:
        clicked_year = int(year_counts.iloc[pts[0]]["year"])
        if cyf == clicked_year:
            st.session_state["dashboard.chart_year_filter"] = None
            st.rerun()
        else:
            st.session_state["dashboard.chart_year_filter"] = clicked_year
            st.rerun()

if cyf is not None:
    st.info(f"Chart filter active: **{int(cyf)}** — showing only year {int(cyf)}. "
            f"Click the same bar again or press Clear to reset.")
    col_clear, _ = st.columns([1, 4])
    with col_clear:
        if st.button("Clear chart filter"):
            st.session_state["dashboard.chart_year_filter"] = None
            st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# ── SCATTER PLOT (price vs wilson_score) ────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.subheader("Price vs Wilson Score")

if cyf is not None:
    scatter_df = df_f[df_f["year"] == cyf]
else:
    scatter_df = df_f

if len(scatter_df) > 0:
    import scipy.stats as scipy_stats
    if len(scatter_df) >= 3:
        r_val, p_val = scipy_stats.pearsonr(scatter_df["price"], scatter_df["wilson_score"])
        st.caption(f"Overall Pearson correlation: **r = {r_val:.4f}** (p = {p_val:.2e})")
        
    sc = px.scatter(
        scatter_df, x="price", y="wilson_score",
        color="price_group" if "price_group" in scatter_df.columns else None,
        hover_data=["name", "year"],
        opacity=0.7,
        labels={"price": "Price (USD)", "wilson_score": "Wilson Score"},
        title="",
        trendline="ols" if len(scatter_df) >= 5 else None,
        color_discrete_map={
            "Free": "#10b981", "<$10": "#3b82f6",
            "$10-30": "#f59e0b", ">$30": "#ef4444",
        } if "price_group" in scatter_df.columns else None,
    )
    sc.update_layout(legend_title_text="Price Group", dragmode=False)
    sc = apply_plotly_theme(sc)
    st.plotly_chart(sc, use_container_width=True)
else:
    st.info("No data to display for scatter plot.")
st.markdown("</div>", unsafe_allow_html=True)

# ── DATAFRAME ────────────────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.subheader("Game Details")

display_cols = [
    "name", "price", "price_group", "rating_ratio", "wilson_score",
    "year", "developer", "genres", "total_ratings",
]
display_cols = [c for c in display_cols if c in df_f.columns]

df_f_display = df_f[display_cols]
assert isinstance(df_f_display, pd.DataFrame)
st.dataframe(
    df_f_display.sort_values(by="wilson_score", ascending=False),
    use_container_width=True, hide_index=True, height=400,
)

st.caption(f"Showing **{len(df_f):,}** of **{len(df):,}** games")

# ── DOWNLOAD ─────────────────────────────────────────────────────────────────
st.markdown("#### Export filtered data")
csv_buf = io.StringIO()
df_f[display_cols].to_csv(csv_buf, index=False)
csv_bytes = csv_buf.getvalue().encode("utf-8")
st.download_button(
    label=f"Download {len(df_f):,} games as CSV",
    data=csv_bytes,
    file_name="steam_games_filtered.csv",
    mime="text/csv",
)
st.markdown("</div>", unsafe_allow_html=True)
