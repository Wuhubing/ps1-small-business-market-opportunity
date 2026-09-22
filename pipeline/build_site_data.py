"""Build privacy-safe, traceable data products for the static website."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

try:
    from pipeline.verify_pipeline import parse_square_feet, vacancy_months
except ModuleNotFoundError:  # Support direct execution: python pipeline/build_site_data.py
    from verify_pipeline import parse_square_feet, vacancy_months

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed"
SITE_DATA = ROOT / "docs/data"
DOWNLOADS = ROOT / "docs/downloads"
ACCESS_DATE = "2026-09-21"

DISTRICT_ALIASES = {
    "Fresh Pond-Alewife": "Alewife / Fresh Pond",
    "Alewife": "Alewife / Fresh Pond",
    "Huron Village": "Huron / Observatory Hill",
    "Observatory Hill": "Huron / Observatory Hill",
    "Huron Village/Observatory Hill": "Huron / Observatory Hill",
    "North Massachusetts Ave": "Porter / North Mass Ave",
    "North Mssachusetts Ave": "Porter / North Mass Ave",
    "North Massachusetts Ave.": "Porter / North Mass Ave",
    "North Mass. Ave.": "Porter / North Mass Ave",
    "Porter Square/North Massachusetts Ave": "Porter / North Mass Ave",
    "Porter Sq-Lower Mass Ave": "Porter / North Mass Ave",
    "Porter Sq-Lower Massachusetts Ave.": "Porter / North Mass Ave",
    "Porter Sq-Lower Massachusetts Avenue": "Porter / North Mass Ave",
    "Porter Sq-Lower Mass. Ave.": "Porter / North Mass Ave",
}

GEO_MAPPING = """# Geographic mapping

