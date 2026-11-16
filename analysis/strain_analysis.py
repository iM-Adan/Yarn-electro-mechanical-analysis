"""Strain conversion and turning-strain calculations."""

import numpy as np
import pandas as pd

from config.constants import INSTRON_EXTENSION_COLUMN, INSTRON_STRAIN_COLUMN


def calculate_strain(
    instron_frame: pd.DataFrame, gauge_length_mm: float
) -> tuple[np.ndarray, np.ndarray]:
    """Use positive composite strain when available, otherwise extension/gauge length."""
    extension_mm = instron_frame[INSTRON_EXTENSION_COLUMN].values
    if (
        INSTRON_STRAIN_COLUMN in instron_frame.columns
        and instron_frame[INSTRON_STRAIN_COLUMN].max() > 0
    ):
        strain_fraction = instron_frame[INSTRON_STRAIN_COLUMN].values
    else:
        strain_fraction = extension_mm / gauge_length_mm
    return strain_fraction, strain_fraction * 100.0


def detect_turning_strain(
    strain_percent: np.ndarray, relative_resistance: np.ndarray
) -> tuple[int, float, float]:
    """Find the minimum relative resistance and corresponding strain."""
    minimum_index = int(np.argmin(relative_resistance))
    return (
        minimum_index,
        float(strain_percent[minimum_index]),
        float(relative_resistance[minimum_index]),
    )
