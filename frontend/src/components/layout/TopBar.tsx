import { Bell, MessageSquare, Search, ChevronDown, Globe } from 'lucide-react';

interface TopBarProps {
  onNewCase?: () => void;
  title?: string;
  subtitle?: string;
  onSearch?: (query: string) => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onSearch }) => {
  return (
    <header className="h-[72px] bg-[var(--color-surface)] border-b border-[var(--color-outline)] flex items-center justify-between px-6 shrink-0">
      <div className="flex-1 flex items-center">
        <div className="relative w-96">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[var(--color-on-surface-variant)]">
            <Search className="w-4 h-4" />
          </div>
          <input
            className="w-full pl-10 pr-4 py-2 bg-[var(--color-surface-container)] border border-transparent rounded-lg text-[var(--color-on-surface)] placeholder-[var(--color-on-surface-variant)]/60 font-[Inter] text-[13px] focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-all duration-150"
            placeholder="Search"
            type="text"
            onChange={(e) => onSearch?.(e.target.value)}
          />
        </div>
      </div>

      <div className="flex items-center gap-5">
        <button className="text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] transition-colors cursor-pointer">
          <MessageSquare className="w-5 h-5" />
        </button>
        <button className="relative text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] transition-colors cursor-pointer">
          <Bell className="w-5 h-5" />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-[var(--color-primary)] rounded-full border-2 border-[var(--color-surface)]"></span>
        </button>
        
        <div className="flex items-center gap-3 ml-2 cursor-pointer group">
          <div className="w-9 h-9 rounded-full overflow-hidden border border-transparent group-hover:border-[var(--color-primary)] transition-colors">
            <img src="https://i.pravatar.cc/150?img=33" alt="User" className="w-full h-full object-cover" />
          </div>
          <div className="flex flex-col text-left">
            <span className="text-[13px] font-semibold text-[var(--color-on-surface)] leading-tight">Austin Robertson</span>
            <span className="text-[11px] text-[var(--color-on-surface-variant)] leading-tight mt-0.5">Marketing Administrator</span>
          </div>
          <ChevronDown className="w-4 h-4 text-[var(--color-on-surface-variant)]" />
        </div>

        <div className="flex items-center gap-1 ml-3 px-2 py-1 bg-[var(--color-surface-container)] rounded-md cursor-pointer border border-[var(--color-outline)]">
          <Globe className="w-4 h-4 text-blue-400" />
          <ChevronDown className="w-3 h-3 text-[var(--color-on-surface-variant)]" />
        </div>
      </div>
    </header>
  );
};


