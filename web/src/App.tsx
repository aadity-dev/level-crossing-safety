import React, { useState, useEffect, useRef } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { OverviewPage } from './pages/OverviewPage';
import { LiveMonitoringPage } from './pages/LiveMonitoringPage';
import { EmergencyEventsPage } from './pages/EmergencyEventsPage';
import { AlertHistoryPage } from './pages/AlertHistoryPage';
import { TelegramDispatcherPage } from './pages/TelegramDispatcherPage';
import { SystemStatusPage } from './pages/SystemStatusPage';
import { SettingsPage } from './pages/SettingsPage';
import { SafetyEvent, CrossingState } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [demoMode, setDemoMode] = useState<boolean>(false);
  const [selectedEvent, setSelectedEvent] = useState<SafetyEvent | null>(null);
  const [crossingState, setCrossingState] = useState<CrossingState>('OPEN');
  const [wsConnected, setWsConnected] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  // WebSocket Live Connection Lifecycle
  useEffect(() => {
    const connectWs = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/live`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'telemetry_frame') {
            if (msg.data?.crossing_state) {
              setCrossingState(msg.data.crossing_state as CrossingState);
            }
          }
        } catch (e) {
          // ignore non-json keep-alive
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        // Auto-reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(connectWs, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connectWs();

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const renderContent = () => {
    switch (currentTab) {
      case 'overview':
        return (
          <OverviewPage
            demoMode={demoMode}
            onNavigateTab={setCurrentTab}
            onSelectEvent={(evt) => {
              setSelectedEvent(evt);
              setCurrentTab('events');
            }}
          />
        );
      case 'monitoring':
        return <LiveMonitoringPage demoMode={demoMode} crossingState={crossingState} />;
      case 'events':
        return (
          <EmergencyEventsPage
            demoMode={demoMode}
            selectedEvent={selectedEvent}
            setSelectedEvent={setSelectedEvent}
          />
        );
      case 'alerts':
        return <AlertHistoryPage demoMode={demoMode} />;
      case 'telegram':
        return <TelegramDispatcherPage demoMode={demoMode} />;
      case 'status':
        return <SystemStatusPage demoMode={demoMode} />;
      case 'settings':
        return <SettingsPage />;
      default:
        return (
          <OverviewPage
            demoMode={demoMode}
            onNavigateTab={setCurrentTab}
            onSelectEvent={setSelectedEvent}
          />
        );
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0B0D10] text-[#F5F7FA]">
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        demoMode={demoMode}
        setDemoMode={setDemoMode}
      />
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <Header
          currentTab={currentTab}
          crossingState={crossingState}
          wsConnected={wsConnected}
          demoMode={demoMode}
        />
        <main className="flex-1 overflow-y-auto bg-[#0B0D10]">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default App;
