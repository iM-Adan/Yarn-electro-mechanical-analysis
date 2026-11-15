import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(page_title="EM Desk", layout="wide")
st.title("Electromechanical Yarn Strain Sensor Analysis Desk")
st.markdown(
    r"Complete diagnostic suite evaluating **Curve Shape & Turning Strain**, **Monotonic Linearity ($R^2$) & Resolution**, "
    r"**Load-Drop vs. Resistance-Event Alignment**, **Normalized Resistivity ($\Omega\cdot\text{den}/\text{cm}$) & Tenacity ($\text{cN}/\text{tex}$)**, "
    r"**Cyclic Hysteresis/Recovery**, and **$R_0$ Quality Screening**."
)

app_mode = st.radio(
    "Mode",
    ["Full analysis", "Plot traces only"],
    horizontal=True,
    help="Plot uploaded Instron or multimeter traces interactively without calculating comparison metrics.",
)


def trapz_compat(y, x):
    """Compatible trapezoidal integration for both NumPy 1.x and 2.x (Python 3.14)."""
    if hasattr(np, "trapezoid"):
        return np.trapezoid(y, x)
    return np.trapz(y, x)


def find_peaks_by_prominence(values, prominence):
    """Return local-maximum indices whose prominence meets the threshold."""
    peaks = []
    start = 1
    while start < len(values) - 1:
        end = start
        while end + 1 < len(values) and values[end + 1] == values[start]:
            end += 1

        if values[start] > values[start - 1] and end < len(values) - 1 and values[end] > values[end + 1]:
            peak = (start + end) // 2
            left = peak - 1
            left_min = values[left]
            while left > 0 and values[left] <= values[peak]:
                left -= 1
                left_min = min(left_min, values[left])

            right = peak + 1
            right_min = values[right]
            while right < len(values) - 1 and values[right] <= values[peak]:
                right += 1
                right_min = min(right_min, values[right])

            if values[peak] - max(left_min, right_min) >= prominence:
                peaks.append(peak)
        start = end + 1

    return np.asarray(peaks, dtype=int)


def detect_file_type(file_buf):
    """Inspects the first 30 lines of a CSV to determine if it is an Instron or DMM file."""
    file_buf.seek(0)
    head_lines = [file_buf.readline().decode('utf-8-sig', errors='ignore') for _ in range(30)]
    text = "\n".join(head_lines)
    if "Time measurement" in text or "Primary load" in text or "Tensile extension" in text:
        return "instron"
    if "Time Stamp" in text or "Resistance (2W)" in text or "AutoRange" in text or "Address,USB" in text:
        return "dmm"
    return "unknown"


def parse_instron(file_buf):
    """Dynamically finds the Instron header row and skips the secondary units row."""
    ftype = detect_file_type(file_buf)
    if ftype == "dmm":
        raise ValueError(
            f"'{file_buf.name}' is a Multimeter (DMM) file, not an Instron file. "
            "Please select an Instron CSV (e.g., Specimen_RawData) for the Instron input."
        )

    file_buf.seek(0)
    lines = [line.decode('utf-8-sig', errors='ignore') for line in file_buf.readlines()]
    header_idx = 0
    for i, line in enumerate(lines[:40]):
        if "Time measurement" in line or "Primary load" in line or "Extension" in line:
            header_idx = i
            break

    # Skip any metadata lines before header_idx, plus the units row immediately following header_idx
    skip_rows = list(range(header_idx))
    if header_idx + 1 < len(lines):
        next_line = lines[header_idx + 1]
        if "(s)" in next_line or "(mm)" in next_line or "(N)" in next_line:
            skip_rows.append(header_idx + 1)

    file_buf.seek(0)
    df = pd.read_csv(file_buf, skiprows=skip_rows)
    column_map = {}
    for column in df.columns:
        normalized = column.strip()
        if normalized.startswith("Time measurement"):
            column_map[column] = "Time (s)"
        elif normalized.startswith("Primary load measurement"):
            column_map[column] = "Primary load (N)"
        elif normalized.startswith("Tensile extension"):
            column_map[column] = "Tensile extension (mm)"
    df = df.rename(columns=column_map)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=[df.columns[0]]).reset_index(drop=True)
    return df


