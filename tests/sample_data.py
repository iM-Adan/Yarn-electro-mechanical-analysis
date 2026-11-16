"""Representative in-memory CSV samples for parser and application tests."""

from datetime import datetime, timedelta


BASELINE_LOADS = [0, 5, 10, 15, 20, 25, 30, 35, 40, 20, 10]
BASELINE_RESISTANCE = [100, 100, 100, 98, 96, 98, 105, 120, 150, 180, 210]

BASELINE_SUMMARY = {
    "Specimen": "Sample 1",
    "R₀ (Ω)": 100.0,
    "Norm. R₀ (kΩ·den/cm)": 26.56,
    "Baseline Noise (Ω)": 0.0,
    "Turning Strain (%)": 2.0,
    "Min ΔR/R₀ at Turn": -0.04,
    "Compaction GF (0→Turn)": -2.0,
    "Compaction R²": 0.781,
    "Rising GF (Turn→Break)": 26.0,
    "Rising R²": 0.848,
    "Strain Resolution (%)": 0.0,
    "Strain at Break (%)": 4.0,
    "Tenacity (cN/tex)": 7.53,
    "Work of Rupture (J/g)": 1.67,
    "Recovery / Hysteresis": "Monotonic to Break (No Unload)",
}


def instron_csv_bytes(loads=BASELINE_LOADS, include_metadata=True) -> bytes:
    """Create an Instron-format CSV with metadata and a units row."""
    lines = []
    if include_metadata:
        lines.append("Instron export metadata")
    lines.extend(
        [
            "Time measurement,Primary load measurement,Tensile extension,Composite strain",
            "(s),(N),(mm),(strain)",
        ]
    )
    lines.extend(
        f"{index},{load},{index},{index * 0.005}"
        for index, load in enumerate(loads)
    )
    return "\n".join(lines).encode("utf-8")


def multimeter_csv_bytes(
    resistance=BASELINE_RESISTANCE,
    invalid_rows=False,
    include_metadata=True,
) -> bytes:
    """Create a timestamped Keysight-style multimeter CSV."""
    lines = []
    if include_metadata:
        lines.extend(["Keysight export metadata", "Address,USB"])
    lines.append("Time Stamp(s),Resistance (2W),AutoRange,Records")
    start = datetime(2026, 1, 1)
    for index, value in enumerate(resistance):
        measurement = value if not (invalid_rows and index == 1) else "overload"
        timestamp = (start + timedelta(seconds=index)).isoformat(sep=" ")
        if invalid_rows and index == 2:
            timestamp = "not-a-timestamp"
        lines.append(f"{timestamp},{measurement},OFF,{index + 1}")
    return "\n".join(lines).encode("utf-8")


def uploaded_file(filename: str, data: bytes):
    """Return a named in-memory upload buffer."""
    from io import BytesIO

    file_buffer = BytesIO(data)
    file_buffer.name = filename
    return file_buffer
