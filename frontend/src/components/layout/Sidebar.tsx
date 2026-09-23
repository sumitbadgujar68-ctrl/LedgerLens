import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  FolderSearch, 
  ShieldCheck, 
  Settings, 
  LogOut, 
  Radar,
  Network
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const location = useLocation();

  const navItems = [
    {
      label: 'Investigations',
      icon: FolderSearch,
      path: '/',
      active: location.pathname === '/' || location.pathname.startsWith('/cases'),
    },
    {
      label: 'Evidence Custody',
      icon: ShieldCheck,
      path: '/evidence',
      active: location.pathname === '/evidence',
    },
    {
      label: 'Node & Telemetry',
      icon: Settings,
      path: '/settings',
      active: location.pathname === '/settings',
    },
  ];

  return (
    <aside className="w-64 bg-[#0D1017] border-r border-[#1F2637] flex flex-col justify-between select-none shrink-0 min-h-screen">
      <div>
        {/* Brand Header */}
        <div className="p-4 border-b border-[#1F2637] flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-blue-600/20 border border-blue-500/50 flex items-center justify-center text-blue-400">
              <Radar className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-sm tracking-wider text-slate-100 flex items-center gap-1.5">
                LEDGERLENS
                <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-blue-900/60 text-blue-300 border border-blue-700/50">
                  MVP
                </span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                FORENSIC SUITE v0.3
              </div>
            </div>
          </Link>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1.5">
          <div className="px-3 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
            Navigation
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.label}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded text-xs font-medium transition-all ${
                  item.active
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#161B26]'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status & Session */}
      <div className="p-3 border-t border-[#1F2637] space-y-2">
        <div className="p-2.5 rounded bg-[#121620] border border-[#1F2637] text-xs">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5 text-emerald-400" />
              Provider
            </span>
            <span className="font-mono text-emerald-400 text-[11px]">ALCH-ETH</span>
          </div>
          <div className="text-[11px] text-slate-400 flex justify-between">
            <span>Latency</span>
            <span className="font-mono text-slate-300">~142ms</span>
          </div>
        </div>

        <div className="flex items-center justify-between px-2 py-1 text-xs text-slate-400">
          <span className="font-mono text-[11px]">OFFICER #402</span>
          <button 
            onClick={() => alert('Session termination requested')} 
            className="hover:text-red-400 p-1 rounded hover:bg-slate-800 transition-colors"
            title="Log out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
