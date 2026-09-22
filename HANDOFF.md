# HANDOFF — Ready for review and publication

## Local preview

```bash
cd /Users/ww/Desktop/26f/software/hw1
/opt/anaconda3/bin/python3 -m http.server 8765 --directory docs
```

Open `http://localhost:8765/`.

## Pages

| Page | File | Purpose |
|---|---|---|
| Decision brief | `docs/index.html` | Problem, audience, KPIs, three charts, findings, recommendations, ranked districts |
| Explore | `docs/explore.html` | District/area/duration/year filters and four chart views |
| Map | `docs/map.html` | Privacy-safe Boston food-license context |
| Method | `docs/methodology.html` | One-page collection and analysis note |
| Data | `docs/data.html` | Dictionary, quality report, sources, five CSV downloads |
| Limitations | `docs/reflection.html` | Missingness, bias, uncertainty, and what the data cannot prove |

## Key numbers for acceptance checking

All values below are generated in `docs/data/findings.json` or `district_summary.json`.

- Latest Cambridge vacancy snapshot: September 2025
- Storefront records: 96 across 10 normalized districts
- Highest priority score: Central Square — 15 storefronts, 47.6 estimated average months, score 714.0
- Second priority: Harvard Square — 12 storefronts, 59.0 estimated average months, score 708.0
- Long-term: 79 of 96 records, 82.3%, estimated over 12 months
- Small long-term spaces: 13 observed records under 1,500 square feet
- Cottage-food permits: 15; median submit-to-issue interval: 26 days
- Privacy-safe mapped Boston license records: 2,150

## Known limitations and choices

- Vacancy dates contain a year only; July is used as a midpoint, so duration is approximate.
- The latest snapshot has complete vacancy-year coverage but only 58.3% usable floor-area coverage.
- Boston license records are regional context, not a Cambridge demand or competition measure.
- County statistics are not used as city-level estimates.
- Cambridge vacancy locations are not mapped because the source contains no coordinates; no locations were invented.
- OpenStreetMap is used as the no-key basemap because the previously specified CARTO endpoint now displays an API-key requirement.

## Verification

```bash
/opt/anaconda3/bin/python3 pipeline/verify_pipeline.py
/opt/anaconda3/bin/python3 -m pytest pipeline/tests -q
/opt/anaconda3/bin/python3 scripts/verify_site.py
node --check docs/assets/app.js
```

Expected endings: `ALL_CHECKS_PASS`, `3 passed`, `SITE_CHECKS_PASS`, and no Node output.

## Publish (Hermes/user executes)

```bash
gh repo create ps1-small-business-market-opportunity --public --source=. --remote=origin --push
gh api -X POST repos/Wuhubing/ps1-small-business-market-opportunity/pages \
  -f 'source[branch]=main' -f 'source[path]=/docs'
```

Expected URL: `https://wuhubing.github.io/ps1-small-business-market-opportunity/`

After publication, verify the live URL and a 390×844 phone viewport, then submit the URL in the PS1 column of the course spreadsheet. Do not submit personal data or raw source files.
