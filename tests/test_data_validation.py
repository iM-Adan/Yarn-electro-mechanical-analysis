"""Regression tests for parsed-data validation."""

import unittest

import numpy as np
import pandas as pd

from core.data_validation import (
    validate_instron_frame,
    validate_multimeter_trace,
)


class DataValidationTests(unittest.TestCase):
    def test_valid_instron_frame(self):
        frame = pd.DataFrame(
            {
                "Time (s)": [0.0],
                "Primary load (N)": [1.0],
                "Tensile extension (mm)": [2.0],
            }
        )
        validate_instron_frame(frame)

    def test_missing_instron_columns_are_reported(self):
        with self.assertRaisesRegex(ValueError, "Primary load"):
            validate_instron_frame(pd.DataFrame({"Time (s)": [0.0]}))

    def test_empty_instron_frame_is_reported(self):
        frame = pd.DataFrame(
            {
                "Time (s)": pd.Series(dtype=float),
                "Primary load (N)": pd.Series(dtype=float),
                "Tensile extension (mm)": pd.Series(dtype=float),
            }
        )
        with self.assertRaisesRegex(ValueError, "no rows"):
            validate_instron_frame(frame)

    def test_unpaired_multimeter_arrays_are_reported(self):
        with self.assertRaisesRegex(ValueError, "different lengths"):
            validate_multimeter_trace(np.asarray([0.0]), np.asarray([1.0, 2.0]))

    def test_empty_multimeter_trace_is_reported(self):
        with self.assertRaisesRegex(ValueError, "no valid"):
            validate_multimeter_trace(np.asarray([]), np.asarray([]))


if __name__ == "__main__":
    unittest.main()