| Level | Website geography | Limitation |
|---|---|---|
| Cambridge business district | Normalized `commercial_district` from the storefront file | Available only for Cambridge; spelling variants are merged and no district land-area denominator is available. |
| Boston neighborhood proxy | License ZIP code and coordinates | Covers licensed food establishments only; it is not a complete business census. |
| County context | Census/BLS FIPS `017` Middlesex and `025` Suffolk | County data are regional context, not Cambridge-versus-Boston city estimates. |
"""


def write_json(filename: str, records: object) -> None:
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    with (SITE_DATA / filename).open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2, allow_nan=False)


def frame_records(frame: pd.DataFrame) -> list[dict]:
    clean = frame.astype(object).where(pd.notna(frame), None)
    return clean.to_dict("records")


def clean_vacancies() -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(RAW / "cambridge_vacant_storefronts.csv", low_memory=False)
    frame["snapshot_date"] = pd.to_datetime(
        frame["dataset_year"].astype("Int64").astype(str)
        + "-"
        + frame["dataset_month"].astype("Int64").astype(str).str.zfill(2)
        + "-01"
    )
    frame["district"] = frame["commercial_district"].replace(DISTRICT_ALIASES)
    frame["square_feet"] = frame["square_footage"].map(parse_square_feet)
    frame["vacancy_year"] = pd.to_numeric(frame["vacancy_date"], errors="coerce")
    # vacancy_date contains a year only. July is used as a transparent midpoint
    # assumption; estimates are capped at the snapshot date.
    frame["vacancy_months"] = frame.apply(
        lambda row: vacancy_months(
            int(row.dataset_year), int(row.dataset_month), int(row.vacancy_year), 7
        )
        if pd.notna(row.vacancy_year)
        else pd.NA,
        axis=1,
    ).astype("Int64")
    frame["age_bucket"] = pd.cut(
        frame["vacancy_months"].astype(float),
        bins=[-1, 3, 6, 12, float("inf")],
        labels=["<3 months", "3–6 months", "6–12 months", ">12 months"],
    ).astype("object")
    frame["area_bucket"] = pd.cut(
        frame["square_feet"],
        bins=[-1, 1000, 2500, float("inf")],
        labels=["<1,000 sqft", "1,000–2,500 sqft", ">2,500 sqft"],
    ).astype("object").fillna("Area not reported")
    latest = frame[frame["snapshot_date"] == frame["snapshot_date"].max()].copy()
    return frame, latest


def build_vacancy_products(frame: pd.DataFrame, latest: pd.DataFrame) -> pd.DataFrame:
    history = (
        frame.groupby(["snapshot_date", "district"], dropna=False)
        .agg(
            vacant_storefronts=("district", "size"),
            median_square_feet=("square_feet", "median"),
            average_vacancy_months=("vacancy_months", "mean"),
        )
        .reset_index()
        .sort_values(["snapshot_date", "district"])
    )
    history["snapshot"] = history["snapshot_date"].dt.strftime("%Y-%m")
    write_json(
        "vacancy_by_district.json",
        frame_records(history.drop(columns="snapshot_date").round(1)),
    )

    complete_age = latest.dropna(subset=["age_bucket"])
    buckets = (
        complete_age.groupby(["district", "age_bucket", "area_bucket"], observed=True)
        .size()
        .rename("storefronts")
        .reset_index()
    )
    write_json("vacancy_age_buckets.json", frame_records(buckets))

    summary = (
        latest.groupby("district")
        .agg(
            vacant_storefronts=("district", "size"),
            average_vacancy_months=("vacancy_months", "mean"),
            total_observed_square_feet=("square_feet", "sum"),
            area_known=("square_feet", "count"),
            age_known=("vacancy_months", "count"),
        )
        .reset_index()
    )
    long_term = latest.assign(long_term=latest["vacancy_months"] > 12).groupby("district")["long_term"].sum()
    summary["long_term_storefronts"] = summary["district"].map(long_term).fillna(0).astype(int)
    summary["priority_score"] = summary["vacant_storefronts"] * summary["average_vacancy_months"]
    summary = summary.sort_values("priority_score", ascending=False)
    summary = summary.round({"average_vacancy_months": 1, "total_observed_square_feet": 0, "priority_score": 1})
    write_json("district_summary.json", frame_records(summary))

    safe_rows = latest[["district", "square_feet", "vacancy_months", "age_bucket", "area_bucket"]].copy()
    safe_rows.insert(0, "record_id", range(1, len(safe_rows) + 1))
    write_json("vacancy_rows.json", frame_records(safe_rows))
    return summary


def build_license_products() -> pd.DataFrame:
    licenses = pd.read_csv(RAW / "boston_food_licenses.csv", low_memory=False)
    licenses["license_date"] = pd.to_datetime(licenses["license_add_dt_tm"], errors="coerce")
    licenses["year"] = licenses["license_date"].dt.year.astype("Int64")
    annual = (
        licenses[licenses["year"].between(2014, 2026)]
        .groupby(["year", "licensecat"])
        .size()
        .rename("new_licenses")
        .reset_index()
    )
    write_json("licenses_by_year.json", frame_records(annual))
    points = licenses.dropna(subset=["latitude", "longitude", "year"])[
        ["latitude", "longitude", "zip", "licensecat", "year"]
    ].copy()
    points.columns = ["lat", "lng", "zip", "license_category", "year"]
    write_json("license_points.json", frame_records(points))
    return annual


def build_industry_products() -> pd.DataFrame:
    cbp = pd.read_csv(RAW / "cbp_ma_counties.csv", dtype={"fipscty": str, "naics": str})
    cbp["fipscty"] = cbp["fipscty"].str.zfill(3)
    county_names = {"017": "Middlesex County", "025": "Suffolk County"}
    codes = {"44----": "Retail trade", "722///": "Food services", "812///": "Personal services"}
    rows = cbp[cbp["naics"].isin(codes)].copy()
    rows["county"] = rows["fipscty"].map(county_names)
    rows["industry"] = rows["naics"].map(codes)
    for field in ["est", "emp", "ap"]:
        rows[field] = pd.to_numeric(rows[field], errors="coerce")
    cbp_rows = rows[["county", "industry", "est", "emp", "ap"]].rename(
        columns={"est": "establishments", "emp": "employment", "ap": "annual_payroll_thousands"}
    )
    trends = []
    for fips, county in county_names.items():
        qcew = pd.read_csv(RAW / f"qcew_area_25{fips}.csv", dtype=str)
        qcew["industry_code"] = qcew["industry_code"].str.strip()
        qcew["own_code"] = qcew["own_code"].str.strip()
        for code, industry in {"44-45": "Retail trade", "722": "Food services", "812": "Personal services"}.items():
            match = qcew[(qcew["industry_code"] == code) & (qcew["own_code"] == "5")]
            if not match.empty:
                row = match.iloc[0]
                trends.append(
                    {
                        "county": county,
                        "industry": industry,
                        "year": int(row["year"]),
                        "quarter": int(row["qtr"]),
                        "establishments": int(float(row["qtrly_estabs"])),
                        "employment": int(float(row["month3_emplvl"])),
                    }
                )
    payload = {"cbp_2022": cbp_rows.to_dict("records"), "qcew_2024_q1": trends}
    write_json("industry_structure.json", payload)
    return cbp_rows


def build_findings(summary: pd.DataFrame, latest: pd.DataFrame) -> dict:
    ranked = summary.dropna(subset=["priority_score"]).sort_values("priority_score", ascending=False)
    top = ranked.iloc[0]
    top_two = ranked.head(2)
    age_known = latest["vacancy_months"].notna().sum()
    long_term = int((latest["vacancy_months"] > 12).sum())
    long_term_share = round(long_term / age_known * 100, 1) if age_known else 0
    small_long_term = int(((latest["vacancy_months"] > 12) & (latest["square_feet"] < 1500)).sum())
    cottage = pd.read_csv(RAW / "cambridge_cottage_food_permits.csv")
    cottage["submitted"] = pd.to_datetime(cottage["applicant_submit_date"], errors="coerce")
    cottage["issued"] = pd.to_datetime(cottage["issue_date"], errors="coerce")
    approval_days = (cottage["issued"] - cottage["submitted"]).dt.days.dropna()
    median_approval = int(approval_days.median()) if not approval_days.empty else None
    snapshot = latest["snapshot_date"].max().strftime("%B %Y")
    findings = [
        {
            "id": "F1",
            "text": f"{top['district']} has {int(top['vacant_storefronts'])} vacant storefronts in the latest snapshot and the highest count-duration priority score.",
            "value": int(top["vacant_storefronts"]),
            "unit": "storefronts",
            "source": "Cambridge Vacant Storefronts",
            "method": "Latest snapshot; districts ranked by storefront count × estimated average vacancy months.",
        },
        {
            "id": "F2",
            "text": f"Among {age_known} storefronts with a reported vacancy year, {long_term} ({long_term_share}%) are estimated to have been vacant for more than 12 months.",
            "value": long_term_share,
            "unit": "percent",
            "source": "Cambridge Vacant Storefronts",
            "method": "Latest snapshot; July assumed when only a vacancy year is supplied.",
        },
        {
            "id": "F3",
            "text": f"The public permit file contains {len(cottage)} cottage-food permits; the median recorded submit-to-issue interval is {median_approval} days.",
            "value": median_approval,
            "unit": "days",
            "source": "Cambridge Cottage Food Operations Permits",
            "method": "Difference between issue_date and applicant_submit_date; personal fields removed.",
        },
    ]
    recommendations = [
        {
            "id": "R1",
            "text": f"Concentrate the first outreach cycle in {top_two.iloc[0]['district']} and {top_two.iloc[1]['district']} instead of distributing effort evenly.",
            "supported_by": ["F1"],
            "action": "Assign a district lead, contact property stakeholders through internal channels, and review progress after 90 days.",
        },
        {
            "id": "R2",
            "text": f"Pilot a small-space matching program for the {small_long_term} observed storefronts under 1,500 sqft that are estimated vacant for more than a year.",
            "supported_by": ["F2"],
            "action": "Package permitting guidance and fit-out support around smaller, lower-capital spaces.",
        },
        {
            "id": "R3",
            "text": "Create an opt-in pathway for permitted cottage-food operators who want to test a shared commercial kitchen or storefront.",
            "supported_by": ["F3"],
            "action": "Invite operators through the City’s own secure records; do not publish or reuse personal contact details.",
        },
    ]
    return {
        "headline": {
            "text": f"Where should Cambridge focus small-business support in {snapshot}?",
            "metric": "highest-priority district",
            "value": top["district"],
        },
        "snapshot": snapshot,
        "findings": findings,
        "recommendations": recommendations,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def export_csvs(latest: pd.DataFrame, summary: pd.DataFrame, annual: pd.DataFrame, industry: pd.DataFrame) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    exports = {
        "cambridge_vacancies_latest.csv": latest[
            ["district", "square_feet", "vacancy_year", "vacancy_months", "age_bucket", "area_bucket"]
        ],
        "district_summary.csv": summary,
        "boston_license_yearly.csv": annual,
        "industry_structure_cbp_2022.csv": industry,
    }
    cottage = pd.read_csv(RAW / "cambridge_cottage_food_permits.csv")
    exports["cambridge_cottage_permit_process.csv"] = cottage
    for filename, frame in exports.items():
        target = PROCESSED / filename
        frame.to_csv(target, index=False)
        shutil.copy2(target, DOWNLOADS / filename)


def main() -> None:
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    (SITE_DATA / "geo_mapping.md").write_text(GEO_MAPPING, encoding="utf-8")
    vacancies, latest = clean_vacancies()
    summary = build_vacancy_products(vacancies, latest)
    annual = build_license_products()
    industry = build_industry_products()
    findings = build_findings(summary, latest)
    write_json("findings.json", findings)
    export_csvs(latest, summary, annual, industry)
    print(f"latest_snapshot={latest.snapshot_date.max().date()} storefronts={len(latest)} districts={latest.district.nunique()}")
    print(f"findings={len(findings['findings'])} recommendations={len(findings['recommendations'])}")
    print(f"site_json={len(list(SITE_DATA.glob('*.json')))} downloads={len(list(DOWNLOADS.glob('*.csv')))}")


if __name__ == "__main__":
    main()
