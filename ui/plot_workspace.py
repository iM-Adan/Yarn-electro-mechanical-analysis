"""Plot-only and arbitrary-CSV graph workspaces."""

from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from parsers.generic_csv_parser import (
    convert_plot_column,
    infer_plot_column_kind,
    parse_generic_csv,
)
from parsers.instron_parser import parse_instron
from parsers.multimeter_parser import parse_multimeter
from visualization.generic_plots import (
    build_combined_plot,
    build_individual_plot,
)


@st.cache_data(show_spinner=False)
def _cached_parse_generic_csv(file_bytes: bytes, file_name: str):
    """Cache CSV parsing while keeping the parser independent of Streamlit."""
    return parse_generic_csv(file_bytes, file_name)


def render_plot_traces_workspace(
    instron_files: dict[str, Any], multimeter_files: dict[str, Any]
) -> None:
    """Render the existing signal picker, full-range option, and trace plots."""
    parsed_instron = {}
    parsed_multimeter = {}
    for name, file_buf in instron_files.items():
        try:
            parsed_instron[name] = parse_instron(file_buf)
        except Exception as error:
            st.error(f"Could not read Instron trace '{name}': {error}")
    for name, file_buf in multimeter_files.items():
        try:
            parsed_multimeter[name] = parse_multimeter(file_buf)
        except Exception as error:
            st.error(f"Could not read multimeter trace '{name}': {error}")

    trace_options = []
    if parsed_multimeter:
        trace_options.append("Resistance (DMM)")
    if parsed_instron:
        available_columns = {
            column
            for frame in parsed_instron.values()
            for column in frame.columns
        }
        for label, column in (
            ("Load (Instron)", "Primary load (N)"),
            ("Extension (Instron)", "Tensile extension (mm)"),
            ("Composite strain (Instron)", "Composite strain"),
        ):
            if column in available_columns:
                trace_options.append(label)

    if trace_options:
        selected_trace = st.selectbox("Trace signal to plot", trace_options)
        if selected_trace == "Resistance (DMM)":
            traces = [
                (name, np.asarray(time_s), np.asarray(resistance))
                for name, (time_s, resistance) in parsed_multimeter.items()
            ]
            x_label = "Time (s)"
            y_label = "Resistance (Ω)"
        else:
            column_by_signal = {
                "Load (Instron)": ("Primary load (N)", "Load (N)"),
                "Extension (Instron)": ("Tensile extension (mm)", "Extension (mm)"),
                "Composite strain (Instron)": (
                    "Composite strain",
                    "Composite strain",
                ),
            }
            column, y_label = column_by_signal[selected_trace]
            traces = [
                (name, frame["Time (s)"].to_numpy(), frame[column].to_numpy())
                for name, frame in parsed_instron.items()
                if column in frame.columns
            ]
            x_label = "Time (s)"

        finite_times = [
            time[np.isfinite(time)]
            for _, time, _ in traces
            if np.issubdtype(time.dtype, np.number) and np.isfinite(time).any()
        ]
        if not finite_times:
            st.warning("The selected trace has no valid numeric time values.")
            return

        time_min = float(min(np.min(time) for time in finite_times))
        time_max = float(max(np.max(time) for time in finite_times))
        time_mode = st.radio(
            "Time range",
            ["Complete data (no time cut)", "Cut to time range"],
            horizontal=True,
            help="Complete data plots every sample in each uploaded trace. Choose a time range only to intentionally crop the traces.",
            key="trace_time_mode",
        )
        if time_mode == "Cut to time range" and time_min < time_max:
            start_column, end_column = st.columns(2)
            range_start = start_column.number_input(
                "Start time (s)",
                min_value=time_min,
                max_value=time_max,
                value=time_min,
                key="trace_range_start",
            )
            range_end = end_column.number_input(
                "End time (s)",
                min_value=time_min,
                max_value=time_max,
                value=time_max,
                key="trace_range_end",
            )
            if range_start > range_end:
                st.error("Start time must be less than or equal to end time.")
                traces_to_plot = []
            else:
                traces_to_plot = []
                for name, time, values in traces:
                    if not np.issubdtype(time.dtype, np.number):
                        continue
                    mask = (
                        np.isfinite(time)
                        & (time >= range_start)
                        & (time <= range_end)
                    )
                    if np.any(mask):
                        traces_to_plot.append((name, time[mask], values[mask]))
        else:
            traces_to_plot = traces

        if traces_to_plot:
            combined_figure = build_combined_plot(
                traces_to_plot,
                x_label,
                y_label,
                "Combined interactive graph",
                use_webgl=False,
            )
            st.subheader("Combined interactive graph")
            st.plotly_chart(combined_figure, use_container_width=True)
            st.subheader("Individual interactive graphs")
            for name, time, values in traces_to_plot:
                figure = build_individual_plot(
                    name,
                    time,
                    values,
                    x_label,
                    y_label,
                    use_webgl=False,
                )
                st.plotly_chart(figure, use_container_width=True)
        elif time_mode == "Cut to time range":
            st.warning("The selected time range contains no samples.")
    elif instron_files or multimeter_files:
        st.warning("No uploaded files contain a readable trace for plotting.")
    else:
        st.info("Upload one or more Instron or multimeter CSV files to plot their traces.")


