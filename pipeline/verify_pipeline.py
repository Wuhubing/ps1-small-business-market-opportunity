"""Data quality checks shared by the pipeline and its tests."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"


def naics_matches(code: object, prefix: str) -> bool:
    """Return whether a CBP NAICS hierarchy code belongs to a prefix."""
    cleaned = str(code).replace("-", "").strip()
    return cleaned.startswith(str(prefix))


def parse_square_feet(value: object) -> float | None:
    """Parse a number or range, using the range midpoint."""
    numbers = [float(item.replace(",", "")) for item in re.findall(r"\d[\d,]*(?:\.\d+)?", str(value))]
    return sum(numbers) / len(numbers) if numbers else None


def vacancy_months(snapshot_year: int, snapshot_month: int, vacancy_year: int, vacancy_month: int = 1) -> int:
    """Calculate completed calendar months between vacancy and snapshot."""
    return max(0, (int(snapshot_year) - int(vacancy_year)) * 12 + int(snapshot_month) - int(vacancy_month))


def coordinates_in_bounds(latitude: object, longitude: object) -> bool:
    try:
        lat, lon = float(latitude), float(longitude)
    except (TypeError, ValueError):
        return False
    return 42.20 <= lat <= 42.45 and -71.30 <= lon <= -70.90


def missingness(frame: pd.DataFrame, dataset: str, fields: list[str]) -> list[dict]:
    rows = []
    for field in fields:
        if field in frame:
            rate = round(float(frame[field].isna().mean() * 100), 1)
            rows.append({"dataset": dataset, "field": field, "missing_percent": rate})
    return rows


def main() -> None:
    failures: list[str] = []
    report: list[dict] = []

    boston = pd.read_csv(RAW / "boston_food_licenses.csv", low_memory=False)
    if len(boston) < 3000:
        failures.append("Boston license rows below 3,000")
    if "dayphn_cleaned" in boston.columns:
        failures.append("Boston phone field is present")
    coordinate_rows = boston.dropna(subset=["latitude", "longitude"])
    if coordinate_rows.empty or not coordinate_rows.apply(
        lambda row: coordinates_in_bounds(row.latitude, row.longitude), axis=1
    ).all():
        failures.append("Boston coordinates outside expected region")
    if boston[["latitude", "longitude"]].isna().any(axis=1).mean() >= 0.10:
        failures.append("Boston coordinate missingness is 10% or greater")
    report += missingness(boston, "Boston licenses", ["latitude", "longitude", "license_add_dt_tm", "zip"])

    vacant = pd.read_csv(RAW / "cambridge_vacant_storefronts.csv", low_memory=False)
    if vacant.empty:
        failures.append("Cambridge vacancy data is empty")
    parsed_area = vacant["square_footage"].map(parse_square_feet)
    if (parsed_area.fillna(0) > 0).mean() < 0.40:
        failures.append("Fewer than 40% of vacancy rows have usable square footage")
    vacancy_year = pd.to_numeric(vacant["vacancy_date"], errors="coerce")
    # The public source leaves vacancy_date blank in many historical snapshots;
    # retain a minimum-coverage guard and disclose the observed missingness.
    if vacancy_year.notna().mean() < 0.20:
        failures.append("Fewer than 20% of vacancy rows contain a usable vacancy year")
    if any(field in vacant.columns for field in ["recorded_owner", "leasing_contact"]):
        failures.append("Cambridge vacancy contact fields are present")
    report += missingness(vacant, "Cambridge vacancies", ["commercial_district", "square_footage", "vacancy_date"])

    cottage = pd.read_csv(RAW / "cambridge_cottage_food_permits.csv", low_memory=False)
    if cottage.empty:
        failures.append("Cambridge cottage permit data is empty")
    forbidden = {
        "applicant_name", "business_name", "business_phone_number", "business_email",
        "full_address", "latitude", "longitude", "coordinates",
    }
    if forbidden.intersection(cottage.columns):
        failures.append("Personal cottage permit fields are present")
    report += missingness(cottage, "Cambridge cottage permits", ["status", "applicant_submit_date", "issue_date"])

    cbp = pd.read_csv(RAW / "cbp_ma_counties.csv", dtype={"fipstate": str, "fipscty": str, "naics": str})
    cbp["fipscty"] = cbp["fipscty"].str.zfill(3)
    if set(cbp["fipscty"].dropna()) != {"017", "025"}:
        failures.append("CBP does not contain exactly Middlesex and Suffolk counties")
    for field in ["est", "emp"]:
        values = pd.to_numeric(cbp[field], errors="coerce")
        if (values.dropna() < 0).any():
            failures.append(f"CBP {field} contains negative values")
    report += missingness(cbp, "Census CBP", ["emp", "est", "ap"])

    report_frame = pd.DataFrame(report)
    print("MISSINGNESS_REPORT")
    print(report_frame.to_string(index=False))
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        sys.exit(1)
    print("ALL_CHECKS_PASS")


if __name__ == "__main__":
    main()
