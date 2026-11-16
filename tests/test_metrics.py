"""Regression tests for scientific specimen metrics."""

import unittest

import numpy as np
import pandas as pd

from analysis.electromechanical_metrics import (
    calculate_strain_resolution,
    fit_metrics,
)
from analysis.mechanical_metrics import (
    calculate_tenacity,
    calculate_work_of_rupture,
)
from analysis.specimen_comparison import analyze_specimen
from core.data_loader import load_specimen_data
from tests.sample_data import (
    BASELINE_SUMMARY,
    instron_csv_bytes,
    multimeter_csv_bytes,
    uploaded_file,
)


class MetricTests(unittest.TestCase):
    def test_linear_fit_metrics(self):
        x = np.asarray([0.0, 0.1, 0.2, 0.3])
        y = 2.0 * x + 1.0
        slope, r2, rmse = fit_metrics(x, y)

        self.assertAlmostEqual(slope, 2.0)
        self.assertAlmostEqual(r2, 1.0)
        self.assertAlmostEqual(rmse, 0.0)

    def test_work_and_tenacity(self):
        tenacity = calculate_tenacity(
            np.asarray([0.0, 10.0, 20.0]), linear_density_tex=100.0
        )
        np.testing.assert_allclose(tenacity, [0.0, 10.0, 20.0])
        specific_energy, integrated_work = calculate_work_of_rupture(
            np.asarray([0.0, 10.0, 20.0]),
            np.asarray([0.0, 1.0, 2.0]),
            linear_density_tex=180.0,
            gauge_length_mm=180.0,
        )
        self.assertAlmostEqual(integrated_work, 20.0)
        self.assertAlmostEqual(specific_energy, 20.0 / 1000.0 / 0.0324)

    def test_strain_resolution_uses_dominant_gauge_factor(self):
        resolution = calculate_strain_resolution(0.02, -2.0, 26.0)
        self.assertAlmostEqual(resolution, (0.02 / 26.0) * 100.0)

    def test_specimen_summary_matches_pre_refactor_baseline(self):
        instron_frame, electrical_time, resistance = load_specimen_data(
            uploaded_file("baseline_instron.csv", instron_csv_bytes()),
            uploaded_file("baseline_dmm.csv", multimeter_csv_bytes()),
        )
        result = analyze_specimen(
            instron_frame,
            electrical_time,
            resistance,
            {
                "label": "Sample 1",
                "tex": 531.11,
                "gauge_mm": 180.0,
                "offset": 0.0,
                "auto_sync": False,
            },
            baseline_window_s=2.0,
            pre_break_trim_pct=0.0,
        )
        self.assertEqual(result.summary, BASELINE_SUMMARY)
        self.assertEqual(result.events, [])
        self.assertEqual(result.warnings, [])
        self.assertEqual(len(result.analysis_plot["time"]), 9)

    def test_analysis_uses_extension_when_composite_strain_is_not_positive(self):
        frame = pd.DataFrame(
            {
                "Time (s)": [0.0, 1.0, 2.0],
                "Primary load (N)": [0.0, 1.0, 2.0],
                "Tensile extension (mm)": [0.0, 1.0, 2.0],
                "Composite strain": [0.0, 0.0, 0.0],
            }
        )
        from analysis.strain_analysis import calculate_strain

        strain_fraction, strain_percent = calculate_strain(frame, 100.0)
        np.testing.assert_allclose(strain_fraction, [0.0, 0.01, 0.02])
        np.testing.assert_allclose(strain_percent, [0.0, 1.0, 2.0])


if __name__ == "__main__":
    unittest.main()
