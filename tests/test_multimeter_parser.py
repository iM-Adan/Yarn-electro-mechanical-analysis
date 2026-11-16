"""Regression tests for multimeter CSV parsing."""

import unittest

import numpy as np

from parsers.multimeter_parser import parse_multimeter
from tests.sample_data import uploaded_file


class MultimeterParserTests(unittest.TestCase):
    def test_metadata_timestamps_and_invalid_measurement_rows(self):
        csv_bytes = (
            b"Keysight metadata\nAddress,USB\n"
            b"Time Stamp(s),Resistance (2W),Records\n"
            b"2026-01-01 00:00:00,10,1\n"
            b"2026-01-01 00:00:01,invalid,2\n"
            b"not-a-time,12,3\n"
            b"2026-01-01 00:00:03,13,4\n"
        )
        time_s, resistance = parse_multimeter(
            uploaded_file("meter.csv", csv_bytes)
        )

        np.testing.assert_array_equal(time_s, [0.0, 3.0])
        np.testing.assert_array_equal(resistance, [10.0, 13.0])

    def test_missing_header_is_reported(self):
        with self.assertRaisesRegex(ValueError, "Could not locate"):
            parse_multimeter(
                uploaded_file("unrecognized.csv", b"one,two\n1,2\n")
            )

    def test_instron_file_is_rejected_by_multimeter_parser(self):
        with self.assertRaisesRegex(ValueError, "Instron"):
            parse_multimeter(
                uploaded_file(
                    "tensile.csv",
                    b"Time measurement,Primary load measurement\n0,1\n",
                )
            )


if __name__ == "__main__":
    unittest.main()
