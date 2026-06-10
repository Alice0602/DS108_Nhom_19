#!/usr/bin/env python3
"""
Steam Game Data Collection Script (Real Data)

Combines SteamSpy API (for ratings, playtime) and Steam Store API
(for release dates, genres, prices). Outputs a raw CSV ready for
the cleaning pipeline in notebooks/02_data_cleaning_and_imputation.ipynb.

IMPORTANT: Steam Store API returns price in CENTS (e.g. 1499 = $14.99).
This script divides by 100 before storing so downstream code sees USD.
"""
import logging
import os
import time
from datetime import datetime
from typing import Any

import pandas as pd
import requests
import steamspypi

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MAX_PAGES = 100          # SteamSpy pages (1000 games/page)
REQUEST_DELAY = 1.0      # Seconds between Store API calls
MIN_APPID = 1500000   # Only games released ~2022+ (reduces crawl time)
OUTPUT_PATH = "data/raw/steam_games_raw.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SteamSpy
# ---------------------------------------------------------------------------
def fetch_steamspy_appids(pages: int = MAX_PAGES) -> pd.DataFrame:
    """Return a DataFrame of SteamSpy metadata for *pages* pages."""
    all_data: list[pd.DataFrame] = []
    for page in range(pages):
        try:
            log.info("Fetching SteamSpy page %d ...", page)
            data: dict[str, Any] = steamspypi.download(
                {"request": "all", "page": page}
            )
            if not data:
                log.info("  Empty response, stopping.")
                break
            df = pd.DataFrame(data).T.reset_index()
            df = df.rename(columns={"index": "appid"})
            # Drop duplicate appid column if SteamSpy returns one
            cols = df.columns.tolist()
            dup_count = cols.count("appid")
            if dup_count > 1:
                first = cols.index("appid")
                df = df.iloc[:, : first + 1].join(df.iloc[:, first + 2 :])
            all_data.append(df)
            log.info("  Page %d: %d games", page, len(df))
        except Exception as exc:
            log.warning("  Error on page %d: %s", page, exc)
            break
        time.sleep(0.5)

    if not all_data:
        return pd.DataFrame()

    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.drop_duplicates(subset="appid", keep="first")
    log.info("Total unique games from SteamSpy: %d", len(combined))
    return combined


# ---------------------------------------------------------------------------
# Steam Store API
# ---------------------------------------------------------------------------
def fetch_store_details(appid: int) -> dict[str, Any] | None:
    """Return parsed JSON for one app, or None on failure."""
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            payload = resp.json()
            app_key = str(appid)
            if app_key in payload and payload[app_key].get("success"):
                return payload[app_key]["data"]
    except requests.RequestException as exc:
        log.debug("Store API error for appid %d: %s", appid, exc)
    return None


def enrich_with_store_data(steamspy_df: pd.DataFrame) -> pd.DataFrame:
    """Merge Steam Store details (release_date, genres, price) into SteamSpy data.

    NOTE: Steam Store API returns price in CENTS. We divide by 100 here
    so every downstream consumer sees USD values.
    """
    appids = steamspy_df["appid"].unique().tolist()
    log.info("Enriching %d games with Steam Store data ...", len(appids))

    records: list[dict[str, Any]] = []
    failed: list[int] = []

    for i, appid in enumerate(appids, 1):
        if i % 100 == 0:
            log.info("  Processed %d / %d", i, len(appids))

        details = fetch_store_details(appid)
        if details:
            price_overview = details.get("price_overview") or {}
            store_price_cents = price_overview.get("final")
            records.append(
                {
                    "appid": appid,
                    "store_name": details.get("name"),
                    "release_date": details.get("release_date", {}).get("date"),
                    "genres": [g["description"] for g in details.get("genres", [])],
                    "developer": (details.get("developers") or [None])[0],
                    "publisher": (details.get("publishers") or [None])[0],
                    # Convert cents -> USD here
                    "store_price": (
                        store_price_cents / 100.0
                        if store_price_cents is not None
                        else None
                    ),
                    "is_free": details.get("is_free", False),
                }
            )
        else:
            failed.append(appid)

        time.sleep(REQUEST_DELAY)

    store_df = pd.DataFrame(records)
    log.info("Successfully enriched: %d | Failed: %d", len(store_df), len(failed))

    # Ensure consistent dtypes before merge
    store_df["appid"] = store_df["appid"].astype("int64")
    steamspy_df["appid"] = steamspy_df["appid"].astype("int64")

    merged = pd.merge(steamspy_df, store_df, on="appid", how="inner")

    # Prefer Store price (already in USD), fall back to SteamSpy price
    spy_price = pd.to_numeric(merged["price"], errors="coerce")
    store_price = merged["store_price"]
    merged["price"] = store_price.where(store_price.notna(), spy_price)
    merged["price"] = merged["price"].fillna(0)

    # Drop the intermediate column so it doesn't leak into raw CSV
    merged = merged.drop(columns=["store_price"], errors="ignore")

    return merged


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------
_DATE_FORMATS = ["%d %b, %Y", "%b %d, %Y", "%Y-%m-%d"]


def parse_release_date(date_str: str | None) -> datetime | None:
    """Parse Steam Store date strings like '21 Aug, 2012'.

    Returns:
        datetime object if parsed successfully, otherwise None.
    """
    if not date_str or pd.isna(date_str):
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    log.debug("Could not parse release_date: %r", date_str)
    return None


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def main() -> None:
    log.info("=" * 60)
    log.info("STEAM GAME DATA COLLECTION (2022-2026)")
    log.info("=" * 60)
    log.info(
        "Config: MAX_PAGES=%d, MIN_APPID=%d, REQUEST_DELAY=%.1fs",
        MAX_PAGES,
        MIN_APPID,
        REQUEST_DELAY,
    )
    log.info("=" * 60)

    os.makedirs("data/raw", exist_ok=True)

    # Step 1: Fetch SteamSpy
    steamspy_df = fetch_steamspy_appids()
    if steamspy_df.empty:
        raise RuntimeError("Failed to fetch SteamSpy data — aborting.")

    # Filter early to reduce Store API calls
    steamspy_df["appid"] = pd.to_numeric(
        steamspy_df["appid"], errors="coerce"
    )
    steamspy_df = steamspy_df[steamspy_df["appid"] >= MIN_APPID].copy()
    # Explicit type assertion for type checkers (filter preserves DataFrame)
    assert isinstance(steamspy_df, pd.DataFrame)
    log.info(
        "After MIN_APPID filter (>= %d): %d games",
        MIN_APPID,
        len(steamspy_df),
    )

    # Step 2: Enrich with Store data
    combined_df = enrich_with_store_data(steamspy_df)

    # Step 3: Parse dates and filter to 2022-2026
    combined_df["release_date"] = combined_df["release_date"].apply(
        parse_release_date
    )
    combined_df["year"] = combined_df["release_date"].dt.year.astype("Int64")

    before = len(combined_df)
    combined_df = combined_df[combined_df["year"].between(2022, 2026)]
    log.info(
        "Filtered to 2022-2026: %d games (from %d)",
        len(combined_df),
        before,
    )

    # Step 4: Save
    combined_df.to_csv(OUTPUT_PATH, index=False)
    log.info("Raw data saved: %s", OUTPUT_PATH)
    log.info("Final shape: %s", combined_df.shape)

    # Quick schema log
    log.info("Columns: %s", list(combined_df.columns))
    log.info(
        "Price range: $%.2f - $%.2f",
        combined_df["price"].min(),
        combined_df["price"].max(),
    )


if __name__ == "__main__":
    main()
