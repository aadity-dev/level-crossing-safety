"""V3.1 SQLite database schema and migration statements."""

V3_1_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS zones (
    zone_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    zone_type TEXT NOT NULL,
    description TEXT,
    polygon_json TEXT NOT NULL,
    criticality INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    track_id INTEGER NOT NULL,
    rule_class TEXT NOT NULL,
    zone_type TEXT NOT NULL,
    initial_severity TEXT NOT NULL,
    current_severity TEXT NOT NULL,
    crossing_state TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL,
    status TEXT NOT NULL,
    unsafe_duration REAL NOT NULL,
    escalation_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_track_id ON events (track_id);
CREATE INDEX IF NOT EXISTS idx_events_status ON events (status);
CREATE INDEX IF NOT EXISTS idx_events_start_time ON events (start_time);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    timestamp REAL NOT NULL,
    wall_clock_time TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    snapshot_path TEXT,
    FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alerts_event_id ON alerts (event_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts (severity);

CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    component TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    context_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_component ON system_logs (component);
"""
