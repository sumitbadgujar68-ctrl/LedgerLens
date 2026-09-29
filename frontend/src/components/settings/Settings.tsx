import React from 'react';
import { TopBar } from '../layout/TopBar';
import {
  CheckCircle2,
  Activity,
  Cpu,
  Database,
  Radio,
  Zap,
} from 'lucide-react';

export const Settings: React.FC = () => {
  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[var(--color-surface-dim)] text-[var(--color-on-surface)] select-none">
      <TopBar />

      <main className="flex-1 overflow-auto p-8">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Header Summary */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[var(--color-outline)] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-wide text-[var(--color-on-surface)]">Infrastructure Telemetry</h1>
              </div>
              <p className="text-sm text-[var(--color-on-surface-variant)] mt-1">Live RPC client latency, consensus sync state, mempool feeds, and AI inference endpoints.</p>
            </div>
          </div>

          {/* Header Telemetry Status Strip */}
          <div className="bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-[var(--color-secondary)]/10 border border-[var(--color-secondary)]/20 flex items-center justify-center text-[var(--color-secondary)]">
                <Radio className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <div className="text-sm font-bold text-[var(--color-on-surface)] uppercase tracking-wide">
                  Ethereum Consensus Client: Fully Synchronized
                </div>
                <div className="text-xs text-[var(--color-on-surface-variant)] mt-1">
                  Block Height #19,842,912 · Slot 8,912,410 · Epoch 278,512 · Finalized
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span className="px-3 py-1 rounded-full bg-[var(--color-secondary)]/10 text-[var(--color-secondary)] border border-[var(--color-secondary)]/20 font-bold uppercase tracking-wider">
                System Status: Nominal
              </span>
            </div>
          </div>

          {/* 4 Infrastructure Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-[var(--color-surface-container-low)] rounded-xl p-5 border border-[var(--color-outline)]/50 flex flex-col justify-between h-32 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-primary)] opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="flex items-center justify-between text-[13px] text-[var(--color-on-surface-variant)] font-medium uppercase tracking-wider">
                <span>RPC Roundtrip</span>
                <Activity className="w-4 h-4 text-[var(--color-primary)]" />
              </div>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold text-[var(--color-on-surface)]">14 ms</span>
                <span className="text-[11px] font-semibold text-[var(--color-on-surface-variant)]">HTTP/2 Normalized</span>
              </div>
            </div>

            <div className="bg-[var(--color-surface-container-low)] rounded-xl p-5 border border-[var(--color-outline)]/50 flex flex-col justify-between h-32 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-amber-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="flex items-center justify-between text-[13px] text-[var(--color-on-surface-variant)] font-medium uppercase tracking-wider">
                <span>24H RPC Calls</span>
                <Zap className="w-4 h-4 text-[var(--color-tertiary)]" />
              </div>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold text-[var(--color-on-surface)]">14.2k</span>
                <span className="text-[11px] font-semibold text-[var(--color-secondary)]">0.02% Error Rate</span>
              </div>
            </div>

            <div className="bg-[var(--color-surface-container-low)] rounded-xl p-5 border border-[var(--color-outline)]/50 flex flex-col justify-between h-32 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="flex items-center justify-between text-[13px] text-[var(--color-on-surface-variant)] font-medium uppercase tracking-wider">
                <span>Mempool Peers</span>
                <Cpu className="w-4 h-4 text-blue-500" />
              </div>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold text-[var(--color-on-surface)]">42</span>
                <span className="text-[11px] font-semibold text-[var(--color-on-surface-variant)]">Connected</span>
              </div>
            </div>

            <div className="bg-[var(--color-surface-container-low)] rounded-xl p-5 border border-[var(--color-outline)]/50 flex flex-col justify-between h-32 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-purple-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="flex items-center justify-between text-[13px] text-[var(--color-on-surface-variant)] font-medium uppercase tracking-wider">
                <span>Database IOPS</span>
                <Database className="w-4 h-4 text-purple-500" />
              </div>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold text-[var(--color-on-surface)]">4.2ms</span>
                <span className="text-[11px] font-semibold text-[var(--color-secondary)]">Healthy</span>
              </div>
            </div>
          </div>

          {/* Detailed Provider Configuration Grid */}
          <div className="bg-[var(--color-surface-container-low)] border border-[var(--color-outline)]/50 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-[var(--color-outline)] flex items-center justify-between">
              <span className="font-semibold text-[var(--color-on-surface)] uppercase text-[12px] tracking-wider">Infrastructure Endpoints</span>
              <span className="text-[12px] font-bold text-[var(--color-secondary)]">ONLINE & RESPONSIVE</span>
            </div>

            <div className="p-6 space-y-4">
              <div className="p-4 bg-[var(--color-surface-dim)] rounded-xl border border-[var(--color-outline)] flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors hover:border-[var(--color-primary)]/50">
                <div>
                  <span className="text-[11px] font-bold text-[var(--color-on-surface-variant)] block uppercase tracking-wider mb-1">RPC Provider Integration</span>
                  <span className="text-sm font-bold text-[var(--color-on-surface)]">Alchemy Ethereum Mainnet Enterprise Gateway</span>
                  <span className="text-xs text-[var(--color-on-surface-variant)] block mt-1 font-bold">
                    Endpoint: https://eth-mainnet.g.alchemy.com/v2/
                  </span>
                </div>
                <div className="flex items-center gap-2 text-[var(--color-secondary)] text-xs font-bold bg-[var(--color-secondary)]/10 px-3 py-1.5 rounded-lg border border-[var(--color-secondary)]/20">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>ONLINE</span>
                </div>
              </div>

              <div className="p-4 bg-[var(--color-surface-dim)] rounded-xl border border-[var(--color-outline)] flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors hover:border-[var(--color-primary)]/50">
                <div>
                  <span className="text-[11px] font-bold text-[var(--color-on-surface-variant)] block uppercase tracking-wider mb-1">Credential Custody & Security</span>
                  <span className="text-sm font-bold text-[var(--color-on-surface)]">alch_live_••••••••••••••••91a2</span>
                  <span className="text-xs text-[var(--color-secondary)] block mt-1">
                    Masked & secured server-side · 0 client leakage · ADR-002 Compliant
                  </span>
                </div>
                <span className="px-3 py-1.5 rounded-lg bg-[var(--color-surface-container-high)] text-[var(--color-on-surface-variant)] border border-[var(--color-outline)] text-xs font-bold">
                  SECURED
                </span>
              </div>

              <div className="p-4 bg-[var(--color-surface-dim)] rounded-xl border border-[var(--color-outline)] flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors hover:border-[var(--color-primary)]/50">
                <div>
                  <span className="text-[11px] font-bold text-[var(--color-on-surface-variant)] block uppercase tracking-wider mb-1">AI Inference Engine Gateway</span>
                  <span className="text-sm font-bold text-purple-400">OpenRouter Inference Gateway (Qwen 27B / Claude 3.5)</span>
                  <span className="text-xs text-[var(--color-on-surface-variant)] block mt-1">
                    Latency: 310ms TTFT · Streaming Enabled · Grounded Heuristics Active
                  </span>
                </div>
                <span className="px-3 py-1.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/30 text-xs font-bold uppercase">
                  Connected
                </span>
              </div>

              <div className="p-4 bg-[var(--color-surface-dim)] rounded-xl border border-[var(--color-outline)] flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors hover:border-[var(--color-primary)]/50">
                <div>
                  <span className="text-[11px] font-bold text-[var(--color-on-surface-variant)] block uppercase tracking-wider mb-1">Relational Evidence Vault</span>
                  <span className="text-sm font-bold text-[var(--color-on-surface)]">PostgreSQL Evidence Store</span>
                  <span className="text-xs text-[var(--color-on-surface-variant)] block mt-1">
                    Pool: 20 connections · SSL Required · Point-in-time recovery active
                  </span>
                </div>
                <span className="px-3 py-1.5 rounded-lg bg-[var(--color-secondary)]/10 text-[var(--color-secondary)] border border-green-500/30 text-xs font-bold uppercase">
                  Synced
                </span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
