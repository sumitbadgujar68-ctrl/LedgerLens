import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  FolderSearch,
  FileCheck2,
  FileSpreadsheet,
  Activity,
  GitBranch,
  Server,
  LogOut,
  PlusCircle,
  Network,
  Settings as SettingsIcon,
  ChevronRight,
} from 'lucide-react';
import { notifySignOut } from '../../services/auth';
import { api } from '../../services/api';
import { useInvestigationStore } from '../../store/investigationStore';

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const { currentCase, setNewCaseModalOpen, language } = useInvestigationStore();

  const handleSignOut = async () => {
    try {
      await api.logout();
    } catch {
      // ignore
    } finally {
      notifySignOut();
    }
  };

  type NavItem = {
    label: string;
    path: string;
    icon: React.FC<any>;
    active: boolean;
    showPulse?: boolean;
    count?: string;
  };

  type NavGroup = {
    title: string;
    badge?: string;
    items: NavItem[];
  };

  const navGroups: NavGroup[] = [
    {
      title: language === 'HI' ? 'फोरेंसिक कोर' : 'FORENSIC CORE',
      items: [
        {
          label: language === 'HI' ? 'जांच (Investigate)' : 'Investigate',
          path: '/',
          icon: Activity,
          active: location.pathname === '/',
        },
        {
          label: language === 'HI' ? 'लाइव ट्रेस' : 'Live Trace',
          path: currentCase ? `/cases/${currentCase.case_id}/graph` : '/cases',
          icon: GitBranch,
          active: location.pathname.endsWith('/graph') || location.pathname.endsWith('/trace'),
          showPulse: true,
        },
        {
          label: language === 'HI' ? 'क्लस्टरिंग' : 'Clustering',
          path: currentCase ? `/cases/${currentCase.case_id}/patterns` : '/cases',
          icon: Network,
          active: location.pathname.endsWith('/patterns') || location.pathname === '/attribution',
        },
      ],
    },
    {
      title: language === 'HI' ? 'कस्टडी एवं डॉज़ियर' : 'CUSTODY & DOSSIERS',
      items: [
        {
          label: language === 'HI' ? 'साक्ष्य लॉकर' : 'Evidence Locker',
          path: currentCase ? `/cases/${currentCase.case_id}/evidence` : '/cases',
          icon: FileCheck2,
          active: location.pathname.endsWith('/evidence'),
        },
        {
          label: language === 'HI' ? 'केस फाइलें' : 'Case Files',
          path: '/cases',
          icon: FolderSearch,
          active: location.pathname === '/cases' || (location.pathname.startsWith('/cases/') && location.pathname.split('/').length <= 3),
        },
        {
          label: language === 'HI' ? 'ऑडिट लॉग' : 'Audit Logs',
          path: currentCase ? `/cases/${currentCase.case_id}/report` : '/cases',
          icon: FileSpreadsheet,
          active: location.pathname.endsWith('/report') || location.pathname === '/reports',
        },
      ],
    },
  ];

  return (
    <aside className="w-64 bg-[var(--color-surface-container)] border-r border-[var(--color-outline)] flex flex-col justify-between p-4 shrink-0 h-screen overflow-y-auto">
      {/* Top Brand & Action Section */}
      <div className="flex flex-col gap-4">
        {/* Brand Header */}
        <div className="flex items-center justify-between pb-6">
          <div className="flex items-center gap-3 w-full justify-center pb-2">
            <img src="/logo.png" alt="LedgerLens" className="w-40 h-auto rounded-xl drop-shadow-lg" />
          </div>
        </div>
        
        {/* Primary CTA: New Investigation */}
        <button 
          onClick={() => setNewCaseModalOpen(true)}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-[var(--color-primary-container)] text-[var(--color-on-primary-container)] rounded-lg font-[Inter] text-[16px] font-semibold hover:brightness-110 active:scale-95 transition-all duration-150 shadow-sm cursor-pointer">
          <PlusCircle className="w-[18px] h-[18px]" />
          <span>New Investigation</span>
        </button>
        
        {/* Navigation Sections */}
        {navGroups.map((group) => (
          <div key={group.title} className="flex flex-col gap-1 mt-4">
            <div className="px-3 py-1 flex items-center justify-between mb-1">
              <span className="font-[Inter] text-[10px] font-semibold tracking-wider text-[var(--color-on-surface-variant)] uppercase">
                {group.title}
              </span>
            </div>
            
            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.label}
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-2.5 my-0.5 transition-colors duration-150 rounded-lg ${
                    item.active
                      ? 'bg-[var(--color-primary)] text-[var(--color-on-primary)] font-[Inter] text-[14px] font-medium'
                      : 'text-[var(--color-on-surface-variant)] font-[Inter] text-[14px] font-medium hover:text-[var(--color-on-surface)]'
                  }`}
                >
                  <Icon className="w-[18px] h-[18px]" />
                  <span className="truncate">{item.label}</span>
                  
                  <ChevronRight className={`ml-auto w-4 h-4 ${item.active ? 'text-white' : 'text-[var(--color-on-surface-variant)]'}`} />
                </Link>
              );
            })}
          </div>
        ))}
      </div>

      {/* Sidebar Bottom: Telemetry & Node Health Footer */}
      <div className="pt-3 border-t border-[var(--color-outline)] flex flex-col gap-2">
        {/* Live RPC Node Telemetry Panel */}
        <div className="p-2.5 rounded-lg bg-[var(--color-surface-container-lowest)] border border-[var(--color-outline)] flex flex-col gap-1.5">
          <div className="flex items-center justify-between font-[JetBrains_Mono] text-[10px] font-semibold tracking-[0.08em]">
            <span className="flex items-center gap-1.5 text-[var(--color-on-surface)]">
              <span className="w-2 h-2 rounded-full bg-[var(--color-tertiary)]"></span>
              RPC NODE HEALTH
            </span>
            <span className="text-[var(--color-tertiary)] font-[JetBrains_Mono] font-normal">99.98%</span>
          </div>
          <div className="flex items-center justify-between font-[JetBrains_Mono] text-[11px] text-[var(--color-on-surface-variant)]">
            <span>PEERS: 64</span>
            <span>LAT: 12ms</span>
          </div>
          <div className="font-[JetBrains_Mono] text-[10px] text-[var(--color-on-surface-variant)]/80 truncate">
            BLOCK: #19,842,912
          </div>
        </div>
        
        {/* Footer Buttons */}
        <div className="flex flex-col gap-0.5">
          <Link
            to="/settings"
            className="flex items-center gap-2.5 px-2.5 py-1.5 text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)] rounded text-[12px] font-[Inter] transition-colors cursor-pointer"
          >
            <Server className="w-[16px] h-[16px]" />
            <span>RPC Node Health</span>
          </Link>
          <Link
            to="/settings"
            className="flex items-center gap-2.5 px-2.5 py-1.5 text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)] rounded text-[12px] font-[Inter] transition-colors cursor-pointer"
          >
            <SettingsIcon className="w-[16px] h-[16px]" />
            <span>System Settings</span>
          </Link>
          <button onClick={handleSignOut} className="flex items-center gap-2.5 px-2.5 py-1.5 text-[var(--color-on-surface-variant)] hover:text-[var(--color-error)] hover:bg-[var(--color-error)]/10 rounded text-[12px] font-[Inter] transition-colors cursor-pointer">
            <LogOut className="w-[16px] h-[16px]" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </aside>
  );
};