def parse_dmm(file_buf):
    """Dynamically locates the 'Time Stamp(s)' header and parses Keysight/Agilent DMM CSVs."""
    ftype = detect_file_type(file_buf)
    if ftype == "instron":
        raise ValueError(
            f"'{file_buf.name}' is an Instron tensile file, not a Multimeter file. "
            "Please select a Multimeter CSV (e.g., Trace 1) for the DMM input."
        )

    file_buf.seek(0)
    lines = [line.decode('utf-8-sig', errors='ignore') for line in file_buf.readlines()]
    header_idx = None
    for i, line in enumerate(lines[:40]):
        if "Time Stamp" in line or ("Resistance" in line and "Records" in line):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError(f"Could not locate 'Time Stamp(s)' or 'Resistance' header in '{file_buf.name}'.")

    file_buf.seek(0)
    df = pd.read_csv(file_buf, skiprows=header_idx)
    time_cols = [c for c in df.columns if 'Time' in c]
    res_cols = [c for c in df.columns if 'Resistance' in c]

    if not time_cols or not res_cols:
        raise ValueError(f"Required Time/Resistance columns missing in '{file_buf.name}'.")

    time_col, res_col = time_cols[0], res_cols[0]
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    df[res_col] = pd.to_numeric(df[res_col], errors='coerce')
    df = df.dropna(subset=[time_col, res_col]).reset_index(drop=True)

    t0 = df[time_col].iloc[0]
    t_sec = (df[time_col] - t0).dt.total_seconds().values
    res = df[res_col].values
    return t_sec, res


def fit_metrics(x_strain_frac, y_dr_r0):
    """Calculates Gauge Factor (slope), R², and RMSE residuals over a strain window."""
    if len(x_strain_frac) < 3 or np.ptp(x_strain_frac) < 1e-5:
        return np.nan, np.nan, np.nan
    slope, intercept = np.polyfit(x_strain_frac, y_dr_r0, 1)
    y_pred = slope * x_strain_frac + intercept
    residuals = y_dr_r0 - y_pred
    rmse = np.sqrt(np.mean(residuals**2))
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y_dr_r0 - np.mean(y_dr_r0))**2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0
    return slope, r2, rmse


# Keep both upload groups rendered so each mode retains its own files when switching modes.
analysis_uploads = st.expander(
    "Full analysis files", expanded=app_mode == "Full analysis"
)
plot_uploads = st.expander(
    "Plot traces only files", expanded=app_mode == "Plot traces only"
)
with analysis_uploads:
    analysis_col_inst, analysis_col_dmm = st.columns(2)
    analysis_instron_uploads = analysis_col_inst.file_uploader(
        "Upload Instron Tensile CSVs",
        type=["csv"],
        accept_multiple_files=True,
        key="analysis_instron_uploads",
    )
    analysis_dmm_uploads = analysis_col_dmm.file_uploader(
        "Upload Multimeter (DMM) CSVs",
        type=["csv"],
        accept_multiple_files=True,
        key="analysis_dmm_uploads",
    )
with plot_uploads:
    plot_col_inst, plot_col_dmm = st.columns(2)
    plot_instron_uploads = plot_col_inst.file_uploader(
        "Upload Instron Tensile CSVs",
        type=["csv"],
        accept_multiple_files=True,
        key="plot_instron_uploads",
    )
    plot_dmm_uploads = plot_col_dmm.file_uploader(
        "Upload Multimeter (DMM) CSVs",
        type=["csv"],
        accept_multiple_files=True,
        key="plot_dmm_uploads",
    )

if app_mode == "Full analysis":
    raw_instron_uploads = analysis_instron_uploads
    raw_dmm_uploads = analysis_dmm_uploads
else:
    raw_instron_uploads = plot_instron_uploads
    raw_dmm_uploads = plot_dmm_uploads

