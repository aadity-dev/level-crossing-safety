import React, { useState, useEffect } from 'react';
import {
  Video,
  Play,
  RotateCcw,
  ShieldAlert,
  Send,
  Eye,
  Camera,
  Layers,
  Train,
  Sliders,
  CheckCircle2,
} from 'lucide-react';
import { ScenarioInfo, CrossingState } from '../types';
import { api } from '../services/api';

interface LiveMonitoringPageProps {
  demoMode: boolean;
  crossingState: CrossingState;
}

export const LiveMonitoringPage: React.FC<LiveMonitoringPageProps> = ({
  demoMode,
  crossingState,
}) => {
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [telegramPush, setTelegramPush] = useState<boolean>(true);
  const [opticalTrain, setOpticalTrain] = useState<boolean>(true);
  const [liveLog, setLiveLog] = useState<string[]>([]);

  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        const scns = await api.getScenarios();
        setScenarios(scns);
        if (scns.length > 0) {
          setSelectedScenario(scns[0].path);
        }
      } catch (e) {
        console.error('Failed to load scenarios', e);
      }
    };
    fetchScenarios();
  }, []);

  const handleRunReplay = async () => {
    if (!selectedScenario) return;
    setIsRunning(true);
    setLiveLog((prev) => [
      `[${new Date().toLocaleTimeString()}] Triggered replay for ${selectedScenario.split('/').pop()}`,
      `[${new Date().toLocaleTimeString()}] Perception Engine: YOLOv8 on Apple MPS`,
      `[${new Date().toLocaleTimeString()}] Telegram Mobile Dispatch: ${telegramPush ? 'ENABLED (@MyRailwaySafety_bot)' : 'DISABLED'}`,
      ...prev,
    ]);

    try {
      await api.runScenarioReplay(selectedScenario, 300, telegramPush);
      setTimeout(() => {
        setIsRunning(false);
        setLiveLog((prev) => [
          `[${new Date().toLocaleTimeString()}] Replay execution in progress. Telemetry streamed live.`,
          ...prev,
        ]);
      }, 3000);
    } catch (e: any) {
      setIsRunning(false);
      setLiveLog((prev) => [
        `[${new Date().toLocaleTimeString()}] [ERROR] ${e.message}`,
        ...prev,
      ]);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* CCTV STREAM & LIVE TELEMETRY OVERLAY */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Feed Container (3 cols) */}
        <div className="lg:col-span-3 bg-[#13171C] border border-[#252B33] rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-[#252B33]">
            <div className="flex items-center space-x-3">
              <Camera className="w-4 h-4 text-cyan-400" />
              <div>
                <h3 className="text-xs font-bold text-[#F5F7FA] uppercase tracking-wide">
                  LC-102 CCTV Trackside Optical Stream
                </h3>
                <span className="text-[10px] text-[#929BA8] font-mono">
                  Down Track KM 142/8 • RTSP Ingestion Pipeline
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
              <span className="text-xs font-mono text-red-400 font-bold">1080p 30FPS</span>
            </div>
          </div>

          {/* Primary Video Canvas */}
          <div className="relative mt-4 aspect-video bg-[#0B0D10] rounded-lg border border-[#252B33] overflow-hidden flex items-center justify-center">
            <video
              className="w-full h-full object-cover"
              src="/api/v1/videos/stream/annotated_scenario_01.mp4"
              autoPlay
              loop
              muted
              playsInline
            />

            {/* OSD Telemetry Watermark */}
            <div className="absolute top-4 left-4 bg-[#0B0D10]/85 backdrop-blur border border-[#252B33] px-3.5 py-2 rounded-lg text-xs font-mono space-y-1 pointer-events-none">
              <div className="flex items-center space-x-2">
                <span className="text-cyan-400 font-bold">CROSSING ASPECT:</span>
                <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                  {crossingState}
                </span>
              </div>
              <div className="text-[11px] text-[#929BA8]">
                INTRUSION DWELL: <span className="text-red-400 font-bold">2.4s (CONFIRMED)</span>
              </div>
              <div className="text-[10px] text-emerald-400">
                ACTIVE HOTSPOT: Track Centerline (X: 280, Y: 245)
              </div>
            </div>

            <div className="absolute bottom-4 left-4 bg-[#0B0D10]/85 backdrop-blur border border-[#252B33] px-3 py-1.5 rounded-lg text-[11px] font-mono flex items-center space-x-3 pointer-events-none">
              <span className="flex items-center space-x-1.5 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>TRACKER: BYTETRACK CONFIRMED</span>
              </span>
              <span className="text-[#636C7A]">|</span>
              <span className="text-cyan-400">CONFIDENCE: 96.5%</span>
            </div>
          </div>

          {/* Video Control Bar */}
          <div className="mt-4 pt-3 border-t border-[#252B33] flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <label className="text-xs text-[#929BA8] font-medium">Replay Scenario:</label>
              <select
                value={selectedScenario}
                onChange={(e) => setSelectedScenario(e.target.value)}
                className="bg-[#0B0D10] border border-[#252B33] rounded px-3 py-1.5 text-xs text-[#F5F7FA] focus:outline-none focus:border-blue-500"
              >
                {scenarios.map((s) => (
                  <option key={s.id} value={s.path}>
                    {s.title}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={handleRunReplay}
                disabled={isRunning}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold flex items-center space-x-2 transition-all disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{isRunning ? 'Processing...' : 'Run Safety Replay'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar Controls & Telemetry (1 col) */}
        <div className="space-y-6">
          {/* Edge AI Parameters */}
          <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-5 space-y-4">
            <h4 className="text-xs font-bold text-[#F5F7FA] uppercase tracking-wide flex items-center space-x-2">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
              <span>Safety Engine Controls</span>
            </h4>

            <div className="space-y-3">
              <label className="flex items-center justify-between p-2 rounded bg-[#0B0D10] border border-[#252B33] cursor-pointer">
                <span className="text-xs text-[#F5F7FA]">Auto Telegram Alerts</span>
                <input
                  type="checkbox"
                  checked={telegramPush}
                  onChange={(e) => setTelegramPush(e.target.checked)}
                  className="rounded bg-[#13171C] border-[#252B33] text-blue-500 focus:ring-0"
                />
              </label>

              <label className="flex items-center justify-between p-2 rounded bg-[#0B0D10] border border-[#252B33] cursor-pointer">
                <span className="text-xs text-[#F5F7FA]">Optical Train Sensing (dA/dt)</span>
                <input
                  type="checkbox"
                  checked={opticalTrain}
                  onChange={(e) => setOpticalTrain(e.target.checked)}
                  className="rounded bg-[#13171C] border-[#252B33] text-blue-500 focus:ring-0"
                />
              </label>
            </div>

            <div className="pt-2 border-t border-[#252B33] text-[11px] text-[#929BA8] space-y-1">
              <div className="flex justify-between">
                <span>Dwell Confirmation:</span>
                <span className="font-mono text-[#F5F7FA]">&ge; 0.5s</span>
              </div>
              <div className="flex justify-between">
                <span>Alarm Escalation:</span>
                <span className="font-mono text-[#F5F7FA]">&ge; 3.0s</span>
              </div>
              <div className="flex justify-between">
                <span>False-Alarm Suppression:</span>
                <span className="font-mono text-emerald-400">ACTIVE</span>
              </div>
            </div>
          </div>

          {/* Real-Time Live Feed Log */}
          <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-5 space-y-3">
            <h4 className="text-xs font-bold text-[#F5F7FA] uppercase tracking-wide flex items-center space-x-2">
              <Layers className="w-3.5 h-3.5 text-amber-400" />
              <span>OCC Telemetry Log</span>
            </h4>

            <div className="space-y-1.5 max-h-56 overflow-y-auto font-mono text-[10px] text-[#929BA8] p-2 bg-[#0B0D10] rounded border border-[#252B33]">
              {liveLog.length === 0 ? (
                <div className="text-[#636C7A]">Ready to execute replay scenario...</div>
              ) : (
                liveLog.map((line, idx) => (
                  <div key={idx} className="leading-tight">
                    {line}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
