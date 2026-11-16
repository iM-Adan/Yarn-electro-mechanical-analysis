"""Regression tests for Instron CSV parsing."""

import unittest

import pandas as pd

from parsers.instron_parser import parse_instron
from tests.sample_data import instron_csv_bytes, uploaded_file


class InstronParserTests(unittest.TestCase):
    def test_metadata_units_row_and_column_normalization(self):
        frame = parse_instron(
            uploaded_file("tensile.csv", instron_csv_bytes(loads=[0, 5, 10]))
        )

        self.assertEqual(
            list(frame.columns),
            [
                "Time (s)",
                "Primary load (N)",
                "Tensile extension (mm)",
                "Composite strain",
            ],
        )
        self.assertEqual(frame["Time (s)"].tolist(), [0, 1, 2])
        self.assertEqual(frame["Primary load (N)"].tolist(), [0, 5, 10])
        self.assertTrue(pd.api.types.is_numeric_dtype(frame["Tensile extension (mm)"]))

    def test_invalid_time_rows_are_dropped(self):
        csv_bytes = (
            b"Metadata\nTime measurement,Primary load measurement,Tensile extension\n"
            b"(s),(N),(mm)\n0,1,2\nbad,3,4\n1,5,6\n"
        )
        frame = parse_instron(uploaded_file("invalid-time.csv", csv_bytes))
        self.assertEqual(frame["Time (s)"].tolist(), [0, 1])

    def test_dmm_file_is_rejected_by_instron_parser(self):
        with self.assertRaisesRegex(ValueError, "Multimeter"):
            parse_instron(
                uploaded_file(
                    "meter.csv",
                    b"Time Stamp(s),Resistance (2W)\n2026-01-01,10\n",
                )
            )


if __name__ == "__main__":
    unittest.main()
