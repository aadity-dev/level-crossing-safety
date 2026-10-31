import React, { useState, useEffect, useRef } from 'react';
import {
  Video,
  Play,
  Upload,
  Link as LinkIcon,
  Film,
  Camera,
  Layers,
  Train,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Download,
  Flame,
  Clock,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { ScenarioInfo, CrossingState } from '../types';
import { api } from '../services/api';

interface LiveMonitoringPageProps {
  demoMode: boolean;
  crossingState: CrossingState;
}

export const LiveMonitoringPage: React.FC<LiveMonitoringPageProps> = ({
  demoMode,
  crossingState: initialCrossingState,
}) => {
  // Ingestion Source State
  const [sourceMode, setSourceMode] = useState<'preset' | 'upload' | 'link'>('preset');
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [selectedVideoPath, setSelectedVideoPath] = useState<string>(
    'data/controlled/validation/scenario_02_multi_person_intrusion.mp4'
  );
  const [customUrl, setCustomUrl] = useState<string>('');
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [isResolving, setIsResolving] = useState<boolean>(false);

  // Replay Execution Parameters
  const [simulatedState, setSimulatedState] = useState<string>('TRAIN_APPROACHING');
  const [frameLimit, setFrameLimit] = useState<number | null>(300);
  const [telegramPush, setTelegramPush] = useState<boolean>(true);
  const [opticalTrain, setOpticalTrain] = useState<boolean>(false);

  // Execution & Results State
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [runProgress, setRunProgress] = useState<number>(0);
  const [inferenceSummary, setInferenceSummary] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState<'video' | 'heatmap'>('video');
  const [activeStreamUrl, setActiveStreamUrl] = useState<string>(
    '/api/v1/videos/stream/annotated_scenario_01.mp4'
  );

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Load available scenarios on mount
  const refreshScenarios = async () => {
    try {
      const scns = await api.getScenarios();
      setScenarios(scns);
      if (scns.length > 0 && !selectedVideoPath) {
        setSelectedVideoPath(scns[0].path);
      }
    } catch (e) {
      console.error('Failed to load scenarios', e);
    }
  };

  useEffect(() => {
    refreshScenarios();
  }, []);

  // Handle Custom Video Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadStatus(`Uploading ${file.name}...`);
    try {
      const res = await api.uploadCustomVideo(file);
      setSelectedVideoPath(res.path);
      setUploadStatus(`Uploaded: ${res.filename} (${res.size_mb} MB)`);
      refreshScenarios();
    } catch (err: any) {
      setUploadStatus(`Upload failed: ${err.message}`);
    }
  };

  // Handle URL / YouTube Resolution
  const handleResolveLink = async () => {
    if (!customUrl.trim()) return;
    setIsResolving(true);
    setUploadStatus('Resolving stream / downloading media via yt-dlp...');
    try {
      const res = await api.resolveVideoLink(customUrl.trim());
      if (res.success && res.resolved_path) {
        setSelectedVideoPath(res.resolved_path);
        setUploadStatus(`Resolved: ${res.filename}`);
        refreshScenarios();
      } else {
        setUploadStatus(`Failed: ${res.error || 'Could not resolve URL'}`);
      }
    } catch (err: any) {
      setUploadStatus(`Error: ${err.message}`);
    } finally {
      setIsResolving(false);
    }
  };

  // Run Inference Execution
  const handleExecuteInference = async () => {
    if (!selectedVideoPath) {
      alert('Please select or upload a video source first.');
      return;
    }

    setIsRunning(true);
    setRunProgress(15);
    setInferenceSummary(null);

    const progressTimer = setInterval(() => {
      setRunProgress((prev) => (prev < 90 ? prev + 15 : prev));
    }, 800);

    try {
      const result = await api.executeInference({
        video_source: selectedVideoPath,
        crossing_state: simulatedState,
        max_frames: frameLimit,
        autonomous_train: opticalTrain,
        enable_telegram: telegramPush,
      });

      clearInterval(progressTimer);
      setRunProgress(100);
      setInferenceSummary(result);
      setActiveStreamUrl(result.annotated_video_url);
      setIsRunning(false);
    } catch (err: any) {
      clearInterval(progressTimer);
      setIsRunning(false);
      alert(`Inference failed: ${err.message}`);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* 2-COLUMN STUDIO LAYOUT */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: CONTROLS & INGESTION (4 cols) */}
        <div className="lg:col-span-4 space-y-5">
          {/* Panel 1: Video Ingestion Source */}
          <div className="bg-[#13171C] border border-[#252B33] rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#252B33]">
              <h3 className="text-xs font-bold text-[#F5F7FA] uppercase tracking-wide flex items-center space-x-2">
                <Film className="w-4 h-4 text-cyan-400" />
                <span>Video Ingestion Source</span>
              </h3>
              <span className="text-[10px] text-[#929BA8] font-mono">ByteTrack V3.1</span>
            </div>

            {/* Ingestion Mode Radio Tabs */}
            <div className="grid grid-cols-3 gap-1 p-1 bg-[#0B0D10] border border-[#252B33] rounded-lg text-[11px] font-medium text-[#929BA8]">
              <button
                onClick={() => setSourceMode('preset')}
                className={`py-1.5 px-2 rounded text-center transition-all ${
                  sourceMode === 'preset'
                    ? 'bg-blue-600 text-white font-semibold shadow'
                    : 'hover:text-[#F5F7FA]'
                }`}
              >
                Preset
              </button>
              <button
                onClick={() => setSourceMode('upload')}
                className={`py-1.5 px-2 rounded text-center transition-all ${
                  sourceMode === 'upload'
                    ? 'bg-blue-600 text-white font-semibold shadow'
                    : 'hover:text-[#F5F7FA]'
                }`}
              >
                Upload File
              </button>
              <button
                onClick={() => setSourceMode('link')}
                className={`py-1.5 px-2 rounded text-center transition-all ${
                  sourceMode === 'link'
                    ? 'bg-blue-600 text-white font-semibold shadow'
                    : 'hover:text-[#F5F7FA]'
                }`}
              >
                URL / Stream
              </button>
            </div>

            {/* Mode 1: Preset Scenarios */}
            {sourceMode === 'preset' && (
              <div className="space-y-2">
                <label className="text-[11px] text-[#929BA8] font-medium block">
                  Select Scenario Footage:
                </label>
                <select
                  value={selectedVideoPath}
                  onChange={(e) => setSelectedVideoPath(e.target.value)}
                  className="w-full bg-[#0B0D10] border border-[#252B33] rounded-lg p-2.5 text-xs text-[#F5F7FA] focus:outline-none focus:border-blue-500 font-mono"
                >
                  {scenarios.map((s) => (
                    <option key={s.id} value={s.path}>
                      {s.title}
                    </option>
                  ))}
                </select>
                <div className="text-[10px] text-[#636C7A] font-mono break-all pt-1">
                  Selected: {selectedVideoPath}
                </div>
              </div>
            )}

            {/* Mode 2: Custom File Upload */}
            {sourceMode === 'upload' && (
              <div className="space-y-3">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  accept=".mp4,.mov,.avi,.mkv"
                  className="hidden"
                />
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-[#252B33] hover:border-blue-500/50 rounded-xl p-5 text-center cursor-pointer bg-[#0B0D10] transition-colors"
                >
                  <Upload className="w-6 h-6 mx-auto text-[#636C7A] mb-2" />
                  <div className="text-xs font-semibold text-[#F5F7FA]">
                    Click to Upload Custom Video
                  </div>
                  <div className="text-[10px] text-[#929BA8] mt-1">
                    Supports .mp4, .mov, .avi, .mkv (Up to 100MB)
                  </div>
                </div>
                {uploadStatus && (
                  <div className="p-2.5 rounded bg-[#0B0D10] border border-[#252B33] text-xs font-mono text-cyan-400">
                    {uploadStatus}
                  </div>
                )}
              </div>
            )}

            {/* Mode 3: Video Link / YouTube / RTSP */}
            {sourceMode === 'link' && (
              <div className="space-y-2.5">
                <label className="text-[11px] text-[#929BA8] font-medium block">
                  Paste YouTube Link, RTSP stream, or Direct MP4 URL:
                </label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={customUrl}
                    onChange={(e) => setCustomUrl(e.target.value)}
                    placeholder="e.g. https://www.youtube.com/watch?v=... or rtsp://..."
                    className="flex-1 bg-[#0B0D10] border border-[#252B33] rounded-lg px-3 py-2 text-xs text-[#F5F7FA] placeholder-[#636C7A] focus:outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={handleResolveLink}
                    disabled={isResolving}
                    className="px-3 py-2 bg-[#252B33] hover:bg-[#323B47] text-white rounded-lg text-xs font-semibold"
                  >
                    {isResolving ? 'Resolving...' : 'Resolve'}
                  </button>
                </div>
                {uploadStatus && (
                  <div className="p-2 rounded bg-[#0B0D10] border border-[#252B33] text-[11px] font-mono text-cyan-400">
                    {uploadStatus}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Panel 2: Simulation & Pipeline Controls */}
          <div className="bg-[#13171C] border border-[#252B33] rounded-2xl p-5 space-y-4">
            <h3 className="text-xs font-bold text-[#F5F7FA] uppercase tracking-wide flex items-center space-x-2 pb-2 border-b border-[#252B33]">
              <Sliders className="w-4 h-4 text-amber-400" />
              <span>Simulation & Interlock State</span>
            </h3>

            {/* Interlock State Select */}
            <div className="space-y-1.5">
              <label className="text-[11px] text-[#929BA8] font-medium flex justify-between">
                <span>Simulated Crossing Interlock State:</span>
                <span className="font-mono text-amber-400 font-bold">{simulatedState}</span>
              </label>
              <select
                value={simulatedState}
                onChange={(e) => setSimulatedState(e.target.value)}
                className="w-full bg-[#0B0D10] border border-[#252B33] rounded-lg p-2.5 text-xs text-[#F5F7FA] focus:outline-none focus:border-blue-500"
              >
                <option value="TRAIN_APPROACHING">TRAIN_APPROACHING (Active Warning)</option>
                <option value="OPEN">OPEN (Safe Pedestrian Crossing)</option>
                <option value="CLOSED">CLOSED (Barriers Dropped)</option>
                <option value="UNKNOWN">UNKNOWN (Degraded Safe Fallback)</option>
              </select>
            </div>

            {/* Frame Limit Select */}
            <div className="space-y-1.5">
              <label className="text-[11px] text-[#929BA8] font-medium flex justify-between">
                <span>Inference Frame Limit:</span>
                <span className="font-mono text-cyan-400">
                  {frameLimit ? `${frameLimit} frames` : 'Full Video'}
                </span>
              </label>
              <select
                value={frameLimit ? String(frameLimit) : 'full'}
                onChange={(e) =>
                  setFrameLimit(e.target.value === 'full' ? null : Number(e.target.value))
                }
                className="w-full bg-[#0B0D10] border border-[#252B33] rounded-lg p-2.5 text-xs text-[#F5F7FA] focus:outline-none focus:border-blue-500"
              >
                <option value="150">Quick Test (150 frames / ~5s)</option>
                <option value="300">Standard Clip (300 frames / ~10s)</option>
                <option value="600">Extended Clip (600 frames / ~20s)</option>
                <option value="full">Full Video (Process all frames)</option>
              </select>
            </div>

            {/* Toggles */}
            <div className="space-y-2 pt-1">
              <label className="flex items-center justify-between p-2.5 rounded-lg bg-[#0B0D10] border border-[#252B33] cursor-pointer">
                <div>
                  <div className="text-xs text-[#F5F7FA] font-medium">
                    🚂 Autonomous Optical Train Sensing
                  </div>
                  <div className="text-[10px] text-[#929BA8]">
                    Infers train approach via area expansion (dA/dt)
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={opticalTrain}
                  onChange={(e) => setOpticalTrain(e.target.checked)}
                  className="rounded bg-[#13171C] border-[#252B33] text-blue-500"
                />
              </label>

              <label className="flex items-center justify-between p-2.5 rounded-lg bg-[#0B0D10] border border-[#252B33] cursor-pointer">
                <div>
                  <div className="text-xs text-[#F5F7FA] font-medium">
                    📱 Auto-Dispatch Alerts to Telegram
                  </div>
                  <div className="text-[10px] text-[#929BA8]">
                    Pushes real-time alerts to @MyRailwaySafety_bot
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={telegramPush}
                  onChange={(e) => setTelegramPush(e.target.checked)}
                  className="rounded bg-[#13171C] border-[#252B33] text-blue-500"
                />
              </label>
            </div>

            {/* Run Button */}
            <button
              onClick={handleExecuteInference}
              disabled={isRunning}
              className="w-full py-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-bold rounded-xl text-xs uppercase tracking-wider flex items-center justify-center space-x-2 shadow-lg transition-all disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{isRunning ? 'Processing Inference...' : '⚡ Run Safety Inference & Video Replay'}</span>
            </button>

            {isRunning && (
              <div className="space-y-1">
                <div className="w-full bg-[#0B0D10] rounded-full h-2 overflow-hidden border border-[#252B33]">
                  <div
                    className="bg-cyan-500 h-full transition-all duration-300"
                    style={{ width: `${runProgress}%` }}
                  ></div>
                </div>
                <div className="text-[10px] text-cyan-400 font-mono text-center">
                  Executing YOLOv8 Perception + ByteTrack Associator...
                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: VIDEO PLAYER & HEATMAP STUDIO (8 cols) */}
        <div className="lg:col-span-8 space-y-5">
          {/* Main Visual Studio Card */}
          <div className="bg-[#13171C] border border-[#252B33] rounded-2xl p-5 space-y-4">
            {/* View Switcher Tabs */}
            <div className="flex items-center justify-between pb-3 border-b border-[#252B33]">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setActiveTab('video')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
                    activeTab === 'video'
                      ? 'bg-blue-600 text-white'
                      : 'bg-[#0B0D10] text-[#929BA8] hover:text-[#F5F7FA]'
                  }`}
                >
                  <Video className="w-3.5 h-3.5" />
                  <span>Visual Telemetry Stream (Annotated)</span>
                </button>
                <button
                  onClick={() => setActiveTab('heatmap')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
                    activeTab === 'heatmap'
                      ? 'bg-amber-600 text-white'
                      : 'bg-[#0B0D10] text-[#929BA8] hover:text-[#F5F7FA]'
                  }`}
                >
                  <Flame className="w-3.5 h-3.5" />
                  <span>Spatial Hazard Density Heatmap</span>
                </button>
              </div>

              <span className="text-xs font-mono text-emerald-400 flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>LC-102 ACTIVE</span>
              </span>
            </div>

            {/* View 1: Annotated Video Stream */}
            {activeTab === 'video' && (
              <div className="space-y-3">
                <div className="relative aspect-video bg-[#0B0D10] rounded-xl border border-[#252B33] overflow-hidden flex items-center justify-center">
                  <video
                    key={activeStreamUrl}
                    className="w-full h-full object-contain"
                    src={activeStreamUrl}
                    controls
                    autoPlay
                    loop
                    playsInline
                  />

                  {/* Watermark OSD */}
                  <div className="absolute top-3 left-3 bg-[#0B0D10]/85 backdrop-blur border border-[#252B33] px-3 py-1.5 rounded text-[11px] font-mono text-[#F5F7FA] pointer-events-none">
                    <span className="text-cyan-400 font-bold">ASPECT: {simulatedState}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-[#929BA8] pt-1">
                  <span className="font-mono text-[11px]">Stream: {activeStreamUrl}</span>
                  <a
                    href={activeStreamUrl}
                    download
                    className="px-3 py-1 bg-[#0B0D10] border border-[#252B33] hover:bg-[#1A2027] rounded text-xs font-medium text-blue-400 flex items-center space-x-1"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download MP4</span>
                  </a>
                </div>
              </div>
            )}

            {/* View 2: Spatial Hazard Density Heatmap */}
            {activeTab === 'heatmap' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Heatmap Image (2 cols) */}
                  <div className="md:col-span-2 aspect-video bg-[#0B0D10] rounded-xl border border-[#252B33] overflow-hidden flex items-center justify-center relative">
                    <img
                      src={
                        inferenceSummary?.heatmap_url ||
                        '/api/v1/videos/heatmap/heatmap_scenario_01.png'
                      }
                      alt="Spatial Hazard Heatmap"
                      className="w-full h-full object-contain"
                      onError={(e) => {
                        e.currentTarget.src =
                          '/api/v1/videos/heatmap/heatmap_scenario_02.png';
                      }}
                    />
                    <div className="absolute bottom-3 left-3 bg-[#0B0D10]/85 backdrop-blur border border-[#252B33] px-2.5 py-1 rounded text-[10px] font-mono text-amber-400">
                      2D THERMAL KDE (GREEN &rarr; YELLOW &rarr; RED)
                    </div>
                  </div>

                  {/* Heatmap Metrics (1 col) */}
                  <div className="space-y-3 font-mono text-xs">
                    <div className="p-3 bg-[#0B0D10] border border-[#252B33] rounded-xl">
                      <div className="text-[#636C7A] text-[10px]">DANGER ZONE VIOLATION RATIO</div>
                      <div className="text-xl font-bold text-red-400 mt-0.5">
                        {inferenceSummary?.heatmap_analytics?.danger_zone_percentage ?? 88.5}%
                      </div>
                      <div className="text-[10px] text-[#929BA8] mt-1 font-sans">
                        Portion of foot ground contacts located in DANGER_TRACK
                      </div>
                    </div>

                    <div className="p-3 bg-[#0B0D10] border border-[#252B33] rounded-xl">
                      <div className="text-[#636C7A] text-[10px]">TOTAL FOOT CONTACTS</div>
                      <div className="text-xl font-bold text-cyan-400 mt-0.5">
                        {inferenceSummary?.heatmap_analytics?.total_foot_samples ?? 245}
                      </div>
                      <div className="text-[10px] text-[#929BA8] mt-1 font-sans">
                        Trajectory points accumulated
                      </div>
                    </div>

                    <div className="p-3 bg-[#0B0D10] border border-[#252B33] rounded-xl">
                      <div className="text-[#636C7A] text-[10px]">PEAK VIOLATION HOTSPOT</div>
                      <div className="text-sm font-bold text-amber-400 mt-0.5">
                        X: {inferenceSummary?.heatmap_analytics?.peak_hotspot_coordinate?.x ?? 280}, Y:{' '}
                        {inferenceSummary?.heatmap_analytics?.peak_hotspot_coordinate?.y ?? 245}
                      </div>
                    </div>

                    {inferenceSummary?.heatmap_url && (
                      <a
                        href={inferenceSummary.heatmap_url}
                        download
                        className="w-full py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all text-center"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>⬇️ Download Heatmap PNG</span>
                      </a>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Replay Inference Summary Banner */}
          {inferenceSummary && (
            <div className="bg-[#13171C] border border-emerald-500/30 rounded-2xl p-5 space-y-3">
              <div className="flex items-center space-x-2 text-emerald-400 font-bold text-xs">
                <CheckCircle2 className="w-4 h-4" />
                <span>SAFETY INFERENCE EXECUTION COMPLETED SUCCESSFULLY</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
                <div className="p-3 bg-[#0B0D10] rounded-lg border border-[#252B33]">
                  <span className="text-[10px] text-[#636C7A] block">FRAMES PROCESSED</span>
                  <span className="font-bold text-[#F5F7FA]">
                    {inferenceSummary.total_frames_processed} ({inferenceSummary.duration_seconds}s)
                  </span>
                </div>
                <div className="p-3 bg-[#0B0D10] rounded-lg border border-[#252B33]">
                  <span className="text-[10px] text-[#636C7A] block">INFERENCE SPEED</span>
                  <span className="font-bold text-cyan-400">
                    {inferenceSummary.average_fps} FPS ({inferenceSummary.elapsed_wall_time_sec}s wall)
                  </span>
                </div>
                <div className="p-3 bg-[#0B0D10] rounded-lg border border-[#252B33]">
                  <span className="text-[10px] text-[#636C7A] block">EVENTS GENERATED</span>
                  <span className="font-bold text-amber-400">
                    {inferenceSummary.events_generated} Events
                  </span>
                </div>
                <div className="p-3 bg-[#0B0D10] rounded-lg border border-[#252B33]">
                  <span className="text-[10px] text-[#636C7A] block">ALERTS DISPATCHED</span>
                  <span className="font-bold text-red-400">
                    {inferenceSummary.alerts_generated} Alerts
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
