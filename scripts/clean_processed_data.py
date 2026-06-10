#!/usr/bin/env python3
"""clean_processed_data.py

Utility script to fix datatype inconsistencies in the **already‑generated**
`steam_games_with_genres.csv` without re‑running the heavy collection pipeline.
It performs the same dtype coercions that were added to `collect_steam_data.py`
but operates directly on the saved CSV.

Steps:
1. Load the CSV.
2. Cast numeric columns to appropriate pandas nullable dtypes:
   - `price`        → float64 (USD, already in dollars)
   - `is_free`      → int64 (0/1)
   - `year`         → Int64 (nullable integer)
   - Integer‑like columns (`positive_ratings`, `negative_ratings`, `total_ratings`,
     `ccu`, `discount`, `owners_min`, `owners_max`, `owners_midpoint`) → Int64
   - One‑hot genre columns (all columns starting with `genre_` except the
     placeholder `genre_X (22 columns)`) → int64 (0/1)
3. Clean any stray non‑numeric values (coerce errors to NaN, then to the nullable
   dtype).
4. Overwrite the original file (the same path used by the dashboard).

The script prints a brief summary of the dtype changes and the number of rows
that were modified.
"""

import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration – paths are relative to the project root.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "steam_games_with_genres.csv"

def load_processed():
    df = pd.read_csv(RAW_PROCESSED_PATH)
    return df

def clean_dtype(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Price – already in USD, ensure float64
    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce").astype("float64")

    # 2. Binary flag for free games (0/1)
    if "is_free" in df.columns:
        df["is_free"] = df["is_free"].astype(bool).astype("int64")

    # Cast release_date to datetime
    if "release_date" in df.columns:
        df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    # 3. Year as nullable integer (Int64)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # 4. Integer‑like columns → nullable Int64
    int_cols = [
        "positive_ratings",
        "negative_ratings",
        "total_ratings",
        "ccu",
        "discount",
        "owners_min",
        "owners_max",
        "owners_midpoint",
    ]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # 5. One‑hot genre columns – ensure only 0 or 1 and cast to int64
    genre_onehot = [c for c in df.columns if c.startswith("genre_") and c not in ("genre_X (22 columns)", "genres")]
    for col in genre_onehot:
        if col in df.columns:
            # Coerce any non‑numeric values to NaN, then fill with 0, finally cast
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")
            # Clip values to {0,1} just in case
            df[col] = df[col].clip(0, 1)

    return df

def main():
    print("--- Cleaning processed Steam data ---")
    df = load_processed()
    original_shape = df.shape
    df_clean = clean_dtype(df)

    # Overwrite the original CSV (preserve column order)
    df_clean.to_csv(RAW_PROCESSED_PATH, index=False)
    print(f"Cleaned {original_shape[0]} rows, {df_clean.shape[1]} columns.")
    print(f"File overwritten at: {RAW_PROCESSED_PATH}")
    # Quick sanity check – show dtype summary
    print("\nFinal dtypes:")
    print(df_clean.dtypes)

if __name__ == "__main__":
    main()
