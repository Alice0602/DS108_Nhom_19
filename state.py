"""Shared state module — single source of truth for data + filters across all pages."""
import os
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "steam_games_with_genres.csv")
KEY = "dashboard"


def init_state() -> None:
    """Initialize session_state with default filter values."""
    defaults = {
        KEY + ".year_range": (2022, 2026),
        KEY + ".price_range": (0.0, 100.0),
        KEY + ".selected_years": [2022, 2023, 2024, 2025, 2026],
        KEY + ".selected_genres": [],
        KEY + ".chart_year_filter": None,
        KEY + ".price_group_filter": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


@st.cache_data
def load_data() -> pd.DataFrame | None:
    """Load the processed dataset from CSV.

    Returns:
        DataFrame with cleaned Steam games data, or None if file not found.
    """
    if not os.path.exists(DATA_PATH):
        return None

    df = pd.read_csv(DATA_PATH)

    # Parse genres column: stored as string representation of list
    if "genres" in df.columns:
        import ast
        df["genres"] = df["genres"].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else x
        )

    # Cast release_date to datetime
    if "release_date" in df.columns:
        df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    # Cast integer and boolean columns to appropriate nullable types
    int_cols = ["owners_min", "owners_max", "ccu", "discount", "positive_ratings", "negative_ratings", "year", "is_free", "owners_midpoint"]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    if "owners_min_known" in df.columns:
        df["owners_min_known"] = df["owners_min_known"].astype(bool)

    return df


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all active filters from session_state to the dataframe.

    Args:
        df: Source dataframe (unfiltered).

    Returns:
        Filtered copy of the dataframe.
    """
    if df is None:
        return pd.DataFrame()

    df_f = df.copy()

    # Year filter
    sy = st.session_state.get(KEY + ".selected_years", [])
    if sy:
        df_f = df_f[df_f["year"].isin(sy)]

    # Price range filter
    pr = st.session_state.get(KEY + ".price_range", (0.0, 100.0))
    if pr:
        df_f = df_f[(df_f["price"] >= pr[0]) & (df_f["price"] <= pr[1])]

    # Genre filter (OR logic: game matches ANY selected genre)
    sg = st.session_state.get(KEY + ".selected_genres", [])
    if sg:
        masks = []
        for g in sg:
            col = f"genre_{g}"
            if col in df_f.columns:
                masks.append(df_f[col] == 1)
        if masks:
            df_f = df_f[pd.concat(masks, axis=1).any(axis=1)]

    # Chart year filter (click-on-bar filter)
    cyf = st.session_state.get(KEY + ".chart_year_filter")
    if cyf is not None:
        df_f = df_f[df_f["year"] == cyf]

    assert isinstance(df_f, pd.DataFrame)
    return df_f


def genre_cols(df: pd.DataFrame) -> list[str]:
    """Get all genre one-hot encoded column names.

    Args:
        df: Source dataframe.

    Returns:
        List of column names starting with 'genre_'.
    """
    if df is None:
        return []
    return [c for c in df.columns if c.startswith("genre_")]


def genres_list(df: pd.DataFrame) -> list[str]:
    """Get sorted list of unique genre names (without 'genre_' prefix).

    Args:
        df: Source dataframe.

    Returns:
        Sorted list of genre names.
    """
    if df is None:
        return []
    return sorted([c.replace("genre_", "") for c in genre_cols(df)])


def total_ratings_for(df):
        """Compute total ratings as sum of positive and negative ratings.

        Replaces the dropped 'total_ratings' column with a derived value
        to avoid redundancy (total_ratings was always equal to pos + neg).

        Args:
            df: Dataframe with 'positive_ratings' and 'negative_ratings' columns.

        Returns:
            Series of total ratings.
        """
        return df["positive_ratings"] + df["negative_ratings"]
