import React, { useState, useEffect } from 'react';
import { Radio, ShieldAlert, Clock, Wifi } from 'lucide-react';
import { CrossingState } from '../../types';

interface HeaderProps {
  currentTab: string;
  crossingState?: CrossingState;
  wsConnected: boolean;
  demoMode: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  crossingState = 'OPEN',
  wsConnected,
  demoMode,
}) => {
  const [timeStr, setTimeStr] = useState<string>('');
  const [utcStr, setUtcStr] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-GB', { hour12: false }));
      setUtcStr(now.toUTCString().slice(17, 25) + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const getTabTitle = (tab: string) => {
    switch (tab) {
      case 'overview':
        return 'Overview Dashboard';
      case 'monitoring':
        return 'Live CCTV Video Stream & Perceptual Telemetry';
      case 'events':
        return 'Emergency Intrusion Incident Registry';
      case 'alerts':
        return 'Auditable Operator Alert Stream';
      case 'telegram':
        return 'Telegram Instant Emergency Dispatcher';
      case 'status':
        return 'Edge System Diagnostic & Hardware Metrics';
      case 'settings':
        return 'Safety Engine Thresholds & Configuration';
      default:
        return 'Railway Safety Monitoring';
    }
  };

  return (
    <header className="h-16 bg-[#13171C] border-b border-[#252B33] px-6 flex items-center justify-between shrink-0 select-none">
      {/* Title & Location Breadcrumb */}
      <div className="flex items-center space-x-3">
        <div>
          <h2 className="text-sm font-bold text-[#F5F7FA] tracking-wide">
            {getTabTitle(currentTab)}
          </h2>
          <div className="flex items-center space-x-2 text-[11px] text-[#929BA8]">
            <span className="font-mono text-cyan-400">LOC: LC-102 (KM 142/8)</span>
            <span>•</span>
            <span>Signal Aspect:</span>
            <span
              className={`font-mono px-1.5 py-0.5 rounded text-[10px] font-bold ${
                crossingState === 'TRAIN_APPROACHING'
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse'
                  : crossingState === 'CLOSED'
                  ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                  : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              }`}
            >
              {crossingState}
            </span>
          </div>
        </div>
      </div>

      {/* Status Pills & Real-Time Indicators */}
      <div className="flex items-center space-x-4">
        {/* Demo Mode Badge */}
        {demoMode && (
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>DEMO MODE ACTIVE</span>
          </div>
        )}

        {/* Operational Status Pill */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>OPERATIONAL</span>
        </div>

        {/* WebSocket Link Status */}
        <div
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${
            wsConnected
              ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
              : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}
        >
          <Wifi className="w-3.5 h-3.5" />
          <span>{wsConnected ? 'WS LIVE' : 'WS RECONNECTING'}</span>
        </div>

        {/* Live Clock */}
        <div className="flex items-center space-x-2 pl-3 border-l border-[#252B33] text-xs font-mono text-[#929BA8]">
          <Clock className="w-3.5 h-3.5 text-[#636C7A]" />
          <span>{timeStr}</span>
          <span className="text-[10px] opacity-60">({utcStr})</span>
        </div>
      </div>
    </header>
  );
};
