"""Load and validate paired specimen measurement files."""

from typing import BinaryIO

import numpy as np
import pandas as pd

from core.data_validation import validate_instron_frame, validate_multimeter_trace
from parsers.instron_parser import parse_instron
from parsers.multimeter_parser import parse_multimeter


def load_specimen_data(
    instron_file: BinaryIO, multimeter_file: BinaryIO
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Parse and validate a paired Instron and multimeter measurement."""
    instron_frame = parse_instron(instron_file)
    validate_instron_frame(instron_frame)
    time_s, resistance = parse_multimeter(multimeter_file)
    validate_multimeter_trace(time_s, resistance)
    return instron_frame, time_s, resistance
