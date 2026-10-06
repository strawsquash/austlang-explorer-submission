"""Interactive explorer of published AIATSIS AustLang metadata."""

from pathlib import Path

import pandas as pd
import streamlit as st

from explorer import load_records, nearest, region_counts, search


DATA = Path(__file__).parent / "data" / "austlang.csv"
SOURCE = "https://data.gov.au/data/dataset/austlang-dataset-001"

st.set_page_config(page_title="AustLang Explorer", page_icon="🗺️", layout="wide")


@st.cache_data
def records():
    return load_records(DATA)


try:
    data = records()
except (OSError, ValueError) as exc:
    st.error(f"The dataset could not be loaded: {exc}")
    st.stop()

counts = region_counts(data)
regions = ["All", *sorted(counts)]

st.title("AustLang Explorer")
st.caption("Explore published language metadata from the Australian Institute of Aboriginal and Torres Strait Islander Studies (AIATSIS).")
st.info(
    "Language names, spellings, and locations are drawn from a published dataset. "
    "Locations are approximate points, not boundaries of Country. This app does not teach language or make cultural claims."
)

view = st.sidebar.radio("Explore", ["Search languages", "Map and nearby", "Patterns in the data", "About the data"])
st.sidebar.markdown(f"**{len(data):,} records** in the bundled data snapshot")

if view == "Search languages":
    st.header("Search languages")
    left, right = st.columns([2, 1])
    query = left.text_input("Language name, alternate spelling, or AustLang code", placeholder="For example: Noongar or A1")
    region = right.selectbox("State or territory tag", regions)
    matches = search(data, query, region, limit=len(data))
    st.write(f"{len(matches):,} matching records")
    if not matches:
        st.warning("No records matched. Try a different spelling or remove the region filter.")
    else:
        display = pd.DataFrame({
            "AustLang code": [item["code"] for item in matches],
            "Name": [item["name"] for item in matches],
            "Region tags": [", ".join(item["regions"]) or "Not listed" for item in matches],
            "Alternate names": [item["alternate_names"] for item in matches],
        })
        st.dataframe(display, width="stretch", hide_index=True, height=430)
        selected_code = st.selectbox("Open a source record", [item["code"] for item in matches], format_func=lambda code: next(f"{r['name']} ({code})" for r in matches if r["code"] == code))
        selected = next(item for item in matches if item["code"] == selected_code)
        st.subheader(selected["name"])
        st.write(f"**AustLang code:** {selected['code']}")
        st.write(f"**Region tags:** {', '.join(selected['regions']) or 'Not listed'}")
        st.write(f"**Alternate names in source:** {selected['alternate_names'] or 'Not listed'}")
        if selected["source_url"]:
            st.link_button("View AIATSIS source record", selected["source_url"])

elif view == "Map and nearby":
    st.header("Approximate location map")
    st.write("Points are published approximate locations. Missing or invalid coordinates are omitted from the map.")
    mapped = [r for r in data if r["latitude"] is not None]
    map_region = st.selectbox("Show region", regions)
    mapped = [r for r in mapped if map_region == "All" or map_region in r["regions"]]
    st.write(f"Showing {len(mapped):,} of {len(data):,} records with usable coordinates")
    if mapped:
        st.map(pd.DataFrame({"lat": [r["latitude"] for r in mapped], "lon": [r["longitude"] for r in mapped]}), size=40)
    st.subheader("Find nearby published points")
    st.caption("Distance is calculated between approximate points. It does not establish a cultural or territorial relationship.")
    col1, col2 = st.columns(2)
    latitude = col1.number_input("Latitude", min_value=-45.0, max_value=-9.0, value=-31.95, step=0.01)
    longitude = col2.number_input("Longitude", min_value=110.0, max_value=155.0, value=115.86, step=0.01)
    nearby = nearest(data, latitude, longitude, 10)
    st.dataframe(pd.DataFrame({
        "Name": [r["name"] for r, _ in nearby],
        "Code": [r["code"] for r, _ in nearby],
        "Approx. distance (km)": [round(distance, 1) for _, distance in nearby],
        "AIATSIS record": [r["source_url"] for r, _ in nearby],
    }), width="stretch", hide_index=True)

elif view == "Patterns in the data":
    st.header("Patterns in the dataset")
    st.write("These charts describe the **dataset's coverage**, not the number of living languages or speakers in a region.")
    with_location = sum(r["latitude"] is not None for r in data)
    with_aliases = sum(bool(r["alternate_names"]) for r in data)
    with_region = sum(bool(r["regions"]) for r in data)
    a, b, c = st.columns(3)
    a.metric("Published records", f"{len(data):,}")
    b.metric("With usable location", f"{with_location:,}", f"{with_location / len(data):.0%}")
    c.metric("With alternate names", f"{with_aliases:,}", f"{with_aliases / len(data):.0%}")
    st.subheader("Records tagged to each region")
    st.caption("A record can have multiple region tags, so bar totals can exceed the number of records.")
    chart = pd.DataFrame({"Region": list(counts), "Records": list(counts.values())}).set_index("Region")
    st.bar_chart(chart, horizontal=True, color="#A35232")
    st.subheader("Completeness")
    st.dataframe(pd.DataFrame({"Field": ["Region tag", "Usable coordinates", "Alternate names"], "Records": [with_region, with_location, with_aliases], "Missing": [len(data)-with_region, len(data)-with_location, len(data)-with_aliases]}), hide_index=True, width="stretch")

else:
    st.header("About the data")
    st.markdown(
        "This app uses a snapshot of **AIATSIS AustLang language metadata**, accessed through the "
        "Australian Government's spatial data service. The [data.gov.au dataset listing](" + SOURCE + ") "
        "identifies AIATSIS as the publisher and states **Creative Commons Attribution 4.0 International**. "
        "Names, alternate spellings, region tags, and approximate coordinates come from the source."
    )
    st.markdown(
        "**Attribution:** Australian Institute of Aboriginal and Torres Strait Islander Studies (AIATSIS), "
        "AustLang dataset, CC BY 4.0. Data adapted for this app by selecting fields, cleaning whitespace, "
        "and treating missing or out-of-range coordinates as unavailable."
    )
    st.write("The snapshot contains", f"{len(data):,}", "records and is bundled as a CSV file so the app works without an API key.")
    st.write("**Limitations:** The dataset is live and may change. A state or territory tag is not a boundary of Country. "
             "Some records have no region tag or usable coordinate. Duplicate or variant names may reflect distinct source records. "
             "For cultural context and current details, follow the AIATSIS source record.")
    st.link_button("Open the dataset listing", SOURCE)
    st.link_button("About AustLang at AIATSIS", "https://aiatsis.gov.au/research/languages/austlang")
