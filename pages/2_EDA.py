"""Page 2 — EDA (Exploratory Data Analysis)

Documents the exploratory analysis: genre distribution, price analysis,
temporal trends, and popularity vs quality relationships.
"""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="EDA", layout="wide")

from state import init_state, load_data, apply_filters, genre_cols, genres_list, total_ratings_for
from utils import inject_custom_css, apply_plotly_theme

init_state()
df = load_data()
if df is None:
    st.error("Dataset not found!")
    st.stop()

df_f = apply_filters(df)
inject_custom_css()

if len(df_f) < 5:
    st.warning("Not enough data after filters. Please adjust sidebar filters.")
    st.stop()

st.title("Exploratory Data Analysis")
st.caption("Exploring relationships between price, genre, and player satisfaction")
st.caption(f"Showing **{len(df_f):,}** of **{len(df):,}** games after filters")

gcols = genre_cols(df)
gl = genres_list(df)

# ── GENRE ANALYSIS ────────────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("Genre Analysis")
tab1, tab2 = st.tabs(["Distribution", "Performance"])
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Game Count by Genre (Top 10)")
        counts = df_f[gcols].sum().sort_values(ascending=False).head(10)
        counts.index = [i.replace("genre_", "") for i in counts.index]
        st.bar_chart(counts)
    with c2:
        st.subheader("Weighted Wilson Score by Genre (Top 10)")
        tr = total_ratings_for(df_f)
        perf = []
        for col in gcols:
            name = col.replace("genre_", "")
            mask = df_f[col] == 1
            if mask.sum() >= 30:
                wws = (df_f.loc[mask, "wilson_score"] * tr[mask]).sum() / tr[mask].sum()
                # pyrefly: ignore [unnecessary-type-conversion]
                perf.append({"Genre": name, "Weighted Wilson": wws, "Games": int(mask.sum())})
        if perf:
            perf_df = pd.DataFrame(perf).sort_values(by="Weighted Wilson", ascending=False)
            st.dataframe(perf_df.head(10), use_container_width=True, hide_index=True)
        else:
            st.info("No genres with at least 30 games match the selected filters.")

with tab2:
    st.subheader("Genre Performance Table")
    tr = total_ratings_for(df_f)
    perf = []
    for col in gcols:
        name = col.replace("genre_", "")
        sub = df_f[df_f[col] == 1]
        if len(sub) >= 30:
            wws = (sub["wilson_score"] * tr[sub.index]).sum() / tr[sub.index].sum()
            perf.append({
                "Genre": name,
                "Games": len(sub),
                "Avg Wilson Score": sub["wilson_score"].mean(),
                "Weighted Wilson Score": wws,
                "Avg Price": sub["price"].mean(),
            })
    if perf:
        perf_df = pd.DataFrame(perf).sort_values(by="Weighted Wilson Score", ascending=False)
        st.dataframe(perf_df, use_container_width=True, hide_index=True)
    else:
        st.info("No genres with at least 30 games match the selected filters.")
st.markdown("</div>", unsafe_allow_html=True)

# ── PRICE ANALYSIS ────────────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("Price Analysis")
tab_p1, tab_p2, tab_p3 = st.tabs(["Price vs Wilson Score", "Price Distribution", "Price Group Summary"])
with tab_p1:
    if len(df_f) > 0:
        tr = total_ratings_for(df_f)
        fig = px.scatter(
            df_f, x="price", y="wilson_score",
            size=tr if tr.sum() > 0 else None,
            color="price_group" if "price_group" in df_f.columns else None,
            hover_data=["name"], opacity=0.7,
            title="Price vs Wilson Score (bubble size = total ratings)",
            labels={"price": "Price (USD)", "wilson_score": "Wilson Score"},
        )
        fig = apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
with tab_p2:
    if "price" in df_f.columns:
        fig = px.histogram(df_f, x="price", nbins=40, title="Price Distribution (USD)", labels={"price": "Price (USD)"})
        fig = apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
with tab_p3:
    if "price_group" in df_f.columns:
        pg_stats = df_f.groupby("price_group").agg(
            games=("name", "count"),
            avg_wilson=("wilson_score", "mean"),
            std_wilson=("wilson_score", "std"),
            avg_price=("price", "mean"),
        ).round(3)
        # Reorder logically
        price_group_order = ['Free', '<$10', '$10-30', '>$30']
        pg_stats = pg_stats.reindex([g for g in price_group_order if g in pg_stats.index])
        st.dataframe(pg_stats, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)



# ── POPULARITY VS QUALITY ─────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("Popularity vs Quality (Owners vs Wilson Score)")
st.caption("Does a higher number of owners correlate with a higher, more stable Wilson Score?")

