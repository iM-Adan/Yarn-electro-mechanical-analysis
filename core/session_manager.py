"""Session defaults and stable workspace keys."""

from collections.abc import MutableMapping
from typing import Any

from config.constants import WORKSPACE_FULL_ANALYSIS

WORKSPACE_STATE_KEY = "workspace_mode"
WORKSPACE_UPLOAD_KEYS = {
    "analysis_instron": "analysis_instron_uploads",
    "analysis_multimeter": "analysis_dmm_uploads",
    "trace_instron": "plot_instron_uploads",
    "trace_multimeter": "plot_dmm_uploads",
    "generic_csv": "plot_csv_uploads",
}


def initialize_session_state(session_state: MutableMapping[str, Any]) -> None:
    """Set a default workspace without overwriting persisted user selections."""
    session_state.setdefault(WORKSPACE_STATE_KEY, WORKSPACE_FULL_ANALYSIS)
