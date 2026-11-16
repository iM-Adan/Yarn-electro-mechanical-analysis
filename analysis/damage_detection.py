"""Load-drop event detection."""

import numpy as np

from config.constants import LOAD_DROP_PROMINENCE
from utils.numerical import find_peaks_by_prominence


def detect_load_drop_events(
    time_s: np.ndarray,
    strain_percent: np.ndarray,
    tenacity: np.ndarray,
    relative_resistance: np.ndarray,
    specimen_label: str,
) -> tuple[np.ndarray, list[dict]]:
    """Detect load drops and format the existing event table rows."""
    tenacity_difference = np.diff(tenacity)
    drop_peaks = find_peaks_by_prominence(
        -tenacity_difference, prominence=LOAD_DROP_PROMINENCE
    )
    event_rows = [
        {
            "Specimen": specimen_label,
            "Time (s)": round(float(time_s[index]), 2),
            "Strain (%)": round(float(strain_percent[index]), 2),
            "Tenacity Drop (cN/tex)": round(float(-tenacity_difference[index]), 3),
            "Local ΔR/R₀": round(float(relative_resistance[index]), 3),
        }
        for index in drop_peaks
    ]
    return drop_peaks, event_rows
