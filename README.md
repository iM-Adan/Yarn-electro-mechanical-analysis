# TexLab by Adan

TexLab by Adan is a Streamlit application for synchronizing tensile-test data with multimeter measurements and comparing electromechanical yarn sensor behavior across specimens. It also provides separate workspaces for instrument traces and arbitrary CSV graphs.

## Features

- Upload multiple Instron and multimeter CSVs and configure up to 50 paired specimens.
- Identify and route instrument files from their headers.
- Configure specimen labels, linear density, gauge length, sync offset, and optional automatic alignment of peak load and resistance rise.
- Adjust the unloaded-baseline window and post-break trimming.
- Review interactive relative-resistance, normalized-resistivity, damage-tracking, resistance-time, and per-specimen load/resistance plots.
- Calculate turning strain, gauge factor, linearity, strain resolution, work of rupture, load-drop events, and recovery/hysteresis where applicable.
- Compare specimens and download the complete summary metrics as CSV.
- Plot Instron and multimeter traces independently of full analysis, with complete-data plotting and optional time cuts.
- Upload arbitrary CSV files, select X and Y columns, and display interactive combined and optional per-file plots with numeric or date range filtering.
- Preserve separate uploads and widget selections while switching workspaces.

## Architecture

`app.py` remains the Streamlit Community Cloud entry point. The application implementation is divided into small modules with one-way imports: user interface → core/data access → parsers and analysis → visualization/export.

```text
TexLab/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── .streamlit/
│   └── config.toml
├── assets/
│   ├── favicon.png
│   └── logo.png
├── demo/
│   └── demo.mp4
├── config/
│   ├── __init__.py
│   ├── constants.py
│   └── settings.py
├── core/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── data_validation.py
│   ├── file_router.py
│   ├── preprocessing.py
│   └── session_manager.py
├── parsers/
│   ├── __init__.py
│   ├── generic_csv_parser.py
│   ├── instron_parser.py
│   └── multimeter_parser.py
├── analysis/
│   ├── __init__.py
│   ├── damage_detection.py
│   ├── electromechanical_metrics.py
│   ├── hysteresis.py
│   ├── mechanical_metrics.py
│   ├── resistance_analysis.py
│   ├── specimen_comparison.py
│   ├── strain_analysis.py
│   └── synchronization.py
├── visualization/
│   ├── __init__.py
│   ├── damage_plots.py
│   ├── generic_plots.py
│   ├── specimen_plots.py
│   ├── strain_plots.py
│   └── time_series_plots.py
├── ui/
│   ├── __init__.py
│   ├── analysis_dashboard.py
│   ├── downloads.py
│   ├── main.py
│   ├── metrics_display.py
│   ├── plot_workspace.py
│   ├── sidebar.py
│   ├── specimen_configuration.py
│   ├── theme.py
│   └── upload.py
├── exports/
│   ├── __init__.py
│   └── csv_export.py
├── utils/
│   ├── __init__.py
│   └── numerical.py
└── tests/
    ├── __init__.py
    ├── sample_data.py
    ├── test_data_validation.py
    ├── test_file_router.py
    ├── test_instron_parser.py
    ├── test_metrics.py
    ├── test_multimeter_parser.py
    ├── test_synchronization.py
    └── test_workspace_baseline.py
```

Scientific functions accept data and configuration and return results without depending on Streamlit. Parsers own CSV decoding and instrument-specific conventions. The UI coordinates uploads, widgets, and rendering; visualization modules build Plotly figures; exports serialize downloads.

## Demo

<video controls width="100%" preload="metadata">
  <source src="https://raw.githubusercontent.com/iM-Adan/Yarn-electro-mechanical-analysis/main/demo/demo.mp4" type="video/mp4">
  Your Markdown viewer does not support embedded video. [Open the demo video](demo/demo.mp4).
</video>

## Requirements

- Python 3.10–3.12
- The pinned packages in [`requirements.txt`](requirements.txt)

The existing dependency pins are preserved. `pyarrow` is explicitly pinned because newer transitive releases require NumPy 2, which conflicts with the pinned NumPy 1.26.4.

## Install and run

From the project directory, create and activate a virtual environment, install dependencies, and start the app:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`). Stop the local server with `Ctrl+C`.

## Streamlit Community Cloud deployment

1. Push the repository to GitHub.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), deploy the repository’s `main` branch with `app.py` as the entry point.
3. Choose Python 3.12 in the app settings.
4. Community Cloud installs dependencies from `requirements.txt` and runs the hosted app independently of your computer.

The configured public app is [yarnanalysisbyadan.streamlit.app](https://yarnanalysisbyadan.streamlit.app/).

## Workspaces

### Full analysis

1. Upload one or more Instron and multimeter CSV files. Files are routed by their headers; keep instrument uploads separate from the trace-only and generic-graph uploads.
2. Configure the number of specimens, pair each Instron file with its multimeter file, and set the specimen label, linear density (`tex`), gauge length (`mm`), and sync offset.
3. Optionally enable automatic peak-load/resistance-rise alignment.
4. Adjust the unloaded baseline window and post-fracture trimming controls in the sidebar.
5. Review the plots, detected events, comparison matrix, and download the summary CSV.

### Plot traces only

Upload Instron and/or multimeter files independently of the full-analysis dataset. Select the signal to display. The complete trace is plotted by default; choose a time range only to crop it. The workspace shows a combined interactive graph and an individual graph for every selected trace.

### Plot graph

Upload a standard delimited CSV with a header row. The app detects columns and suggests likely time/date and measurement axes; select the X and Y columns manually. Choose one or more compatible files for a combined graph and optionally show individual graphs. Numeric and date-like X axes can be filtered; all data is shown by default. Rows with invalid selected-axis values are omitted and the plotted point count is reported.

## CSV formats

### Instron tensile CSV

The export should contain these columns:

- `Time measurement`
- `Primary load measurement`
- `Tensile extension`
- `Composite strain` (optional; extension divided by the configured gauge length is used if this column is unavailable or has no positive values)

The parser searches the first 40 lines for the table header, skips preceding metadata, and skips the following units row when it contains common units such as `(s)`, `(mm)`, or `(N)`. Values are converted to numeric, and rows with invalid values in the first column are dropped.

### Multimeter (DMM) CSV

The export should contain a timestamp column containing `Time` (typically `Time Stamp(s)`) and a resistance column containing `Resistance` (typically `Resistance (2W)`). The parser searches the first 40 lines for the measurement header, ignores rows where timestamps or resistance cannot be parsed, and returns elapsed seconds from the first valid timestamp.

## Analysis details

Resistance is interpolated onto Instron time points only where the measurement timelines overlap. If fewer than five points overlap, adjust the sync offset or check the input files.

The resistance-versus-time plot uses raw DMM samples from the analysis window, aligned to the first positive Instron load (or to the specimen start when there is no positive load). Per-specimen plots overlay Instron load and DMM resistance on separate y axes. Scientific formulas and reported metrics are retained from the original application.

## Tests

Run the standard-library regression suite with:

```powershell
python -m unittest discover -s tests -v
```
