import React from 'react';
import { LogOut, Search, Plus } from 'lucide-react';
import { api } from '../../services/api';
import { clearSession, notifyUnauthorized } from '../../services/auth';

interface TopBarProps {
  onNewCase?: () => void;
  title?: string;
}

export const TopBar: React.FC<TopBarProps> = ({ onNewCase, title = 'Investigator Dispatch Console' }) => {
  const handleSignOut = async () => {
    try {
      await api.logout();
    } catch {
      clearSession();
    }
    notifyUnauthorized();
  };

  return (
    <header className="h-14 bg-[#090B10] border-b border-[#1F2637] px-6 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-4">
        <h1 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
          {title}
        </h1>
        <div className="h-4 w-px bg-[#1F2637]" />
        <span className="text-xs text-slate-400 font-mono hidden md:inline">
          DATABASE: CONNECTED (POSTGRESQL)
        </span>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative w-64 hidden sm:block">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search address, hash, or case..."
            className="w-full bg-[#121620] border border-[#1F2637] rounded pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-mono"
          />
        </div>

        {onNewCase && (
          <button
            onClick={onNewCase}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold shadow-sm transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>New Investigation</span>
          </button>
        )}

        <button
          onClick={handleSignOut}
          className="flex items-center gap-1.5 px-3 py-1.5 border border-[#1F2637] hover:border-slate-500 text-slate-300 rounded text-xs font-semibold transition-colors cursor-pointer"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign out</span>
        </button>
      </div>
    </header>
  );
};
