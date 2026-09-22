"""Fetch and privacy-clean Boston food establishment licenses."""

from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

URL = "https://data.boston.gov/dataset/5e4182e3-ba1e-4511-88f8-08a70383e1b6/resource/f1e13724-284d-478c-b8bc-ef042aa5b70b/download/tmp3aemwqxo.csv"
OUT = Path(__file__).resolve().parents[1] / "data/raw/boston_food_licenses.csv"


def main() -> None:
    response = requests.get(
        URL,
        allow_redirects=True,
        headers={"User-Agent": "MIT-1.125-PS1-research/1.0"},
        timeout=120,
    )
    response.raise_for_status()
    df = pd.read_csv(BytesIO(response.content), low_memory=False)
    df.columns = [str(column).strip().lower() for column in df.columns]
    # The assignment forbids collecting contact details. The source contains a
    # merchant phone field, so delete it before writing any local deliverable.
    df = df.drop(columns=["dayphn_cleaned"], errors="ignore")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"rows={len(df)}")
    print(f"columns={list(df.columns)}")


if __name__ == "__main__":
    main()
