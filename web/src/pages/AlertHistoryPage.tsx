import React, { useState, useEffect } from 'react';
import { Bell, Search, Filter, History, Download, ShieldCheck } from 'lucide-react';
import { AlertRecord } from '../types';
import { api } from '../services/api';

interface AlertHistoryPageProps {
  demoMode: boolean;
}

export const AlertHistoryPage: React.FC<AlertHistoryPageProps> = ({ demoMode }) => {
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('ALL');

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const alts = await api.getAlerts(100, demoMode);
        setAlerts(alts);
      } catch (e) {
        console.error('Failed to load alerts', e);
      }
    };
    fetchAlerts();
  }, [demoMode]);

  const filteredAlerts = alerts.filter((a) => {
    const matchesSearch =
      a.alert_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.event_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.message.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSev = severityFilter === 'ALL' || a.severity === severityFilter;
    return matchesSearch && matchesSev;
  });

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
      {/* Header & Filter Controls */}
      <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#636C7A]" />
          <input
            type="text"
            placeholder="Search by Alert ID, Event ID, or Advisory Message..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#0B0D10] border border-[#252B33] rounded-lg pl-9 pr-4 py-2 text-xs text-[#F5F7FA] placeholder-[#636C7A] focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center space-x-3 text-xs text-[#929BA8]">
          <Filter className="w-3.5 h-3.5" />
          <span>Severity:</span>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-[#0B0D10] border border-[#252B33] rounded px-2.5 py-1.5 text-xs text-[#F5F7FA] focus:outline-none"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
          </select>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="bg-[#13171C] border border-[#252B33] rounded-xl overflow-hidden">
        <div className="px-5 py-3.5 border-b border-[#252B33] flex items-center justify-between text-xs text-[#929BA8]">
          <div className="flex items-center space-x-2">
            <Bell className="w-4 h-4 text-amber-400" />
            <span className="font-semibold text-[#F5F7FA]">
              Auditable Dispatched Alert Log ({filteredAlerts.length})
            </span>
          </div>
          <span className="text-[11px] font-mono">Immutable SQLite3 Audit Trail</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B0D10] text-[#929BA8] border-b border-[#252B33] uppercase text-[10px] tracking-wider font-mono">
              <tr>
                <th className="px-5 py-3">Alert ID</th>
                <th className="px-4 py-3">Parent Event</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Advisory Message</th>
                <th className="px-4 py-3">Active Time</th>
                <th className="px-5 py-3 text-right">Dispatch Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#252B33]/60 text-[#F5F7FA]">
              {filteredAlerts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-[#636C7A]">
                    No alert records match the search filter.
                  </td>
                </tr>
              ) : (
                filteredAlerts.map((alt) => (
                  <tr key={alt.alert_id} className="hover:bg-[#1A2027] transition-colors">
                    <td className="px-5 py-3.5 font-mono font-bold text-amber-400">
                      {alt.alert_id}
                    </td>
                    <td className="px-4 py-3.5 font-mono text-blue-400 text-xs">
                      {alt.event_id}
                    </td>
                    <td className="px-4 py-3.5 font-mono text-[11px]">
                      {alt.alert_type}
                    </td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getSeverityBadge(
                          alt.severity
                        )}`}
                      >
                        {alt.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-xs text-[#929BA8] max-w-xs truncate">
                      {alt.message}
                    </td>
                    <td className="px-4 py-3.5 font-mono text-[11px] text-[#636C7A]">
                      {alt.timestamp.toFixed(2)}s
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        {alt.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
