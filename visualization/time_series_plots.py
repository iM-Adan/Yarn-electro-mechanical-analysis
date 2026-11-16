"""Plot builders for resistance time series."""

import plotly.graph_objects as go

from analysis.specimen_comparison import SpecimenAnalysis


def build_resistance_time_figure(results: list[SpecimenAnalysis]) -> go.Figure:
    """Build raw resistance traces aligned to the Instron pull onset."""
    figure = go.Figure()
    for result in results:
        plot_data = result.resistance_time_plot
        if plot_data is None:
            continue
        figure.add_trace(
            go.Scatter(
                x=plot_data["time"],
                y=plot_data["resistance"],
                mode="lines",
                name=result.label,
                line={"color": plot_data["color"], "width": 2},
            )
        )

    figure.update_layout(
        title="3. Resistance (Ω) vs. Time Since Pull Onset",
        xaxis_title="Time Since Pull Onset (s)",
        yaxis_title="Resistance (Ω)",
        hovermode="x unified",
    )
    figure.update_xaxes(showgrid=True)
    figure.update_yaxes(showgrid=True)
    return figure
