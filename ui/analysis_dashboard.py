"""Full specimen-analysis workspace orchestration."""

import streamlit as st
import plotly.express as px

from analysis.specimen_comparison import SpecimenAnalysis, analyze_specimen
from core.data_loader import load_specimen_data
from ui.downloads import render_summary_download
from ui.metrics_display import render_load_drop_events, render_metrics
from ui.sidebar import render_analysis_settings
from ui.specimen_configuration import render_specimen_configurations
from ui.upload import UploadSelection
from visualization.damage_plots import build_damage_figure
from visualization.specimen_plots import build_specimen_figure
from visualization.strain_plots import build_curve_figure
from visualization.time_series_plots import build_resistance_time_figure


def _render_analysis_results(results: list[SpecimenAnalysis]) -> None:
    """Render the existing analysis plots, individual traces, metrics, and export."""
    curve_figure = build_curve_figure(results)
    damage_figure = build_damage_figure(results)
    resistance_time_figure = build_resistance_time_figure(results)

    st.subheader("1. Curve Shape, Turning Strain & Normalized Resistivity")
    st.plotly_chart(curve_figure, use_container_width=True)
    st.subheader("2. Mechanical Damage Tracking & Load-Drop Alignment")
    st.plotly_chart(damage_figure, use_container_width=True)
    st.subheader("3. Resistance vs. Time Since Pull Onset")
    st.plotly_chart(resistance_time_figure, use_container_width=True)

    if results:
        st.subheader("4. Per-Specimen Load and Resistance vs. Time")
        specimen_columns = st.columns(3)
        for index, result in enumerate(results):
            with specimen_columns[index % 3]:
                st.plotly_chart(
                    build_specimen_figure(result), use_container_width=True
                )

    summary_frame = render_metrics(results)
    if summary_frame is not None:
        render_summary_download(summary_frame)
    render_load_drop_events(results)


def render_analysis_workspace(selection: UploadSelection) -> None:
    """Render specimen setup and scientific analysis for paired uploaded files."""
    instron_files = selection.instron_files
    multimeter_files = selection.multimeter_files
    if not instron_files or not multimeter_files:
        if instron_files or multimeter_files:
            st.warning(
                "Please upload at least one Instron CSV (e.g., `Specimen_RawData_2.csv`) "
                "AND one Multimeter CSV (e.g., `Trace 1.csv`)."
            )
        return

    configurations = render_specimen_configurations(
        instron_files, multimeter_files
    )
    baseline_window_s, pre_break_trim_pct = render_analysis_settings()
    colors = px.colors.qualitative.Plotly
    results = []

    for index, configuration in enumerate(configurations):
        try:
            instron_frame, electrical_time, resistance = load_specimen_data(
                configuration["instron_file"],
                configuration["multimeter_file"],
            )
        except Exception as error:
            st.error(
                f"Error parsing files for {configuration['label']}: {error}"
            )
            continue

        result = analyze_specimen(
            instron_frame,
            electrical_time,
            resistance,
            configuration,
            baseline_window_s,
            pre_break_trim_pct,
        )
        color = colors[index % len(colors)]
        if result.analysis_plot is not None:
            result.analysis_plot["color"] = color
        if result.resistance_time_plot is not None:
            result.resistance_time_plot["color"] = color
        for warning in result.warnings:
            st.warning(warning)
        results.append(result)

    _render_analysis_results(results)
