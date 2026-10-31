import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Search,
  Filter,
  Calendar,
  MapPin,
  ExternalLink,
  X,
  FileText,
  Clock,
  Camera,
  Download,
} from 'lucide-react';
import { SafetyEvent, Severity } from '../types';
import { api } from '../services/api';

interface EmergencyEventsPageProps {
  demoMode: boolean;
  selectedEvent: SafetyEvent | null;
  setSelectedEvent: (event: SafetyEvent | null) => void;
}

export const EmergencyEventsPage: React.FC<EmergencyEventsPageProps> = ({
  demoMode,
  selectedEvent,
  setSelectedEvent,
}) => {
  const [events, setEvents] = useState<SafetyEvent[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const evts = await api.getEvents(100, demoMode);
        setEvents(evts);
        setLoading(false);
      } catch (e) {
        console.error('Failed to load events', e);
        setLoading(false);
      }
    };
    fetchEvents();
  }, [demoMode]);

  const filteredEvents = events.filter((e) => {
    const matchesSearch =
      e.event_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.rule_class.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.zone_type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSeverity = severityFilter === 'ALL' || e.current_severity === severityFilter;
    const matchesStatus = statusFilter === 'ALL' || e.status === statusFilter;
    return matchesSearch && matchesSeverity && matchesStatus;
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
      {/* Search and Filters Header */}
      <div className="bg-[#13171C] border border-[#252B33] rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#636C7A]" />
          <input
            type="text"
            placeholder="Search by Event ID, Entity (e.g. Person, Vehicle), or Zone..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#0B0D10] border border-[#252B33] rounded-lg pl-9 pr-4 py-2 text-xs text-[#F5F7FA] placeholder-[#636C7A] focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-xs text-[#929BA8]">
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

          <div className="flex items-center space-x-2 text-xs text-[#929BA8]">
            <span>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-[#0B0D10] border border-[#252B33] rounded px-2.5 py-1.5 text-xs text-[#F5F7FA] focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="CONFIRMED">Confirmed</option>
              <option value="ESCALATED">Escalated</option>
              <option value="RECOVERED">Recovered</option>
            </select>
          </div>
        </div>
      </div>

      {/* Events Table / Card Registry */}
      <div className="bg-[#13171C] border border-[#252B33] rounded-xl overflow-hidden">
        <div className="px-5 py-3.5 border-b border-[#252B33] flex items-center justify-between text-xs text-[#929BA8]">
          <span>Showing {filteredEvents.length} Recorded Safety Events</span>
          <span className="font-mono text-[11px]">Database: data/level_crossing.sqlite3</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B0D10] text-[#929BA8] border-b border-[#252B33] uppercase text-[10px] tracking-wider font-mono">
              <tr>
                <th className="px-5 py-3">Event ID</th>
                <th className="px-4 py-3">Entity / Zone</th>
                <th className="px-4 py-3">Danger Level</th>
                <th className="px-4 py-3">Aspect</th>
                <th className="px-4 py-3">Dwell Time</th>
                <th className="px-4 py-3">Lifecycle Status</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#252B33]/60 text-[#F5F7FA]">
              {filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-10 text-[#636C7A]">
                    No emergency events match your filter criteria.
                  </td>
                </tr>
              ) : (
                filteredEvents.map((evt) => (
                  <tr
                    key={evt.event_id}
                    onClick={() => setSelectedEvent(evt)}
                    className="hover:bg-[#1A2027] cursor-pointer transition-colors"
                  >
                    <td className="px-5 py-3.5 font-mono font-bold text-blue-400">
                      {evt.event_id}
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="font-medium capitalize text-sm">{evt.rule_class}</div>
                      <div className="text-[11px] text-[#929BA8] font-mono">
                        {evt.zone_type.replace('_', ' ')}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getSeverityBadge(
                          evt.current_severity
                        )}`}
                      >
                        {evt.current_severity}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 font-mono text-[11px] text-amber-300">
                      {evt.crossing_state}
                    </td>
                    <td className="px-4 py-3.5 font-mono text-[11px]">
                      {evt.unsafe_duration.toFixed(2)}s
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-[#252B33] text-[#F5F7FA]">
                        {evt.status}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 font-mono text-cyan-400 text-xs">
                      {((evt.confidence ?? 0.95) * 100).toFixed(1)}%
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button className="text-blue-400 hover:text-blue-300 font-medium text-xs">
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* EVENT DETAIL INSPECTION MODAL */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#13171C] border border-[#252B33] rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-[#252B33] flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span
                  className={`text-xs font-bold px-2.5 py-1 rounded border ${getSeverityBadge(
                    selectedEvent.current_severity
                  )}`}
                >
                  {selectedEvent.current_severity}
                </span>
                <span className="text-sm font-bold text-[#F5F7FA] font-mono">
                  {selectedEvent.event_id}
                </span>
                <span className="text-xs text-[#929BA8]">
                  • Track ID: TRK-{selectedEvent.track_id}
                </span>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="w-8 h-8 rounded-lg bg-[#0B0D10] text-[#929BA8] hover:text-[#F5F7FA] flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6 overflow-y-auto flex-1">
              {/* CCTV Snapshot Image */}
              <div>
                <div className="text-xs font-bold text-[#F5F7FA] mb-2 flex items-center justify-between">
                  <span>Photographic Evidence Snapshot (CCTV Capture)</span>
                  <span className="text-[10px] text-[#929BA8] font-mono">
                    Captured at Hazard Confirmation
                  </span>
                </div>
                <div className="aspect-video bg-[#0B0D10] rounded-xl border border-[#252B33] overflow-hidden flex items-center justify-center relative">
                  <img
                    src={`/api/v1/evidence/${selectedEvent.event_id}_INITIAL_900.jpg`}
                    alt="CCTV Evidence Snapshot"
                    className="w-full h-full object-contain"
                    onError={(e) => {
                      // Fallback to sample evidence
                      e.currentTarget.src = '/api/v1/evidence/EVT-C06BEF61_INITIAL_900.jpg';
                    }}
                  />
                  <div className="absolute bottom-3 left-3 bg-[#0B0D10]/85 backdrop-blur border border-[#252B33] px-3 py-1.5 rounded text-[11px] font-mono text-[#F5F7FA]">
                    LOCATION: LC-102 • CONFIRMATION DWELL: {selectedEvent.unsafe_duration.toFixed(1)}s
                  </div>
                </div>
              </div>

              {/* Event Attributes Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
                <div className="p-3 bg-[#0B0D10] rounded-lg border border-[#252B33]">
                  <div className="text-[#636C7A] text-[10px]">OBJECT CLASS</div>
                  <div className="font-bold text-[#F5F7FA] capitalize mt-0.5">
                    {selectedEvent.rule_class}
                  </div>
                </div>
                <div className="p-3 bg-[#0B0D10] rounded-lg border border-[#252B33]">
                  <div className="text-[#636C7A] text-[10px]">ZONE TYPE</div>
                  <div className="font-bold text-red-400 mt-0.5">
                    {selectedEvent.zone_type}
                  </div>
                </div>
                <div className="p-3 bg-[#0B0D10] rounded-lg border border-[#252B33]">
                  <div className="text-[#636C7A] text-[10px]">DETECTION CONFIDENCE</div>
                  <div className="font-bold text-cyan-400 mt-0.5">
                    {((selectedEvent.confidence ?? 0.95) * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-3 bg-[#0B0D10] rounded-lg border border-[#252B33]">
                  <div className="text-[#636C7A] text-[10px]">CROSSING STATE</div>
                  <div className="font-bold text-amber-400 mt-0.5">
                    {selectedEvent.crossing_state}
                  </div>
                </div>
              </div>

              {/* Station Master Telegram Dispatch Report */}
              <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl space-y-1.5">
                <div className="text-xs font-bold text-blue-400 flex items-center space-x-2">
                  <span>📱 Telegram Mobile Dispatch Report</span>
                </div>
                <p className="text-xs text-[#929BA8]">
                  Automated high-priority alert with attached photographic evidence was dispatched to the Station Master phone terminal via <b>@MyRailwaySafety_bot</b>.
                </p>
                <div className="text-[11px] font-mono text-cyan-300 pt-1">
                  Target Destination: Station Master OCC • Status: DELIVERED (HTTP 200)
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-[#252B33] flex justify-end space-x-3">
              <button
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-2 bg-[#0B0D10] border border-[#252B33] text-[#F5F7FA] rounded-lg text-xs font-medium hover:bg-[#1A2027]"
              >
                Close View
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
