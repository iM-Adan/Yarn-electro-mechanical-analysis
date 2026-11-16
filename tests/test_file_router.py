"""Regression tests for header-based instrument routing."""

import unittest

from core.file_router import route_uploaded_files
from tests.sample_data import (
    instron_csv_bytes,
    multimeter_csv_bytes,
    uploaded_file,
)


class FileRouterTests(unittest.TestCase):
    def test_instruments_are_routed_by_header_not_uploader(self):
        instron_files_uploaded = [
            uploaded_file("tensile_one.csv", instron_csv_bytes()),
            uploaded_file("tensile_two.csv", instron_csv_bytes()),
        ]
        multimeter_files_uploaded = [
            uploaded_file("meter_one.csv", multimeter_csv_bytes()),
            uploaded_file("meter_two.csv", multimeter_csv_bytes()),
        ]

        instron_files, multimeter_files, notes = route_uploaded_files(
            multimeter_files_uploaded, instron_files_uploaded
        )

        self.assertEqual(
            list(instron_files), ["tensile_one.csv", "tensile_two.csv"]
        )
        self.assertEqual(
            list(multimeter_files), ["meter_one.csv", "meter_two.csv"]
        )
        self.assertEqual(len(notes), 4)
        self.assertTrue(
            any("Auto-routed `meter_one.csv` to **Multimeter CSVs**" in note
                for note in notes)
        )


if __name__ == "__main__":
    unittest.main()
