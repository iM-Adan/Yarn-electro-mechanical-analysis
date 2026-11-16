"""Header-based routing for Instron and multimeter uploads."""

from typing import BinaryIO


def detect_file_type(file_buf: BinaryIO) -> str:
    """Inspect the first 30 lines of a CSV to identify Instron or DMM exports."""
    file_buf.seek(0)
    head_lines = [
        file_buf.readline().decode("utf-8-sig", errors="ignore")
        for _ in range(30)
    ]
    text = "\n".join(head_lines)
    if (
        "Time measurement" in text
        or "Primary load" in text
        or "Tensile extension" in text
    ):
        return "instron"
    if (
        "Time Stamp" in text
        or "Resistance (2W)" in text
        or "AutoRange" in text
        or "Address,USB" in text
    ):
        return "dmm"
    return "unknown"


def route_uploaded_files(instron_uploads, dmm_uploads):
    """Route uploaded files by headers and return categorized files and routing notes."""
    instron_files = {}
    dmm_files = {}
    notes = []
    instron_uploads = instron_uploads or []
    dmm_uploads = dmm_uploads or []

    for file_buf in instron_uploads + dmm_uploads:
        file_type = detect_file_type(file_buf)
        if file_type == "instron":
            instron_files[file_buf.name] = file_buf
            if file_buf in dmm_uploads:
                notes.append(
                    f"Auto-routed `{file_buf.name}` to **Instron CSVs** based on its headers."
                )
        elif file_type == "dmm":
            dmm_files[file_buf.name] = file_buf
            if file_buf in instron_uploads:
                notes.append(
                    f"Auto-routed `{file_buf.name}` to **Multimeter CSVs** based on its headers."
                )
        elif file_buf in instron_uploads:
            instron_files[file_buf.name] = file_buf
        else:
            dmm_files[file_buf.name] = file_buf

    return instron_files, dmm_files, sorted(set(notes))
