# Electromechanical Yarn Sensor Analysis Suite

A Streamlit application for synchronizing tensile-test data with multimeter resistance measurements and comparing electromechanical yarn sensor behavior across specimens.

## Features

- Upload multiple Instron and multimeter CSV files and configure up to 50 specimens.
- Identify and route uploaded files using their headers.
- Set specimen label, linear density, gauge length, and time offset; optionally auto-align the peak load with the steepest resistance increase.
- Review relative resistance versus strain, normalized resistivity versus strain, batch resistance versus time since pull onset, and per-specimen load/resistance overlay plots.
- Inspect sensor and mechanical metrics, including turning strain, gauge factor, linearity, strain resolution, work of rupture, and recovery/hysteresis where applicable.
- Download the comparison summary as a CSV.

## Demo video

<video controls width="100%" preload="metadata">
  <source src="https://raw.githubusercontent.com/iM-Adan/Yarn-electro-mechanical-analysis/main/demo/demo.mp4" type="video/mp4">
  Your Markdown viewer does not support embedded video. [Open the full demo video](demo/demo.mp4).
</video>

## Requirements


Use Python 3.10–3.12 with the versions pinned in [`requirement.txt`](requirement.txt). Python 3.14 may not be compatible with all of these pinned package versions.

## Install and run

From the project directory, create and activate a virtual environment, then install the dependencies and start Streamlit:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirement.txt
python -m streamlit run app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`) to open in your browser. To stop the app, press `Ctrl+C` in the terminal.

## Input CSV files

Upload CSV files in the app. It can route a file to the other category if its headers identify it as an Instron or multimeter export.

### Instron tensile CSV

The export should contain a table with these columns:

- `Time measurement`
- `Primary load measurement`
- `Tensile extension`
- `Composite strain` (optional; extension divided by the configured gauge length is used if this column is unavailable or has no positive values)

The parser searches the file for the table header and skips metadata before it. It also skips the following units row when it contains common unit labels such as `(s)`, `(mm)`, or `(N)`.

### Multimeter (DMM) CSV

The export should contain a header with a time column containing `Time` (typically `Time Stamp(s)`) and a resistance column containing `Resistance` (typically `Resistance (2W)`). The parser searches for the table header and ignores rows where the timestamp or resistance cannot be parsed. Elapsed DMM time is measured from the first valid timestamp.

## Using the analysis

1. Upload one or more Instron and DMM CSV files.
2. Configure each specimen by selecting its paired files and entering its label, linear density (`tex`), and gauge length (`mm`).
3. Set the sync offset in seconds, or enable automatic alignment to align the peak load with the steepest resistance increase.
4. Adjust the baseline noise window and post-break trimming controls in the sidebar as needed.
5. Review the plots, comparison metrics, and detected load-drop events. Use **Download Complete Summary Metrics CSV** to export the summary table.

Resistance is interpolated onto the Instron time points only where the measurement timelines overlap. If too few points overlap, adjust the sync offset or check the input files.

The resistance-versus-time plot uses raw resistance samples from each specimen's DMM trace. The first positive Instron load, aligned using the configured sync offset, sets time zero; samples are shown through the selected pre-break analysis window.

Each specimen also has its own load/resistance overlay graph, arranged in three columns. The load uses the Instron data, and resistance uses raw DMM trace samples on a secondary y-axis; both are aligned to the same onset-relative time axis. If no positive load is present, the specimen recording start is used as the time origin.
