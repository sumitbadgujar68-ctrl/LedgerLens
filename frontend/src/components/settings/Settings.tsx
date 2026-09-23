import React from 'react';
import { TopBar } from '../layout/TopBar';
import { Server, CheckCircle } from 'lucide-react';

export const Settings: React.FC = () => {
  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[#090B10]">
      <TopBar title="System Configuration & Node Telemetry" />

      <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-4xl">
        <div className="bg-[#121620] border border-[#1F2637] rounded p-6 space-y-4">
          <div className="flex items-center gap-3">
            <Server className="w-5 h-5 text-blue-400" />
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Blockchain RPC Provider Configuration
            </h2>
          </div>

          <div className="space-y-3 font-mono text-xs text-slate-300">
            <div className="p-3 bg-[#090B10] rounded border border-[#1F2637] flex justify-between items-center">
              <div>
                <span className="text-slate-400 block text-[11px]">ACTIVE PROVIDER</span>
                <span className="text-emerald-400 font-bold">AlchemyProvider (Ethereum Adapter)</span>
              </div>
              <span className="flex items-center gap-1 text-[11px] text-emerald-400">
                <CheckCircle className="w-3.5 h-3.5" />
                ONLINE
              </span>
            </div>

            <div className="p-3 bg-[#090B10] rounded border border-[#1F2637] flex justify-between items-center">
              <div>
                <span className="text-slate-400 block text-[11px]">TARGET RPC NETWORK</span>
                <span className="text-slate-200">eth-mainnet.g.alchemy.com</span>
              </div>
              <span className="text-[11px] text-slate-400">HTTP/2 NORMALIZED</span>
            </div>

            <div className="p-3 bg-[#090B10] rounded border border-[#1F2637] flex justify-between items-center">
              <div>
                <span className="text-slate-400 block text-[11px]">API KEY STATUS</span>
                <span className="text-slate-200">MASKED (backend-secured, 0 client leakage)</span>
              </div>
              <span className="text-[11px] text-blue-400">ADR-002 COMPLIANT</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
