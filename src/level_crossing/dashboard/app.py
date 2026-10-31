"""Interactive Streamlit dashboard for real-time monitoring and scenario inspection."""

import streamlit as st
import time
from pathlib import Path
import pandas as pd
from PIL import Image

from level_crossing.common.types import CrossingState, SeverityLevel, HealthStatus
from level_crossing.common.config import SystemConfig
from level_crossing.database.db import DatabaseManager
from level_crossing.api.services.safety_service import SafetyService

st.set_page_config(
    page_title="Railway Level Crossing Safety System",
    page_icon="🚦",
    layout="wide",
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

# ----------------------------------------------------
# Sidebar Controls & System Health
# ----------------------------------------------------
st.sidebar.title("🚦 System Control")

# Crossing state selector
selected_state = st.sidebar.selectbox(
    "Crossing Operational State",
    [CrossingState.OPEN, CrossingState.TRAIN_APPROACHING, CrossingState.TRAIN_PASSING, CrossingState.UNKNOWN],
    index=0,
)
service.set_crossing_state(selected_state)

health_data = service.check_health()
system_health = health_data["status"]

if system_health == HealthStatus.HEALTHY:
    st.sidebar.success(f"System Health: {system_health.value}")
elif system_health == HealthStatus.DEGRADED:
    st.sidebar.warning(f"System Health: {system_health.value} (Degraded Mode Active)")
else:
    st.sidebar.error(f"System Health: {system_health.value}")

st.sidebar.markdown("---")
st.sidebar.subheader("Monitored Safety Zones")
for z in config.zones.zones:
    st.sidebar.markdown(f"- **{z.name}** (`{z.zone_type.value}`)")

# ----------------------------------------------------
# Main Dashboard
# ----------------------------------------------------
st.title("🛡️ Level Crossing Safety Monitoring System")
st.caption("Automated Intruder Alerting via Edge Computer Vision (V3.1 Master Implementation Specification)")

# Top KPI Metric Cards
col1, col2, col3, col4 = st.columns(4)

events = service.list_events(limit=100)
alerts = service.list_alerts(limit=100)

confirmed_events = [e for e in events if e.status in ("CONFIRMED", "ESCALATED")]
critical_alerts = [a for a in alerts if a.severity == "CRITICAL"]

with col1:
    st.metric("Crossing State", selected_state.value)
with col2:
    st.metric("Total Events Detected", len(events))
with col3:
    st.metric("Confirmed Hazards", len(confirmed_events))
with col4:
    st.metric("Critical Alerts Emitted", len(critical_alerts))

st.markdown("---")

tab_events, tab_alerts, tab_snapshots, tab_zones = st.tabs(
    ["🚨 Active & Historical Events", "🔔 Alert Audit Trail", "📸 Evidence Snapshots", "🗺️ Safety Zones & Matrix"]
)

with tab_events:
    st.subheader("Event Lifecycle History")
    if events:
        events_data = [
            {
                "Event ID": e.event_id,
                "Track ID": e.track_id,
                "Class": e.rule_class,
                "Zone": e.zone_type,
                "Initial Risk": e.initial_severity,
                "Current Risk": e.current_severity,
                "Crossing State": e.crossing_state,
                "Start Time (s)": f"{e.start_time:.2f}",
                "Duration (s)": f"{e.unsafe_duration:.2f}",
                "Status": e.status,
                "Escalations": e.escalation_count,
            }
            for e in events
        ]
        df_events = pd.DataFrame(events_data)
        st.dataframe(df_events, use_container_width=True)
    else:
        st.info("No safety events logged yet. Run a replay scenario to populate records.")

with tab_alerts:
    st.subheader("Auditable Alerts Dispatched")
    if alerts:
        alerts_data = [
            {
                "Alert ID": a.alert_id,
                "Event ID": a.event_id,
                "Type": a.alert_type,
                "Severity": a.severity,
                "Timestamp (s)": f"{a.timestamp:.2f}",
                "Status": a.status,
                "Message": a.message,
                "Wall Clock (UTC)": a.wall_clock_time,
            }
            for a in alerts
        ]
        df_alerts = pd.DataFrame(alerts_data)
        st.dataframe(df_alerts, use_container_width=True)
    else:
        st.info("No alerts generated yet.")

with tab_snapshots:
    st.subheader("Visual Evidence Snapshots")
    snapshots_dir = Path("data/snapshots")
    if snapshots_dir.exists():
        snapshot_files = list(snapshots_dir.glob("*.jpg"))
        if snapshot_files:
            snap_cols = st.columns(3)
            for idx, snap_path in enumerate(snapshot_files[:9]):
                with snap_cols[idx % 3]:
                    st.image(str(snap_path), caption=snap_path.name, use_container_width=True)
        else:
            st.info("No snapshots captured yet.")
    else:
        st.info("Snapshots directory empty.")

with tab_zones:
    st.subheader("Zone Definitions & Severity Matrix Rules")
    col_z, col_m = st.columns([1, 1])
    with col_z:
        st.write("#### Defined Zones")
        for z in config.zones.zones:
            st.markdown(f"**{z.name}** (`{z.id}`)")
            st.write(f"- Type: `{z.zone_type.value}`")
            st.write(f"- Criticality: {z.criticality}")
            st.write(f"- Description: {z.description}")
    with col_m:
        st.write("#### Severity Rules (Total: 64 combinations)")
        st.write(f"Fallback Severity: `{config.severity_matrix.fallback_severity.value}`")
        matrix_data = [
            {
                "State": r.crossing_state.value,
                "Zone": r.zone_type.value,
                "Class": r.rule_class.value,
                "Severity": r.severity.value,
            }
            for r in config.severity_matrix.rules[:20]
        ]
        st.dataframe(pd.DataFrame(matrix_data), use_container_width=True)
