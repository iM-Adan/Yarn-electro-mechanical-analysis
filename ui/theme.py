"""TexLab page layout and shared visual styling."""

import streamlit as st

from config.constants import WORKSPACE_OPTIONS
from config.settings import APP_NAME, LOGO_PATH, PAGE_ICON, PAGE_LAYOUT, PAGE_TITLE
from core.session_manager import WORKSPACE_STATE_KEY, initialize_session_state


def render_page_header() -> str:
    """Configure the Streamlit page and show its branded workspace selector."""
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=PAGE_LAYOUT,
    )
    initialize_session_state(st.session_state)
    st.markdown(
        """
        <style>
        :root {
            --ink: #172b45;
            --muted: #52677f;
            --line: #dce5ef;
        }
        .stApp {
            background: linear-gradient(180deg, #f3f7fb 0%, #fbfcfe 36rem);
            color: var(--ink);
        }
        [data-testid="stHeader"] {
            background: rgba(243, 247, 251, 0.88);
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 1440px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }
        .hero {
            padding: 1.55rem 1.8rem;
            margin-bottom: 1.25rem;
            border: 1px solid #d6e5ed;
            border-radius: 18px;
            background: linear-gradient(115deg, #ffffff 0%, #edf6f8 100%);
            box-shadow: 0 8px 26px rgba(27, 55, 80, 0.06);
        }
        .hero h1 {
            margin: 0 0 0.45rem 0;
            color: var(--ink);
            font-size: clamp(1.7rem, 3vw, 2.45rem);
            font-weight: 750;
            letter-spacing: -0.035em;
        }
        .hero p {
            max-width: 980px;
            margin: 0;
            color: var(--muted);
            line-height: 1.65;
        }
        h2, h3 {
            color: var(--ink);
            letter-spacing: -0.02em;
        }
        div[data-testid="stExpander"] {
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.88);
        }
        div[data-testid="stFileUploader"] {
            padding: 0.5rem;
            border: 1px dashed #a9bfce;
            border-radius: 12px;
            background: #f9fbfd;
        }
        div[data-testid="stRadio"] > div {
            gap: 0.55rem;
        }
        div[data-testid="stPlotlyChart"] {
            padding: 0.35rem;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: #ffffff;
        }
        [data-testid="stSidebar"] {
            background: #f0f5f9;
            border-right: 1px solid var(--line);
        }
        .stButton > button {
            border-radius: 10px;
            border-color: #b7cbd7;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    logo_column, hero_column = st.columns([0.75, 8])
    logo_column.image(LOGO_PATH, width=76)
    with hero_column:
        st.markdown(
            f"""
            <section class="hero">
              <h1>{APP_NAME}</h1>
              <p>Explore yarn sensor data with interactive plots or run a full electromechanical analysis
              for curve shape, strain resolution, resistivity, load-drop alignment, recovery, and sensor quality.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
    return st.radio(
        "Workspace",
        WORKSPACE_OPTIONS,
        horizontal=True,
        help="Choose full specimen analysis, legacy Instron/multimeter traces, or plotting of arbitrary CSV data.",
        key=WORKSPACE_STATE_KEY,
    )
