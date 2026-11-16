"""Validation helpers for parsed measurement data."""

import numpy as np
import pandas as pd

from config.constants import (
    INSTRON_EXTENSION_COLUMN,
    INSTRON_LOAD_COLUMN,
    INSTRON_TIME_COLUMN,
)


def validate_instron_frame(frame: pd.DataFrame) -> None:
    """Ensure the parsed tensile trace has the columns and samples used by analysis."""
    required = (
        INSTRON_TIME_COLUMN,
        INSTRON_LOAD_COLUMN,
        INSTRON_EXTENSION_COLUMN,
    )
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Instron CSV is missing required columns: {', '.join(missing)}.")
    if frame.empty:
        raise ValueError("Instron CSV contains no rows with a valid time value.")


def validate_multimeter_trace(time_s: np.ndarray, resistance: np.ndarray) -> None:
    """Ensure a multimeter trace has paired numeric timestamps and measurements."""
    if len(time_s) != len(resistance):
        raise ValueError("Multimeter timestamps and resistance values have different lengths.")
    if not len(time_s):
        raise ValueError("Multimeter CSV contains no valid time/resistance measurements.")
