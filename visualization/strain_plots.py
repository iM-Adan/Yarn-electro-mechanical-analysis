"""Plot builders for resistance, resistivity, and strain."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.specimen_comparison import SpecimenAnalysis


def build_curve_figure(results: list[SpecimenAnalysis]) -> go.Figure:
    """Build the existing relative-resistance and normalized-resistivity plot."""
    figure = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "1A. Relative Resistance (ΔR/R₀) vs. Strain",
            "1B. Normalized Resistivity vs. Strain",
        ),
    )
    for result in results:
        plot_data = result.analysis_plot
        if plot_data is None:
            continue
        color = plot_data["color"]
        figure.add_trace(
            go.Scatter(
                x=plot_data["strain_percent"],
                y=plot_data["relative_resistance"],
                mode="lines",
                name=result.label,
                line={"color": color, "width": 2},
            ),
            row=1,
            col=1,
        )
        figure.add_trace(
            go.Scatter(
                x=[plot_data["turning_strain_percent"]],
                y=[plot_data["turning_relative_resistance"]],
                mode="markers",
                name=f"{result.label} turning strain",
                marker={"color": color, "size": 9},
                showlegend=False,
            ),
            row=1,
            col=1,
        )
        figure.add_trace(
            go.Scatter(
                x=plot_data["strain_percent"],
                y=plot_data["normalized_resistance"],
                mode="lines",
                name=result.label,
                line={"color": color, "width": 2},
                showlegend=False,
            ),
            row=1,
            col=2,
        )

    figure.add_hline(y=0, line_dash="dot", line_color="gray", row=1, col=1)
    figure.update_xaxes(title_text="Strain (%)", showgrid=True)
    figure.update_yaxes(title_text="ΔR/R₀", showgrid=True, row=1, col=1)
    figure.update_yaxes(
        title_text="Normalized Resistance (Ω·den/cm)", showgrid=True, row=1, col=2
    )
    figure.update_layout(hovermode="x unified", height=500)
    return figure
