import React, { useState, useEffect } from 'react';
import {
  Send,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Smartphone,
  ExternalLink,
  Lock,
  RefreshCw,
  Image as ImageIcon,
} from 'lucide-react';
import { TelegramStatus } from '../types';
import { api } from '../services/api';

interface TelegramDispatcherPageProps {
  demoMode: boolean;
}

export const TelegramDispatcherPage: React.FC<TelegramDispatcherPageProps> = ({ demoMode }) => {
  const [status, setStatus] = useState<TelegramStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any | null>(null);

  const fetchStatus = async () => {
    try {
      const data = await api.getTelegramStatus(demoMode);
      setStatus(data);
      setLoading(false);
    } catch (e) {
      console.error('Failed to load telegram status', e);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, [demoMode]);

  const handleSendTestAlert = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.sendTestTelegramAlert();
      setTestResult(res);
      fetchStatus();
    } catch (e: any) {
      setTestResult({
        success: false,
        error: e.message || 'Dispatch failure',
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Bot Status & Credentials Shield Banner */}
      <div className="bg-[#13171C] border border-[#252B33] rounded-2xl p-6 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-[#252B33]">
          <div className="flex items-center space-x-3.5">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Send className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-bold text-[#F5F7FA]">
                  Telegram Emergency Dispatcher Gateway
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  {status?.configured ? 'CONNECTED' : 'DISCONNECTED'}
                </span>
              </div>
              <p className="text-xs text-[#929BA8] mt-0.5">
                Instant high-priority push notifications and CCTV photographic evidence to Station Master
              </p>
            </div>
          </div>

          <button
            onClick={fetchStatus}
            className="p-2 rounded-lg bg-[#0B0D10] border border-[#252B33] text-[#929BA8] hover:text-[#F5F7FA]"
            title="Refresh Status"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Security Shield Card */}
        <div className="p-4 rounded-xl bg-[#0B0D10] border border-[#252B33] space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-400">
              <Lock className="w-4 h-4" />
              <span>Railway OCC Credential Vault: ACTIVE & ENCRYPTED</span>
            </div>
            <span className="text-[10px] font-mono text-[#636C7A]">Server .env Enforced</span>
          </div>
          <p className="text-xs text-[#929BA8] leading-relaxed">
            The Bot Token is securely stored in the backend environment. It is never exposed in browser JavaScript or client-side responses.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 text-xs font-mono">
            <div className="p-2.5 rounded bg-[#13171C] border border-[#252B33]">
              <span className="text-[10px] text-[#636C7A] block">BOT CHANNEL</span>
              <span className="font-bold text-blue-400">{status?.bot_username}</span>
            </div>
            <div className="p-2.5 rounded bg-[#13171C] border border-[#252B33]">
              <span className="text-[10px] text-[#636C7A] block">STATION MASTER DESTINATION</span>
              <span className="font-bold text-cyan-400">
                Chat ID: {status?.target_chat_id}
              </span>
            </div>
            <div className="p-2.5 rounded bg-[#13171C] border border-[#252B33]">
              <span className="text-[10px] text-[#636C7A] block">DELIVERY MODE</span>
              <span className="font-bold text-emerald-400">{status?.delivery_mode}</span>
            </div>
          </div>
        </div>

        {/* Delivery Telemetry Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-[#0B0D10] border border-[#252B33] text-center">
            <div className="text-2xl font-bold text-[#F5F7FA]">
              {status?.total_dispatched ?? 0}
            </div>
            <div className="text-xs text-emerald-400 mt-1">Delivered to Mobile</div>
          </div>
          <div className="p-4 rounded-xl bg-[#0B0D10] border border-[#252B33] text-center">
            <div className="text-2xl font-bold text-[#F5F7FA]">
              {status?.total_suppressed ?? 0}
            </div>
            <div className="text-xs text-[#929BA8] mt-1">Duplicate Suppressed</div>
          </div>
          <div className="p-4 rounded-xl bg-[#0B0D10] border border-[#252B33] text-center">
            <div className="text-2xl font-bold text-[#F5F7FA]">
              {status?.total_failed ?? 0}
            </div>
            <div className="text-xs text-red-400 mt-1">Failed Transmissions</div>
          </div>
        </div>

        {/* Test Notification Action Panel */}
        <div className="pt-4 border-t border-[#252B33] space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h4 className="text-xs font-bold text-[#F5F7FA] uppercase tracking-wide">
                Live Verification Push Test
              </h4>
              <p className="text-xs text-[#929BA8]">
                Dispatches a verified emergency test alert with an actual CCTV snapshot to your phone.
              </p>
            </div>
            <button
              onClick={handleSendTestAlert}
              disabled={testing || !status?.configured}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-2 transition-all disabled:opacity-50 shadow-md hover:shadow-blue-600/20"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{testing ? 'Transmitting to Telegram...' : '🚀 Send Safe Test Alert with Evidence Snapshot'}</span>
            </button>
          </div>

          {/* Test Dispatch Result Card */}
          {testResult && (
            <div
              className={`p-4 rounded-xl border space-y-2 ${
                testResult.success
                  ? 'bg-emerald-500/10 border-emerald-500/30'
                  : 'bg-red-500/10 border-red-500/30'
              }`}
            >
              <div className="flex items-center space-x-2">
                {testResult.success ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-red-400" />
                )}
                <span className="text-xs font-bold text-[#F5F7FA]">
                  {testResult.success
                    ? '🎉 REAL TELEGRAM EMERGENCY ALERT & CCTV PHOTO DELIVERED!'
                    : 'Dispatch Failed'}
                </span>
              </div>

              {testResult.success ? (
                <div className="text-xs text-[#929BA8] space-y-1 font-mono">
                  <div>• Telegram Message ID: <span className="text-[#F5F7FA] font-bold">{testResult.message_id}</span></div>
                  <div>• Evidence Photo Attached: <span className="text-cyan-400">{testResult.evidence_used}</span></div>
                  <div>• Timestamp: {testResult.timestamp}</div>
                  <div className="text-[11px] text-amber-300 pt-1">
                    ⚠️ Note: Dispatched successfully to Telegram OCC. Operator acknowledgment pending on mobile terminal.
                  </div>
                </div>
              ) : (
                <div className="text-xs text-red-400 font-mono">
                  Error: {testResult.error}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
