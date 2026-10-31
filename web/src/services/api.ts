import {
  SystemOverview,
  SafetyEvent,
  AlertRecord,
  CameraInfo,
  TelegramStatus,
  DetailedHealth,
  ScenarioInfo,
} from '../types';

const API_BASE = '/api/v1';

// Sample demo events for DEMO MODE (clearly labeled)
export const DEMO_EVENTS: SafetyEvent[] = [
  {
    event_id: 'EVT-DEMO-001',
    track_id: 12,
    rule_class: 'person',
    zone_type: 'DANGER_TRACK',
    initial_severity: 'MEDIUM',
    current_severity: 'CRITICAL',
    crossing_state: 'TRAIN_APPROACHING',
    start_time: 1.45,
    end_time: null,
    status: 'CONFIRMED',
    unsafe_duration: 3.2,
    escalation_count: 1,
    created_at: new Date().toISOString(),
    confidence: 0.965,
  },
  {
    event_id: 'EVT-DEMO-002',
    track_id: 15,
    rule_class: 'person',
    zone_type: 'CAUTION_APPROACH',
    initial_severity: 'MEDIUM',
    current_severity: 'HIGH',
    crossing_state: 'OPEN',
    start_time: 4.8,
    end_time: null,
    status: 'CONFIRMED',
    unsafe_duration: 1.8,
    escalation_count: 0,
    created_at: new Date(Date.now() - 45000).toISOString(),
    confidence: 0.942,
  },
  {
    event_id: 'EVT-DEMO-003',
    track_id: 8,
    rule_class: 'truck',
    zone_type: 'STALL_HAZARD',
    initial_severity: 'HIGH',
    current_severity: 'CRITICAL',
    crossing_state: 'CLOSED',
    start_time: 8.2,
    end_time: 14.5,
    status: 'RECOVERED',
    unsafe_duration: 6.3,
    escalation_count: 1,
    created_at: new Date(Date.now() - 120000).toISOString(),
    confidence: 0.981,
  },
];

export const DEMO_OVERVIEW: SystemOverview = {
  system_status: 'OPERATIONAL (DEMO)',
  operational: true,
  active_cameras: 1,
  total_cameras: 1,
  active_intrusions: 2,
  total_alerts: 4,
  total_events: 3,
  telegram_status: 'CONNECTED',
  crossing_state: 'TRAIN_APPROACHING',
  location: 'LC-102 (DEMO SIMULATION)',
};