instron_dict = {}
dmm_dict = {}
misrouted_notes = []

for f in (raw_instron_uploads or []) + (raw_dmm_uploads or []):
    ftype = detect_file_type(f)
    if ftype == "instron":
        instron_dict[f.name] = f
        if f in (raw_dmm_uploads or []):
            misrouted_notes.append(f"Auto-routed `{f.name}` to **Instron CSVs** based on its headers.")
    elif ftype == "dmm":
        dmm_dict[f.name] = f
        if f in (raw_instron_uploads or []):
            misrouted_notes.append(f"Auto-routed `{f.name}` to **Multimeter CSVs** based on its headers.")
    else:
        # Fallback to whichever uploader it was placed in
        if f in (raw_instron_uploads or []):
            instron_dict[f.name] = f
        else:
            dmm_dict[f.name] = f

for note in set(misrouted_notes):
    st.info(note)

if app_mode == "Plot traces only":
    parsed_instron = {}
    parsed_dmm = {}

    for name, file_buf in instron_dict.items():
        try:
            parsed_instron[name] = parse_instron(file_buf)
        except Exception as e:
            st.error(f"Could not read Instron trace '{name}': {e}")

    for name, file_buf in dmm_dict.items():
        try:
            parsed_dmm[name] = parse_dmm(file_buf)
        except Exception as e:
            st.error(f"Could not read multimeter trace '{name}': {e}")

    trace_options = []
    if parsed_dmm:
        trace_options.append("Resistance (DMM)")
    if parsed_instron:
        available_columns = {
            column
            for df in parsed_instron.values()
            for column in df.columns
        }
        for label, column in (
            ("Load (Instron)", "Primary load (N)"),
            ("Extension (Instron)", "Tensile extension (mm)"),
            ("Composite strain (Instron)", "Composite strain"),
        ):
            if column in available_columns:
                trace_options.append(label)

    if trace_options:
        selected_trace = st.selectbox("Trace signal to plot", trace_options)
        if selected_trace == "Resistance (DMM)":
            traces = [
                (name, np.asarray(time_s), np.asarray(resistance))
                for name, (time_s, resistance) in parsed_dmm.items()
            ]
            x_label = "Time (s)"
            y_label = "Resistance (Ω)"
        else:
            column_by_signal = {
                "Load (Instron)": ("Primary load (N)", "Load (N)"),
                "Extension (Instron)": ("Tensile extension (mm)", "Extension (mm)"),
                "Composite strain (Instron)": ("Composite strain", "Composite strain"),
            }
            column, y_label = column_by_signal[selected_trace]
            traces = [
                (name, df["Time (s)"].to_numpy(), df[column].to_numpy())
                for name, df in parsed_instron.items()
                if column in df.columns
            ]
            x_label = "Time (s)"

        finite_times = [
            time[np.isfinite(time)]
            for _, time, _ in traces
            if np.issubdtype(time.dtype, np.number) and np.isfinite(time).any()
        ]
        if not finite_times:
            st.warning("The selected trace has no valid numeric time values.")
        else:
            time_min = float(min(np.min(time) for time in finite_times))
            time_max = float(max(np.max(time) for time in finite_times))
            time_mode = st.radio(
                "Time range",
                ["Complete data (no time cut)", "Cut to time range"],
                horizontal=True,
                help="Complete data plots every sample in each uploaded trace. Choose a time range only to intentionally crop the traces.",
            )
            if time_mode == "Cut to time range" and time_min < time_max:
                range_col1, range_col2 = st.columns(2)
                range_start = range_col1.number_input(
                    "Start time (s)",
                    min_value=time_min,
                    max_value=time_max,
                    value=time_min,
                    key="trace_range_start",
                )
                range_end = range_col2.number_input(
                    "End time (s)",
                    min_value=time_min,
                    max_value=time_max,
                    value=time_max,
                    key="trace_range_end",
                )
                if range_start > range_end:
                    st.error("Start time must be less than or equal to end time.")
                    traces_to_plot = []
                else:
                    traces_to_plot = []
                    for name, time, values in traces:
                        if not np.issubdtype(time.dtype, np.number):
                            continue
                        mask = (
                            np.isfinite(time)
                            & (time >= range_start)
                            & (time <= range_end)
                        )
                        if np.any(mask):
                            traces_to_plot.append((name, time[mask], values[mask]))
            else:
                traces_to_plot = traces

            if traces_to_plot:
                combined_fig = go.Figure()
                for name, time, values in traces_to_plot:
                    combined_fig.add_trace(
                        go.Scatter(x=time, y=values, mode="lines", name=name)
                    )
                combined_fig.update_layout(
                    title=f"Combined {selected_trace} traces",
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    hovermode="x unified",
                )
                st.subheader("Combined interactive graph")
                st.plotly_chart(combined_fig, use_container_width=True)

                st.subheader("Individual interactive graphs")
                for name, time, values in traces_to_plot:
                    individual_fig = go.Figure(
                        go.Scatter(x=time, y=values, mode="lines", name=name)
                    )
                    individual_fig.update_layout(
                        title=name,
                        xaxis_title=x_label,
                        yaxis_title=y_label,
                        hovermode="x",
                    )
                    st.plotly_chart(individual_fig, use_container_width=True)
            elif time_mode == "Cut to time range":
                st.warning("The selected time range contains no samples.")
    elif raw_instron_uploads or raw_dmm_uploads:
        st.warning("No uploaded files contain a readable trace for plotting.")
    else:
        st.info("Upload one or more Instron or multimeter CSV files to plot their traces.")
