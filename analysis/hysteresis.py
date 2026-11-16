"""Cyclic recovery and hysteresis calculations."""

import numpy as np

from utils.numerical import trapz_compat


def calculate_recovery_and_hysteresis(
    strain_percent: np.ndarray,
    synchronized_resistance: np.ndarray,
    valid_mask: np.ndarray,
    resistance_0: float,
) -> str:
    """Return the existing recovery/hysteresis description when unloading is present."""
    maximum_strain_index = int(np.argmax(strain_percent[valid_mask]))
    strain_valid = strain_percent[valid_mask]
    relative_resistance_valid = (
        synchronized_resistance[valid_mask] - resistance_0
    ) / resistance_0
    if (
        maximum_strain_index < len(strain_valid) - 10
        and strain_valid[-1] < 0.5 * strain_valid[maximum_strain_index]
    ):
        recovery_ratio = float(synchronized_resistance[valid_mask][-1] / resistance_0)
        loop_area = float(
            abs(
                trapz_compat(
                    relative_resistance_valid[: maximum_strain_index + 1],
                    strain_valid[: maximum_strain_index + 1],
                )
                + trapz_compat(
                    relative_resistance_valid[maximum_strain_index:],
                    strain_valid[maximum_strain_index:],
                )
            )
        )
        return f"R_end/R₀ = {recovery_ratio:.2f} (Hyst: {loop_area:.2f})"
    return "Monotonic to Break (No Unload)"
