"""Plot builders for arbitrary CSVs and legacy trace-only signals."""

import plotly.graph_objects as go


def _trace_type(x_kind: str, y_kind: str, use_webgl: bool):
    if (
        use_webgl
        and x_kind in ("numeric", "datetime")
        and y_kind in ("numeric", "datetime")
    ):
        return go.Scattergl
    return go.Scatter


def build_combined_plot(
    series,
    x_label: str,
    y_label: str,
    title: str,
    x_kind: str = "numeric",
    y_kind: str = "numeric",
    use_webgl: bool = True,
) -> go.Figure:
    """Build an interactive combined graph from named X/Y data series."""
    figure = go.Figure()
    trace_type = _trace_type(x_kind, y_kind, use_webgl)
    for name, x_values, y_values in series:
        figure.add_trace(
            trace_type(
                x=x_values,
                y=y_values,
                mode="lines",
                name=name,
                connectgaps=False,
            )
        )
    figure.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        hovermode="x unified",
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
    )
    return figure


def build_individual_plot(
    name: str,
    x_values,
    y_values,
    x_label: str,
    y_label: str,
    x_kind: str = "numeric",
    y_kind: str = "numeric",
    use_webgl: bool = True,
) -> go.Figure:
    """Build one interactive graph for an individual file or trace."""
    trace_type = _trace_type(x_kind, y_kind, use_webgl)
    figure = go.Figure(
        trace_type(
            x=x_values,
            y=y_values,
            mode="lines",
            name=name,
            connectgaps=False,
        )
    )
    figure.update_layout(
        title=name,
        xaxis_title=x_label,
        yaxis_title=y_label,
        hovermode="x",
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
    )
    return figure
