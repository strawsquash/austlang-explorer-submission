"""Presentation helpers for the Streamlit interface."""

import streamlit as st


def apply_style() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #f8f7f2; color: #20322d; }
        .block-container { max-width: 1120px; padding-top: 2rem; padding-bottom: 4rem; }
        h1, h2, h3 { color: #193a32 !important; letter-spacing: -.03em; }
        h2 { margin-top: .6rem !important; }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stMetric"] { background: #fffdf8; border: 1px solid #e4e4d8; border-radius: 16px; padding: 1.1rem 1.3rem; }
        [data-testid="stMetricLabel"] { color: #52655e; }
        [data-testid="stAlert"] { border-radius: 14px; }
        [data-testid="stDataFrame"] { border: 1px solid #e4e4d8; border-radius: 14px; overflow: hidden; }
        div.stButton > button, div.stLinkButton > a { border-radius: 10px; font-weight: 650; }
        [data-testid="stSegmentedControl"] { background: #e9ede5; border-radius: 14px; padding: .4rem; margin-bottom: .4rem; }
        [data-testid="stSegmentedControl"] button { border-radius: 10px; font-weight: 650; }
        .hero { background: linear-gradient(135deg,#174e40,#1f6453); color: white; border-radius: 22px; padding: 2rem 2.2rem; margin-bottom: 1rem; }
        .hero h1 { color: white !important; margin: .15rem 0 .55rem; font-size: clamp(2rem,5vw,3.2rem); }
        .hero p { margin: 0; max-width: 720px; color: #e6f0e8; font-size: 1.04rem; }
        .eyebrow { color: #c8deca; font-size: .75rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
        .note { background: #ecf1e8; border-left: 4px solid #8f9e7b; border-radius: 0 12px 12px 0; padding: .75rem 1rem; color: #344940; margin: .4rem 0 1.25rem; }
        .section-lead { color: #53665e; margin-top: -.5rem; margin-bottom: 1.1rem; }
        .quick-start { background: #fffdf8; border: 1px solid #dedfd3; border-radius: 14px; padding: .9rem 1rem; margin: 0 0 1.1rem; color: #344940; }
        @media (max-width: 640px) {
          .block-container { padding: .8rem .8rem 3rem; }
          .hero { padding: 1.35rem; border-radius: 17px; }
          .hero p { font-size: .93rem; }
          [data-testid="stSegmentedControl"] button { padding: .2rem .45rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(record_count: int) -> None:
    st.markdown(
        f'<div class="hero"><div class="eyebrow">Published AIATSIS metadata · {record_count:,} records</div>'
        '<h1>AustLang Explorer</h1>'
        '<p>Find language records, examine how the dataset is organised, and follow each result back to its AIATSIS source.</p></div>',
        unsafe_allow_html=True,
    )


def note() -> None:
    st.markdown(
        '<div class="note">Locations are approximate published points, not boundaries of Country. '
        'Charts describe this dataset, not language vitality or speaker numbers.</div>',
        unsafe_allow_html=True,
    )
