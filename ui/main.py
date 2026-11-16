"""Main Streamlit workspace router."""

from config.constants import (
    WORKSPACE_FULL_ANALYSIS,
    WORKSPACE_PLOT_GRAPH,
    WORKSPACE_PLOT_TRACES,
)
from ui.analysis_dashboard import render_analysis_workspace
from ui.plot_workspace import (
    render_generic_plot_workspace,
    render_plot_traces_workspace,
)
from ui.theme import render_page_header
from ui.upload import render_uploads


def run_app() -> None:
    """Configure the TexLab page and dispatch to its selected workspace."""
    workspace = render_page_header()
    selection = render_uploads(workspace)
    if workspace == WORKSPACE_FULL_ANALYSIS:
        render_analysis_workspace(selection)
    elif workspace == WORKSPACE_PLOT_TRACES:
        render_plot_traces_workspace(
            selection.instron_files, selection.multimeter_files
        )
    elif workspace == WORKSPACE_PLOT_GRAPH:
        render_generic_plot_workspace(selection.generic_csv_files)
