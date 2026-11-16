"""Per-specimen load and resistance time-series overlays."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.specimen_comparison import SpecimenAnalysis


def build_specimen_figure(result: SpecimenAnalysis) -> go.Figure:
    """Build the existing two-axis load/resistance time plot for one specimen."""
    plot_data = result.time_plot
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Scatter(
            x=plot_data["load_time"],
            y=plot_data["load"],
            mode="lines",
            name="Load (Instron)",
            line={"color": "blue", "width": 1.8},
        ),
        secondary_y=False,
    )
    if len(plot_data["resistance_time"]):
        figure.add_trace(
            go.Scatter(
                x=plot_data["resistance_time"],
                y=plot_data["resistance"],
                mode="lines",
                name="Resistance (DMM trace)",
                line={"color": "red", "width": 1.8},
            ),
            secondary_y=True,
        )

    figure.update_layout(
        title=f"{result.label}: Load & Resistance vs. Time",
        hovermode="x unified",
    )
    figure.update_xaxes(title_text=plot_data["time_axis_label"], showgrid=True)
    figure.update_yaxes(title_text="Load (N)", secondary_y=False)
    figure.update_yaxes(
        title_text="Resistance (Ω)", secondary_y=True, showgrid=False
    )
    return figure
