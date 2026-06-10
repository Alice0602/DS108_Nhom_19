"""Page 4 — Dataset Curation, Data Dictionary & QA Schema Explorer

Interactive data dictionary, automated QA validation, target variable evaluation,
and dataset search/export functionality.
"""
import io

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Schema & Curation", layout="wide")

from state import init_state, load_data, apply_filters, total_ratings_for
from utils import inject_custom_css, apply_plotly_theme

init_state()
df = load_data()
if df is None:
    st.error("Dataset not found!")
    st.stop()

df_f = apply_filters(df)
inject_custom_css()

st.title("Dataset Curation & Schema Explorer")
st.caption("Automated QA Validation, Target Evaluation, and Interactive Data Dictionary")
st.caption(f"Showing **{len(df_f):,}** games (after filters)")

# Compute total_ratings on the fly
df_f = df_f.copy()
df_f["total_ratings"] = total_ratings_for(df_f)

# ── TARGET VARIABLE EVALUATION ────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("1. Target Variable Evaluation: Wilson Score")
st.markdown(
    "**The Small-Sample Bias Problem:**  \n"
    "A game with 3 positive reviews and 0 negative reviews has a raw rating ratio of **100%** (1.0).  \n"
    "A blockbuster game with 10,000 positive and 500 negative reviews has a rating ratio of **95.2%** (0.952).  \n"
    "Using rating ratio as the target variable leads to severe rating inflation and penalizes popular, highly reviewed games."
)
st.markdown(
    "**The Wilson Score Interval Solution:**  \n"
    "By computing the lower bound of the Wilson confidence interval (at 95% confidence level, z = 1.96), "
    "we mathematically penalize games with low rating volume.  \n"
    "- Game with 3 positive / 0 negative -> Wilson Score: **~56%**  \n"
    "- Game with 10,000 positive / 500 negative -> Wilson Score: **~94.8%**"
)

