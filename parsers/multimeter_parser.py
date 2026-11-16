"""Parser for timestamped Keysight/Agilent multimeter CSV exports."""

from typing import BinaryIO

import numpy as np
import pandas as pd

from core.file_router import detect_file_type
from core.data_validation import validate_multimeter_trace


def parse_multimeter(file_buf: BinaryIO) -> tuple[np.ndarray, np.ndarray]:
    """Locate time and resistance columns and return elapsed seconds and resistance."""
    file_type = detect_file_type(file_buf)
    if file_type == "instron":
        raise ValueError(
            f"'{file_buf.name}' is an Instron tensile file, not a Multimeter file. "
            "Please select a Multimeter CSV (e.g., Trace 1) for the DMM input."
        )

    file_buf.seek(0)
    lines = [
        line.decode("utf-8-sig", errors="ignore")
        for line in file_buf.readlines()
    ]
    header_idx = None
    for index, line in enumerate(lines[:40]):
        if "Time Stamp" in line or ("Resistance" in line and "Records" in line):
            header_idx = index
            break

    if header_idx is None:
        raise ValueError(
            f"Could not locate 'Time Stamp(s)' or 'Resistance' header in '{file_buf.name}'."
        )

    file_buf.seek(0)
    frame = pd.read_csv(file_buf, skiprows=header_idx)
    time_columns = [column for column in frame.columns if "Time" in column]
    resistance_columns = [
        column for column in frame.columns if "Resistance" in column
    ]
    if not time_columns or not resistance_columns:
        raise ValueError(f"Required Time/Resistance columns missing in '{file_buf.name}'.")

    time_column, resistance_column = time_columns[0], resistance_columns[0]
    frame[time_column] = pd.to_datetime(frame[time_column], errors="coerce")
    frame[resistance_column] = pd.to_numeric(
        frame[resistance_column], errors="coerce"
    )
    frame = frame.dropna(subset=[time_column, resistance_column]).reset_index(drop=True)

    t0 = frame[time_column].iloc[0]
    time_s = (frame[time_column] - t0).dt.total_seconds().to_numpy()
    resistance = frame[resistance_column].to_numpy()
    validate_multimeter_trace(time_s, resistance)
    return time_s, resistance
