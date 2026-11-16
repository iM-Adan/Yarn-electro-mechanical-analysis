"""Analysis-specific Streamlit sidebar controls."""

import streamlit as st


def render_analysis_settings() -> tuple[float, float]:
    """Render the existing baseline and post-break controls."""
    st.sidebar.header("Signal & Window Settings")
    baseline_window_s = st.sidebar.slider(
        "Unloaded Baseline Noise Window (s)", 0.5, 5.0, 2.0, 0.5
    )
    pre_break_trim_pct = st.sidebar.slider(
        "Trim post-fracture tail after peak load (%)", 0.0, 1.0, 0.0, 0.05
    )
    return baseline_window_s, pre_break_trim_pct
