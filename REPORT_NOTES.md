# Technical report notes — working file only

These are evidence and decisions for a later report, **not** the final report. Keep the final report below 3,000 words and export it to PDF only after the app is checked and deployed.

## Team and links

- Student name(s): to add.
- GitHub repository: to add.
- Public deployment URL: to add.
- Contribution statement: to add based on actual work.

## Purpose and users

- Intended user: a student or general visitor who wants to locate AIATSIS AustLang records by language name, variant spelling, code, or broad state/territory tag.
- Main tasks: find a source record, inspect approximate published points, and understand patterns and gaps in dataset coverage.
- Four views: Search languages; Map and nearby; Patterns in the data; About the data.

## Data provenance and preparation

- Original publisher: Australian Institute of Aboriginal and Torres Strait Islander Studies (AIATSIS).
- Dataset listing: https://data.gov.au/data/dataset/austlang-dataset-001 — identifies CC BY 4.0.
- Machine-readable snapshot obtained 2026-10-06 via https://spatial.infrastructure.gov.au/server/rest/services/Hosted/Indigenous_Language_Austlang/FeatureServer/19/query?where=1%3D1&outFields=*&returnGeometry=false&f=geojson .
- 1,209 source features exported to `data/austlang.csv`; fields selected: code, name, alternate names, region tags, approximate latitude/longitude, AIATSIS record URL.
- Snapshot checks: 1,209 unique valid records; 840 have usable coordinates, 1,007 have alternate names, and 984 have a region tag. The app calculates these from the file rather than hard-coding them.
- Whitespace trimmed. Missing and out-of-range coordinates are left blank. No coordinates invented. Source links retained.
- Check exact attribution and whether the spatial service's snapshot matches the current AIATSIS download before final submission.
- Cultural scope: only source-published metadata. No AI-generated cultural descriptions, translations, or historical assertions. No images, voices, or names of deceased people intentionally added.

## Architecture and algorithm

- Streamlit `app.py` loads CSV through `explorer.py`; all views use the validated in-memory records. Mermaid diagram in README.
- Search scores exact code and name-prefix matches above incidental or alternate-name matches; filters by broad region tag. Ties sort by name and code.
- Nearby feature computes Haversine great-circle distance to every record with usable coordinates, sorts, and returns ten. It is an approximate point comparison, not a claim about Country.
- Region analysis counts each record once per listed region; totals may exceed 1,209 when records have multiple tags.
- Missing coordinates are excluded from map and distance calculation. Dataset threshold and required columns are validated.

## Analysis and visualisation

- Bar chart: number of source records tagged to each state/territory. Interpret as dataset coverage only.
- Completeness table: region tags, usable coordinates, and alternate names, including missing counts.
- Map: approximate source points with a region filter.
- Capture actual figures from the app after testing and add one or two carefully limited observations.

## Interface and reliability

- Sidebar navigation; labels and feedback for no search matches; source-record links; consistent theme.
- Automated tests in `tests/test_explorer.py` (12 tests). On 2026-10-06, `python -m pytest -q` reported **12 passed**.
- Streamlit `AppTest` loaded all four views on 2026-10-06 with zero exceptions.
- Manual workflow checks still needed: search by name/code, filter, source link, map, invalid/empty input, mobile width.

## Security and privacy

- No login, user accounts, uploads, personal data collection, or API keys.
- Search input is treated as text, not executed as code or SQL. Latitude and longitude constrained in UI and validated in algorithm.
- Bundled read-only CSV avoids a runtime API dependency.

## Deployment and limitations

- Deployment target: Streamlit Community Cloud from GitHub. Must confirm external access and record URL.
- Source dataset is live; this bundled snapshot can become stale. Region tags and approximate locations cannot be treated as cultural boundaries. Missing coordinates and tags reduce map coverage.
- Instructor/facilitator should review any uncertainty over appropriate cultural use.

## Demo outline

1. Search a language name, alternate spelling, and an exact code; open the AIATSIS record.
2. Filter by a region and explain that tags are broad metadata.
3. Show approximate points and nearby calculation, with its limitation.
4. Show counts and completeness, then an empty search result.
5. Run `python -m pytest -q` and explain search ranking and Haversine distance.
