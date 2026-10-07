"""Interactive explorer of published AIATSIS AustLang metadata."""

from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from explorer import compare_regions, load_records, nearest, region_counts, search
from ui_style import apply_style, hero, note


DATA = Path(__file__).parent / "data" / "austlang.csv"
SOURCE = "https://data.gov.au/data/dataset/austlang-dataset-001"

st.set_page_config(page_title="AustLang Explorer", page_icon="🗺️", layout="wide", initial_sidebar_state="collapsed")
apply_style()


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

hero()
view = st.segmented_control(
    "Explore",
    ["Search Languages", "Language Map", "Dataset Statistics", "Compare Regions", "About the Data"],
    default="Search Languages",
    label_visibility="collapsed",
)
note()

if view == "Search Languages":
    st.header("Search language records")
    st.markdown('<p class="section-lead">Find a published AustLang record and follow it back to the AIATSIS collection.</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="quick-start"><strong>Start here:</strong> Enter a language name, alternate spelling, or code. '
        'You can narrow the results using a state or territory tag.</div>',
        unsafe_allow_html=True,
    )
    left, right = st.columns([2, 1])
    query = left.text_input("Language name, alternate spelling, or AustLang code", placeholder="For example: Noongar or A1")
    region = right.selectbox("State or territory tag", regions)
    matches = search(data, query, region, limit=len(data))
    st.markdown(f"**{len(matches):,} matching records**")
    if not matches:
        st.warning("No records matched. Try a different spelling or remove the region filter.")
    else:
        page_size = 25
        pages = (len(matches) + page_size - 1) // page_size
        page = st.number_input("Results page", min_value=1, max_value=pages, value=1, step=1)
        page_records = matches[(page - 1) * page_size : page * page_size]
        st.caption(f"Showing {(page - 1) * page_size + 1}–{min(page * page_size, len(matches))} of {len(matches):,}")
        display = pd.DataFrame({
            "Code": [item["code"] for item in page_records],
            "Name": [item["name"] for item in page_records],
            "Region tags": [", ".join(item["regions"]) or "Not listed" for item in page_records],
            "Alternate names": [item["alternate_names"] for item in page_records],
        })
        st.dataframe(display, width="stretch", hide_index=True, height=400)
        selected_code = st.selectbox("View details for", [item["code"] for item in page_records], format_func=lambda code: next(f"{r['name']} ({code})" for r in page_records if r["code"] == code))
        selected = next(item for item in page_records if item["code"] == selected_code)
        with st.container(border=True):
            st.subheader(selected["name"])
            detail_a, detail_b = st.columns(2)
            detail_a.write(f"**AustLang code:** {selected['code']}")
            detail_b.write(f"**Region tags:** {', '.join(selected['regions']) or 'Not listed'}")
            st.write(f"**Alternate names in source:** {selected['alternate_names'] or 'Not listed'}")
            if selected["source_url"]:
                st.link_button("Open this record at AIATSIS", selected["source_url"])

elif view == "Language Map":
    st.header("Approximate location map")
    st.markdown('<p class="section-lead">Explore published approximate points. Records without valid coordinates are omitted.</p>', unsafe_allow_html=True)
    mapped = [r for r in data if r["latitude"] is not None]
    map_region = st.selectbox("Show region", regions)
    mapped = [r for r in mapped if map_region == "All" or map_region in r["regions"]]
    st.write(f"Showing {len(mapped):,} of {len(data):,} records with usable coordinates")
    if mapped:
        map_data = pd.DataFrame({
            "name": [r["name"] for r in mapped],
            "code": [r["code"] for r in mapped],
            "regions": [", ".join(r["regions"]) or "Not listed" for r in mapped],
            "lat": [r["latitude"] for r in mapped],
            "lon": [r["longitude"] for r in mapped],
        })
        layer = pdk.Layer(
            "ScatterplotLayer",
            map_data,
            get_position="[lon, lat]",
            get_fill_color=[163, 82, 50, 180],
            get_radius=18000,
            radius_min_pixels=4,
            radius_max_pixels=12,
            pickable=True,
        )
        view_state = pdk.ViewState(
            latitude=float(map_data["lat"].mean()),
            longitude=float(map_data["lon"].mean()),
            zoom=3.2 if map_region == "All" else 4.2,
        )
        st.pydeck_chart(
            pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                tooltip={"html": "<b>{name}</b> ({code})<br/>Region tags: {regions}"},
            ),
            width="stretch",
        )
        st.caption("Point at a marker to see the language name, AustLang code, and region tags.")
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

elif view == "Dataset Statistics":
    st.header("Patterns in the dataset")
    st.markdown('<p class="section-lead">See where the dataset has region tags, coordinates and alternate names.</p>', unsafe_allow_html=True)
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

elif view == "Compare Regions":
    st.header("Compare region tags")
    st.markdown('<p class="section-lead">Compare how many records carry two broad region tags, including records tagged to both.</p>', unsafe_allow_html=True)
    available = [region for region in regions if region != "All"]
    first_col, second_col = st.columns(2)
    first = first_col.selectbox("First region", available, index=available.index("WA") if "WA" in available else 0)
    second = second_col.selectbox("Second region", available, index=available.index("NT") if "NT" in available else min(1, len(available) - 1))
    if first == second:
        st.warning("Choose two different regions to compare.")
    else:
        comparison = compare_regions(data, first, second)
        a, b, c = st.columns(3)
        a.metric(f"{first} records", comparison["first_total"])
        b.metric(f"{second} records", comparison["second_total"])
        c.metric("Tagged to both", comparison["both"])
        st.bar_chart(pd.DataFrame({"Record group": [f"{first} only", "Both", f"{second} only"], "Records": [comparison["first_only"], comparison["both"], comparison["second_only"]]}).set_index("Record group"), color="#A35232")
        st.caption("The comparison counts distinct AustLang codes within each group. It reflects the source's broad region metadata.")

else:
    st.header("About the data")
    st.info(
        "This app explores published records about Australian Indigenous languages and approximate locations. "
        "It does not provide translations or teach the languages."
    )
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
