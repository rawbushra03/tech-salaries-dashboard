"""Utilities for loading and standardising the salary dataset.

The dashboard can receive either the raw CSV from the public data source or the
already processed CSV committed in ``data/``.  Keeping ``clean_data`` here,
separate from Streamlit, makes the same pipeline usable by the dashboard,
notebooks, and command-line scripts.
"""

from pathlib import Path
from typing import Optional, Union

import pandas as pd


MIN_WORK_YEAR = 2021

# These are deliberately kept outside ``clean_data`` so that the cleaning
# function is deterministic and easy to reuse or test.
COUNTRY_TO_REGION = {
    # North America (the dashboard keeps this label as US for continuity with
    # the original analysis).
    "US": "US",
    "CA": "US",
    # Europe
    "AD": "EU",
    "AT": "EU",
    "BE": "EU",
    "BG": "EU",
    "CH": "EU",
    "CY": "EU",
    "CZ": "EU",
    "DE": "EU",
    "DK": "EU",
    "EE": "EU",
    "ES": "EU",
    "FI": "EU",
    "FR": "EU",
    "GB": "EU",
    "GR": "EU",
    "HR": "EU",
    "HU": "EU",
    "IE": "EU",
    "IS": "EU",
    "IT": "EU",
    "LT": "EU",
    "LU": "EU",
    "LV": "EU",
    "MT": "EU",
    "NL": "EU",
    "NO": "EU",
    "PL": "EU",
    "PT": "EU",
    "RO": "EU",
    "SE": "EU",
    "SI": "EU",
    "SK": "EU",
    # Latin America and the Caribbean
    "AR": "LATAM",
    "BO": "LATAM",
    "BR": "LATAM",
    "CL": "LATAM",
    "CO": "LATAM",
    "CR": "LATAM",
    "CU": "LATAM",
    "DO": "LATAM",
    "EC": "LATAM",
    "GT": "LATAM",
    "HN": "LATAM",
    "MX": "LATAM",
    "NI": "LATAM",
    "PA": "LATAM",
    "PE": "LATAM",
    "PR": "LATAM",
    "SV": "LATAM",
    "UY": "LATAM",
    "VE": "LATAM",
    # Asia
    "AE": "ASIA",
    "BD": "ASIA",
    "CN": "ASIA",
    "HK": "ASIA",
    "ID": "ASIA",
    "IN": "ASIA",
    "IL": "ASIA",
    "JP": "ASIA",
    "KR": "ASIA",
    "MY": "ASIA",
    "PH": "ASIA",
    "PK": "ASIA",
    "SA": "ASIA",
    "SG": "ASIA",
    "TH": "ASIA",
    "TR": "ASIA",
    "TW": "ASIA",
    "VN": "ASIA",
    # Oceania
    "AU": "OCEANIA",
    "NZ": "OCEANIA",
    # Africa
    "EG": "AFRICA",
    "KE": "AFRICA",
    "MA": "AFRICA",
    "NG": "AFRICA",
    "TN": "AFRICA",
    "ZA": "AFRICA",
}

EXPERIENCE_LEVEL_NAMES = {
    "EN": "Entry-level",
    "MI": "Mid-level",
    "SE": "Senior-level",
    "EX": "Executive-level",
}

REMOTE_STATUS_NAMES = {
    0: "On-site",
    50: "Hybrid",
    100: "Remote",
}

REQUIRED_COLUMNS = (
    "work_year",
    "experience_level",
    "job_title",
    "salary_in_usd",
    "remote_ratio",
    "company_location",
)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich a raw tech-salary dataframe.

    Parameters
    ----------
    df:
        A dataframe containing the source dataset columns.  The input is never
        modified in place.

    Returns
    -------
    pandas.DataFrame
        A de-duplicated dataframe from ``MIN_WORK_YEAR`` onwards with the
        derived ``region``, ``experience_level_name`` and ``remote_status``
        columns used by the dashboard.

    Raises
    ------
    TypeError
        If ``df`` is not a pandas dataframe.
    ValueError
        If one or more columns required by the dashboard are missing.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("clean_data expects a pandas DataFrame")

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Salary data is missing required column(s): {missing}")

    # Work on a copy so callers can safely reuse their raw dataframe.
    cleaned = df.copy()

    # Normalise the string fields before dropping missing values.  Empty cells
    # occasionally arrive as empty strings rather than proper NaN values.
    for column in ("experience_level", "job_title", "company_location"):
        cleaned[column] = cleaned[column].astype("string").str.strip()
        cleaned.loc[cleaned[column].isin(["", "nan", "None"]), column] = pd.NA

    # Normalise codes before de-duplicating so values such as ``mx`` and
    # ``MX`` are recognised as the same company location.
    cleaned["company_location"] = cleaned["company_location"].str.upper()
    cleaned["experience_level"] = cleaned["experience_level"].str.upper()

    # The public CSV stores these values as numbers, but coercion also makes
    # the function safe for uploaded files and small hand-built test frames.
    for column in ("work_year", "salary_in_usd", "remote_ratio"):
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    # Only fields used by the dashboard are required.  Optional source fields
    # such as salary_currency or company_size may legitimately be absent.
    cleaned = cleaned.dropna(subset=REQUIRED_COLUMNS).drop_duplicates()
    cleaned = cleaned[cleaned["work_year"] >= MIN_WORK_YEAR].copy()

    if cleaned.empty:
        # Keep predictable dtypes even when a filter removes every row.
        cleaned["work_year"] = cleaned["work_year"].astype("int64")
    else:
        cleaned["work_year"] = cleaned["work_year"].astype(int)
    cleaned["region"] = (
        cleaned["company_location"].map(COUNTRY_TO_REGION).fillna("Other").astype(str)
    )
    cleaned["experience_level_name"] = (
        cleaned["experience_level"].map(EXPERIENCE_LEVEL_NAMES).fillna("Unknown").astype(str)
    )
    cleaned["remote_status"] = (
        cleaned["remote_ratio"].map(REMOTE_STATUS_NAMES).fillna("On-site").astype(str)
    )

    return cleaned.reset_index(drop=True)


def load_and_clean_data(
    raw_path: Union[str, Path] = "data/salaries_raw.csv",
    cleaned_path: Union[str, Path] = "data/salaries_cleaned.csv",
) -> Optional[pd.DataFrame]:
    """Load a local raw CSV, clean it, and write the processed CSV.

    This helper is intentionally independent of Streamlit.  The app uses it as
    a last-resort fallback when neither the remote CSV nor the committed local
    cache is available.
    """
    raw_path = Path(raw_path)
    cleaned_path = Path(cleaned_path)

    if not raw_path.exists():
        print(f"Error: {raw_path} not found.")
        return None

    cleaned = clean_data(pd.read_csv(raw_path))
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(cleaned_path, index=False)
    print(f"Cleaned data saved to {cleaned_path}")
    return cleaned


if __name__ == "__main__":
    load_and_clean_data()
