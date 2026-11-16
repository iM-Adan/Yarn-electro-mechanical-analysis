"""Pure scientific analysis for a paired tensile/electrical specimen."""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from analysis.damage_detection import detect_load_drop_events
from analysis.electromechanical_metrics import (
    calculate_strain_resolution,
    fit_metrics,
)
from analysis.hysteresis import calculate_recovery_and_hysteresis
from analysis.mechanical_metrics import (
    calculate_tenacity,
    calculate_work_of_rupture,
)
from analysis.resistance_analysis import (
    calculate_normalized_resistivity,
    calculate_relative_resistance,
    calculate_resistance_baseline,
)
from analysis.strain_analysis import calculate_strain, detect_turning_strain
from analysis.synchronization import synchronize_traces
from config.constants import (
    INSTRON_LOAD_COLUMN,
    INSTRON_TIME_COLUMN,
)


@dataclass
class SpecimenAnalysis:
    """Calculated specimen output, plot-ready arrays, and user-facing warnings."""

    label: str
    summary: dict[str, Any] | None
    events: list[dict[str, Any]]
    warnings: list[str]
    time_plot: dict[str, Any]
    resistance_time_plot: dict[str, Any] | None
    analysis_plot: dict[str, Any] | None


def analyze_specimen(
    instron_frame: pd.DataFrame,
    electrical_time: np.ndarray,
    resistance: np.ndarray,
    configuration: dict[str, Any],
    baseline_window_s: float,
    pre_break_trim_pct: float,
) -> SpecimenAnalysis:
    """Calculate all original per-specimen metrics without any Streamlit dependency."""
    label = configuration["label"]
    tex = configuration["tex"]
    gauge_length_mm = configuration["gauge_mm"]
    denier = tex * 9.0
    gauge_cm = gauge_length_mm / 10.0

    mechanical_time = instron_frame[INSTRON_TIME_COLUMN].values
    load = instron_frame[INSTRON_LOAD_COLUMN].values
    extension_mm = instron_frame["Tensile extension (mm)"].values
    strain_fraction, strain_percent = calculate_strain(
        instron_frame, gauge_length_mm
    )
    tenacity = calculate_tenacity(load, tex)

    synchronized = synchronize_traces(
        mechanical_time,
        load,
        electrical_time,
        resistance,
        configuration["offset"],
        configuration["auto_sync"],
    )
    baseline = calculate_resistance_baseline(
        electrical_time, resistance, baseline_window_s, synchronized.offset
    )
    normalized_r0 = (baseline.resistance_0 / gauge_cm) * denier
    synchronized_resistance = synchronized.synchronized_resistance

    valid_mask = ~np.isnan(synchronized_resistance)
    cutoff_index = (
        int(synchronized.peak_load_index * (1.0 - pre_break_trim_pct))
        if pre_break_trim_pct > 0
        else synchronized.peak_load_index
    )
    active_indices = np.arange(len(mechanical_time)) <= cutoff_index
    active_mask = valid_mask & active_indices

    warnings = []
    if synchronized.pull_onset_time is not None:
        time_origin = synchronized.pull_onset_time
    else:
        time_origin = float(mechanical_time[0])
        warnings.append(
            f"No positive Instron load found for {label}; using specimen start as the time origin."
        )

    load_window = (
        (mechanical_time >= time_origin)
        & (np.arange(len(mechanical_time)) <= cutoff_index)
    )
    pull_onset_electrical_time = time_origin + synchronized.offset
    analysis_end_electrical_time = (
        mechanical_time[cutoff_index] + synchronized.offset
    )
    trace_window = (
        (electrical_time >= pull_onset_electrical_time)
        & (electrical_time <= analysis_end_electrical_time)
    )
    if np.any(trace_window):
        trace_order = np.argsort(electrical_time[trace_window])
        specimen_resistance_time = electrical_time[trace_window][trace_order]
        specimen_resistance = resistance[trace_window][trace_order]
    else:
        specimen_resistance_time = np.asarray([])
        specimen_resistance = np.asarray([])
        warnings.append(
            f"No DMM trace samples fall within the analysis window for {label}."
        )

    time_axis_label = (
        "Time Since Pull Onset (s)"
        if synchronized.pull_onset_time is not None
        else "Time Since Specimen Start (s)"
    )
    time_plot = {
        "label": label,
        "time_axis_label": time_axis_label,
        "load_time": mechanical_time[load_window] - time_origin,
        "load": load[load_window],
        "resistance_time": specimen_resistance_time,
        "resistance": specimen_resistance,
    }

    if np.sum(active_mask) < 5:
        warnings.append(
            f"Not enough overlapping time data for {label}. Check your Sync Offset."
        )
        return SpecimenAnalysis(
            label=label,
            summary=None,
            events=[],
            warnings=warnings,
            time_plot=time_plot,
            resistance_time_plot=None,
            analysis_plot=None,
        )

    active_time = mechanical_time[active_mask]
    active_strain_percent = strain_percent[active_mask]
    active_strain_fraction = strain_fraction[active_mask]
    active_load = load[active_mask]
    active_extension = extension_mm[active_mask]
    active_tenacity = tenacity[active_mask]
    active_resistance = synchronized_resistance[active_mask]

    relative_resistance = calculate_relative_resistance(
        active_resistance, baseline.resistance_0
    )
    normalized_resistance = calculate_normalized_resistivity(
        active_resistance, gauge_cm, denier
    )

    (
        turning_index,
        turning_strain_percent,
        turning_relative_resistance,
    ) = detect_turning_strain(active_strain_percent, relative_resistance)
    compaction_gf, compaction_r2, _ = fit_metrics(
        active_strain_fraction[: turning_index + 1],
        relative_resistance[: turning_index + 1],
    )
    rising_gf, rising_r2, _ = fit_metrics(
        active_strain_fraction[turning_index:], relative_resistance[turning_index:]
    )
    strain_resolution_percent = calculate_strain_resolution(
        baseline.relative_noise, compaction_gf, rising_gf
    )

    specific_energy_j_g, _ = calculate_work_of_rupture(
        active_load, active_extension, tex, gauge_length_mm
    )
    recovery_status = calculate_recovery_and_hysteresis(
        strain_percent,
        synchronized_resistance,
        valid_mask,
        baseline.resistance_0,
    )
    drop_peaks, event_rows = detect_load_drop_events(
        active_time,
        active_strain_percent,
        active_tenacity,
        relative_resistance,
        label,
    )

    if synchronized.pull_onset_time is not None:
        if np.any(trace_window):
            resistance_time_plot = {
                "time": specimen_resistance_time - pull_onset_electrical_time,
                "resistance": specimen_resistance,
                "label": label,
            }
        else:
            resistance_time_plot = None
            warnings.append(
                f"Cannot plot resistance since pull onset for {label}: no DMM trace samples in the analysis window."
            )
    else:
        resistance_time_plot = None
        warnings.append(
            f"Cannot plot resistance since pull onset for {label}: Instron load never exceeds zero."
        )

    summary = {
        "Specimen": label,
        "R₀ (Ω)": round(baseline.resistance_0, 2),
        "Norm. R₀ (kΩ·den/cm)": round(normalized_r0 / 1000.0, 2),
        "Baseline Noise (Ω)": round(baseline.standard_deviation, 4),
        "Turning Strain (%)": round(turning_strain_percent, 2),
        "Min ΔR/R₀ at Turn": round(turning_relative_resistance, 3),
        "Compaction GF (0→Turn)": (
            round(compaction_gf, 2) if not np.isnan(compaction_gf) else None
        ),
        "Compaction R²": (
            round(compaction_r2, 3) if not np.isnan(compaction_r2) else None
        ),
        "Rising GF (Turn→Break)": (
            round(rising_gf, 2) if not np.isnan(rising_gf) else None
        ),
        "Rising R²": round(rising_r2, 3) if not np.isnan(rising_r2) else None,
        "Strain Resolution (%)": (
            round(strain_resolution_percent, 4)
            if not np.isnan(strain_resolution_percent)
            else None
        ),
        "Strain at Break (%)": round(float(active_strain_percent[-1]), 2),
        "Tenacity (cN/tex)": round(float(np.max(active_tenacity)), 2),
        "Work of Rupture (J/g)": round(specific_energy_j_g, 2),
        "Recovery / Hysteresis": recovery_status,
    }
    analysis_plot = {
        "time": active_time,
        "strain_percent": active_strain_percent,
        "relative_resistance": relative_resistance,
        "turning_strain_percent": turning_strain_percent,
        "turning_relative_resistance": turning_relative_resistance,
        "normalized_resistance": normalized_resistance,
        "tenacity": active_tenacity,
        "drop_peaks": drop_peaks,
    }
    return SpecimenAnalysis(
        label=label,
        summary=summary,
        events=event_rows,
        warnings=warnings,
        time_plot=time_plot,
        resistance_time_plot=resistance_time_plot,
        analysis_plot=analysis_plot,
    )
