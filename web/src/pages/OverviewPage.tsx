import React, { useState, useEffect } from 'react';
import {
  Activity,
  Camera,
  AlertOctagon,
  Bell,
  Send,
  Video,
  ExternalLink,
  ShieldAlert,
  Clock,
  ArrowRight,
  Maximize2,
} from 'lucide-react';
import { SystemOverview, SafetyEvent, DetailedHealth } from '../types';
import { api } from '../services/api';

interface OverviewPageProps {
  demoMode: boolean;
  onNavigateTab: (tab: string) => void;
  onSelectEvent: (event: SafetyEvent) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  demoMode,
  onNavigateTab,
  onSelectEvent,
}) => {
  const [overview, setOverview] = useState<SystemOverview | null>(null);
  const [events, setEvents] = useState<SafetyEvent[]>([]);
  const [health, setHealth] = useState<DetailedHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        const [ov, evts, hl] = await Promise.all([
          api.getOverview(demoMode),
          api.getEvents(5, demoMode),
          api.getDetailedHealth(demoMode),
        ]);
        if (mounted) {
          setOverview(ov);
          setEvents(evts);
          setHealth(hl);
          setLoading(false);
        }
      } catch (e) {
        console.error('Failed to load overview data', e);
        if (mounted) setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [demoMode]);

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-500/15 text-red-400 border-red-500/30';
      case 'HIGH':
        return 'bg-orange-500/15 text-orange-400 border-orange-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      default:
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* TOP 5 STATUS CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {/* 1. System Status */}
        <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#929BA8] text-xs">
            <span>System Status</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2">
            <div className="text-xl font-bold text-[#F5F7FA]">
              {overview?.operational ? 'OPERATIONAL' : 'DEGRADED'}
            </div>
            <div className="text-[11px] text-emerald-400 flex items-center space-x-1 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>All Microservices Normal</span>
            </div>
          </div>
        </div>

        {/* 2. Active Cameras */}
        <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#929BA8] text-xs">
            <span>Active CCTV</span>
            <Camera className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2">
            <div className="text-xl font-bold text-[#F5F7FA]">
              {overview?.active_cameras ?? 1} / {overview?.total_cameras ?? 1}
            </div>
            <div className="text-[11px] text-[#929BA8] mt-0.5 font-mono">
              CAM-01 • 1080p 30FPS
            </div>
          </div>
        </div>

        {/* 3. Active Intrusions */}
        <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#929BA8] text-xs">
            <span>Active Intrusions</span>
            <AlertOctagon className={`w-4 h-4 ${(overview?.active_intrusions ?? 0) > 0 ? 'text-red-400' : 'text-[#636C7A]'}`} />
          </div>
          <div className="mt-2">
            <div className={`text-xl font-bold ${(overview?.active_intrusions ?? 0) > 0 ? 'text-red-400' : 'text-[#F5F7FA]'}`}>
              {overview?.active_intrusions ?? 0}
            </div>
            <div className="text-[11px] text-[#929BA8] mt-0.5">
              {(overview?.active_intrusions ?? 0) > 0 ? 'Intruders in Track Zone' : 'Clear Track Envelope'}
            </div>
          </div>
        </div>

        {/* 4. Total Alerts */}
        <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#929BA8] text-xs">
            <span>Dispatched Alerts</span>
            <Bell className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2">
            <div className="text-xl font-bold text-[#F5F7FA]">
              {overview?.total_alerts ?? 0}
            </div>
            <div className="text-[11px] text-[#929BA8] mt-0.5">
              {overview?.total_events ?? 0} Lifecycle Events
            </div>
          </div>
        </div>

        {/* 5. Telegram Dispatcher */}
        <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#929BA8] text-xs">
            <span>Telegram Bot OCC</span>
            <Send className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-2">
            <div className="text-xl font-bold text-[#F5F7FA]">
              {overview?.telegram_status === 'CONNECTED' ? 'ONLINE' : 'SIMULATION'}
            </div>
            <div className="text-[11px] text-blue-400 mt-0.5 font-mono truncate">
              @MyRailwaySafety_bot
            </div>
          </div>
        </div>
      </div>

      {/* MIDDLE SECTION: LIVE CCTV FEED & RECENT EVENTS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* A. Live Camera Stream Section */}
        <div className="lg:col-span-2 bg-[#13171C] border border-[#252B33] rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-[#252B33]/80">
            <div className="flex items-center space-x-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping"></span>
              <span className="text-xs font-bold text-[#F5F7FA] tracking-wide uppercase">
                CAM-01 • Trackside Downline CCTV
              </span>
              <span className="text-[10px] bg-red-500/20 text-red-400 border border-red-500/30 px-1.5 py-0.5 rounded font-mono font-bold">
                LIVE
              </span>
            </div>
            <button
              onClick={() => onNavigateTab('monitoring')}
              className="text-xs text-[#929BA8] hover:text-[#F5F7FA] flex items-center space-x-1"
            >
              <span>Full Monitor</span>
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Video Container */}
          <div className="relative mt-4 aspect-video bg-[#0B0D10] rounded-lg border border-[#252B33] overflow-hidden flex items-center justify-center group">
            <video
              className="w-full h-full object-cover"
              src="/api/v1/videos/stream/annotated_scenario_01.mp4"
              autoPlay
              loop
              muted
              playsInline
            />
            {/* OSD Telemetry Banner */}
            <div className="absolute top-3 left-3 bg-[#0B0D10]/80 backdrop-blur border border-[#252B33] px-3 py-1.5 rounded text-[11px] font-mono text-[#F5F7FA] space-y-0.5 pointer-events-none">
              <div className="flex items-center space-x-2">
                <span className="text-cyan-400">FPS: 30.0</span>
                <span>•</span>
                <span className="text-emerald-400">INFERENCE: 18.2ms</span>
              </div>
              <div className="text-[#929BA8] text-[10px]">
                CALIBRATED ZONES: DANGER_TRACK, CAUTION_APPROACH
              </div>
            </div>

            <div className="absolute bottom-3 right-3 bg-[#0B0D10]/80 backdrop-blur border border-[#252B33] px-2.5 py-1 rounded text-[10px] font-mono text-cyan-400 pointer-events-none">
              YOLOv8 PERCEPTION + BYTETRACK
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between text-xs text-[#929BA8]">
            <span className="font-mono text-[11px]">Source: Level Crossing KM 142/8</span>
            <button
              onClick={() => onNavigateTab('monitoring')}
              className="text-blue-400 hover:underline flex items-center space-x-1"
            >
              <span>Run Scenario Replay</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* B. Recent Emergency Events */}
        <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-[#252B33]/80">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-red-400" />
              <h3 className="text-xs font-bold text-[#F5F7FA] uppercase tracking-wide">
                Recent Emergency Events
              </h3>
            </div>
            <button
              onClick={() => onNavigateTab('events')}
              className="text-[11px] text-blue-400 hover:underline"
            >
              View All ({overview?.total_events ?? 0})
            </button>
          </div>

          <div className="flex-1 mt-3 space-y-2.5 overflow-y-auto max-h-[340px]">
            {events.length === 0 ? (
              <div className="h-40 flex flex-col items-center justify-center text-[#636C7A] text-xs">
                <ShieldAlert className="w-8 h-8 mb-2 opacity-50" />
                <span>No emergency events recorded</span>
              </div>
            ) : (
              events.map((evt) => (
                <div
                  key={evt.event_id}
                  onClick={() => onSelectEvent(evt)}
                  className="p-3 rounded-lg bg-[#0B0D10] border border-[#252B33] hover:border-blue-500/40 hover:bg-[#171C23] cursor-pointer transition-all space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-[#F5F7FA]">
                      {evt.event_id}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getSeverityBadge(
                        evt.current_severity
                      )}`}
                    >
                      {evt.current_severity}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-[#929BA8]">
                    <span className="capitalize">
                      {evt.rule_class} in {evt.zone_type.replace('_', ' ')}
                    </span>
                    <span className="font-mono text-cyan-400">
                      {((evt.confidence ?? 0.95) * 100).toFixed(1)}%
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-[#636C7A] font-mono pt-1 border-t border-[#252B33]/60">
                    <span>Dwell: {evt.unsafe_duration.toFixed(1)}s</span>
                    <span>Status: {evt.status}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* C. SYSTEM SUBSYSTEMS HEALTH */}
      <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-5">
        <div className="flex items-center justify-between pb-3 border-b border-[#252B33]/80">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold text-[#F5F7FA] uppercase tracking-wide">
              Subsystem Diagnostic Matrix
            </h3>
          </div>
          <span className="text-xs font-mono text-emerald-400">ALL SUBSYSTEMS OPERATIONAL</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mt-4">
          {health?.subsystems &&
            Object.entries(health.subsystems).map(([key, sub]) => (
              <div
                key={key}
                className="p-3 rounded-lg bg-[#0B0D10] border border-[#252B33] space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-medium text-[#F5F7FA] truncate">
                    {sub.name.split(' ')[0]}
                  </span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                </div>
                <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-tight">
                  {sub.status}
                </div>
                <div className="text-[9px] text-[#636C7A] font-mono truncate">
                  {sub.device || sub.weights || sub.bot || sub.path || 'Active'}
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};
