"""Fetch and privacy-clean Boston food establishment licenses."""

from pathlib import Path

import pandas as pd
import requests

URL = "https://data.boston.gov/api/3/action/datastore_search"
RESOURCE = "f1e13724-284d-478c-b8bc-ef042aa5b70b"
SAFE_FIELDS = ("license_add_dt_tm", "licensecat", "zip", "latitude", "longitude")
OUT = Path(__file__).resolve().parents[1] / "data/raw/boston_food_licenses.csv"


def fetch_licenses() -> pd.DataFrame:
    records = []
    expected = None
    while expected is None or len(records) < expected:
        response = requests.get(
            URL,
            params={"resource_id": RESOURCE, "fields": ",".join(SAFE_FIELDS),
                    "limit": 1000, "offset": len(records), "sort": "_id asc"},
            headers={"User-Agent": "MIT-1.125-PS1-research/1.0"}, timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success"):
            raise ValueError("Projected Boston API request failed; full CSV fallback is prohibited")
        result = payload["result"]
        if expected is not None and expected != result["total"]:
            raise ValueError("Source row count changed during pagination; retry the snapshot")
        expected = result["total"]
        batch = result["records"]
        if any(set(row) - set(SAFE_FIELDS) for row in batch):
            raise ValueError("Source returned fields outside the approved projection")
        if not batch and len(records) < expected:
            raise ValueError("Truncated Boston API response")
        records.extend(batch)
    if len(records) != expected:
        raise ValueError("Boston row count mismatch")
    return pd.DataFrame(records, columns=SAFE_FIELDS)


def main() -> None:
    # Coordinates refer to licensed commercial premises, not people's homes.
    # Server-side fields selection excludes names, phones, and street addresses.
    df = fetch_licenses()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"rows={len(df)}")
    print(f"columns={list(df.columns)}")


if __name__ == "__main__":
    main()