if "owners_midpoint" in df_f.columns and "wilson_score" in df_f.columns:
    tab_o1, tab_o2 = st.tabs(["Scatter Plot", "Boxplot by Owner Tiers"])
    with tab_o1:
        fig_scatter = px.scatter(
            df_f, x="owners_midpoint", y="wilson_score",
            log_x=True,
            color="wilson_score" if "wilson_score" in df_f.columns else None,
            hover_data=["name", "owners_min", "owners_max"],
            opacity=0.6,
            title="Owners vs Wilson Score (Log Scale)",
            color_continuous_scale="Viridis",
        )
        fig_scatter = apply_plotly_theme(fig_scatter)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with tab_o2:
        df_f_plot = df_f.copy()
        def get_popularity_tier(row):
            if row['owners_min_known'] == False or pd.isna(row['owners_midpoint']):
                return '1. Very Low (<20k)'
            mid = row['owners_midpoint']
            if mid <= 75000:
                return '2. Low (20k-100k)'
            elif mid <= 350000:
                return '3. Medium (100k-500k)'
            elif mid <= 1500000:
                return '4. High (500k-2M)'
            else:
                return '5. Very High (>2M)'
        df_f_plot["popularity_tier"] = df_f_plot.apply(get_popularity_tier, axis=1)
        popularity_order = ['1. Very Low (<20k)', '2. Low (20k-100k)', '3. Medium (100k-500k)', '4. High (500k-2M)', '5. Very High (>2M)']
        
        fig_box = px.box(
            df_f_plot, x="popularity_tier", y="wilson_score",
            title="Wilson Score Distribution by Popularity Tier",
            category_orders={"popularity_tier": popularity_order},
            color="popularity_tier",
        )
        fig_box.update_layout(xaxis_tickangle=-45)
        fig_box = apply_plotly_theme(fig_box)
        st.plotly_chart(fig_box, use_container_width=True)
else:
    st.info("Missing 'owners_midpoint' or 'wilson_score' columns in the dataset.")
st.markdown("</div>", unsafe_allow_html=True)

# ── GENRE CO-OCCURRENCE HEATMAP ────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("Genre Co-occurrence Matrix")
st.caption(
    "Which genres appear together? Darker cells = stronger co-occurrence "
    "(games tagged with both genres)."
)
if len(df_f) > 0 and len(gcols) >= 2:
    genre_binary = df_f[gcols]
    co_mat = genre_binary.T.dot(genre_binary)
    # Mask upper triangle for cleaner display
    mask = np.triu(np.ones_like(co_mat, dtype=bool), k=1)
    co_mat_display = co_mat.where(~mask)
    fig_heat = px.imshow(
        co_mat_display,
        labels=dict(color="Games"),
        aspect="auto",
        color_continuous_scale="Blues",
        title="",
    )
    fig_heat.update_layout(xaxis_tickangle=-45)
    fig_heat = apply_plotly_theme(fig_heat)
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Not enough data to compute genre co-occurrence.")
st.markdown("</div>", unsafe_allow_html=True)

# ── DEVELOPER RANKINGS ────────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("Top Developers (>= 3 games)")
tr = total_ratings_for(df_f)
dev_stats = []
for dev, sub in df_f.groupby("developer"):
    if len(sub) >= 3:
        wws = (sub["wilson_score"] * tr[sub.index]).sum() / tr[sub.index].sum()
        dev_stats.append({
            "Developer": dev,
            "Games": len(sub),
            "Weighted Wilson Score": wws,
            "Avg Price": sub["price"].mean(),
        })

if dev_stats:
    dev_df = pd.DataFrame(dev_stats).sort_values(by="Weighted Wilson Score", ascending=False)
    st.dataframe(dev_df.head(15), use_container_width=True, hide_index=True)

    # Developer Treemap: top 30 by game count, colored by avg Wilson Score
    if len(dev_df) > 0:
        treemap_df = dev_df.head(30).copy()
        treemap_df["developer_short"] = treemap_df["Developer"].str.slice(0, 30)
        fig_tree = px.treemap(
            treemap_df,
            path=["developer_short"],
            values="Games",
            color="Weighted Wilson Score",
            color_continuous_scale="RdYlGn",
            title="Top 30 Developers — Size = Game Count, Color = Weighted Wilson Score",
        )
        fig_tree = apply_plotly_theme(fig_tree)
        st.plotly_chart(fig_tree, use_container_width=True)
else:
    st.info("No developers with at least 3 games match the selected filters.")
st.markdown("</div>", unsafe_allow_html=True)
