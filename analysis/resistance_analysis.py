"""Resistance baseline and normalized resistance calculations."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ResistanceBaseline:
    resistance_0: float
    standard_deviation: float
    relative_noise: float


def calculate_resistance_baseline(
    electrical_time: np.ndarray, resistance: np.ndarray, baseline_window_s: float, offset: float
) -> ResistanceBaseline:
    """Calculate R0 and baseline noise using the initial unloaded time window."""
    static_mask = electrical_time <= max(baseline_window_s, offset)
    if np.sum(static_mask) >= 2:
        resistance_0 = float(np.mean(resistance[static_mask]))
        standard_deviation = float(np.std(resistance[static_mask], ddof=1))
    else:
        resistance_0 = float(resistance[0])
        standard_deviation = 0.0
    relative_noise = (
        standard_deviation / resistance_0 if resistance_0 > 0 else 0.0
    )
    return ResistanceBaseline(
        resistance_0=resistance_0,
        standard_deviation=standard_deviation,
        relative_noise=relative_noise,
    )


def calculate_relative_resistance(resistance: np.ndarray, resistance_0: float):
    """Calculate the existing relative resistance (ΔR/R₀) representation."""
    return (resistance - resistance_0) / resistance_0


def calculate_normalized_resistivity(
    resistance: np.ndarray, gauge_cm: float, denier: float
):
    """Normalize resistance by gauge length and denier."""
    return (resistance / gauge_cm) * denier
