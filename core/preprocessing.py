"""Data-cleaning operations shared by CSV parsers."""

import pandas as pd


def preprocess_instron_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize Instron columns, coerce numeric values, and retain valid time rows."""
    column_map = {}
    for column in frame.columns:
        normalized = column.strip()
        if normalized.startswith("Time measurement"):
            column_map[column] = "Time (s)"
        elif normalized.startswith("Primary load measurement"):
            column_map[column] = "Primary load (N)"
        elif normalized.startswith("Tensile extension"):
            column_map[column] = "Tensile extension (mm)"
    frame = frame.rename(columns=column_map)
    for column in frame.columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=[frame.columns[0]]).reset_index(drop=True)
    return frame
