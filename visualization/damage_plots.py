"""Plot builders for tenacity and load-drop events."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.specimen_comparison import SpecimenAnalysis


def build_damage_figure(results: list[SpecimenAnalysis]) -> go.Figure:
    """Build the existing tenacity and resistance/damage comparison plot."""
    figure = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "2A. Tenacity vs. Time",
            "2B. Relative Resistance vs. Tenacity",
        ),
    )
    for result in results:
        plot_data = result.analysis_plot
        if plot_data is None:
            continue
        color = plot_data["color"]
        figure.add_trace(
            go.Scatter(
                x=plot_data["time"],
                y=plot_data["tenacity"],
                mode="lines",
                name=f"{result.label} Tenacity",
                line={"color": color, "width": 1.8},
            ),
            row=1,
            col=1,
        )
        if len(plot_data["drop_peaks"]) > 0:
            figure.add_trace(
                go.Scatter(
                    x=plot_data["time"][plot_data["drop_peaks"]],
                    y=plot_data["tenacity"][plot_data["drop_peaks"]],
                    mode="markers",
                    name=f"{result.label} load-drop events",
                    marker={"color": "red", "size": 9, "symbol": "x"},
                ),
                row=1,
                col=1,
            )
        figure.add_trace(
            go.Scatter(
                x=plot_data["tenacity"],
                y=plot_data["relative_resistance"],
                mode="lines",
                name=result.label,
                line={"color": color, "width": 2},
                showlegend=False,
            ),
            row=1,
            col=2,
        )

    figure.update_xaxes(showgrid=True, row=1, col=1, title_text="Time (s)")
    figure.update_yaxes(
        showgrid=True, row=1, col=1, title_text="Tenacity (cN/tex)"
    )
    figure.update_xaxes(
        showgrid=True, row=1, col=2, title_text="Tenacity (cN/tex)"
    )
    figure.update_yaxes(showgrid=True, row=1, col=2, title_text="ΔR/R₀")
    figure.update_layout(hovermode="closest", height=500)
    return figure
