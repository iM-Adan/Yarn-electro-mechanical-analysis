"""Summary and event-table presentation."""

import numpy as np
import pandas as pd
import streamlit as st

from analysis.specimen_comparison import SpecimenAnalysis


def render_metrics(results: list[SpecimenAnalysis]) -> pd.DataFrame | None:
    """Show specimen summary metrics and batch comparisons."""
    summary_rows = [
        result.summary for result in results if result.summary is not None
    ]
    if not summary_rows:
        return None

    summary_frame = pd.DataFrame(summary_rows)
    st.subheader("5. Complete Electromechanical & Sensor Viability Matrix")
    st.dataframe(summary_frame, use_container_width=True)
    if len(summary_frame) > 1:
        resistance_0_values = summary_frame["R₀ (Ω)"].values
        resistance_0_cv = (
            np.std(resistance_0_values, ddof=1) / np.mean(resistance_0_values)
        ) * 100.0
        mean_column, spread_column, correlation_column = st.columns(3)
        mean_column.metric(
            "Batch Mean R₀", f"{np.mean(resistance_0_values):.2f} Ω"
        )
        spread_column.metric("Batch R₀ Spread (CV%)", f"{resistance_0_cv:.2f}%")
        if len(resistance_0_values) >= 2 and np.ptp(resistance_0_values) > 0:
            correlation = np.corrcoef(
                resistance_0_values,
                summary_frame["Strain at Break (%)"].values,
            )[0, 1]
            correlation_column.metric(
                "R₀ vs. Break Strain Correlation (r)", f"{correlation:.2f}"
            )
    return summary_frame


def render_load_drop_events(results: list[SpecimenAnalysis]) -> None:
    """Show the detected mid-test load-drop table when events are present."""
    event_rows = [event for result in results for event in result.events]
    if event_rows:
        st.subheader("6. Detected Mid-Test Load-Drop Events (Slippage / Fiber Fracture)")
        st.dataframe(pd.DataFrame(event_rows), use_container_width=True)
