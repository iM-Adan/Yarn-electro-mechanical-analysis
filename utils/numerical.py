"""Numerical helpers shared by the analysis package."""

import numpy as np


def trapz_compat(y, x):
    """Integrate with the NumPy API available in the active runtime."""
    if hasattr(np, "trapezoid"):
        return np.trapezoid(y, x)
    return np.trapz(y, x)


def find_peaks_by_prominence(values, prominence):
    """Return local-maximum indices whose prominence meets the threshold."""
    peaks = []
    start = 1
    while start < len(values) - 1:
        end = start
        while end + 1 < len(values) and values[end + 1] == values[start]:
            end += 1

        if (
            values[start] > values[start - 1]
            and end < len(values) - 1
            and values[end] > values[end + 1]
        ):
            peak = (start + end) // 2
            left = peak - 1
            left_min = values[left]
            while left > 0 and values[left] <= values[peak]:
                left -= 1
                left_min = min(left_min, values[left])

            right = peak + 1
            right_min = values[right]
            while right < len(values) - 1 and values[right] <= values[peak]:
                right += 1
                right_min = min(right_min, values[right])

            if values[peak] - max(left_min, right_min) >= prominence:
                peaks.append(peak)
        start = end + 1

    return np.asarray(peaks, dtype=int)
