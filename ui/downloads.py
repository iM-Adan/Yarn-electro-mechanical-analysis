"""Streamlit download controls."""

import streamlit as st
import pandas as pd

from exports.csv_export import dataframe_to_csv_bytes


def render_summary_download(summary_frame: pd.DataFrame) -> None:
    """Render the existing complete summary metrics CSV download."""
    st.download_button(
        label="Download Complete Summary Metrics CSV",
        data=dataframe_to_csv_bytes(summary_frame),
        file_name="yarn_sensor_comparison_metrics.csv",
        mime="text/csv",
    )