def render_generic_plot_workspace(uploaded_files: list[Any]) -> None:
    """Render column selection, optional filtering, and generic CSV Plotly charts."""
    plot_frames = {}
    numeric_columns_by_file = {}
    for file_buf in uploaded_files:
        display_name = file_buf.name
        duplicate_number = 2
        while display_name in plot_frames:
            display_name = f"{file_buf.name} ({duplicate_number})"
            duplicate_number += 1
        try:
            plot_frames[display_name], numeric_columns_by_file[display_name] = (
                _cached_parse_generic_csv(file_buf.getvalue(), file_buf.name)
            )
        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            UnicodeDecodeError,
            ValueError,
        ) as error:
            st.error(f"Could not read `{file_buf.name}`: {error}")

    if not plot_frames:
        if uploaded_files:
            st.warning("None of the uploaded CSV files could be read.")
        else:
            st.info("Upload one or more CSV files to choose their X and Y columns and plot them.")
        return

    selected_files = st.multiselect(
        "CSV files to plot",
        options=list(plot_frames),
        default=[next(iter(plot_frames))],
        help="Choose one or more files. Combined plots use columns shared by every selected file.",
        key="generic_plot_files",
    )
    if not selected_files:
        st.info("Select at least one uploaded file to configure the graph.")
        return

    selected_frames = {name: plot_frames[name] for name in selected_files}
    shared_columns = [
        column
        for column in next(iter(selected_frames.values())).columns
        if all(column in frame.columns for frame in selected_frames.values())
    ]
    shared_numeric_columns = [
        column
        for column in numeric_columns_by_file[selected_files[0]]
        if all(
            column in numeric_columns_by_file[name] for name in selected_files
        )
    ]
    row_number_label = "Row number"
    while row_number_label in shared_columns:
        row_number_label += " (generated)"
    x_options = [*shared_columns, row_number_label]

    if not shared_columns:
        st.warning(
            "The selected files do not share any columns. Select a single file "
            "or choose files with a common column."
        )
        return

    default_x = next(
        (
            column
            for column in x_options
            if column != row_number_label
            and any(
                hint in column.lower() for hint in ("time", "date", "stamp")
            )
        ),
        row_number_label if row_number_label in x_options else x_options[0],
    )
    column_x, column_y = st.columns(2)
    x_column = column_x.selectbox(
        "X axis",
        x_options,
        index=x_options.index(default_x),
        key="generic_plot_x",
    )
    y_options = [column for column in shared_columns if column != x_column]
    if not y_options:
        st.warning(
            "Choose a different X axis or upload a CSV with at least two "
            "columns to select a Y axis."
        )
        return

    preferred_y_options = [
        column for column in y_options if column in shared_numeric_columns
    ]
    y_default = next(
        (
            column
            for column in preferred_y_options
            if any(
                hint in column.lower()
                for hint in (
                    "resistance",
                    "load",
                    "force",
                    "strain",
                    "voltage",
                    "current",
                )
            )
        ),
        preferred_y_options[0] if preferred_y_options else y_options[0],
    )
    y_column = column_y.selectbox(
        "Y axis",
        y_options,
        index=y_options.index(y_default),
        key="generic_plot_y",
    )
    x_kind = (
        "numeric"
        if x_column == row_number_label
        else infer_plot_column_kind(
            selected_frames[selected_files[0]][x_column], x_column
        )
    )
    y_kind = infer_plot_column_kind(
        selected_frames[selected_files[0]][y_column], y_column
    )
    plot_series = []
    for name, frame in selected_frames.items():
        x_values = (
            pd.Series(np.arange(1, len(frame) + 1), index=frame.index)
            if x_column == row_number_label
            else convert_plot_column(frame[x_column], x_kind)
        )
        y_values = convert_plot_column(frame[y_column], y_kind)
        valid = x_values.notna() & y_values.notna()
        if x_kind == "numeric":
            valid &= np.isfinite(
                x_values.to_numpy(dtype=float, na_value=np.nan)
            )
        if y_kind == "numeric":
            valid &= np.isfinite(
                y_values.to_numpy(dtype=float, na_value=np.nan)
            )
        plot_series.append((name, x_values, y_values, valid, len(frame)))

    valid_x_values = [
        x_values[valid]
        for _, x_values, _, valid, _ in plot_series
        if valid.any()
    ]
    range_mode = "Complete data (no cut)"
    if x_kind in ("numeric", "datetime"):
        range_mode = st.radio(
            "X-axis range",
            ["Complete data (no cut)", "Choose range"],
            horizontal=True,
            help="Complete data is shown by default. Choose a range only to crop the selected X-axis values.",
            key="generic_plot_range_mode",
        )
    else:
        st.caption(
            "All rows are shown. Select a numeric or date-like X axis to filter by range."
        )

    range_start = None
    range_end = None
    if valid_x_values and range_mode == "Choose range":
        if x_kind == "numeric":
            x_min = float(min(values.min() for values in valid_x_values))
            x_max = float(max(values.max() for values in valid_x_values))
            if x_min < x_max:
                range_column_start, range_column_end = st.columns(2)
                range_start = range_column_start.number_input(
                    "X-axis start",
                    min_value=x_min,
                    max_value=x_max,
                    value=x_min,
                    key="generic_plot_range_start",
                )
                range_end = range_column_end.number_input(
                    "X-axis end",
                    min_value=x_min,
                    max_value=x_max,
                    value=x_max,
                    key="generic_plot_range_end",
                )
        elif x_kind == "datetime":
            all_dates = pd.concat(valid_x_values)
            date_min = all_dates.min().date()
            date_max = all_dates.max().date()
            if date_min < date_max:
                date_range = st.date_input(
                    "X-axis date range",
                    value=(date_min, date_max),
                    min_value=date_min,
                    max_value=date_max,
                    key="generic_plot_date_range",
                )
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    range_start = pd.Timestamp(date_range[0])
                    range_end = (
                        pd.Timestamp(date_range[1])
                        + pd.Timedelta(days=1)
                        - pd.Timedelta(nanoseconds=1)
                    )

    if (
        range_start is not None
        and range_end is not None
        and range_start > range_end
    ):
        st.error("The X-axis start must not be after its end.")
        return

    chart_series = []
    plotted_count = 0
    omitted_count = 0
    for name, x_values, y_values, valid, row_count in plot_series:
        if range_start is not None and range_end is not None:
            valid &= (x_values >= range_start) & (x_values <= range_end)
        x_plot = x_values[valid]
        y_plot = y_values[valid]
        if len(x_plot):
            plotted_count += len(x_plot)
            omitted_count += row_count - len(x_plot)
            chart_series.append((name, x_plot, y_plot))
        else:
            omitted_count += row_count

    if chart_series:
        x_label = "Row number" if x_column == row_number_label else x_column
        title = (
            "Interactive graph"
            if len(chart_series) == 1
            else "Combined interactive graph"
        )
        combined_figure = build_combined_plot(
            chart_series, x_label, y_column, title, x_kind, y_kind
        )
        st.plotly_chart(
            combined_figure,
            use_container_width=True,
            config={"displaylogo": False, "scrollZoom": True},
        )
        st.caption(
            f"{plotted_count:,} points plotted; "
            f"{omitted_count:,} rows not shown (invalid axis values "
            "or outside the selected range)."
        )
        if len(chart_series) > 1:
            show_individual = st.checkbox(
                "Show a separate interactive graph for each file",
                value=len(chart_series) <= 5,
                key="generic_plot_individual",
            )
            if show_individual:
                for name, x_plot, y_plot in chart_series:
                    figure = build_individual_plot(
                        name, x_plot, y_plot, x_label, y_column, x_kind, y_kind
                    )
                    st.plotly_chart(
                        figure,
                        use_container_width=True,
                        config={"displaylogo": False, "scrollZoom": True},
                    )
    else:
        st.warning(
            "No rows have valid values for both selected axes "
            "within the chosen range."
        )

    with st.expander("Preview detected columns and sample rows"):
        selected_frame = selected_frames[selected_files[0]]
        st.caption(
            f"`{selected_files[0]}` · {len(selected_frame):,} rows · "
            f"{len(selected_frame.columns):,} columns"
        )
        st.dataframe(selected_frame.head(10), use_container_width=True)