elif instron_dict and dmm_dict:
    st.subheader("Configure Specimens for Comparison")
    num_tests = st.number_input("Number of specimens/tests to compare", min_value=1, max_value=50, value=1)

    tests_config = []
    inst_keys = list(instron_dict.keys())
    dmm_keys = list(dmm_dict.keys())

    for i in range(num_tests):
        with st.expander(f"Specimen {i+1} Configuration", expanded=(i == 0)):
            c1, c2, c3 = st.columns(3)
            label = c1.text_input("Label / Design Parameter", value=f"Sample {i+1}", key=f"lbl_{i}")
            inst_name = c2.selectbox("Instron CSV", inst_keys, index=min(i, len(inst_keys)-1), key=f"inst_{i}")
            dmm_name = c3.selectbox("Multimeter CSV", dmm_keys, index=min(i, len(dmm_keys)-1), key=f"dmm_{i}")

            c4, c5, c6, c7 = st.columns(4)
            tex = c4.number_input("Linear Density (tex)", value=531.11, min_value=1.0, step=10.0, key=f"tex_{i}")
            gauge_mm = c5.number_input("Gauge Length (mm)", value=180.0, min_value=1.0, step=10.0, key=f"gl_{i}")
            offset = c6.number_input("Sync Offset: Instron Start in DMM Time (s)", value=0.0, min_value=-30.0, max_value=30.0, step=0.1, key=f"off_{i}")
            auto_sync = c7.checkbox("Auto-align peak break to R spike", value=False, key=f"auto_{i}")

            tests_config.append({
                "label": label,
                "inst_file": instron_dict[inst_name],
                "dmm_file": dmm_dict[dmm_name],
                "tex": tex,
                "gauge_mm": gauge_mm,
                "offset": offset,
                "auto_sync": auto_sync
            })

    st.sidebar.header("Signal & Window Settings")
    baseline_window_s = st.sidebar.slider("Unloaded Baseline Noise Window (s)", 0.5, 5.0, 2.0, 0.5)
    pre_break_trim_pct = st.sidebar.slider("Trim post-fracture tail after peak load (%)", 0.0, 1.0, 0.0, 0.05)

    fig_curve = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "1A. Relative Resistance (ΔR/R₀) vs. Strain",
            "1B. Normalized Resistivity vs. Strain",
        ),
    )
    fig_damage = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "2A. Tenacity vs. Time",
            "2B. Relative Resistance vs. Tenacity",
        ),
    )
    fig_res_time = go.Figure()

    colors = px.colors.qualitative.Plotly
    summary_rows = []
    event_logs = []
    specimen_time_figures = []

    for idx, cfg in enumerate(tests_config):
        color = colors[idx % len(colors)]
        label = cfg["label"]
        tex = cfg["tex"]
        denier = tex * 9.0
        gauge_cm = cfg["gauge_mm"] / 10.0

        try:
            df_mech = parse_instron(cfg["inst_file"])
            t_elec, res_raw = parse_dmm(cfg["dmm_file"])
        except Exception as e:
            st.error(f"Error parsing files for {label}: {e}")
            continue

        t_mech = df_mech['Time (s)'].values
        load_N = df_mech['Primary load (N)'].values
        ext_mm = df_mech['Tensile extension (mm)'].values

        if 'Composite strain' in df_mech.columns and df_mech['Composite strain'].max() > 0:
            strain_frac = df_mech['Composite strain'].values
        else:
            strain_frac = ext_mm / cfg["gauge_mm"]
        strain_pct = strain_frac * 100.0

        # Normalized mechanical tenacity (cN/tex)
        tenacity_cN_tex = (load_N * 100.0) / tex

        # Auto-sync option: align peak load drop to steepest resistance jump
        offset = cfg["offset"]
        peak_load_idx = int(np.argmax(load_N))
        t_break_mech = t_mech[peak_load_idx]
        positive_load_indices = np.flatnonzero(load_N > 0)
        pull_onset_time = (
            float(t_mech[positive_load_indices[0]]) if len(positive_load_indices) else None
        )
        if cfg["auto_sync"]:
            d_res = np.gradient(res_raw, t_elec)
            spike_elec_idx = int(np.argmax(d_res))
            offset = float(t_elec[spike_elec_idx] - t_break_mech)

        # Baseline R0 and Noise from initial unloaded window
        static_mask = t_elec <= max(baseline_window_s, offset)
        if np.sum(static_mask) >= 2:
            R0 = float(np.mean(res_raw[static_mask]))
            r0_std = float(np.std(res_raw[static_mask], ddof=1))
        else:
            R0 = float(res_raw[0])
            r0_std = 0.0

        noise_dr_r0 = r0_std / R0 if R0 > 0 else 0.0
        R0_norm_ohm_den_cm = (R0 / gauge_cm) * denier

        # Synchronize timelines & interpolate resistance onto Instron timestamps
        t_mech_aligned = t_mech + offset
        order = np.argsort(t_elec)
        res_sync = np.interp(
            t_mech_aligned, t_elec[order], res_raw[order], left=np.nan, right=np.nan
        )

        valid_mask = ~np.isnan(res_sync)
        cutoff_idx = int(peak_load_idx * (1.0 - pre_break_trim_pct)) if pre_break_trim_pct > 0 else peak_load_idx
        active_indices = np.arange(len(t_mech)) <= cutoff_idx
        mask_active = valid_mask & active_indices

        if pull_onset_time is not None:
            time_origin = pull_onset_time
            onset_description = "first positive load"
        else:
            time_origin = float(t_mech[0])
            onset_description = "specimen start (no positive load)"
            st.warning(
                f"No positive Instron load found for {label}; using specimen start as the time origin."
            )

        fig_specimen = make_subplots(specs=[[{"secondary_y": True}]])
        load_window = (
            (t_mech >= time_origin)
            & (np.arange(len(t_mech)) <= cutoff_idx)
        )
        fig_specimen.add_trace(
            go.Scatter(
                x=t_mech[load_window] - time_origin,
                y=load_N[load_window],
                mode="lines",
                name="Load (Instron)",
                line={"color": "blue", "width": 1.8},
            ),
            secondary_y=False,
        )
        pull_onset_dmm_time = time_origin + offset
        analysis_end_dmm_time = t_mech[cutoff_idx] + offset
        trace_window = (
            (t_elec >= pull_onset_dmm_time)
            & (t_elec <= analysis_end_dmm_time)
        )
        if np.any(trace_window):
            trace_order = np.argsort(t_elec[trace_window])
            fig_specimen.add_trace(
                go.Scatter(
                    x=t_elec[trace_window][trace_order],
                    y=res_raw[trace_window][trace_order],
                    mode="lines",
                    name="Resistance (DMM trace)",
                    line={"color": "red", "width": 1.8},
                ),
                secondary_y=True,
            )
        else:
            st.warning(
                f"No DMM trace samples fall within the analysis window for {label}."
            )

        x_axis_label = (
            "Time Since Pull Onset (s)"
            if pull_onset_time is not None
            else "Time Since Specimen Start (s)"
        )
        fig_specimen.update_layout(
            title=f"{label}: Load & Resistance vs. Time",
            hovermode="x unified",
        )
        fig_specimen.update_xaxes(title_text=x_axis_label, showgrid=True)
        fig_specimen.update_yaxes(title_text="Load (N)", secondary_y=False)
        fig_specimen.update_yaxes(
            title_text="Resistance (Ω)", secondary_y=True, showgrid=False
        )
        specimen_time_figures.append(fig_specimen)

        if np.sum(mask_active) < 5:
            st.warning(f"Not enough overlapping time data for {label}. Check your Sync Offset.")
            continue

        t_act = t_mech[mask_active]
        strain_pct_act = strain_pct[mask_active]
        strain_frac_act = strain_frac[mask_active]
        load_N_act = load_N[mask_active]
        ext_mm_act = ext_mm[mask_active]
        tenacity_act = tenacity_cN_tex[mask_active]
        res_act = res_sync[mask_active]

        dr_r0_act = (res_act - R0) / R0
        norm_res_act = (res_act / gauge_cm) * denier

        # 1. Turning Strain Detection (where resistance stops falling and begins rising)
        min_idx = int(np.argmin(dr_r0_act))
        turning_strain_pct = float(strain_pct_act[min_idx])
        turning_dr_r0 = float(dr_r0_act[min_idx])

        # 2. Zone 1 (Compaction: 0 to Turning Strain) & Zone 2 (Rising/Monotonic: Turning Strain to Break)
        gf_comp, r2_comp, rmse_comp = fit_metrics(strain_frac_act[:min_idx+1], dr_r0_act[:min_idx+1])
        gf_rise, r2_rise, rmse_rise = fit_metrics(strain_frac_act[min_idx:], dr_r0_act[min_idx:])

        dom_gf = gf_rise if not np.isnan(gf_rise) and abs(gf_rise) >= abs(gf_comp or 0) else gf_comp
        min_detectable_strain_pct = (noise_dr_r0 / abs(dom_gf)) * 100.0 if (dom_gf and abs(dom_gf) > 1e-6) else np.nan

        # 3. Mechanical Energy / Specific Work of Rupture (J/g)
        work_mJ = float(trapz_compat(load_N_act, ext_mm_act))
        specimen_mass_g = (tex * (cfg["gauge_mm"] / 1000.0)) / 1000.0
        specific_energy_J_g = (work_mJ / 1000.0) / specimen_mass_g if specimen_mass_g > 0 else np.nan

        # 4. Cyclic / Unloading Hysteresis Check
        max_strain_idx = int(np.argmax(strain_pct[valid_mask]))
        strain_valid = strain_pct[valid_mask]
        dr_r0_valid = (res_sync[valid_mask] - R0) / R0
        if max_strain_idx < len(strain_valid) - 10 and strain_valid[-1] < 0.5 * strain_valid[max_strain_idx]:
            recovery_ratio = float(res_sync[valid_mask][-1] / R0)
            loop_area = float(abs(trapz_compat(dr_r0_valid[:max_strain_idx+1], strain_valid[:max_strain_idx+1]) +
                                  trapz_compat(dr_r0_valid[max_strain_idx:], strain_valid[max_strain_idx:])))
            cyclic_status = f"R_end/R₀ = {recovery_ratio:.2f} (Hyst: {loop_area:.2f})"
        else:
            cyclic_status = "Monotonic to Break (No Unload)"

        # 5. Damage Tracking: Detect mid-test load drops
        d_tenacity = np.diff(tenacity_act)
        drop_peaks = find_peaks_by_prominence(-d_tenacity, prominence=0.15)
        for dp in drop_peaks:
            event_logs.append({
                "Specimen": label,
                "Time (s)": round(float(t_act[dp]), 2),
                "Strain (%)": round(float(strain_pct_act[dp]), 2),
                "Tenacity Drop (cN/tex)": round(float(-d_tenacity[dp]), 3),
                "Local ΔR/R₀": round(float(dr_r0_act[dp]), 3)
            })

        fig_curve.add_trace(
            go.Scatter(
                x=strain_pct_act,
                y=dr_r0_act,
                mode="lines",
                name=label,
                line={"color": color, "width": 2},
            ),
            row=1,
            col=1,
        )
        fig_curve.add_trace(
            go.Scatter(
                x=[turning_strain_pct],
                y=[turning_dr_r0],
                mode="markers",
                name=f"{label} turning strain",
                marker={"color": color, "size": 9},
                showlegend=False,
            ),
            row=1,
            col=1,
        )

        fig_curve.add_trace(
            go.Scatter(
                x=strain_pct_act,
                y=norm_res_act,
                mode="lines",
                name=label,
                line={"color": color, "width": 2},
                showlegend=False,
            ),
            row=1,
            col=2,
        )

        fig_damage.add_trace(
            go.Scatter(
                x=t_act,
                y=tenacity_act,
                mode="lines",
                name=f"{label} Tenacity",
                line={"color": color, "width": 1.8},
            ),
            row=1,
            col=1,
        )
        if len(drop_peaks) > 0:
            fig_damage.add_trace(
                go.Scatter(
                    x=t_act[drop_peaks],
                    y=tenacity_act[drop_peaks],
                    mode="markers",
                    name=f"{label} load-drop events",
                    marker={"color": "red", "size": 9, "symbol": "x"},
                ),
                row=1,
                col=1,
            )

        fig_damage.add_trace(
            go.Scatter(
                x=tenacity_act,
                y=dr_r0_act,
                mode="lines",
                name=label,
                line={"color": color, "width": 2},
                showlegend=False,
            ),
            row=1,
            col=2,
        )

        # Plot 3: Raw DMM trace resistance vs. elapsed time from pull onset
        if pull_onset_time is not None:
            if np.any(trace_window):
                trace_order = np.argsort(t_elec[trace_window])
                fig_res_time.add_trace(
                    go.Scatter(
                        x=t_elec[trace_window][trace_order] - pull_onset_dmm_time,
                        y=res_raw[trace_window][trace_order],
                        mode="lines",
                        name=label,
                        line={"color": color, "width": 2},
                    )
                )
            else:
                st.warning(f"Cannot plot resistance since pull onset for {label}: no DMM trace samples in the analysis window.")
        else:
            st.warning(f"Cannot plot resistance since pull onset for {label}: Instron load never exceeds zero.")

        summary_rows.append({
            "Specimen": label,
            "R₀ (Ω)": round(R0, 2),
            "Norm. R₀ (kΩ·den/cm)": round(R0_norm_ohm_den_cm / 1000.0, 2),
            "Baseline Noise (Ω)": round(r0_std, 4),
            "Turning Strain (%)": round(turning_strain_pct, 2),
            "Min ΔR/R₀ at Turn": round(turning_dr_r0, 3),
            "Compaction GF (0→Turn)": round(gf_comp, 2) if not np.isnan(gf_comp) else None,
            "Compaction R²": round(r2_comp, 3) if not np.isnan(r2_comp) else None,
            "Rising GF (Turn→Break)": round(gf_rise, 2) if not np.isnan(gf_rise) else None,
            "Rising R²": round(r2_rise, 3) if not np.isnan(r2_rise) else None,
            "Strain Resolution (%)": round(min_detectable_strain_pct, 4) if not np.isnan(min_detectable_strain_pct) else None,
            "Strain at Break (%)": round(float(strain_pct_act[-1]), 2),
            "Tenacity (cN/tex)": round(float(np.max(tenacity_act)), 2),
            "Work of Rupture (J/g)": round(specific_energy_J_g, 2),
            "Recovery / Hysteresis": cyclic_status
        })

    fig_curve.add_hline(y=0, line_dash="dot", line_color="gray", row=1, col=1)
    fig_curve.update_xaxes(title_text="Strain (%)", showgrid=True)
    fig_curve.update_yaxes(title_text="ΔR/R₀", showgrid=True, row=1, col=1)
    fig_curve.update_yaxes(
        title_text="Normalized Resistance (Ω·den/cm)", showgrid=True, row=1, col=2
    )
    fig_curve.update_layout(hovermode="x unified", height=500)

    fig_damage.update_xaxes(showgrid=True, row=1, col=1, title_text="Time (s)")
    fig_damage.update_yaxes(
        showgrid=True, row=1, col=1, title_text="Tenacity (cN/tex)"
    )
    fig_damage.update_xaxes(
        showgrid=True, row=1, col=2, title_text="Tenacity (cN/tex)"
    )
    fig_damage.update_yaxes(showgrid=True, row=1, col=2, title_text="ΔR/R₀")
    fig_damage.update_layout(hovermode="closest", height=500)

    fig_res_time.update_layout(
        title="3. Resistance (Ω) vs. Time Since Pull Onset",
        xaxis_title="Time Since Pull Onset (s)",
        yaxis_title="Resistance (Ω)",
        hovermode="x unified",
    )
    fig_res_time.update_xaxes(showgrid=True)
    fig_res_time.update_yaxes(showgrid=True)

    st.subheader("1. Curve Shape, Turning Strain & Normalized Resistivity")
    st.plotly_chart(fig_curve, use_container_width=True)

    st.subheader("2. Mechanical Damage Tracking & Load-Drop Alignment")
    st.plotly_chart(fig_damage, use_container_width=True)

    st.subheader("3. Resistance vs. Time Since Pull Onset")
    st.plotly_chart(fig_res_time, use_container_width=True)

    if specimen_time_figures:
        st.subheader("4. Per-Specimen Load and Resistance vs. Time")
        specimen_columns = st.columns(3)
        for idx, fig_specimen in enumerate(specimen_time_figures):
            with specimen_columns[idx % 3]:
                st.plotly_chart(fig_specimen, use_container_width=True)

    if summary_rows:
        df_summary = pd.DataFrame(summary_rows)
        st.subheader("5. Complete Electromechanical & Sensor Viability Matrix")
        st.dataframe(df_summary, use_container_width=True)

        if len(df_summary) > 1:
            r0_vals = df_summary["R₀ (Ω)"].values
            r0_cv = (np.std(r0_vals, ddof=1) / np.mean(r0_vals)) * 100.0
            c_m1, c_m2, c_m3 = st.columns(3)
            c_m1.metric("Batch Mean R₀", f"{np.mean(r0_vals):.2f} Ω")
            c_m2.metric("Batch R₀ Spread (CV%)", f"{r0_cv:.2f}%")
            if len(r0_vals) >= 2 and np.ptp(r0_vals) > 0:
                corr = np.corrcoef(r0_vals, df_summary["Strain at Break (%)"].values)[0, 1]
                c_m3.metric("R₀ vs. Break Strain Correlation (r)", f"{corr:.2f}")

        csv_bytes = df_summary.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Complete Summary Metrics CSV",
            data=csv_bytes,
            file_name="yarn_sensor_comparison_metrics.csv",
            mime="text/csv"
        )

    if event_logs:
        st.subheader("6. Detected Mid-Test Load-Drop Events (Slippage / Fiber Fracture)")
        st.dataframe(pd.DataFrame(event_logs), use_container_width=True)
elif raw_instron_uploads or raw_dmm_uploads:
    st.warning("Please upload at least one Instron CSV (e.g., `Specimen_RawData_2.csv`) AND one Multimeter CSV (e.g., `Trace 1.csv`).")