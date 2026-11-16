"""Regression tests for specimen trace synchronization."""

import unittest

import numpy as np

from analysis.synchronization import synchronize_traces


class SynchronizationTests(unittest.TestCase):
    def test_manual_offset_preserves_interpolation_overlap(self):
        result = synchronize_traces(
            mechanical_time=np.asarray([0.0, 1.0, 2.0, 3.0]),
            load=np.asarray([0.0, 2.0, 5.0, 3.0]),
            electrical_time=np.asarray([0.0, 1.0, 2.0]),
            resistance=np.asarray([10.0, 20.0, 30.0]),
            offset=0.0,
            auto_sync=False,
        )

        self.assertEqual(result.offset, 0.0)
        self.assertEqual(result.peak_load_index, 2)
        self.assertEqual(result.pull_onset_time, 1.0)
        np.testing.assert_allclose(
            result.synchronized_resistance[:3], [10.0, 20.0, 30.0]
        )
        self.assertTrue(np.isnan(result.synchronized_resistance[3]))

    def test_auto_sync_aligns_peak_load_with_steepest_rise(self):
        result = synchronize_traces(
            mechanical_time=np.asarray([0.0, 1.0, 2.0, 3.0]),
            load=np.asarray([0.0, 1.0, 5.0, 2.0]),
            electrical_time=np.asarray([0.0, 1.0, 2.0, 3.0, 4.0]),
            resistance=np.asarray([0.0, 0.0, 1.0, 2.0, 10.0]),
            offset=0.0,
            auto_sync=True,
        )

        self.assertEqual(result.offset, 2.0)
        np.testing.assert_allclose(
            result.synchronized_resistance[:3], [1.0, 2.0, 10.0]
        )
        self.assertTrue(np.isnan(result.synchronized_resistance[3]))


if __name__ == "__main__":
    unittest.main()
