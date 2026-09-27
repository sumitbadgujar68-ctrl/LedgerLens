import React, { useState } from 'react';
import { X, Bot, Gauge, FileText } from 'lucide-react';
import { CopilotPanel } from '../copilot/CopilotPanel';
import { ReportsPanel } from '../reports/ReportsPanel';
import { RiskCard } from '../risk/RiskCard';
import { RiskSummaryCard } from '../risk/RiskSummaryCard';

interface AnalysisPanelProps {
  caseId: string;
  seedWalletAddress: string;
  selectedWalletAddress?: string | null;
  onClose: () => void;
}

type AnalysisTab = 'copilot' | 'risk' | 'reports';

const TABS: Array<{ id: AnalysisTab; label: string; icon: React.ReactNode }> = [
  { id: 'copilot', label: 'COPILOT', icon: <Bot className="w-3.5 h-3.5" /> },
  { id: 'risk', label: 'RISK', icon: <Gauge className="w-3.5 h-3.5" /> },
  { id: 'reports', label: 'REPORTS', icon: <FileText className="w-3.5 h-3.5" /> },
];

export const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  caseId,
  seedWalletAddress,
  selectedWalletAddress,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<AnalysisTab>('copilot');
  const riskWallet = selectedWalletAddress || seedWalletAddress;

  return (
    <aside className="w-[450px] bg-[var(--color-surface-dim)] border-l border-[var(--color-outline)] flex flex-col h-full overflow-hidden shadow-2xl shrink-0 z-20">
      <div className="h-14 bg-[var(--color-surface-dim)] border-b border-[var(--color-outline)] px-4 flex items-center justify-between shrink-0 select-none">
        <div className="flex items-center gap-2">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                activeTab === tab.id
                  ? 'bg-[var(--color-surface-container-low)] text-[var(--color-primary)] border border-[var(--color-outline)] shadow-sm'
                  : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] border border-transparent'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
        <button
          onClick={onClose}
          title="Close analysis panel"
          className="p-1.5 rounded-lg text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)] transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 min-h-0 overflow-hidden">
        {activeTab === 'copilot' && (
          <CopilotPanel caseId={caseId} selectedWalletAddress={selectedWalletAddress} />
        )}

        {activeTab === 'risk' && (
          <div className="h-full overflow-y-auto p-4 space-y-4">
            <RiskSummaryCard caseId={caseId} />
            <div className="space-y-2">
              <div className="flex items-center justify-between px-1">
                <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-on-surface-variant)]">
                  Wallet Risk Detail
                </span>
                {!selectedWalletAddress && (
                  <span className="text-[10px] font-bold text-[var(--color-tertiary)] uppercase tracking-wider bg-[var(--color-tertiary)]/10 px-2 py-0.5 rounded-md">Seed Fallback</span>
                )}
              </div>
              <RiskCard caseId={caseId} walletAddress={riskWallet} />
            </div>
          </div>
        )}

        {activeTab === 'reports' && <ReportsPanel caseId={caseId} />}
      </div>
    </aside>
  );
};
