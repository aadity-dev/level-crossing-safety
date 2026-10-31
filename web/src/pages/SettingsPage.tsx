import React from 'react';
import { Settings, Shield, Bell, Volume2, Send, Save, RefreshCw } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="bg-[#13171C] border border-[#252B33] rounded-2xl p-6 space-y-6">
        <div className="pb-4 border-b border-[#252B33]">
          <h3 className="text-sm font-bold text-[#F5F7FA]">
            Safety Thresholds & Operations Configuration
          </h3>
          <p className="text-xs text-[#929BA8] mt-0.5">
            Operational settings calibrated in accordance with Railway Level Crossing Standards V3.1
          </p>
        </div>

        <div className="space-y-4">
          {/* Threshold 1 */}
          <div className="p-4 rounded-xl bg-[#0B0D10] border border-[#252B33] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#F5F7FA]">
                Intrusion Confirmation Dwell Time
              </span>
              <span className="text-xs font-mono text-cyan-400 font-bold">0.5 seconds</span>
            </div>
            <p className="text-xs text-[#929BA8]">
              Continuous dwell duration required inside the DANGER_TRACK polygon before transitioning an intrusion candidate from PENDING to CONFIRMED.
            </p>
          </div>

          {/* Threshold 2 */}
          <div className="p-4 rounded-xl bg-[#0B0D10] border border-[#252B33] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#F5F7FA]">
                Alert Escalation Cooldown Window
              </span>
              <span className="text-xs font-mono text-cyan-400 font-bold">3.0 seconds</span>
            </div>
            <p className="text-xs text-[#929BA8]">
              Minimum cooldown period between repeat notifications to prevent overwhelming the Station Master or loco-pilot cab during persistent hazards.
            </p>
          </div>

          {/* Threshold 3 */}
          <div className="p-4 rounded-xl bg-[#0B0D10] border border-[#252B33] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#F5F7FA]">
                Locomotive Area Looming Expansion Rate (dA/dt)
              </span>
              <span className="text-xs font-mono text-cyan-400 font-bold">+15% / second</span>
            </div>
            <p className="text-xs text-[#929BA8]">
              Visual optical velocity threshold used at unmanned rural crossings to automatically infer locomotive approach without track circuits.
            </p>
          </div>

          {/* Threshold 4 */}
          <div className="p-4 rounded-xl bg-[#0B0D10] border border-[#252B33] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#F5F7FA]">
                Acoustic Siren Synthesizer
              </span>
              <span className="text-xs font-mono text-emerald-400 font-bold">16-bit PCM WAV (2000 Hz)</span>
            </div>
            <p className="text-xs text-[#929BA8]">
              Automated trackside emergency siren tone synthesis generated upon confirmation of CRITICAL intrusions.
            </p>
          </div>
        </div>

        <div className="pt-4 border-t border-[#252B33] flex justify-between items-center text-xs text-[#929BA8]">
          <span className="font-mono">Config Root: configs/thresholds.yaml</span>
          <span className="text-emerald-400 font-medium">Read-Only Enforced</span>
        </div>
      </div>
    </div>
  );
};
