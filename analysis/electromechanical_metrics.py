"""Electromechanical curve-fit metrics and strain resolution."""

import numpy as np


def fit_metrics(x_strain_fraction, y_relative_resistance):
    """Calculate gauge factor, R², and RMSE over a strain window."""
    if len(x_strain_fraction) < 3 or np.ptp(x_strain_fraction) < 1e-5:
        return np.nan, np.nan, np.nan
    slope, intercept = np.polyfit(x_strain_fraction, y_relative_resistance, 1)
    predicted = slope * x_strain_fraction + intercept
    residuals = y_relative_resistance - predicted
    rmse = np.sqrt(np.mean(residuals**2))
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y_relative_resistance - np.mean(y_relative_resistance)) ** 2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0
    return slope, r2, rmse


def calculate_strain_resolution(
    relative_noise: float, compaction_gauge_factor: float, rising_gauge_factor: float
) -> float:
    """Calculate strain resolution from baseline noise and the dominant gauge factor."""
    dominant_gauge_factor = (
        rising_gauge_factor
        if not np.isnan(rising_gauge_factor)
        and abs(rising_gauge_factor) >= abs(compaction_gauge_factor or 0)
        else compaction_gauge_factor
    )
    return (
        (relative_noise / abs(dominant_gauge_factor)) * 100.0
        if dominant_gauge_factor and abs(dominant_gauge_factor) > 1e-6
        else np.nan
    )
