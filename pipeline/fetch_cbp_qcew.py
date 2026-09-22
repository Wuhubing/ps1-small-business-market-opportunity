"""Fetch Census County Business Patterns and BLS QCEW source files."""

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
HEADERS = {"User-Agent": "MIT-1.125-PS1-research/1.0"}
CBP_URL = "https://www2.census.gov/programs-surveys/cbp/datasets/2022/cbp22co.zip"
QCEW_URLS = {
    "qcew_area_25017.csv": "https://data.bls.gov/cew/data/api/2024/1/area/25017.csv",
    "qcew_area_25025.csv": "https://data.bls.gov/cew/data/api/2024/1/area/25025.csv",
    "qcew_industry_722.csv": "https://data.bls.gov/cew/data/api/2024/1/industry/722.csv",
}


def get(url: str) -> bytes:
    response = requests.get(url, headers=HEADERS, timeout=180)
    response.raise_for_status()
    return response.content


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    archive = get(CBP_URL)
    with ZipFile(BytesIO(archive)) as zipped:
        member = next(name for name in zipped.namelist() if name.endswith("cbp22co.txt"))
        with zipped.open(member) as source:
            cbp = pd.read_csv(
                source,
                dtype={"fipstate": str, "fipscty": str, "naics": str},
                low_memory=False,
            )
    cbp.columns = [column.strip().lower() for column in cbp.columns]
    cbp["fipstate"] = cbp["fipstate"].str.zfill(2)
    cbp["fipscty"] = cbp["fipscty"].str.zfill(3)
    cbp = cbp[(cbp["fipstate"] == "25") & cbp["fipscty"].isin(["017", "025"])]
    cbp.to_csv(RAW / "cbp_ma_counties.csv", index=False)
    print(f"cbp rows={len(cbp)} counties={sorted(cbp.fipscty.unique())} naics={cbp.naics.nunique()}")
    for filename, url in QCEW_URLS.items():
        content = get(url)
        (RAW / filename).write_bytes(content)
        print(f"{filename} bytes={len(content)}")


if __name__ == "__main__":
    main()
