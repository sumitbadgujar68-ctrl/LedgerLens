import React from 'react';
import { Search } from 'lucide-react';
import { useInvestigationStore } from '../../store/investigationStore';
import { NetworkChip } from '../common/Badge';

export function TopNav() {
  const { globalSearchQuery, setGlobalSearchQuery, currentCase, language, setLanguage } = useInvestigationStore();
  const [isDarkMode, setIsDarkMode] = React.useState(() => document.documentElement.classList.contains('dark'));

  const toggleTheme = () => {
    const isDark = document.documentElement.classList.toggle('dark');
    setIsDarkMode(isDark);
  };

  return (
    <header className="h-14 border-b border-[var(--color-outline-variant)] bg-[var(--color-surface-container)] flex items-center justify-between px-[var(--spacing-space-lg)] shrink-0 z-30">
      <div className="flex items-center gap-3 w-1/3 min-w-[320px]">
        <div className="relative w-full">
          <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-[var(--color-on-surface-variant)]">
            <Search className="w-[18px] h-[18px]" />
          </div>
          <input
            className="w-full pl-9 pr-14 py-1.5 bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] rounded-lg text-[var(--color-on-surface)] placeholder-[var(--color-on-surface-variant)]/60 font-[JetBrains_Mono] text-[12px] focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-all duration-150"
            placeholder={language === 'HI' ? "पता, tx हैश, या डॉज़ियर खोजें..." : "Search address, tx hash, or dossier..."}
            type="text"
            value={globalSearchQuery}
            onChange={(e) => setGlobalSearchQuery(e.target.value)}
          />
          <div className="absolute inset-y-0 right-0 pr-2 flex items-center pointer-events-none">
            <span className="font-[JetBrains_Mono] text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-surface-container-highest)] text-[var(--color-on-surface-variant)] border border-[var(--color-outline)]">Ctrl+K</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {currentCase?.blockchain && (
          <div className="flex items-center gap-2 px-2.5 py-1 bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] rounded-lg font-[JetBrains_Mono] text-[12px]">
            <NetworkChip network={currentCase.blockchain} className="bg-transparent border-0 p-0 shadow-none text-[var(--color-on-surface)] uppercase font-semibold text-[11px]" />
          </div>
        )}

        <div className="hidden xl:flex items-center gap-2 px-2 py-1 bg-[var(--color-surface-container-lowest)] border border-[var(--color-outline)] rounded text-[11px] font-[JetBrains_Mono]">
          <span className="text-[var(--color-on-surface-variant)]">RPC: <span className="text-[var(--color-tertiary)]">4ms</span></span>
          <span className="text-[var(--color-outline)]">|</span>
          <span className="text-[var(--color-on-surface-variant)]">DB: <span className="text-[var(--color-tertiary)]">SYNCED</span></span>
        </div>

        <div className="h-5 w-[1px] bg-[var(--color-outline)] mx-1"></div>

        <div className="flex items-center gap-2 pl-1 cursor-pointer">
          <div className="w-7 h-7 rounded-full bg-[var(--color-primary-container)]/20 border border-[var(--color-primary)]/40 flex items-center justify-center text-[var(--color-primary)] font-[Inter] text-xs font-bold">
            KV
          </div>
          <div className="flex flex-col text-left leading-tight hidden sm:flex">
            <span className="font-[Inter] text-[12px] font-semibold text-[var(--color-on-surface)]">{language === 'HI' ? "डिटेक्टिव के. वेंस" : "Det. K. Vance"}</span>
            <span className="font-[JetBrains_Mono] text-[10px] text-[var(--color-on-surface-variant)]">LL-8491 • {language === 'HI' ? 'प्रमुख' : 'LEAD'}</span>
          </div>
        </div>

        <div className="h-5 w-[1px] bg-[var(--color-outline)] mx-1"></div>

        {/* Language Toggle */}
        <div className="flex items-center gap-0.5 bg-[var(--color-surface-container-high)] p-0.5 rounded-md border border-[var(--color-outline)]">
          <button 
            onClick={() => setLanguage('EN')}
            className={`px-1.5 py-0.5 text-[9px] font-bold rounded-sm transition-all cursor-pointer ${language === 'EN' ? 'bg-[var(--color-primary)] text-[var(--color-on-primary)] shadow-sm' : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)]'}`}
          >
            EN
          </button>
          <button 
            onClick={() => setLanguage('HI')}
            className={`px-1.5 py-0.5 text-[9px] font-bold rounded-sm transition-all cursor-pointer ${language === 'HI' ? 'bg-[var(--color-primary)] text-[var(--color-on-primary)] shadow-sm' : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)]'}`}
          >
            HI
          </button>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="relative inline-flex h-5 w-9 items-center rounded-full bg-[var(--color-surface-container-high)] border border-[var(--color-outline)] transition-colors cursor-pointer ml-1"
        >
          <span className="sr-only">Toggle dark mode</span>
          <span className={`inline-block h-3 w-3 transform rounded-full bg-[var(--color-primary)] transition-transform duration-200 ${isDarkMode ? 'translate-x-5' : 'translate-x-1'}`} />
        </button>
      </div>
    </header>
  );
}
