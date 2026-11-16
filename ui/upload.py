"""Independent upload controls for each TexLab workspace."""

from dataclasses import dataclass
from typing import Any

import streamlit as st

from config.constants import (
    WORKSPACE_FULL_ANALYSIS,
    WORKSPACE_PLOT_GRAPH,
    WORKSPACE_PLOT_TRACES,
)
from core.file_router import route_uploaded_files
from core.session_manager import WORKSPACE_UPLOAD_KEYS


@dataclass
class UploadSelection:
    """Uploaded files selected for the active workspace."""

    instron_files: dict[str, Any]
    multimeter_files: dict[str, Any]
    generic_csv_files: list[Any]
    routing_notes: list[str]


def render_uploads(workspace: str) -> UploadSelection:
    """Render independent uploaders and route files for the selected workspace."""
    analysis_expander = st.expander(
        "Full analysis files", expanded=workspace == WORKSPACE_FULL_ANALYSIS
    )
    trace_expander = st.expander(
        "Plot traces only files", expanded=workspace == WORKSPACE_PLOT_TRACES
    )
    generic_expander = st.expander(
        "Plot graph files", expanded=workspace == WORKSPACE_PLOT_GRAPH
    )

    with analysis_expander:
        analysis_column_instron, analysis_column_multimeter = st.columns(2)
        analysis_instron = analysis_column_instron.file_uploader(
            "Upload Instron Tensile CSVs",
            type=["csv"],
            accept_multiple_files=True,
            key=WORKSPACE_UPLOAD_KEYS["analysis_instron"],
        )
        analysis_multimeter = analysis_column_multimeter.file_uploader(
            "Upload Multimeter (DMM) CSVs",
            type=["csv"],
            accept_multiple_files=True,
            key=WORKSPACE_UPLOAD_KEYS["analysis_multimeter"],
        )

    with trace_expander:
        trace_column_instron, trace_column_multimeter = st.columns(2)
        trace_instron = trace_column_instron.file_uploader(
            "Upload Instron Tensile CSVs",
            type=["csv"],
            accept_multiple_files=True,
            key=WORKSPACE_UPLOAD_KEYS["trace_instron"],
        )
        trace_multimeter = trace_column_multimeter.file_uploader(
            "Upload Multimeter (DMM) CSVs",
            type=["csv"],
            accept_multiple_files=True,
            key=WORKSPACE_UPLOAD_KEYS["trace_multimeter"],
        )

    with generic_expander:
        st.caption(
            "Upload any CSV with a header row. Choose detected X and Y columns in the graph workspace."
        )
        generic_csv_files = st.file_uploader(
            "Upload CSV files",
            type=["csv"],
            accept_multiple_files=True,
            key=WORKSPACE_UPLOAD_KEYS["generic_csv"],
        )

    if workspace == WORKSPACE_FULL_ANALYSIS:
        instron_uploads, multimeter_uploads = analysis_instron, analysis_multimeter
    elif workspace == WORKSPACE_PLOT_TRACES:
        instron_uploads, multimeter_uploads = trace_instron, trace_multimeter
    else:
        instron_uploads, multimeter_uploads = [], []

    instron_files, multimeter_files, routing_notes = route_uploaded_files(
        instron_uploads, multimeter_uploads
    )
    for note in routing_notes:
        st.info(note)

    return UploadSelection(
        instron_files=instron_files,
        multimeter_files=multimeter_files,
        generic_csv_files=generic_csv_files or [],
        routing_notes=routing_notes,
    )
