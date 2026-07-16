"""
Race Engineer Dashboard.

Answers: "Why was this lap faster or slower than the previous one?"

Provides:
  - Multi-lap summary table (Stage 9)
  - Lap time / tire / fuel evolution charts
  - Lap-to-lap comparison with sector + corner breakdown
  - Root cause analysis (Stage 10) — plain English explanation
  - Next lap prediction (Stage 11)
  - Telemetry deep-dive (speed, throttle, brake, derived metrics)
"""

import streamlit as st
import sys, os, json, glob, math
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

from simulator.race_engineer import RaceEngineer

st.set_page_config(page_title="Race Engineer", layout="wide")
st.title("🏎️ Race Engineer")

# ------------------------------------------------------------------
#  SIDEBAR — Data Source
# ------------------------------------------------------------------

st.sidebar.header("Session Data")

log_dir = os.path.join(ROOT, "data", "logs")
log_files = sorted(glob.glob(os.path.join(log_dir, "*.json")))
log_names = [os.path.basename(f) for f in log_files]

selected_log = st.sidebar.selectbox(
    "Session Log", log_names,
    format_func=lambda x: x.replace(".json", ""),
    index=len(log_names) - 1 if log_names else 0,
)

load_btn = st.sidebar.button("Load & Analyze", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### Comparison")
lap_a = st.sidebar.number_input("Lap A", min_value=1, value=1)
lap_b = st.sidebar.number_input("Lap B", min_value=1, value=2)

# ------------------------------------------------------------------
#  MAIN — Analysis
# ------------------------------------------------------------------

if load_btn or "engineer" in st.session_state:
    if load_btn or "engineer" not in st.session_state:
        with st.spinner("Analyzing session..."):
            engineer = RaceEngineer()
            engineer.load_from_file(os.path.join(log_dir, selected_log))
            engineer.analyze()
            st.session_state.engineer = engineer
            st.session_state.log_name = selected_log
    else:
        engineer = st.session_state.engineer

    st.caption(f"Session: {st.session_state.log_name}")

    tab_multi, tab_compare, tab_telemetry, tab_predict = st.tabs([
        "📊 Multi-Lap", "🔍 Lap Comparison", "📈 Telemetry", "🔮 Prediction"
    ])

    table = engineer.get_multi_lap_table()

    # ================================================================
    # TAB 1 — MULTI-LAP OVERVIEW
    # ================================================================
    with tab_multi:
        st.subheader("Multi-Lap Summary")

        if table:
            # Summary table
            rows = []
            for s in table:
                rows.append({
                    "Lap": s["lap"],
                    "Time (s)": s["lap_time"],
                    "Avg Speed": f'{s["avg_speed_kmh"]:.1f}',
                    "Top Speed": f'{s["top_speed_kmh"]:.1f}',
                    "Throttle": f'{s["avg_throttle_pct"]:.0f}%',
                    "Brake": f'{s["avg_brake_pct"]:.0f}%',
                    "Max G": f'{s["max_long_accel_ms2"]:.2f}',
                    "Fuel End": f'{s["fuel_end_kg"]:.1f}kg',
                    "Tire Wear": f'{s["tire_wear_end_pct"]:.1f}%',
                    "Grip": f'{s["tire_grip_end"]:.3f}',
                    "Score": s["driver_score"],
                })

            st.dataframe(rows, use_container_width=True, hide_index=True)

            # Evolution charts
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Lap Time Evolution")
                laps = [s["lap"] for s in table]
                times = [s["lap_time"] for s in table]
                st.line_chart({"Lap Time (s)": times}, x=laps)

                st.subheader("Fuel Load")
                fuels = [s["fuel_start_kg"] for s in table]
                st.line_chart({"Fuel (kg)": fuels}, x=laps)

            with col2:
                st.subheader("Tire Wear")
                wears = [s["tire_wear_end_pct"] for s in table]
                st.line_chart({"Wear (%)": wears}, x=laps)

                st.subheader("Tire Surface Temperature")
                temps = [s["tire_surface_temp_end"] for s in table]
                st.line_chart({"Surface Temp (°C)": temps}, x=laps)

            # Per-lap speed summary
            st.subheader("Speed Stats per Lap")
            speed_data = {
                "Avg Speed": [s["avg_speed_kmh"] for s in table],
                "Top Speed": [s["top_speed_kmh"] for s in table],
            }
            st.line_chart(speed_data, x=[s["lap"] for s in table])

    # ================================================================
    # TAB 2 — LAP COMPARISON
    # ================================================================
    with tab_compare:
        st.subheader(f"Lap {lap_a} vs Lap {lap_b}")

        result = engineer.compare_laps(lap_a, lap_b)

        if "error" in result:
            st.error(result["error"])
        else:
            # Root cause banner
            direction = result["direction"]
            color = "green" if direction == "faster" else "red"
            st.markdown(
                f"<h3 style='color:{color};'>"
                f"Lap {lap_b} was {abs(result['delta_total']):.3f}s {direction} than Lap {lap_a}"
                f"</h3>",
                unsafe_allow_html=True,
            )

            st.info(result["root_cause"])

            # Sector comparison
            if result["sector_deltas"]:
                st.subheader("Sector Breakdown")
                sectors = list(result["sector_deltas"].keys())
                deltas = list(result["sector_deltas"].values())
                colors = ["green" if d < 0 else "red" for d in deltas]
                st.bar_chart({"Delta (s)": deltas}, x=sectors)

            # Corner comparison
            if result["corner_deltas"]:
                st.subheader("Corner-by-Corner Comparison")
                corner_rows = []
                for cd in result["corner_deltas"]:
                    corner_rows.append({
                        "Turn": cd["corner"],
                        "Entry Δ": f'{cd["entry_delta"]:+.1f}',
                        "Apex Δ": f'{cd["apex_delta"]:+.1f}',
                        "Exit Δ": f'{cd["exit_delta"]:+.1f}',
                        "Brake Dist Δ": f'{cd["brake_distance_delta"]:+.1f}m',
                    })
                st.dataframe(corner_rows, use_container_width=True, hide_index=True)

            # Tire & fuel delta
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Tire State Change")
                td = result["tire_delta"]
                st.metric("Grip Change", f"{td['grip_change']:+.3f}")
                st.metric("Wear Change", f"{td['wear_change']:+.1f}%")
                st.metric("Temp Change", f"{td['temp_change']:+.0f}°C")
            with col2:
                st.subheader("Fuel State Difference")
                fd = result["fuel_delta"]
                st.metric("Fuel at Start", f"{fd['start_diff']:+.1f}kg")
                st.metric("Fuel Used", f"{fd['used_diff']:+.1f}kg")

            # Lap A vs Lap B side-by-side stats
            st.subheader("Side-by-Side Lap Stats")
            sa = engineer.get_lap_summary(lap_a)
            sb = engineer.get_lap_summary(lap_b)
            if sa and sb:
                stat_cols = st.columns(3)
                metrics_to_show = [
                    ("lap_time", "Lap Time", "s", True),
                    ("avg_speed_kmh", "Avg Speed", "km/h", False),
                    ("top_speed_kmh", "Top Speed", "km/h", False),
                    ("avg_throttle_pct", "Avg Throttle", "%", False),
                    ("avg_brake_pct", "Avg Brake", "%", False),
                    ("max_long_accel_ms2", "Max Accel", "m/s²", False),
                    ("tire_wear_end_pct", "Tire Wear", "%", False),
                    ("fuel_used_kg", "Fuel Used", "kg", False),
                    ("driver_score", "Driver Score", "", False),
                ]
                for i, (key, label, unit, swap_color) in enumerate(metrics_to_show):
                    va = sa.get(key, 0)
                    vb = sb.get(key, 0)
                    delta = round(vb - va, 3)
                    with stat_cols[i % 3]:
                        if swap_color:
                            better = delta < 0  # lower is better for time
                        else:
                            better = delta > 0  # higher is better for most
                        st.metric(
                            f"{label}",
                            f"{vb} {unit}" if unit else f"{vb}",
                            f"{delta:+.3f}" if delta != 0 else "—",
                            delta_color="inverse" if swap_color else "normal",
                        )

    # ================================================================
    # TAB 3 — TELEMETRY DEEP-DIVE
    # ================================================================
    with tab_telemetry:
        st.subheader("Telemetry Overlay")

        lap_choice = st.selectbox(
            "Select Lap", [s["lap"] for s in table],
            index=min(len(table) - 1, 1),
        )

        packets = engineer.lap_data.get(lap_choice, [])
        if packets:
            enriched = engineer.compute_derived(packets)
            n = len(enriched)

            speeds = [p.get("true", {}).get("speed_kmh", 0) for p in enriched]
            throttles = [p.get("true", {}).get("throttle", 0) for p in enriched]
            brakes = [p.get("true", {}).get("brake_cmd", 0) for p in enriched]
            yaws = [p.get("true", {}).get("yaw_deg", 0) for p in enriched]
            long_accels = [p.get("derived", {}).get("long_accel_ms2", 0) for p in enriched]
            power = [p.get("derived", {}).get("power_kw", 0) for p in enriched]
            yaw_rates = [p.get("derived", {}).get("yaw_rate_dps", 0) for p in enriched]

            x = list(range(n))

            # Speed + controls
            st.subheader("Speed & Controls")
            data = {
                "Speed (km/h)": speeds,
                "Throttle (0-1)": throttles,
                "Brake (0-1)": brakes,
            }
            st.line_chart(data, x=x, height=300)

            # Yaw
            st.subheader("Yaw & Yaw Rate")
            yaw_data = {
                "Yaw (deg)": yaws,
                "Yaw Rate (deg/s)": yaw_rates,
            }
            st.line_chart(yaw_data, x=x, height=250)

            # Acceleration & Power
            st.subheader("Acceleration & Power")
            accel_data = {
                "Long Accel (m/s²)": long_accels,
                "Power (kW)": [p / 10 for p in power],
            }
            st.line_chart(accel_data, x=x, height=250)

            # Derived metrics table
            with st.expander("Derived Metrics Table (first 50 rows)"):
                rows = []
                fields = ["t", "speed_kmh", "throttle", "brake_cmd", "yaw_deg"]
                derived_fields = ["long_accel_ms2", "yaw_rate_dps", "slip_angle_deg", "power_kw"]
                for i, p in enumerate(enriched[:50]):
                    true = p.get("true", {})
                    d = p.get("derived", {})
                    row = {"idx": i}
                    for f in fields:
                        row[f] = true.get(f, 0)
                    for f in derived_fields:
                        row[f] = d.get(f, 0)
                    rows.append(row)
                st.dataframe(rows, use_container_width=True, hide_index=True)

    # ================================================================
    # TAB 4 — PREDICTION
    # ================================================================
    with tab_predict:
        st.subheader("Next Lap Prediction")

        if len(table) >= 3:
            current_lap = max(s["lap"] for s in table)
            pred = engineer.predict_next_lap(current_lap)

            if "error" not in pred:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Predicted Lap Time", f"{pred['predicted_lap_time']:.3f}s")
                col2.metric("Confidence Range",
                            f"[{pred['ci_lower']:.2f} - {pred['ci_upper']:.2f}]s")
                col3.metric("Fuel Remaining", f"{pred['fuel_remaining_kg']:.1f}kg")
                col4.metric("Tire Wear", f"{pred['tire_wear_pct']:.1f}%")

                st.subheader("Contributing Factors")
                fcol1, fcol2, fcol3 = st.columns(3)
                fcol1.metric("Trend Slope", f"{pred['trend_slope']:+.4f}s/lap")
                fcol2.metric("Grip Penalty", f"+{pred['grip_penalty_s']:.3f}s")
                fcol3.metric("Fuel Benefit", f"{pred['fuel_benefit_s']:+.3f}s")

                st.info(
                    f"Estimated {pred['remaining_laps_estimate']} laps remaining "
                    f"before tires reach 100% wear."
                )

                # Trend chart
                st.subheader("Lap Time Trend")
                laps = [s["lap"] for s in table]
                times = [s["lap_time"] for s in table]
                trend_data = {"Actual": times}
                st.line_chart(trend_data, x=laps, height=250)
            else:
                st.warning(pred.get("error", "Cannot predict"))
        else:
            st.warning("Need at least 3 laps to make a prediction.")

else:
    st.info("Select a session log from the sidebar and click **Load & Analyze**.")
    st.markdown("""
    ### What does the Race Engineer do?

    This dashboard answers one question:

    **"Why was this lap faster or slower than the previous one?"**

    It processes telemetry through the race engineer's pipeline:

    1. **Derived metrics** — acceleration, yaw rate, slip angle, power
    2. **Track segmentation** — corner detection from yaw trace
    3. **Per-corner analysis** — entry, apex, exit speeds; braking points
    4. **Lap summaries** — sector times, tire wear, fuel use, driver score
    5. **Multi-lap comparison** — evolution across the stint
    6. **Root cause** — which sector, corner, or factor caused the delta
    7. **Prediction** — next lap time based on tire/fuel trends
    """)
