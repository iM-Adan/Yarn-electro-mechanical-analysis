"""Parser for Instron tensile-test CSV exports."""

from typing import BinaryIO

import pandas as pd

from core.file_router import detect_file_type
from core.preprocessing import preprocess_instron_frame


def parse_instron(file_buf: BinaryIO) -> pd.DataFrame:
    """Find the Instron table, skip metadata and its optional units row."""
    file_type = detect_file_type(file_buf)
    if file_type == "dmm":
        raise ValueError(
            f"'{file_buf.name}' is a Multimeter (DMM) file, not an Instron file. "
            "Please select an Instron CSV (e.g., Specimen_RawData) for the Instron input."
        )

    file_buf.seek(0)
    lines = [
        line.decode("utf-8-sig", errors="ignore")
        for line in file_buf.readlines()
    ]
    header_idx = 0
    for index, line in enumerate(lines[:40]):
        if (
            "Time measurement" in line
            or "Primary load" in line
            or "Extension" in line
        ):
            header_idx = index
            break

    skip_rows = list(range(header_idx))
    if header_idx + 1 < len(lines):
        next_line = lines[header_idx + 1]
        if "(s)" in next_line or "(mm)" in next_line or "(N)" in next_line:
            skip_rows.append(header_idx + 1)

    file_buf.seek(0)
    frame = pd.read_csv(file_buf, skiprows=skip_rows)
    return preprocess_instron_frame(frame)
