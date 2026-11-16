"""CSV serialization for analysis results."""

import pandas as pd


def dataframe_to_csv_bytes(frame: pd.DataFrame) -> bytes:
    """Serialize a summary dataframe using the existing UTF-8 CSV format."""
    return frame.to_csv(index=False).encode("utf-8")
