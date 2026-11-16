"""Parser and column inference for arbitrary plotting CSVs."""

import re
from io import BytesIO, StringIO

import numpy as np
import pandas as pd

from core.file_router import detect_file_type
from parsers.instron_parser import parse_instron


def parse_generic_csv(file_bytes: bytes, file_name: str) -> tuple[pd.DataFrame, tuple[str, ...]]:
    """Read generic delimited CSV data and preserve legacy instrument-header handling."""
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = file_bytes.decode("cp1252")

    file_buffer = BytesIO(file_bytes)
    file_buffer.name = file_name
    file_type = detect_file_type(file_buffer)
    if file_type == "instron":
        frame = parse_instron(file_buffer)
    elif file_type == "dmm":
        header_idx = next(
            (
                index
                for index, line in enumerate(text.splitlines()[:40])
                if "Time Stamp" in line
                or ("Resistance" in line and "Records" in line)
            ),
            None,
        )
        if header_idx is None:
            raise ValueError(f"Could not locate the data header in '{file_name}'.")
        frame = pd.read_csv(
            StringIO(text),
            skiprows=header_idx,
            sep=None,
            engine="python",
            skip_blank_lines=False,
        )
    else:
        frame = pd.read_csv(
            StringIO(text),
            sep=None,
            engine="python",
            skip_blank_lines=False,
        )

    frame.columns = [
        str(column).strip() or f"Column {index + 1}"
        for index, column in enumerate(frame.columns)
    ]
    if not len(frame.columns):
        raise ValueError("No column headers were found in this CSV.")
    numeric_columns = tuple(
        column
        for column in frame.columns
        if pd.to_numeric(frame[column], errors="coerce").notna().any()
    )
    return frame, numeric_columns


def infer_plot_column_kind(series: pd.Series, column_name: str = "") -> str:
    """Identify numeric and date-like values while keeping other values categorical."""
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    non_missing = int(series.notna().sum())
    if not non_missing:
        return "category"
    threshold = max(1, int(np.ceil(non_missing * 0.8)))
    if pd.to_numeric(series, errors="coerce").notna().sum() >= threshold:
        return "numeric"
    date_hints = ("time", "date", "stamp", "timestamp")
    date_patterns = (
        r"^\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?(?:[T ].*)?$",
        r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}(?:[T ].*)?$",
        r"^\d{1,2}[-/][A-Za-z]{3,9}[-/]\d{2,4}",
        r"^[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}",
    )
    date_candidate = any(hint in column_name.lower() for hint in date_hints) or any(
        re.match(pattern, str(value).strip())
        for value in series.dropna().head(5)
        for pattern in date_patterns
    )
    if not date_candidate:
        return "category"
    if pd.to_datetime(series, errors="coerce", utc=True).notna().sum() >= threshold:
        return "datetime"
    return "category"


def convert_plot_column(series: pd.Series, kind: str) -> pd.Series:
    """Convert inferred X/Y values using the same rules as the plot workspace."""
    if kind == "numeric":
        return pd.to_numeric(series, errors="coerce")
    if kind == "datetime":
        return pd.to_datetime(series, errors="coerce", utc=True).dt.tz_convert(None)
    return series
