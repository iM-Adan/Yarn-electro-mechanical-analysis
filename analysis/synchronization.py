"""Time alignment between Instron and multimeter measurements."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SynchronizedTrace:
    offset: float
    peak_load_index: int
    break_time: float
    pull_onset_time: float | None
    aligned_mechanical_time: np.ndarray
    synchronized_resistance: np.ndarray


def synchronize_traces(
    mechanical_time: np.ndarray,
    load: np.ndarray,
    electrical_time: np.ndarray,
    resistance: np.ndarray,
    offset: float,
    auto_sync: bool,
) -> SynchronizedTrace:
    """Apply the existing offset or align peak load with the steepest resistance jump."""
    peak_load_index = int(np.argmax(load))
    break_time = mechanical_time[peak_load_index]
    positive_load_indices = np.flatnonzero(load > 0)
    pull_onset_time = (
        float(mechanical_time[positive_load_indices[0]])
        if len(positive_load_indices)
        else None
    )
    if auto_sync:
        resistance_derivative = np.gradient(resistance, electrical_time)
        spike_index = int(np.argmax(resistance_derivative))
        offset = float(electrical_time[spike_index] - break_time)

    aligned_mechanical_time = mechanical_time + offset
    order = np.argsort(electrical_time)
    synchronized_resistance = np.interp(
        aligned_mechanical_time,
        electrical_time[order],
        resistance[order],
        left=np.nan,
        right=np.nan,
    )
    return SynchronizedTrace(
        offset=offset,
        peak_load_index=peak_load_index,
        break_time=break_time,
        pull_onset_time=pull_onset_time,
        aligned_mechanical_time=aligned_mechanical_time,
        synchronized_resistance=synchronized_resistance,
    )
