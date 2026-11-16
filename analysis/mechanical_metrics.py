"""Tensile and mechanical energy metrics."""

import numpy as np

from utils.numerical import trapz_compat


def calculate_tenacity(load_n: np.ndarray, linear_density_tex: float) -> np.ndarray:
    """Convert load in newtons to tenacity in centinewtons per tex."""
    return (load_n * 100.0) / linear_density_tex


def calculate_work_of_rupture(
    load_n: np.ndarray,
    extension_mm: np.ndarray,
    linear_density_tex: float,
    gauge_length_mm: float,
) -> tuple[float, float]:
    """Return work in J/g and the integrated load-extension work in N·mm."""
    work_mj = float(trapz_compat(load_n, extension_mm))
    specimen_mass_g = (linear_density_tex * (gauge_length_mm / 1000.0)) / 1000.0
    specific_energy_j_g = (
        (work_mj / 1000.0) / specimen_mass_g
        if specimen_mass_g > 0
        else np.nan
    )
    return specific_energy_j_g, work_mj
