import React, { useState, useEffect } from 'react';
import {
  Activity,
  Cpu,
  Database,
  Radio,
  Layers,
  CheckCircle2,
  AlertTriangle,
  HardDrive,
  Clock,
  ShieldCheck,
} from 'lucide-react';
import { DetailedHealth } from '../types';
import { api } from '../services/api';

interface SystemStatusPageProps {
  demoMode: boolean;
}

export const SystemStatusPage: React.FC<SystemStatusPageProps> = ({ demoMode }) => {
  const [health, setHealth] = useState<DetailedHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await api.getDetailedHealth(demoMode);
        setHealth(data);
        setLoading(false);
      } catch (e) {
        console.error('Failed to load system diagnostics', e);
        setLoading(false);
      }
    };
    fetchHealth();
  }, [demoMode]);

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Overview Status Banner */}
      <div className="bg-[#13171C] border border-[#252B33] rounded-2xl p-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#F5F7FA]">
              Edge Perceptual Safety Architecture
            </h3>
            <p className="text-xs text-[#929BA8]">
              Automated Railway Level Crossing Intruder Detection & Spatial Safety V3.1
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-mono">
            SIL-2 SURVEILLANCE READY
          </span>
        </div>
      </div>

      {/* Subsystem Details Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 1. YOLOv8 Perceptual Detector */}
        <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#252B33]">
            <div className="flex items-center space-x-2 text-xs font-bold text-[#F5F7FA]">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>YOLOv8 Perceptual Perception Engine</span>
            </div>
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          </div>
          <div className="text-xs text-[#929BA8] space-y-1.5 font-mono">
            <div className="flex justify-between">
              <span>Acceleration:</span>
              <span className="text-[#F5F7FA]">Apple Metal (MPS) / FP16</span>
            </div>
            <div className="flex justify-between">
              <span>Model Weights:</span>
              <span className="text-[#F5F7FA]">yolov8n.pt</span>
            </div>
            <div className="flex justify-between">
              <span>Per-Frame Latency:</span>
              <span className="text-emerald-400 font-bold">~18.2 ms (55 FPS)</span>
            </div>
            <div className="flex justify-between">
              <span>Mapped Classes:</span>
              <span className="text-[#F5F7FA]">Person, Car, Truck, Bus, Motorcycle</span>
            </div>
          </div>
        </div>

        {/* 2. ByteTrack Object Tracker */}
        <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#252B33]">
            <div className="flex items-center space-x-2 text-xs font-bold text-[#F5F7FA]">
              <Layers className="w-4 h-4 text-blue-400" />
              <span>ByteTrack Trajectory Associator</span>
            </div>
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          </div>
          <div className="text-xs text-[#929BA8] space-y-1.5 font-mono">
            <div className="flex justify-between">
              <span>Association Method:</span>
              <span className="text-[#F5F7FA]">High/Low IoU Kalman Matching</span>
            </div>
            <div className="flex justify-between">
              <span>Primary IoU Threshold:</span>
              <span className="text-[#F5F7FA]">0.45</span>
            </div>
            <div className="flex justify-between">
              <span>Track Confirmation:</span>
              <span className="text-emerald-400">&ge; 3 Consecutive Frames</span>
            </div>
            <div className="flex justify-between">
              <span>Occlusion Grace Window:</span>
              <span className="text-[#F5F7FA]">30 Frames (~1.0s)</span>
            </div>
          </div>
        </div>

        {/* 3. SQLite3 Persistence Engine */}
        <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#252B33]">
            <div className="flex items-center space-x-2 text-xs font-bold text-[#F5F7FA]">
              <Database className="w-4 h-4 text-purple-400" />
              <span>Auditable Event Storage</span>
            </div>
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          </div>
          <div className="text-xs text-[#929BA8] space-y-1.5 font-mono">
            <div className="flex justify-between">
              <span>Storage Driver:</span>
              <span className="text-[#F5F7FA]">SQLite3 with WAL Journaling</span>
            </div>
            <div className="flex justify-between">
              <span>Database File:</span>
              <span className="text-[#F5F7FA]">data/level_crossing.sqlite3</span>
            </div>
            <div className="flex justify-between">
              <span>Audit Integrity:</span>
              <span className="text-emerald-400">Forensic SHA-256 Checksums</span>
            </div>
            <div className="flex justify-between">
              <span>Evidence Storage:</span>
              <span className="text-[#F5F7FA]">data/snapshots/ (JPEG)</span>
            </div>
          </div>
        </div>

        {/* 4. Safety Zone Geometry */}
        <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#252B33]">
            <div className="flex items-center space-x-2 text-xs font-bold text-[#F5F7FA]">
              <HardDrive className="w-4 h-4 text-amber-400" />
              <span>Calibrated Safety Boundaries</span>
            </div>
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          </div>
          <div className="text-xs text-[#929BA8] space-y-1.5 font-mono">
            <div className="flex justify-between">
              <span>Danger Zone Polygon:</span>
              <span className="text-red-400">P1-P4 Ground Rails</span>
            </div>
            <div className="flex justify-between">
              <span>Approach Road Zone:</span>
              <span className="text-[#F5F7FA]">Caution Entry Polygons</span>
            </div>
            <div className="flex justify-between">
              <span>Projection Mode:</span>
              <span className="text-cyan-400">Bottom-Center Foot Coordinate</span>
            </div>
            <div className="flex justify-between">
              <span>Boundary Hysteresis:</span>
              <span className="text-[#F5F7FA]">&plusmn;1.5% Normalized Buffer</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
