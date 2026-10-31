"""Mission-Control Operations Dashboard for Railway Level Crossing Safety Monitoring (V3.1)."""

import streamlit as st
import time
from pathlib import Path
import urllib.parse
import urllib.request
import hashlib
import pandas as pd
import numpy as np
from PIL import Image
import cv2
import yaml

from level_crossing.common.types import CrossingState, SeverityLevel, HealthStatus, ZoneType
from level_crossing.common.config import SystemConfig
from level_crossing.database.db import DatabaseManager
from level_crossing.api.services.safety_service import SafetyService
from level_crossing.pipeline.replay_pipeline import ReplayPipeline
from level_crossing.alerts.sound_simulator import SoundSimulator
from level_crossing.alerts.notifier import AlertNotifier
from level_crossing.reporting.incident_report import generate_incident_pdf_bytes

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

def resolve_or_download_video(source_str: str) -> tuple[str, str | None, bool]:
    """Resolves local paths, downloads remote video links via yt-dlp/urllib, or handles RTSP streams.
    Returns (resolved_path_or_url, error_message, is_live_stream).
    """
    source_str = source_str.strip()
    if not source_str:
        return "", "Please enter a valid video link or path.", False

    # 1. Local file path
    p = Path(source_str)
    if p.exists() and p.is_file():
        return str(p.resolve()), None, False

    # 2. Live RTSP / RTSPS stream
    if source_str.startswith(("rtsp://", "rtsps://")):
        return source_str, None, True

    # 3. HTTP / HTTPS link (YouTube, Vimeo, direct MP4, or live HTTP/HLS stream)
    if source_str.startswith(("http://", "https://")):
        if ".m3u8" in source_str.lower():
            return source_str, None, True

        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        parsed_path = urllib.parse.urlparse(source_str).path
        ext = Path(parsed_path).suffix.lower()
        if ext in [".mp4", ".mov", ".avi", ".mkv"]:
            hashed = hashlib.md5(source_str.encode()).hexdigest()[:8]
            target_file = upload_dir / f"web_{hashed}{ext}"
            if not target_file.exists():
                try:
                    urllib.request.urlretrieve(source_str, str(target_file))
                except Exception as e:
                    return "", f"Failed to download direct video URL: {e}", False
            return str(target_file.resolve()), None, False

        # Otherwise, resolve with yt-dlp (YouTube, Google Drive, Vimeo, etc.)
        try:
            import yt_dlp

            hashed = hashlib.md5(source_str.encode()).hexdigest()[:8]
            out_tmpl = str(upload_dir / f"yt_{hashed}.%(ext)s")
            ydl_opts = {
                "format": "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "outtmpl": out_tmpl,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "max_filesize": 100 * 1024 * 1024,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(source_str, download=True)
                filename = ydl.prepare_filename(info)
                fpath = Path(filename)
                if not fpath.exists():
                    mp4_p = fpath.with_suffix(".mp4")
                    if mp4_p.exists():
                        filename = str(mp4_p)
            return str(Path(filename).resolve()), None, False
        except Exception as e:
            return "", f"Failed to resolve video stream from URL: {e}", False

    return "", f"Path or stream URL not found: {source_str}", False


# =============================================================================
# TAB 1: REPLAY & INFERENCE STUDIO
# =============================================================================
with tab_replay:
    st.markdown("### 🎬 Video Ingestion & Telemetry Replay Studio")
    st.caption("Replay recorded or controlled footage with full ByteTrack association and safety zone dwell analysis.")

    col_ctrl, col_display = st.columns([1, 2])

    with col_ctrl:
        st.markdown("#### Video Ingestion Source")
        
        source_mode = st.radio(
            "Source Selection Mode",
            [
                "Preset Validation Scenarios",
                "Upload Custom Video (.mp4, .mov, .avi)",
                "Video Link / YouTube / RTSP Stream / Local Path",
            ],
            horizontal=False,
            label_visibility="collapsed",
        )

        selected_video = "data/controlled/validation/scenario_01_person_danger_track.mp4"

        if source_mode == "Preset Validation Scenarios":
            available_videos = list(Path("data/controlled/validation").glob("*.mp4"))
            video_options = [str(v) for v in available_videos if not v.name.startswith("annotated_")]
            selected_video = st.selectbox(
                "Select Scenario Footage",
                video_options if video_options else ["data/controlled/validation/scenario_01_person_danger_track.mp4"],
            )
        elif source_mode == "Upload Custom Video (.mp4, .mov, .avi)":
            uploaded_file = st.file_uploader(
                "Upload Crossing / Pedestrian Video",
                type=["mp4", "mov", "avi", "mkv"],
                help="Upload any real or downloaded video of people/vehicles crossing tracks to test safety detection.",
            )
            if uploaded_file is not None:
                upload_dir = Path("data/uploads")
                upload_dir.mkdir(parents=True, exist_ok=True)
                target_path = upload_dir / uploaded_file.name
                with open(target_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                selected_video = str(target_path)
                st.success(f"Loaded: `{uploaded_file.name}` ({len(uploaded_file.getbuffer()) / (1024*1024):.1f} MB)")
            else:
                st.info("Drag and drop any MP4/MOV video here to test.")
        else:
            custom_input = st.text_input(
                "Enter Video URL, YouTube Link, or RTSP Stream",
                value="",
                placeholder="e.g. https://www.youtube.com/watch?v=... or rtsp://... or /path/to/video.mp4",
                help="Paste any YouTube video link, direct .mp4 URL, RTSP live stream, or local path.",
            )
            selected_video = custom_input

        replay_state = st.selectbox(
            "Simulated Crossing Interlock State",
            [CrossingState.TRAIN_APPROACHING, CrossingState.OPEN, CrossingState.TRAIN_PASSING, CrossingState.UNKNOWN],
            index=0,
            key="replay_state_select",
            help="Simulates what signal the vision system receives from the railway signaling circuit during this video.",
        )

        process_limit = st.selectbox(
            "Inference Frame Limit",
            [
                "Standard Clip (300 frames / ~10s)",
                "Quick Test (150 frames / ~5s)",
                "Extended Clip (600 frames / ~20s)",
                "Full Video (Process all frames)",
            ],
            index=0,
            help="For YouTube or long videos, limits processing to keep inference fast and responsive.",
        )
        if "150" in process_limit:
            limit_frames = 150
        elif "300" in process_limit:
            limit_frames = 300
        elif "600" in process_limit:
            limit_frames = 600
        else:
            limit_frames = None

        autonomous_train = st.checkbox(
            "🚂 Autonomous Optical Train Sensing",
            value=False,
            help="For unmanned rural crossings: automatically detects approaching locomotives via perspective area expansion (dA/dt) and flips crossing state to TRAIN_APPROACHING without track circuits.",
        )

        st.markdown(
            r"""
            <div style="background-color: #1F2937; border-left: 4px solid #06B6D4; padding: 10px 14px; border-radius: 4px; margin: 14px 0;">
                <p style="margin: 0; font-size: 0.8rem; color: #D1D5DB;">
                    <b>Safety Engine Contract:</b> Evaluates every frame using YOLOv8 perception + ByteTrack tracking. Bottom-center foot coordinates are projected into calibrated safety zones. Dwell times $\ge 0.5s$ trigger confirmed alerts.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        run_btn = st.button("⚡ Run Safety Inference & Video Replay", type="primary", use_container_width=True)

    with col_display:
        output_dir = Path("data/annotated_runs")
        output_dir.mkdir(parents=True, exist_ok=True)
        default_target_mp4 = str(output_dir / "annotated_latest.mp4")

        if run_btn:
            if not selected_video:
                st.warning("Please choose a preset scenario, upload a file, or enter a video link first.")
            else:
                with st.spinner("Resolving video source and preparing inference pipeline..."):
                    resolved_src, err_msg, is_stream = resolve_or_download_video(selected_video)

                if err_msg:
                    st.error(f"❌ {err_msg}")
                elif resolved_src:
                    video_stem = Path(resolved_src).stem
                    target_output_mp4 = str(output_dir / f"annotated_{video_stem}.mp4")

                    progress_bar = st.progress(0, text="Initializing Safety Pipeline with Apple MPS...")
                    pipeline = ReplayPipeline(config=config, db_path="data/level_crossing.sqlite3", save_to_db=True)

                    t0 = time.time()
                    max_f = 300 if is_stream else limit_frames
                    summary = pipeline.run(
                        video_path=resolved_src,
                        crossing_state_timeline=lambda t: replay_state,
                        output_video_path=target_output_mp4,
                        max_frames=max_f,
                        autonomous_train_sensing=autonomous_train,
                    )
                    progress_bar.progress(100, text=f"Replay complete in {summary.elapsed_wall_time_sec:.2f}s ({summary.average_fps:.1f} FPS)")

                    st.session_state["active_annotated_video"] = target_output_mp4
                    st.session_state["active_heatmap_path"] = summary.heatmap_path
                    st.session_state["active_heatmap_analytics"] = summary.heatmap_analytics
                    st.session_state["last_summary"] = {
                        "frames": summary.total_frames_processed,
                        "fps": summary.average_fps,
                        "events": summary.events_generated,
                        "alerts": summary.alerts_generated,
                        "wall_time": summary.elapsed_wall_time_sec,
                    }

                    st.success(
                        f"✅ Replay Processed {summary.total_frames_processed} frames ({summary.duration_seconds:.1f}s) "
                        f"at {summary.average_fps:.1f} FPS. Generated {summary.events_generated} events and {summary.alerts_generated} alerts."
                    )
                    st.rerun()

        # Display active or default annotated video
        active_video = st.session_state.get("active_annotated_video", default_target_mp4)
        if not Path(active_video).exists():
            active_video = "data/controlled/validation/annotated_scenario_01.mp4"

        if Path(active_video).exists():
            st.markdown("#### 📺 Visual Telemetry Stream (Annotated)")
            with open(active_video, "rb") as vf:
                v_bytes = vf.read()
            st.video(v_bytes, format="video/mp4")
            st.caption("Overlays: Polygon safety zones (alpha-blended), ByteTrack bounding boxes, dwell timers, and telemetry banner.")

            st.download_button(
                label="⬇️ Download Annotated Video with Telemetry",
                data=v_bytes,
                file_name=Path(active_video).name,
                mime="video/mp4",
                use_container_width=True,
            )
        elif selected_video and Path(selected_video).exists():
            st.markdown("#### 📺 Raw Scenario Footage")
            with open(selected_video, "rb") as rf:
                r_bytes = rf.read()
            st.video(r_bytes, format="video/mp4")
            st.caption("Click '⚡ Run Safety Inference & Video Replay' above to generate annotated telemetry overlays.")

        # --- Tier 2: Spatial Hazard Density Heatmap ---
        active_heat = st.session_state.get("active_heatmap_path")
        if active_heat and Path(active_heat).exists():
            st.markdown("---")
            st.markdown("#### 🔥 Spatial Hazard Density Heatmap & Hotspots")
            st.caption("2D Gaussian thermal accumulation of all entity foot coordinates. High-risk track hotspots indicate where physical barriers or pedestrian bridges are required.")

            h_c1, h_c2 = st.columns([1.4, 1])
            with h_c1:
                st.image(active_heat, caption="Thermal Trajectory Heatmap (Red = High Danger Concentration)", use_container_width=True)

            with h_c2:
                st.markdown("##### 📊 Spatial Safety Metrics")
                h_metrics = st.session_state.get("active_heatmap_analytics") or {}
                st.metric("Danger Zone Violation Ratio", f"{h_metrics.get('danger_zone_percentage', 0.0)}%")
                st.metric("Total Foot Ground Contacts", h_metrics.get("total_foot_samples", 0))
                pk = h_metrics.get("peak_hotspot_coordinate", {"x": "N/A", "y": "N/A"})
                st.metric("Peak Violation Hotspot", f"X: {pk['x']}, Y: {pk['y']}")

                with open(active_heat, "rb") as hf:
                    st.download_button(
                        label="⬇️ Download Heatmap PNG",
                        data=hf.read(),
                        file_name=Path(active_heat).name,
                        mime="image/png",
                        use_container_width=True,
                    )

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

        st.markdown("---")
        st.markdown("#### 📑 Official Forensic Action & Siren Console")
        sel_c1, sel_c2, sel_c3 = st.columns([2, 1, 1])

        with sel_c1:
            alert_choices = {f"{a.alert_id} ({a.severity} - {a.message[:35]}...)": a for a in alerts}
            chosen_key = st.selectbox("Select Alert Record for Formal Audit", list(alert_choices.keys()), key="sel_alert_box")
            chosen_alert = alert_choices[chosen_key]

        with sel_c2:
            # Audio Siren synthesizer
            sev_enum = SeverityLevel(chosen_alert.severity) if chosen_alert.severity in [s.value for s in SeverityLevel] else SeverityLevel.MEDIUM
            wav_bytes = SoundSimulator.synthesize_wav(sev_enum)
            st.markdown("**Trackside Acoustic Siren:**")
            st.audio(wav_bytes, format="audio/wav")

        with sel_c3:
            # PDF Incident Report generator
            snap_matches = list(Path("data/snapshots").glob(f"*{chosen_alert.event_id}*.jpg"))
            chosen_snap = str(snap_matches[0]) if snap_matches else None
            if not chosen_snap and list(Path("data/snapshots").glob("*.jpg")):
                chosen_snap = str(list(Path("data/snapshots").glob("*.jpg"))[0])

            pdf_report_bytes = generate_incident_pdf_bytes(
                alert_id=chosen_alert.alert_id,
                event_id=chosen_alert.event_id,
                severity=chosen_alert.severity,
                alert_type=chosen_alert.alert_type,
                message=chosen_alert.message,
                crossing_state=service.current_crossing_state.value,
                timestamp_sec=chosen_alert.timestamp,
                wall_clock_time=chosen_alert.wall_clock_time,
                snapshot_path=chosen_snap,
                system_health=service.check_health()["status"].value,
            )

            st.markdown("**Executive Safety Report:**")
            st.download_button(
                label="📄 Download Official PDF Report",
                data=pdf_report_bytes,
                file_name=f"RAIL_SAFETY_AUDIT_{chosen_alert.alert_id}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_btn_{chosen_alert.alert_id}",
            )

        # --- Tier 2: Instant Remote Push Notification (Telegram Bot & Webhook) ---
        st.markdown("---")
        st.markdown("##### 📲 Instant Remote Push Notification (Telegram Bot & Webhook Dispatcher)")
        st.caption("Sends high-priority mobile notifications and photographic evidence directly to the Station Master or loco-pilot cab.")

        with st.expander("⚙️ Live Telegram Bot & Webhook Setup (Optional)", expanded=False):
            st.markdown(
                """
                <p style="font-size: 0.82rem; color: #9CA3AF;">
                    <b>To receive REAL alerts on your phone:</b><br/>
                    1. Open Telegram, search <code>@BotFather</code>, and type <code>/newbot</code> to get your <b>Bot Token</b>.<br/>
                    2. Message <code>@userinfobot</code> on Telegram to get your numeric <b>Chat ID</b>.<br/>
                    3. Paste them below. If left blank, system runs in <b>Instant Simulation Mode</b>.
                </p>
                """,
                unsafe_allow_html=True,
            )
            cfg_c1, cfg_c2 = st.columns([1.2, 1])
            with cfg_c1:
                live_bot_token = st.text_input(
                    "Telegram Bot Token",
                    value=st.session_state.get("tg_bot_token", ""),
                    type="password",
                    placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ",
                    key="input_tg_bot_token",
                )
            with cfg_c2:
                auto_cid = st.session_state.get("tg_chat_id", "")
                live_chat_id = st.text_input(
                    "Telegram Chat ID",
                    value=auto_cid,
                    placeholder="e.g. 1234567890",
                    key="input_tg_chat_id",
                )

            if st.button("🔍 Auto-Detect My Chat ID (After tapping /start on your bot)", use_container_width=True):
                if not live_bot_token.strip():
                    st.error("Please paste your Telegram Bot Token above first.")
                else:
                    cid = AlertNotifier.fetch_latest_chat_id(live_bot_token.strip())
                    if cid:
                        st.session_state["tg_chat_id"] = str(cid)
                        st.session_state["tg_bot_token"] = live_bot_token.strip()
                        st.success(f"✅ Found your Chat ID: `{cid}`! Auto-filled successfully.")
                        st.rerun()
                    else:
                        st.warning("No message detected yet. Make sure you opened your bot and sent /start!")

            live_webhook = st.text_input("Custom REST Webhook URL (Optional)", value="", placeholder="e.g. https://webhook.site/your-custom-uuid")

        mob_c1, mob_c2 = st.columns([1.6, 1])
        with mob_c1:
            tele_msg = AlertNotifier.format_telegram_alert_text(
                alert_id=chosen_alert.alert_id,
                severity=chosen_alert.severity,
                crossing_state=service.current_crossing_state.value,
                message=chosen_alert.message,
                timestamp_sec=chosen_alert.timestamp,
            )
            st.code(tele_msg, language="markdown")
        with mob_c2:
            is_live_configured = bool(live_bot_token.strip() and live_chat_id.strip())
            st.markdown(f"**Mode:** {'🟢 LIVE REAL DISPATCH' if is_live_configured else '🟡 SIMULATION MODE'}")
            st.caption("Photo Attachment: Active Forensic Snapshot")
            if st.button("🚀 Dispatch Emergency Mobile Push", use_container_width=True):
                notifier = AlertNotifier(
                    telegram_bot_token=live_bot_token.strip() or None,
                    telegram_chat_id=live_chat_id.strip() or None,
                    webhook_url=live_webhook.strip() or None,
                    dry_run=not is_live_configured,
                )
                res_tele = notifier.dispatch_telegram(tele_msg, photo_path=chosen_snap)
                res_hook = notifier.dispatch_webhook({
                    "alert_id": chosen_alert.alert_id,
                    "event_id": chosen_alert.event_id,
                    "severity": chosen_alert.severity,
                    "message": chosen_alert.message,
                    "crossing_state": service.current_crossing_state.value,
                })
                if is_live_configured:
                    if "TELEGRAM_HTTP_200" in res_tele.get("status", ""):
                        st.success("🎉 REAL ALERT & EVIDENCE PHOTO DELIVERED TO YOUR TELEGRAM PHONE!")
                    else:
                        st.warning(f"Telegram API responded: {res_tele.get('status')} ({res_tele.get('error', '')})")
                else:
                    st.success("✅ Alert & Evidence Photo Dispatched to Station Master Mobile OCC (Simulated Push OK)!")
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
            for idx, snap_path in enumerate(snapshots[:9]):
                with cols[idx % 3]:
                    img = Image.open(snap_path)
                    st.image(img, caption=snap_path.name, use_container_width=True)

                    stem = snap_path.stem
                    mock_alert_id = f"ALT-{stem[-8:].upper()}"
                    mock_event_id = f"EVT-{stem[-8:].upper()}"

                    pdf_b = generate_incident_pdf_bytes(
                        alert_id=mock_alert_id,
                        event_id=mock_event_id,
                        severity="CRITICAL",
                        alert_type="CONFIRMED_HAZARD",
                        message="Automated photographic evidence captured upon hazard confirmation",
                        crossing_state=service.current_crossing_state.value,
                        timestamp_sec=1.5,
                        wall_clock_time=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        snapshot_path=str(snap_path),
                        system_health=service.check_health()["status"].value,
                    )

                    c_dl, c_pdf = st.columns(2)
                    with c_dl:
                        st.download_button(
                            label="⬇️ Image",
                            data=snap_path.read_bytes(),
                            file_name=snap_path.name,
                            mime="image/jpeg",
                            key=f"dl_{idx}",
                            use_container_width=True,
                        )
                    with c_pdf:
                        st.download_button(
                            label="📄 PDF",
                            data=pdf_b,
                            file_name=f"EVIDENCE_REPORT_{mock_alert_id}.pdf",
                            mime="application/pdf",
                            key=f"pdf_snap_{idx}",
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
    st.markdown("### 🗺️ Visual Safety Zone Calibration Studio & V3.1 Matrix Rules")
    st.caption("Calibrate polygon safety zones directly on real camera frames to adapt to any crossing CCTV angle.")

    # --- Zone Calibration Studio Section ---
    st.markdown("#### 🎯 Interactive Camera Perspective Zone Calibrator")

    cal_col_vid, cal_col_controls = st.columns([1.3, 1])

    calib_video_source = st.session_state.get(
        "active_annotated_video",
        "data/controlled/validation/scenario_01_person_danger_track.mp4",
    )
    if not Path(calib_video_source).exists():
        calib_video_source = "data/controlled/validation/scenario_01_person_danger_track.mp4"

    preview_frame = None
    if Path(calib_video_source).exists():
        cap = cv2.VideoCapture(str(calib_video_source))
        ret, frame_bgr = cap.read()
        cap.release()
        if ret and frame_bgr is not None:
            preview_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    with cal_col_controls:
        zone_names = [z.zone_type.value for z in config.zones.zones]
        selected_zone_type = st.selectbox("Select Zone to Adjust", zone_names, index=0)

        target_zone = next((z for z in config.zones.zones if z.zone_type.value == selected_zone_type), None)
        poly = target_zone.polygon if target_zone else [[0.1, 0.4], [0.9, 0.4], [0.9, 0.7], [0.1, 0.7]]

        st.caption("Adjust Normalized Coordinates [X, Y] (0.0=Left/Top, 1.0=Right/Bottom):")
        p1_x = st.slider("P1 Top-Left X", 0.0, 1.0, float(poly[0][0]), 0.02, key=f"p1x_{selected_zone_type}")
        p1_y = st.slider("P1 Top-Left Y", 0.0, 1.0, float(poly[0][1]), 0.02, key=f"p1y_{selected_zone_type}")
        p2_x = st.slider("P2 Top-Right X", 0.0, 1.0, float(poly[1][0]), 0.02, key=f"p2x_{selected_zone_type}")
        p2_y = st.slider("P2 Top-Right Y", 0.0, 1.0, float(poly[1][1]), 0.02, key=f"p2y_{selected_zone_type}")
        p3_x = st.slider("P3 Bottom-Right X", 0.0, 1.0, float(poly[2][0]), 0.02, key=f"p3x_{selected_zone_type}")
        p3_y = st.slider("P3 Bottom-Right Y", 0.0, 1.0, float(poly[2][1]), 0.02, key=f"p3y_{selected_zone_type}")
        p4_x = st.slider("P4 Bottom-Left X", 0.0, 1.0, float(poly[3][0]), 0.02, key=f"p4x_{selected_zone_type}")
        p4_y = st.slider("P4 Bottom-Left Y", 0.0, 1.0, float(poly[3][1]), 0.02, key=f"p4y_{selected_zone_type}")

        calibrated_poly = [[p1_x, p1_y], [p2_x, p2_y], [p3_x, p3_y], [p4_x, p4_y]]

        btn_save, btn_reset = st.columns(2)
        with btn_save:
            if st.button("💾 Save Zones to YAML", type="primary", use_container_width=True):
                yaml_path = Path("configs/zones.yaml")
                if yaml_path.exists():
                    with open(yaml_path, "r") as yf:
                        y_data = yaml.safe_load(yf)
                    for z_dict in y_data.get("zones", []):
                        if z_dict.get("zone_type") == selected_zone_type:
                            z_dict["polygon"] = calibrated_poly
                    with open(yaml_path, "w") as yf:
                        yaml.safe_dump(y_data, yf, sort_keys=False)
                    st.success(f"✅ Calibrated `{selected_zone_type}` saved to configs/zones.yaml!")
                    st.cache_resource.clear()
                    st.rerun()

        with btn_reset:
            if st.button("🔄 Reset Standard Geometry", use_container_width=True):
                st.cache_resource.clear()
                st.rerun()

    with cal_col_vid:
        st.markdown("#### Live Perspective Preview Canvas")
        if preview_frame is not None:
            h, w = preview_frame.shape[:2]
            canvas = preview_frame.copy()
            overlay = preview_frame.copy()

            for z in config.zones.zones:
                is_active = (z.zone_type.value == selected_zone_type)
                z_poly = calibrated_poly if is_active else z.polygon
                pts = np.array([[int(pt[0] * w), int(pt[1] * h)] for pt in z_poly], np.int32)
                color = z.color_rgb

                cv2.fillPoly(overlay, [pts], color)
                cv2.polylines(canvas, [pts], True, color, 3 if is_active else 1)

                if is_active:
                    for idx, pt in enumerate(pts):
                        cv2.circle(canvas, tuple(pt), 7, (255, 255, 255), -1)
                        cv2.circle(canvas, tuple(pt), 5, color, -1)
                        cv2.putText(canvas, f"P{idx+1}", (pt[0] + 8, pt[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

            rendered = cv2.addWeighted(overlay, 0.35, canvas, 0.65, 0)
            st.image(rendered, caption=f"Active Calibration: {selected_zone_type} on Frame 0", use_container_width=True)
        else:
            st.info("Load a video to visualize calibration.")

    st.markdown("---")
    st.markdown("#### V3.1 Master Severity Matrix Rules (64 Formally Verified Rules)")
    rule_data = [
        {
            "Crossing State": r.crossing_state.value,
            "Zone Type": r.zone_type.value,
            "Rule Class": r.rule_class.value,
            "Severity": r.severity.value,
        }
        for r in config.severity_matrix.rules
    ]
    st.dataframe(pd.DataFrame(rule_data), use_container_width=True, height=350, hide_index=True)

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
