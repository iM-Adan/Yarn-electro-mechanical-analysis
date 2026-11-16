"""Specimen pairing and measurement configuration widgets."""

import streamlit as st

from config.constants import DEFAULT_GAUGE_LENGTH_MM, DEFAULT_TEX, MAX_SPECIMENS


def render_specimen_configurations(
    instron_files: dict, multimeter_files: dict
) -> list[dict]:
    """Render the existing specimen controls and return their configuration values."""
    st.subheader("Configure Specimens for Comparison")
    specimen_count = st.number_input(
        "Number of specimens/tests to compare",
        min_value=1,
        max_value=MAX_SPECIMENS,
        value=1,
    )
    configurations = []
    instron_names = list(instron_files)
    multimeter_names = list(multimeter_files)

    for index in range(specimen_count):
        with st.expander(
            f"Specimen {index + 1} Configuration", expanded=index == 0
        ):
            label_column, instron_column, multimeter_column = st.columns(3)
            label = label_column.text_input(
                "Label / Design Parameter",
                value=f"Sample {index + 1}",
                key=f"lbl_{index}",
            )
            instron_name = instron_column.selectbox(
                "Instron CSV",
                instron_names,
                index=min(index, len(instron_names) - 1),
                key=f"inst_{index}",
            )
            multimeter_name = multimeter_column.selectbox(
                "Multimeter CSV",
                multimeter_names,
                index=min(index, len(multimeter_names) - 1),
                key=f"dmm_{index}",
            )

            tex_column, gauge_column, offset_column, sync_column = st.columns(4)
            tex = tex_column.number_input(
                "Linear Density (tex)",
                value=DEFAULT_TEX,
                min_value=1.0,
                step=10.0,
                key=f"tex_{index}",
            )
            gauge_length_mm = gauge_column.number_input(
                "Gauge Length (mm)",
                value=DEFAULT_GAUGE_LENGTH_MM,
                min_value=1.0,
                step=10.0,
                key=f"gl_{index}",
            )
            offset = offset_column.number_input(
                "Sync Offset: Instron Start in DMM Time (s)",
                value=0.0,
                min_value=-30.0,
                max_value=30.0,
                step=0.1,
                key=f"off_{index}",
            )
            auto_sync = sync_column.checkbox(
                "Auto-align peak break to R spike",
                value=False,
                key=f"auto_{index}",
            )

            configurations.append(
                {
                    "label": label,
                    "instron_file": instron_files[instron_name],
                    "multimeter_file": multimeter_files[multimeter_name],
                    "tex": tex,
                    "gauge_mm": gauge_length_mm,
                    "offset": offset,
                    "auto_sync": auto_sync,
                }
            )
    return configurations
