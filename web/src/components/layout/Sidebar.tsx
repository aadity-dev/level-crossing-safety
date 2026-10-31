import React from 'react';
import {
  LayoutDashboard,
  Video,
  AlertTriangle,
  History,
  Activity,
  Settings,
  Send,
  Train,
  ShieldCheck,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  demoMode: boolean;
  setDemoMode: (val: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  demoMode,
  setDemoMode,
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'monitoring', label: 'Live Monitoring', icon: Video },
    { id: 'events', label: 'Emergency Events', icon: AlertTriangle },
    { id: 'alerts', label: 'Alert History', icon: History },
    { id: 'telegram', label: 'Telegram Dispatcher', icon: Send },
    { id: 'status', label: 'System Status', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-[#13171C] border-r border-[#252B33] flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="h-16 px-5 border-b border-[#252B33] flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-500">
            <Train className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wider uppercase text-[#F5F7FA]">
              RailSafe OCC
            </h1>
            <p className="text-[10px] text-[#929BA8] font-mono tracking-tight">
              LEVEL CROSSING AI
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold text-[#636C7A] uppercase tracking-wider">
          Operations Center
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentTab(item.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 font-semibold shadow-sm'
                  : 'text-[#929BA8] hover:text-[#F5F7FA] hover:bg-[#1A2027]'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-[#929BA8]'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Demo Mode Toggle & Footer */}
      <div className="p-3 border-t border-[#252B33] space-y-2">
        <div
          onClick={() => setDemoMode(!demoMode)}
          className={`p-2.5 rounded-lg border cursor-pointer transition-all flex items-center justify-between ${
            demoMode
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
              : 'bg-[#0B0D10] border-[#252B33] text-[#929BA8] hover:border-[#323B47]'
          }`}
        >
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4" />
            <div className="text-left">
              <div className="text-xs font-semibold">Demo Mode</div>
              <div className="text-[10px] opacity-75">
                {demoMode ? 'Simulated Telemetry' : 'Production Live'}
              </div>
            </div>
          </div>
          {demoMode ? (
            <ToggleRight className="w-5 h-5 text-amber-400" />
          ) : (
            <ToggleLeft className="w-5 h-5 text-[#636C7A]" />
          )}
        </div>

        <div className="px-2 py-1 text-[10px] font-mono text-[#636C7A] flex justify-between items-center">
          <span>Engine: YOLOv8 MPS</span>
          <span>v3.1.0</span>
        </div>
      </div>
    </aside>
  );
};
