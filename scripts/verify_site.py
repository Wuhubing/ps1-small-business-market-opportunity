"""Fail-fast checks for the GitHub Pages deliverable."""

from __future__ import annotations

import csv
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EXPECTED = {"index.html", "explore.html", "map.html", "methodology.html", "data.html", "reflection.html"}


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.paths: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        key = "href" if tag in {"a", "link"} else "src" if tag == "script" else None
        if key and values.get(key):
            self.paths.append(str(values[key]))


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def main() -> None:
    failures: list[str] = []
    pages = {path.name for path in DOCS.glob("*.html")}
    if pages != EXPECTED:
        fail(f"Expected six pages {sorted(EXPECTED)}, found {sorted(pages)}", failures)
    if not (DOCS / ".nojekyll").exists():
        fail("docs/.nojekyll is missing", failures)

    for name in sorted(EXPECTED):
        path = DOCS / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if '<meta name="viewport" content="width=device-width, initial-scale=1">' not in text:
            fail(f"{name} lacks the required viewport meta", failures)
        if 'href="assets/style.css"' not in text:
            fail(f"{name} does not use the shared stylesheet", failures)
        if not re.search(r"Sources?:", text, re.IGNORECASE) and name not in {"explore.html"}:
            fail(f"{name} has no visible source note", failures)
        parser = AssetParser()
        parser.feed(text)
        for asset in parser.paths:
            if asset.startswith(("http://", "https://", "data:", "#", "mailto:")):
                continue
            local = (path.parent / asset.split("?")[0]).resolve()
            if not local.exists():
                fail(f"{name} links to missing local asset {asset}", failures)

    json_files = list((DOCS / "data").glob("*.json"))
    if not json_files:
        fail("No website JSON files found", failures)
    json_text = ""
    for path in json_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not payload:
                fail(f"{path.name} is empty", failures)
            json_text += json.dumps(payload, ensure_ascii=False)
        except json.JSONDecodeError as error:
            fail(f"{path.name} is invalid JSON: {error}", failures)

    findings_path = DOCS / "data/findings.json"
    if findings_path.exists():
        findings = json.loads(findings_path.read_text(encoding="utf-8"))
        if len(findings.get("findings", [])) < 3:
            fail("findings.json contains fewer than three findings", failures)
        if len(findings.get("recommendations", [])) < 2:
            fail("findings.json contains fewer than two recommendations", failures)

    data_html = (DOCS / "data.html").read_text(encoding="utf-8")
    if len(re.findall(r"https?://", data_html)) < 5 or "accessed" not in data_html.lower():
        fail("data.html must contain at least five source URLs and access dates", failures)

    downloads = list((DOCS / "downloads").glob("*.csv"))
    if len(downloads) < 3:
        fail("Fewer than three CSV downloads", failures)
    forbidden = {"dayphn_cleaned", "business_phone_number", "business_email", "applicant_name", "full_address", "recorded_owner", "leasing_contact"}
    for path in downloads + list((ROOT / "data/processed").glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = {value.strip().lower() for value in next(reader, [])}
            if header.intersection(forbidden):
                fail(f"{path} exposes forbidden personal fields: {header.intersection(forbidden)}", failures)
            if next(reader, None) is None:
                fail(f"{path} has no data rows", failures)

    index_text = (DOCS / "index.html").read_text(encoding="utf-8")
    for percentage in re.findall(r"\b\d+(?:\.\d+)?%", index_text):
        if percentage.rstrip("%") not in json_text:
            fail(f"Hard-coded percentage {percentage} in index.html has no JSON match", failures)
    if "@media (max-width: 720px)" not in (DOCS / "assets/style.css").read_text(encoding="utf-8"):
        fail("Shared stylesheet lacks the required mobile breakpoint", failures)

    if failures:
        for message in failures:
            print(f"FAIL: {message}", file=sys.stderr)
        sys.exit(1)
    print(f"pages={len(EXPECTED)} json={len(json_files)} downloads={len(downloads)}")
    print("SITE_CHECKS_PASS")


if __name__ == "__main__":
    main()