export const api = {
  async getOverview(isDemo = false): Promise<SystemOverview> {
    if (isDemo) return DEMO_OVERVIEW;
    const res = await fetch(`${API_BASE}/system/overview`);
    if (!res.ok) throw new Error('Failed to fetch system overview');
    return res.json();
  },

  async getCameras(isDemo = false): Promise<CameraInfo[]> {
    if (isDemo) {
      return [
        {
          id: 'CAM-DEMO-01',
          name: 'Trackside Downline Camera (LC-102 DEMO)',
          location: 'LC-102 (Track KM 142/8)',
          status: 'ONLINE',
          resolution: '1920x1080 @ 30FPS',
          lens: 'Wide-Angle HDR Low-Light Sensor',
          stream_url: '/api/v1/videos/stream/annotated_scenario_01.mp4',
          active_tracks_count: 2,
        },
      ];
    }
    const res = await fetch(`${API_BASE}/system/cameras`);
    if (!res.ok) throw new Error('Failed to fetch cameras');
    return res.json();
  },

  async getEvents(limit = 50, isDemo = false): Promise<SafetyEvent[]> {
    if (isDemo) return DEMO_EVENTS;
    const res = await fetch(`${API_BASE}/events?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch events');
    return res.json();
  },

  async getEventDetail(eventId: string, isDemo = false): Promise<any> {
    if (isDemo) {
      const found = DEMO_EVENTS.find((e) => e.event_id === eventId) || DEMO_EVENTS[0];
      return { ...found, alerts: [] };
    }
    const res = await fetch(`${API_BASE}/events/${eventId}`);
    if (!res.ok) throw new Error(`Failed to fetch event ${eventId}`);
    return res.json();
  },

  async getAlerts(limit = 50, isDemo = false): Promise<AlertRecord[]> {
    if (isDemo) {
      return [
        {
          alert_id: 'ALT-DEMO-01',
          event_id: 'EVT-DEMO-001',
          alert_type: 'INITIAL',
          severity: 'CRITICAL',
          timestamp: 1.45,
          wall_clock_time: new Date().toISOString(),
          status: 'DISPATCHED',
          message: 'Confirmed intrusion: person in DANGER_TRACK (Severity: CRITICAL)',
        },
        {
          alert_id: 'ALT-DEMO-02',
          event_id: 'EVT-DEMO-001',
          alert_type: 'ESCALATION',
          severity: 'CRITICAL',
          timestamp: 3.2,
          wall_clock_time: new Date().toISOString(),
          status: 'DISPATCHED',
          message: 'Escalated hazard: person persists in DANGER_TRACK (Dwell: 3.2s)',
        },
      ];
    }
    const res = await fetch(`${API_BASE}/alerts?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch alerts');
    return res.json();
  },

  async getTelegramStatus(isDemo = false): Promise<TelegramStatus> {
    if (isDemo) {
      return {
        configured: true,
        bot_username: '@MyRailwaySafety_bot',
        target_chat_id: '1295***495',
        location: 'LC-102 (DEMO)',
        delivery_mode: 'DEMO_SIMULATION',
        total_dispatched: 11,
        total_failed: 0,
        total_suppressed: 4,
        latest_evidence_snapshot: 'EVT-C06BEF61_INITIAL_900.jpg',
      };
    }
    const res = await fetch(`${API_BASE}/telegram/status`);
    if (!res.ok) throw new Error('Failed to fetch Telegram status');
    return res.json();
  },

  async sendTestTelegramAlert(): Promise<any> {
    const res = await fetch(`${API_BASE}/telegram/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Network failure' }));
      throw new Error(err.detail || 'Test alert failed');
    }
    return res.json();
  },

  async getDetailedHealth(isDemo = false): Promise<DetailedHealth> {
    if (isDemo) {
      return {
        overall_status: 'HEALTHY',
        crossing_state: 'TRAIN_APPROACHING',
        subsystems: {
          yolo_detector: { name: 'YOLOv8 Perceptual Engine', status: 'OPERATIONAL', weights: 'yolov8n.pt', device: 'Apple MPS', latency_ms: 18.2 },
          bytetrack_tracker: { name: 'ByteTrack Associator', status: 'OPERATIONAL', iou_threshold: 0.45 },
          cctv_stream: { name: 'CCTV Pipeline', status: 'OPERATIONAL', fps: 30.0 },
          sqlite_database: { name: 'SQLite3 Storage', status: 'OPERATIONAL', path: 'data/level_crossing.sqlite3' },
          telegram_dispatcher: { name: 'Telegram Dispatcher', status: 'OPERATIONAL', bot: '@MyRailwaySafety_bot' },
        },
      };
    }
    const res = await fetch(`${API_BASE}/system/health-detailed`);
    if (!res.ok) throw new Error('Failed to fetch detailed health');
    return res.json();
  },

  async getScenarios(): Promise<ScenarioInfo[]> {
    const res = await fetch(`${API_BASE}/videos/scenarios`);
    if (!res.ok) return [];
    return res.json();
  },

  async uploadCustomVideo(file: File): Promise<{ success: boolean; filename: string; path: string; size_mb: number; stream_url: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/videos/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async resolveVideoLink(url: string): Promise<{ success: boolean; resolved_path: string; filename: string; is_stream: boolean; stream_url: string; error?: string }> {
    const res = await fetch(`${API_BASE}/videos/resolve-link`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to resolve URL' }));
      throw new Error(err.detail || 'Resolution failed');
    }
    return res.json();
  },

  async executeInference(params: {
    video_source: string;
    crossing_state: string;
    max_frames: number | null;
    autonomous_train: boolean;
    enable_telegram: boolean;
  }): Promise<{
    success: boolean;
    total_frames_processed: number;
    duration_seconds: number;
    events_generated: number;
    alerts_generated: number;
    highest_severity_observed: string;
    average_fps: number;
    elapsed_wall_time_sec: number;
    annotated_video_url: string;
    heatmap_url?: string;
    heatmap_analytics?: {
      danger_zone_percentage: number;
      total_foot_samples: number;
      peak_hotspot_coordinate: { x: number; y: number };
    };
  }> {
    const res = await fetch(`${API_BASE}/videos/execute-inference`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Inference failed' }));
      throw new Error(err.detail || 'Inference execution failed');
    }
    return res.json();
  },

  async runScenarioReplay(videoPath: string, maxFrames = 300, enableTelegram = true): Promise<any> {
    const res = await fetch(`${API_BASE}/videos/run-replay`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        video_path: videoPath,
        max_frames: maxFrames,
        enable_telegram: enableTelegram,
      }),
    });
    if (!res.ok) throw new Error('Failed to trigger scenario run');
    return res.json();
  },

  async listEvidence(): Promise<Array<{ filename: string; url: string; size_bytes: number }>> {
    const res = await fetch(`${API_BASE}/evidence`);
    if (!res.ok) return [];
    return res.json();
  },
};
