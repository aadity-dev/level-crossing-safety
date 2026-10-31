export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'IGNORE';
export type CrossingState = 'OPEN' | 'TRAIN_APPROACHING' | 'CLOSED' | 'UNKNOWN';
export type EventStatus = 'PENDING' | 'CONFIRMED' | 'ESCALATED' | 'RECOVERED' | 'CLOSED';

export interface SystemOverview {
  system_status: string;
  operational: boolean;
  active_cameras: number;
  total_cameras: number;
  active_intrusions: number;
  total_alerts: number;
  total_events: number;
  telegram_status: 'CONNECTED' | 'DISCONNECTED';
  crossing_state: CrossingState;
  location: string;
}

export interface SafetyEvent {
  event_id: string;
  track_id: number;
  rule_class: string;
  zone_type: string;
  initial_severity: Severity;
  current_severity: Severity;
  crossing_state: CrossingState;
  start_time: number;
  end_time?: number | null;
  status: EventStatus;
  unsafe_duration: number;
  escalation_count: number;
  created_at: string;
  confidence?: number;
  evidence_url?: string;
}

export interface AlertRecord {
  alert_id: string;
  event_id: string;
  alert_type: string;
  severity: Severity;
  timestamp: number;
  wall_clock_time: string;
  status: string;
  message: string;
  snapshot_path?: string | null;
}

export interface CameraInfo {
  id: string;
  name: string;
  location: string;
  status: 'ONLINE' | 'OFFLINE';
  resolution: string;
  lens: string;
  stream_url: string;
  active_tracks_count: number;
}

export interface TelegramStatus {
  configured: boolean;
  bot_username: string;
  target_chat_id: string;
  location: string;
  delivery_mode: string;
  total_dispatched: number;
  total_failed: number;
  total_suppressed: number;
  latest_evidence_snapshot?: string | null;
}

export interface ScenarioInfo {
  id: string;
  title: string;
  description: string;
  path: string;
  annotated_path?: string;
  available: boolean;
  has_annotated: boolean;
  stream_url?: string | null;
}

export interface HealthSubsystem {
  name: string;
  status: 'OPERATIONAL' | 'DEGRADED' | 'FAILED' | 'UNCONFIGURED';
  [key: string]: any;
}

export interface DetailedHealth {
  overall_status: string;
  crossing_state: CrossingState;
  subsystems: {
    yolo_detector: HealthSubsystem;
    bytetrack_tracker: HealthSubsystem;
    cctv_stream: HealthSubsystem;
    sqlite_database: HealthSubsystem;
    telegram_dispatcher: HealthSubsystem;
  };
}
