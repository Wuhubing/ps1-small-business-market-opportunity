"""Fetch Cambridge vacant storefront and cottage-food permit datasets."""

from pathlib import Path

import pandas as pd
import requests

BASE = "https://data.cambridgema.gov/resource"
ROOT = Path(__file__).resolve().parents[1]
HEADERS = {"User-Agent": "MIT-1.125-PS1-research/1.0"}
SAFE_FIELDS = {
    "swpv-8j3w": ("dataset_year", "dataset_month", "commercial_district", "square_footage", "vacancy_date"),
    "q9yz-5w2v": ("status", "applicant_submit_date", "issue_date", "permit_type"),
}


def soda(dataset_id: str, limit: int = 50000) -> tuple[pd.DataFrame, int]:
    fields = SAFE_FIELDS[dataset_id]  # Reject unreviewed datasets before any request.
    count_response = requests.get(
        f"{BASE}/{dataset_id}.json",
        params={"$select": "count(*)"},
        headers=HEADERS,
        timeout=120,
    )
    count_response.raise_for_status()
    expected = int(count_response.json()[0]["count"])
    response = requests.get(
        f"{BASE}/{dataset_id}.json",
        params={"$select": ",".join(fields), "$limit": limit, "$order": ":id"},
        headers=HEADERS,
        timeout=120,
    )
    response.raise_for_status()
    frame = pd.DataFrame(response.json())
    if set(frame.columns) - set(fields):
        raise ValueError("Source returned fields outside the approved projection")
    frame = frame.reindex(columns=fields)
    assert len(frame) == expected, f"{dataset_id}: expected {expected}, fetched {len(frame)}"
    return frame, expected


def main() -> None:
    vacant, vacant_count = soda("swpv-8j3w")
    cottage, cottage_count = soda("q9yz-5w2v")
    # Socrata performs the field projection on the server. No names, contacts,
    # addresses, coordinates, or linkable permit IDs are requested.
    raw_dir = ROOT / "data/raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    vacant.to_csv(raw_dir / "cambridge_vacant_storefronts.csv", index=False)
    cottage.to_csv(raw_dir / "cambridge_cottage_food_permits.csv", index=False)
    print(f"vacant expected={vacant_count} fetched={len(vacant)}")
    print(f"cottage expected={cottage_count} fetched={len(cottage)}")
    if {"dataset_year", "dataset_month"}.issubset(vacant.columns):
        periods = (
            vacant[["dataset_year", "dataset_month"]]
            .astype(str)
            .agg("-".join, axis=1)
        )
        print(f"vacancy_period min={periods.min()} max={periods.max()} unique={periods.nunique()}")


if __name__ == "__main__":
    main()
