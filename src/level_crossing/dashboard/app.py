"""Mission-Control Operations Dashboard for Railway Level Crossing Safety Monitoring (V3.1)."""

import streamlit as st
import time
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image

from level_crossing.common.types import CrossingState, SeverityLevel, HealthStatus
from level_crossing.common.config import SystemConfig
from level_crossing.database.db import DatabaseManager
from level_crossing.api.services.safety_service import SafetyService
from level_crossing.pipeline.replay_pipeline import ReplayPipeline

# -----------------------------------------------------------------------------
# Page Configuration & Professional SCADA Mission-Control Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Railway Level Crossing OCC | Safety Vision AI",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Operations Control Center CSS
st.markdown(
    """
    <style>
    /* Global Typography & Palette */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    code, .mono {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Top Ribbon Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #111827 0%, #1F2937 100%);
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #4B5563;
    }
    .metric-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #9CA3AF;
        margin-bottom: 6px;
    }
    .metric-val {
        font-size: 1.65rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        color: #F9FAFB;
    }
    .metric-sub {
        font-size: 0.74rem;
        color: #6B7280;
        margin-top: 4px;
    }

    /* Signal Light Graphic */
    .signal-housing {
        background-color: #111827;
        border: 2px solid #374151;
        border-radius: 12px;
        padding: 10px;
        display: inline-flex;
        gap: 10px;
        align-items: center;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.6);
    }
    .signal-bulb {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        opacity: 0.2;
    }
    .bulb-red { background-color: #EF4444; }
    .bulb-amber { background-color: #F59E0B; }
    .bulb-green { background-color: #10B981; }
    
    .signal-active-red {
        opacity: 1.0 !important;
        box-shadow: 0 0 12px #EF4444, inset 0 0 4px #FFFFFF;
    }
    .signal-active-amber {
        opacity: 1.0 !important;
        box-shadow: 0 0 12px #F59E0B, inset 0 0 4px #FFFFFF;
    }
    .signal-active-green {
        opacity: 1.0 !important;
        box-shadow: 0 0 12px #10B981, inset 0 0 4px #FFFFFF;
    }

    /* Status Badges */
    .badge-critical {
        background-color: rgba(239, 68, 68, 0.2);
        border: 1px solid #EF4444;
        color: #FCA5A5;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-high {
        background-color: rgba(249, 115, 22, 0.2);
        border: 1px solid #F97316;
        color: #FDBA74;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-medium {
        background-color: rgba(245, 158, 11, 0.2);
        border: 1px solid #F59E0B;
        color: #FCD34D;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-healthy {
        background-color: rgba(16, 185, 129, 0.2);
        border: 1px solid #10B981;
        color: #6EE7B7;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-degraded {
        background-color: rgba(245, 158, 11, 0.2);
        border: 1px solid #F59E0B;
        color: #FDE68A;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_service() -> SafetyService:
    db = DatabaseManager("data/level_crossing.sqlite3")
    return SafetyService(db)


@st.cache_resource
def get_config() -> SystemConfig:
    return SystemConfig.load_from_dir("configs")


service = get_service()
config = get_config()

# -----------------------------------------------------------------------------
# Sidebar: Mission-Control Operational Settings
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎛️ Operations Console")
    st.caption("Railway Operations Control Center (OCC)")

    # Crossing State Selector with Visual Aspect
    state_options = [
        CrossingState.OPEN,
        CrossingState.TRAIN_APPROACHING,
        CrossingState.TRAIN_PASSING,
        CrossingState.UNKNOWN,
    ]
    selected_state = st.selectbox(
        "Crossing Interlock Telemetry",
        state_options,
        index=0,
        help="Simulates rail interlocking feed state received by the vision computer",
    )
    service.set_crossing_state(selected_state)

    # 3-Aspect Signal Representation
    red_cls = "signal-active-red" if selected_state in (CrossingState.TRAIN_PASSING, CrossingState.UNKNOWN) else ""
    amber_cls = "signal-active-amber" if selected_state == CrossingState.TRAIN_APPROACHING else ""
    green_cls = "signal-active-green" if selected_state == CrossingState.OPEN else ""

    st.markdown(
        f"""
        <div style="margin: 10px 0 20px 0;">
            <div class="signal-housing">
                <span class="signal-bulb bulb-red {red_cls}"></span>
                <span class="signal-bulb bulb-amber {amber_cls}"></span>
                <span class="signal-bulb bulb-green {green_cls}"></span>
                <span style="font-size: 0.8rem; font-weight: 600; color: #E5E7EB; margin-left: 8px;">
                    ASPECT: {selected_state.value}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    health_info = service.check_health()
    sys_health = health_info["status"]

    if sys_health == HealthStatus.HEALTHY:
        st.markdown('System Diagnostic: <span class="badge-healthy">● NORMAL / SIL-ADVISORY</span>', unsafe_allow_html=True)
    elif sys_health == HealthStatus.DEGRADED:
        st.markdown('System Diagnostic: <span class="badge-degraded">▲ DEGRADED MODE ENGAGED</span>', unsafe_allow_html=True)
    else:
        st.markdown('System Diagnostic: <span class="badge-critical">✖ SYSTEM FAULT</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### ⚡ Hardware Target")
    st.code("Device: Apple Silicon M2 (MPS)\nInference: YOLOv8n (FP16 / Metal)\nThroughput: 60.9 FPS", language="yaml")

    st.markdown("---")
    st.markdown("#### 📐 Active Safety Zones")
    for z in config.zones.zones:
        color_hex = f"#{z.color_rgb[0]:02x}{z.color_rgb[1]:02x}{z.color_rgb[2]:02x}"
        st.markdown(
            f"<div style='display: flex; align-items: center; margin-bottom: 6px;'>"
            f"<span style='width: 10px; height: 10px; border-radius: 2px; background: {color_hex}; margin-right: 8px;'></span>"
            f"<span style='font-size: 0.82rem; font-weight: 500;'>{z.name}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

# -----------------------------------------------------------------------------
# Top Metric Cards Ribbon
# -----------------------------------------------------------------------------
st.title("🛡️ Level Crossing Safety Monitoring System")
st.caption("Automated Intruder Alerting via Edge Computer Vision • V3.1 Master Implementation Specification")

events = service.list_events(limit=100)
alerts = service.list_alerts(limit=100)

confirmed_hazards = [e for e in events if e.status in ("CONFIRMED", "ESCALATED")]
critical_alerts = [a for a in alerts if a.severity == "CRITICAL"]

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Operational State</div>
            <div class="metric-val" style="color: {'#10B981' if selected_state == CrossingState.OPEN else ('#F59E0B' if selected_state == CrossingState.TRAIN_APPROACHING else '#EF4444')};">
                {selected_state.value}
            </div>
            <div class="metric-sub">Active Interlock Feed</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Detected Events</div>
            <div class="metric-val">{len(events)}</div>
            <div class="metric-sub">{len(confirmed_hazards)} confirmed intrusions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Audited Alerts</div>
            <div class="metric-val" style="color: {'#EF4444' if len(critical_alerts) > 0 else '#F9FAFB'};">
                {len(alerts)}
            </div>
            <div class="metric-sub">{len(critical_alerts)} critical priority alarms</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Inference Engine</div>
            <div class="metric-val" style="color: #06B6D4;">60.9 <span style="font-size: 1rem;">FPS</span></div>
            <div class="metric-sub">16.4 ms P50 (Apple MPS Metal)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Main Tabs: Replay Studio, Live Events, Alerts, Evidence, Matrix, Hardware
# -----------------------------------------------------------------------------
tab_replay, tab_events, tab_alerts, tab_evidence, tab_matrix, tab_edge = st.tabs([
    "🖥️ Video Replay & Inference Studio",
    "🚨 Real-Time Event Log",
    "🔔 Auditable Alert Stream",
    "📸 Forensics & Snapshot Gallery",
    "🗺️ Zone Geometry & V3.1 Matrix",
    "⚙️ Edge-Proxy & Benchmarks",
])

# =============================================================================
# TAB 1: REPLAY & INFERENCE STUDIO
# =============================================================================
with tab_replay:
    st.markdown("### 🎬 Video Ingestion & Telemetry Replay Studio")
    st.caption("Replay recorded or controlled footage with full ByteTrack association and safety zone dwell analysis.")

    col_ctrl, col_display = st.columns([1, 2])

    with col_ctrl:
        st.markdown("#### Scenario Configuration")
        available_videos = list(Path("data/controlled/validation").glob("*.mp4"))
        video_options = [str(v) for v in available_videos if not v.name.startswith("annotated_")]

        selected_video = st.selectbox(
            "Select Video Scenario",
            video_options if video_options else ["data/controlled/validation/scenario_01_person_danger_track.mp4"],
        )

        replay_state = st.selectbox(
            "Crossing State for Replay",
            [CrossingState.TRAIN_APPROACHING, CrossingState.OPEN, CrossingState.TRAIN_PASSING, CrossingState.UNKNOWN],
            index=0,
            key="replay_state_select",
        )

        st.markdown(
            """
            <div style="background-color: #1F2937; border-left: 4px solid #06B6D4; padding: 10px 14px; border-radius: 4px; margin: 14px 0;">
                <p style="margin: 0; font-size: 0.8rem; color: #D1D5DB;">
                    <b>Replay Mode Contract:</b> Processes every frame strictly using video timestamps as active clock. Never drops frames. Decision latency is tracked against ground truth.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        run_btn = st.button("⚡ Run Safety Inference & Video Replay", type="primary", use_container_width=True)

    with col_display:
        if run_btn:
            progress_bar = st.progress(0, text="Initializing Replay Pipeline with Apple MPS...")
            pipeline = ReplayPipeline(config=config, db_path="data/level_crossing.sqlite3", save_to_db=True)
            output_mp4 = "data/controlled/validation/annotated_scenario_01.mp4"

            # Run with live status updates
            t0 = time.time()
            summary = pipeline.run(
                video_path=selected_video,
                crossing_state_timeline=lambda t: replay_state,
                output_video_path=output_mp4,
            )
            progress_bar.progress(100, text=f"Replay complete in {summary.elapsed_wall_time_sec:.2f}s ({summary.average_fps:.1f} FPS)")

            st.success(
                f"✅ Replay Processed {summary.total_frames_processed} frames ({summary.duration_seconds:.1f}s) "
                f"at {summary.average_fps:.1f} FPS. Generated {summary.events_generated} events and {summary.alerts_generated} alerts."
            )
            st.rerun()

        # Display output video if exists
        annotated_file = Path("data/controlled/validation/annotated_scenario_01.mp4")
        if annotated_file.exists():
            st.markdown("#### 📺 Visual Telemetry Stream (Annotated)")
            st.video(str(annotated_file))
            st.caption("Overlays: Polygon safety zones (alpha-blended), ByteTrack bounding boxes, dwell timers, and telemetry banner.")
        else:
            raw_file = Path(selected_video)
            if raw_file.exists():
                st.markdown("#### 📺 Raw Scenario Footage")
                st.video(str(raw_file))
                st.caption("Click 'Run Safety Inference & Video Replay' to generate annotated telemetry overlays.")

# =============================================================================
# TAB 2: REAL-TIME EVENT LOG
# =============================================================================
with tab_events:
    st.markdown("### 🚨 Safety Event Lifecycle Register")
    st.caption("Persistent record of all spatial intrusion events, durations, and state transitions.")

    if events:
        event_rows = []
        for e in events:
            # Severity badge styling
            if e.current_severity == "CRITICAL":
                sev_badge = "CRITICAL 🔴"
            elif e.current_severity == "HIGH":
                sev_badge = "HIGH 🟠"
            elif e.current_severity == "MEDIUM":
                sev_badge = "MEDIUM 🟡"
            else:
                sev_badge = "LOW 🟢"

            # Status pill
            if e.status == "CONFIRMED":
                stat_badge = "CONFIRMED ⚠️"
            elif e.status == "ESCALATED":
                stat_badge = "ESCALATED 🚨"
            elif e.status == "RECOVERED":
                stat_badge = "RECOVERED 🛡️"
            else:
                stat_badge = e.status

            event_rows.append({
                "Event ID": e.event_id,
                "Track ID": f"TRK-{e.track_id}",
                "Class": e.rule_class.upper(),
                "Zone": e.zone_type,
                "Risk Level": sev_badge,
                "Crossing State": e.crossing_state,
                "Start Time": f"{e.start_time:.2f}s",
                "Unsafe Duration": f"{e.unsafe_duration:.2f}s",
                "Lifecycle Status": stat_badge,
                "Escalations": e.escalation_count,
                "Timestamp (UTC)": e.created_at[:19].replace("T", " "),
            })

        df_evt = pd.DataFrame(event_rows)
        st.dataframe(
            df_evt,
            use_container_width=True,
            column_config={
                "Event ID": st.column_config.TextColumn("Event ID", help="Unique event UUID"),
                "Unsafe Duration": st.column_config.TextColumn("Unsafe Dwell"),
            },
            hide_index=True,
        )
    else:
        st.info("No safety events logged yet. Execute a replay run above to generate events.")

# =============================================================================
# TAB 3: AUDITABLE ALERT STREAM
# =============================================================================
with tab_alerts:
    st.markdown("### 🔔 Dispatched Alert Audit Log")
    st.caption("Immutable record of operator advisories, acoustic alarms, and notification dispatches.")

    if alerts:
        alert_rows = []
        for a in alerts:
            alert_rows.append({
                "Alert ID": a.alert_id,
                "Parent Event": a.event_id,
                "Alert Type": a.alert_type,
                "Severity": a.severity,
                "Active Clock": f"{a.timestamp:.2f}s",
                "Message": a.message,
                "Dispatch Status": a.status,
                "UTC Timestamp": a.wall_clock_time[:19].replace("T", " "),
            })
        df_alt = pd.DataFrame(alert_rows)
        st.dataframe(df_alt, use_container_width=True, hide_index=True)
    else:
        st.info("No alerts generated yet.")

# =============================================================================
# TAB 4: FORENSICS & SNAPSHOT GALLERY
# =============================================================================
with tab_evidence:
    st.markdown("### 📸 Forensic Snapshot Evidence Gallery")
    st.caption("Evidence images automatically captured at the exact moment of hazard confirmation or escalation.")

    snap_dir = Path("data/snapshots")
    if snap_dir.exists():
        snapshots = sorted(list(snap_dir.glob("*.jpg")), key=lambda p: p.stat().st_mtime, reverse=True)
        if snapshots:
            cols = st.columns(3)
            for idx, snap_path in enumerate(snapshots[:12]):
                with cols[idx % 3]:
                    img = Image.open(snap_path)
                    st.image(img, caption=snap_path.name, use_container_width=True)
                    st.download_button(
                        label=f"⬇️ Download {snap_path.name}",
                        data=snap_path.read_bytes(),
                        file_name=snap_path.name,
                        mime="image/jpeg",
                        key=f"dl_{idx}",
                        use_container_width=True,
                    )
        else:
            st.info("No snapshots captured in data/snapshots yet.")
    else:
        st.info("Snapshots directory empty.")

# =============================================================================
# TAB 5: ZONE GEOMETRY & V3.1 MATRIX
# =============================================================================
with tab_matrix:
    st.markdown("### 🗺️ Crossing Geometry & V3.1 Severity Matrix Rules")
    col_geom, col_rules = st.columns([1, 1])

    with col_geom:
        st.markdown("#### Configured Safety Zones")
        for z in config.zones.zones:
            with st.expander(f"📍 {z.name} (`{z.zone_type.value}`)", expanded=True):
                st.write(f"**Criticality Tier:** {z.criticality} (Tier 1 = Maximum Risk)")
                st.write(f"**Description:** {z.description}")
                st.write(f"**Polygon Vertices:** `{z.polygon}`")

    with col_rules:
        st.markdown("#### V3.1 Severity Matrix (All 64 Rule Combinations)")
        rule_data = [
            {
                "Crossing State": r.crossing_state.value,
                "Zone Type": r.zone_type.value,
                "Rule Class": r.rule_class.value,
                "Severity": r.severity.value,
            }
            for r in config.severity_matrix.rules
        ]
        st.dataframe(pd.DataFrame(rule_data), use_container_width=True, height=450, hide_index=True)

# =============================================================================
# TAB 6: EDGE-PROXY & BENCHMARKS
# =============================================================================
with tab_edge:
    st.markdown("### ⚙️ Multi-Target Edge Benchmarks")
    st.caption("Empirical latency and throughput benchmarking conducted on Apple Silicon M2 host hardware.")

    bench_json = Path("experiments/EXP-001/benchmark.json")
    if bench_json.exists():
        import json
        with open(bench_json, "r") as f:
            bench_data = json.load(f)

        b_rows = []
        for k, v in bench_data.items():
            if isinstance(v, dict):
                b_rows.append({
                    "Target Device": v.get("target", k),
                    "Mean Latency (ms)": v.get("mean_ms"),
                    "P50 Latency (ms)": v.get("p50_ms"),
                    "P95 Latency (ms)": v.get("p95_ms"),
                    "Throughput (FPS)": v.get("fps"),
                    "Classification": v.get("classification", "Host Local"),
                })
        st.dataframe(pd.DataFrame(b_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Run `python scripts/run_benchmark.py` to generate hardware benchmarks.")