if len(df_f) > 0:
    fig_target = px.scatter(
        df_f, x="rating_ratio", y="wilson_score",
        color="total_ratings", hover_data=["name", "total_ratings"],
        color_continuous_scale="Viridis",
        title="Wilson Score vs Rating Ratio (Convergence at Large Sample Sizes)",
        labels={"rating_ratio": "Rating Ratio (Raw)", "wilson_score": "Wilson Score (Target)", "total_ratings": "Total Ratings"},
    )
    fig_target = apply_plotly_theme(fig_target)
    st.plotly_chart(fig_target, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# ── DATA DICTIONARY ───────────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("2. Interactive Data Dictionary")
st.markdown("This dictionary documents the final, curated columns, their data types, descriptions, and validation constraints.")

schema_data = [
    {"Column": "appid", "Type": "int64", "Source": "SteamSpy", "Storage": "Stored (CSV)", "Description": "Unique Steam App ID. Primary key.", "QA Constraint": "Unique, non-null"},
    {"Column": "name", "Type": "string", "Source": "SteamSpy + Store", "Storage": "Stored (CSV)", "Description": "Official game title on Steam.", "QA Constraint": "Non-null"},
    {"Column": "release_date", "Type": "date (YYYY-MM-DD)", "Source": "Steam Store API", "Storage": "Stored (CSV)", "Description": "Official release date.", "QA Constraint": "Valid date format"},
    {"Column": "year", "Type": "int64", "Source": "Derived", "Storage": "Stored (CSV)", "Description": "Release year extracted from release_date.", "QA Constraint": "2022 <= year <= 2026"},
    {"Column": "developer", "Type": "string", "Source": "SteamSpy + Store (merged)", "Storage": "Stored (CSV)", "Description": "Game developer name (unified from both APIs).", "QA Constraint": "Non-null"},
    {"Column": "publisher", "Type": "string", "Source": "SteamSpy + Store (merged)", "Storage": "Stored (CSV)", "Description": "Game publisher name (unified from both APIs).", "QA Constraint": "Nullable"},
    {"Column": "price", "Type": "float64", "Source": "Derived (Store API / 100)", "Storage": "Stored (CSV)", "Description": "Price in USD. Fixed from cents-to-USD bug.", "QA Constraint": "price >= 0.0"},
    {"Column": "is_free", "Type": "int64 (binary)", "Source": "Steam Store API", "Storage": "Stored (CSV)", "Description": "1 if game is free-to-play, 0 otherwise.", "QA Constraint": "0 or 1; implies price == 0"},
    {"Column": "discount", "Type": "int64", "Source": "Steam Store API", "Storage": "Stored (CSV)", "Description": "Current discount percentage (0-100).", "QA Constraint": "0 <= discount <= 100"},
    {"Column": "price_group", "Type": "string (categorical)", "Source": "Derived", "Storage": "Stored (CSV)", "Description": "Pricing segment: Free, <$10, $10-30, >$30.", "QA Constraint": "One of: Free, <$10, $10-30, >$30"},
    {"Column": "positive_ratings", "Type": "int64", "Source": "SteamSpy API", "Storage": "Stored (CSV)", "Description": "Count of positive user reviews.", "QA Constraint": ">= 0"},
    {"Column": "negative_ratings", "Type": "int64", "Source": "SteamSpy API", "Storage": "Stored (CSV)", "Description": "Count of negative user reviews.", "QA Constraint": ">= 0"},
    {"Column": "total_ratings", "Type": "int64", "Source": "Derived", "Storage": "Calculated (On-the-fly)", "Description": "Total count of user reviews (positive + negative).", "QA Constraint": ">= 100"},
    {"Column": "rating_ratio", "Type": "float64", "Source": "Derived", "Storage": "Stored (CSV)", "Description": "Raw positive ratio: positive / (positive + negative).", "QA Constraint": "0.0 <= rating_ratio <= 1.0"},
    {"Column": "wilson_score", "Type": "float64", "Source": "Derived (Wilson CI)", "Storage": "Stored (CSV)", "Description": "Lower bound of Wilson Score Interval (z=1.96). Target variable.", "QA Constraint": "0.0 <= wilson_score <= 1.0"},
    {"Column": "owners_min", "Type": "int64 (nullable)", "Source": "Derived (SteamSpy)", "Storage": "Stored (CSV)", "Description": "Lower bound of estimated owner range. NaN for '0..20,000' bucket (MNAR).", "QA Constraint": ">= 0 or NaN"},
    {"Column": "owners_max", "Type": "int64", "Source": "Derived (SteamSpy)", "Storage": "Stored (CSV)", "Description": "Upper bound of estimated owner range.", "QA Constraint": ">= owners_min"},
    {"Column": "owners_midpoint", "Type": "int64", "Source": "Derived", "Storage": "Stored (CSV)", "Description": "Midpoint of owner range: (owners_min + owners_max) / 2.", "QA Constraint": ">= 0"},
    {"Column": "owners_min_known", "Type": "bool", "Source": "Derived", "Storage": "Stored (CSV)", "Description": "True if owners_min is reliable, False if MNAR (bucket '0..20,000').", "QA Constraint": "True or False"},
    {"Column": "ccu", "Type": "int64", "Source": "SteamSpy API", "Storage": "Stored (CSV)", "Description": "Peak concurrent users. MNAR: all 0 after 2023.", "QA Constraint": ">= 0"},
    {"Column": "genres", "Type": "list[string]", "Source": "Steam Store API", "Storage": "Stored (CSV)", "Description": "List of genre labels from the store page.", "QA Constraint": "List of strings"},
    {"Column": "genre_X (22 cols)", "Type": "int64 (binary)", "Source": "Derived (One-Hot)", "Storage": "Stored (CSV)", "Description": "Binary indicator (0/1) for each genre category.", "QA Constraint": "0 or 1"},
]
schema_df = pd.DataFrame(schema_data)
st.dataframe(schema_df, use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

# ── AUTOMATED QA TESTS ────────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("3. Automated Quality Assurance Checklist")
st.markdown("Automated QA assertion checks on the dataset to verify schema compliance.")

qa_checks = []
if len(df_f) > 0:
    # 1. Uniqueness of appid
    qa_checks.append({
        "QA Check": "AppID Uniqueness",
        "Constraint": "No duplicate game records",
        "Status": "PASS" if df_f["appid"].nunique() == len(df_f) else "FAIL",
        "Details": f"{df_f['appid'].nunique()} unique IDs / {len(df_f)} total records",
    })
    # 2. Non-negative prices
    qa_checks.append({
        "QA Check": "Price Non-Negativity",
        "Constraint": "Price >= $0.00",
        "Status": "PASS" if bool((df_f["price"] >= 0).all()) else "FAIL",
        "Details": f"Minimum price: ${df_f['price'].min():.2f}",
    })
    # 3. Rating ratio bounds
    qa_checks.append({
        "QA Check": "Rating Ratio bounds",
        "Constraint": "0.0 <= rating_ratio <= 1.0",
        "Status": "PASS" if bool(df_f["rating_ratio"].between(0, 1).all()) else "FAIL",
        "Details": f"Range: [{df_f['rating_ratio'].min():.3f}, {df_f['rating_ratio'].max():.3f}]",
    })
    # 4. Wilson score bounds
    if "wilson_score" in df_f.columns:
        qa_checks.append({
            "QA Check": "Wilson Score bounds",
            "Constraint": "0.0 <= wilson_score <= 1.0",
            "Status": "PASS" if bool(df_f["wilson_score"].between(0, 1).all()) else "FAIL",
            "Details": f"Range: [{df_f['wilson_score'].min():.3f}, {df_f['wilson_score'].max():.3f}]",
        })
    # 5. Year bounds
    qa_checks.append({
        "QA Check": "Year range validation",
        "Constraint": "Release year in [2022, 2026]",
        "Status": "PASS" if bool(df_f["year"].between(2022, 2026).all()) else "FAIL",
        "Details": f"Release years: {sorted(df_f['year'].unique())}",
    })
    # 6. Quality threshold (MIN_RATINGS >= 100)
    qa_checks.append({
        "QA Check": "Total ratings threshold",
        "Constraint": "Total ratings >= 100",
        "Status": "PASS" if bool((df_f["total_ratings"] >= 100).all()) else "FAIL",
        "Details": f"Minimum ratings: {df_f['total_ratings'].min():,}",
    })
    # 7. Redundant check (runs on df, the raw stored CSV columns)
    redundant_cols = ["store_name", "developer_spy", "developer_store", "publisher_spy", "publisher_store",
                      "price_spy", "price_store", "initialprice", "temp_total", "owners", "total_ratings"]
    cols_dropped = not any(c in df.columns for c in redundant_cols)
    qa_checks.append({
        "QA Check": "Redundant Columns Check",
        "Constraint": "Raw/temporary columns dropped",
        "Status": "PASS" if cols_dropped else "FAIL",
        "Details": "All redundant columns removed" if cols_dropped else "Detected duplicate variables",
    })
    # 8. owners_min MNAR flag
    qa_checks.append({
        "QA Check": "MNAR owners_min handling",
        "Constraint": "owners_min is NaN for '0..20,000' bucket",
        "Status": "PASS" if bool(df_f[df_f["owners_min_known"] == False]["owners_min"].isna().all()) else "FAIL",
        "Details": "MNAR bucket correctly marked as NaN",
    })
    # 9. is_free/price consistency
    qa_checks.append({
        "QA Check": "is_free/price consistency",
        "Constraint": "is_free=1 implies price=0",
        "Status": "PASS" if ((df_f["is_free"] == 1) & (df_f["price"] > 0)).sum() == 0 else "FAIL",
        "Details": "All free games have price=0",
    })

qa_report_df = pd.DataFrame(qa_checks)
st.dataframe(qa_report_df, use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

# ── DATASET SEARCH & EXPORT ───────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("4. Search and Export Dataset")
st.markdown("Filter the curated dataset and download your custom slice as a CSV file.")

search_query = st.text_input("Search games by name", "")
developer_filter = st.selectbox("Filter by Developer", ["All"] + sorted(df_f["developer"].dropna().unique().tolist()))

export_df = df_f.copy()
if search_query:
    export_df = export_df[export_df["name"].str.contains(search_query, case=False, na=False)]
if developer_filter != "All":
    export_df = export_df[export_df["developer"] == developer_filter]

export_df_display = export_df[["appid", "name", "developer", "price", "year", "total_ratings", "rating_ratio", "wilson_score"]]
assert isinstance(export_df_display, pd.DataFrame)
st.dataframe(
    export_df_display.sort_values(by="wilson_score", ascending=False),
    use_container_width=True, hide_index=True, height=300,
)

csv_buf = io.StringIO()
export_df.to_csv(csv_buf, index=False)
csv_bytes = csv_buf.getvalue().encode("utf-8")
st.download_button(
    label=f"Export {len(export_df):,} games as CSV",
    data=csv_bytes,
    file_name="steam_games_curated_export.csv",
    mime="text/csv",
)
st.markdown("</div>", unsafe_allow_html=True)
