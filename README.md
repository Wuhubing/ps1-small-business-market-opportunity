# Cambridge Storefront Opportunity

An interactive, traceable, and privacy-conscious data decision tool for the Cambridge Community Development Department. The site helps staff prioritize limited business-recruitment and small-business support resources by identifying commercial districts and storefront types that warrant further investigation.

## Site Contents

- `docs/index.html`: Decision summary, key indicators, findings, recommendations, and district rankings
- `docs/explore.html`: Filters for district, floor area, vacancy duration, and year
- `docs/map.html`: Geographic context based on Boston food-service licenses
- `docs/methodology.html`: One-page data and methodology note
- `docs/data.html`: Data dictionary, missing-data rates, and CSV downloads
- `docs/reflection.html`: What the data supports and what it cannot prove

## Data Sources

| Data source | Access URL | Accessed |
|---|---|---|
| Boston active food establishment licenses | https://data.boston.gov/dataset/5e4182e3-ba1e-4511-88f8-08a70383e1b6/resource/f1e13724-284d-478c-b8bc-ef042aa5b70b/download/tmp3aemwqxo.csv | 2026-09-21 |
| Cambridge vacant storefronts and cottage-food permits | https://data.cambridgema.gov/resource/swpv-8j3w.json / https://data.cambridgema.gov/resource/q9yz-5w2v.json | 2026-09-21 |
| U.S. Census County Business Patterns 2022 | https://www2.census.gov/programs-surveys/cbp/datasets/2022/cbp22co.zip | 2026-09-21 |
| U.S. Bureau of Labor Statistics QCEW, 2024 Q1 | https://data.bls.gov/cew/data/api/2024/1/area/25017.csv / https://data.bls.gov/cew/data/api/2024/1/area/25025.csv | 2026-09-21 |

## Reproducing the Analysis

Run the following commands from the repository root. The pipeline requires `pandas`, `requests`, and `pytest`.

```sh
/opt/anaconda3/bin/python3 pipeline/fetch_boston_licenses.py
/opt/anaconda3/bin/python3 pipeline/fetch_cambridge.py
/opt/anaconda3/bin/python3 pipeline/fetch_cbp_qcew.py
/opt/anaconda3/bin/python3 pipeline/build_site_data.py
/opt/anaconda3/bin/python3 pipeline/verify_pipeline.py
/opt/anaconda3/bin/python3 -m pytest pipeline/tests -q
/opt/anaconda3/bin/python3 scripts/verify_site.py
```

Raw data files are excluded from Git. Boston phone-number fields are removed before data are written to disk. Names, contact details, home addresses, and coordinates from cottage-food permits are not retained. Owner and leasing-contact fields from the storefront dataset are also removed.

## Local Preview

```sh
/opt/anaconda3/bin/python3 -m http.server 8765 --directory docs
```

Then open `http://localhost:8765/`.

## Published Project

- Live site: https://cambridge-storefront-opportunity.wuhubing19.chatgpt.site/
- Public repository: https://github.com/Wuhubing/ps1-small-business-market-opportunity

The published site is hosted on `chatgpt.site`. The repository contains the complete website, processed datasets, reproducible data pipeline, methodology documentation, presentation materials, and project reflection.

## Five-Minute Presentation

Watch the [five-minute narrated site walkthrough](https://cambridge-storefront-opportunity.wuhubing19.chatgpt.site/data.html#presentation) or download the MP4 from that page. The video uses actual website views and filter states, English synthetic narration, and on-screen captions. A transcript and WebVTT captions are included in `docs/media/`.

To regenerate the video on macOS, start the local preview server, run `node scripts/capture_demo.cjs` with Playwright available, and then run `python3 scripts/render_demo.py` with Pillow and FFmpeg installed. The narration source is `presentation/video-scenes.json`. Intermediate media is stored in the ignored `.sites-runtime/video/` directory.

## Development Record

Detailed commands, results, and exceptions are recorded in `LOG.md`.

- Phase 0: Initialized Git, project directories, README, and work log.
- Phase 1: Collected four public datasets, removed sensitive fields, and completed data-quality assertions and unit tests.
- Phase 2: Generated nine site-data JSON files, five downloadable CSV files, findings, and recommendations.
- Phase 3: Completed the responsive site, interactive filters, map, presentation materials, and automated acceptance checks.
