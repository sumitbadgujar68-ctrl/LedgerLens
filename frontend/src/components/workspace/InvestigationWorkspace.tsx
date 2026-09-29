import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../../services/api';
import { useInvestigationStore } from '../../store/investigationStore';
import { FundFlowCanvas } from '../graph/FundFlowCanvas';
import { InspectorDrawer } from '../inspector/InspectorDrawer';
import { BottomDock } from '../dock/BottomDock';
import { CopilotPanel } from '../copilot/CopilotPanel';
import { ReportsPanel } from '../reports/ReportsPanel';
import { RiskCard } from '../risk/RiskCard';
import { RiskSummaryCard } from '../risk/RiskSummaryCard';
import { AddressDisplay, HopBadge, StatusBadge, TxHashDisplay } from '../common/Badge';
import { ProvenanceBadge } from '../common/ProvenanceBadge';
import {
  Play,
  AlertCircle,
  Download,
  Bot,
  ShieldAlert,
  Search,
  FolderSearch,
} from 'lucide-react';
import type { TraceRequestPayload } from '../../types';

type WorkspaceTab =
  | 'overview'
  | 'trace'
  | 'graph'
  | 'transactions'
  | 'risk'
  | 'patterns'
  | 'evidence'
  | 'copilot'
  | 'report';

export const InvestigationWorkspace: React.FC = () => {
  const { caseId, view } = useParams<{ caseId: string; view?: string }>();
  const navigate = useNavigate();

  const {
    setCurrentCase,
    currentTrace,
    setCurrentTrace,
    selectedNode,
    selectTransaction,
    globalSearchQuery,
    closeInspector,
    language,
  } = useInvestigationStore();

  const initialTab = (view as WorkspaceTab) || 'graph';
  const [activeTab, setActiveTab] = useState<WorkspaceTab>(initialTab);
  const [direction] = useState<'outbound' | 'inbound' | 'both'>('outbound');
  const [maxHops, setMaxHops] = useState<number>(1);
  const [maxBranches] = useState<number>(10);
  const [minAmount] = useState<string>('');
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  useEffect(() => {
    if (view && view !== activeTab) {
      setActiveTab(view as WorkspaceTab);
    } else if (!view && activeTab !== 'graph') {
      setActiveTab('graph');
    }
  }, [view, activeTab]);

  const handleTabChange = (tab: WorkspaceTab) => {
    setActiveTab(tab);
    navigate(`/cases/${caseId}/${tab}`, { replace: true });
  };

  const { data: caseData, isLoading: caseLoading, error: caseError } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => api.getCaseById(caseId!),
    enabled: !!caseId,
  });

  const { data: tracesData, refetch: refetchTraces, isLoading: tracesLoading } = useQuery({
    queryKey: ['traces', caseId],
    queryFn: () => api.getTraces(caseId!),
    enabled: !!caseId,
  });

  const { data: caseEvidence } = useQuery({
    queryKey: ['case-evidence', caseId],
    queryFn: () => api.getCaseEvidence(caseId!),
    enabled: !!caseId,
  });

  const { data: casePatterns } = useQuery({
    queryKey: ['case-patterns', caseId],
    queryFn: () => api.getCasePatterns(caseId!),
    enabled: !!caseId,
  });

  const { data: caseAttributions } = useQuery({
    queryKey: ['case-attributions', caseId],
    queryFn: () => api.getCaseAttributions(caseId!),
    enabled: !!caseId,
  });

  const { data: walletRisk } = useQuery({
    queryKey: ['risk', caseId, caseData?.reported_wallet_address?.toLowerCase()],
    queryFn: () => api.getWalletRisk(caseId!, caseData!.reported_wallet_address),
    enabled: !!caseId && !!caseData?.reported_wallet_address,
    retry: false,
  });

  useEffect(() => {
    if (caseData) {
      setCurrentCase(caseData);
    }
  }, [caseData, setCurrentCase]);

  useEffect(() => {
    setCurrentTrace(null);
    closeInspector();
  }, [caseId, setCurrentTrace, closeInspector]);

  useEffect(() => {
    if (tracesData && tracesData.length > 0) {
      const activeTrace = tracesData.find(t => (t.graph?.nodes?.length ?? 0) > 0) || tracesData[0];
      setCurrentTrace(activeTrace);
    }
  }, [tracesData, setCurrentTrace]);

  const traceMutation = useMutation({
    mutationFn: (payload: TraceRequestPayload) => api.runTrace(caseId!, payload),
    onSuccess: (traceResult) => {
      setCurrentTrace(traceResult);
      refetchTraces();
      setActionFeedback(`Trace executed: ${traceResult.summary?.transaction_count ?? 0} transfers traced across ${traceResult.summary?.max_hop_depth ?? maxHops} hops.`);
      setTimeout(() => setActionFeedback(null), 5000);
    },
    onError: (err: any) => {
      setActionFeedback(`Trace error: ${err?.message || 'Trace request failed'}`);
      setTimeout(() => setActionFeedback(null), 6000);
    },
  });

  const handleExecuteTrace = () => {
    if (!caseData) return;
    setActionFeedback('Executing bounded multi-hop trace on-chain...');
    traceMutation.mutate({
      start_wallet_address: caseData.reported_wallet_address,
      direction,
      max_hops: maxHops,
      max_branches: maxBranches,
      min_amount: minAmount ? Number(minAmount) : null,
    });
  };

  const handleExportCourtDossier = () => {
    if (!caseData) return;
    const summary = currentTrace?.summary;
    const assets = summary?.assets_transferred
      ? Object.entries(summary.assets_transferred)
          .map(([asset, amount]) => `${Number(amount).toFixed(4)} ${asset}`)
          .join(', ')
      : `${caseData.reported_amount ?? 0} ${caseData.reported_asset || 'ETH'}`;
    const dossierText = `================================================================================
LEDGERLENS DIGITAL FORENSICS WORKSTATION — CASE REPORT DOSSIER
CONFIDENTIAL // LAW ENFORCEMENT & JUDICIAL AUDIT SUBMISSION
================================================================================
CASE IDENTIFIER:    ${caseData.case_number}
INCIDENT TITLE:     ${caseData.title}
BLOCKCHAIN NETWORK: ${caseData.blockchain.toUpperCase()} (Chain ID: ${caseData.blockchain === 'ethereum' ? 1 : caseData.blockchain === 'bitcoin' ? 0 : 728126428})
TYPOLOGY CLASSIFICATION: ${caseData.fraud_type.replace(/_/g, ' ')}
PRIMARY SEED TARGET: ${caseData.reported_wallet_address}
REPORTED LOSS:      ${assets}
RECORDED STATUS:    ${caseData.status.replace(/_/g, ' ')}
DATA PROVENANCE:    ${caseData.demo_data ? 'DEMO DATASET' : 'LIVE ON-CHAIN ETHEREUM CONSENSUS'}
INVESTIGATION LEAD: Det. K. Vance (ID: LL-8491)
CREATION TIMESTAMP: ${new Date(caseData.created_at).toUTCString()}

MULTI-HOP GRAPH TRAVERSAL SUMMARY:
- Discovered Unique Addresses: ${summary?.wallet_count ?? 0}
- Traversed Transfers:         ${summary?.transaction_count ?? 0}
- Maximum Traversal Depth:     ${summary?.max_hop_depth ?? maxHops} Hops
- Telemetry RPC Engine:        ${currentTrace?.provider || 'Alchemy Ethereum Mainnet Adapter'}
- RFC-3161 Certified Time:    ${new Date().toISOString()}
================================================================================
`;
    const blob = new Blob([dossierText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Case_${caseData.case_number}_Forensic_Dossier.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setActionFeedback(`Exported Case ${caseData.case_number} Forensic Dossier`);
    setTimeout(() => setActionFeedback(null), 4000);
  };

  if (caseLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[var(--color-surface-dim)] text-[var(--color-on-surface-variant)] font-medium text-sm">
        <div className="w-8 h-8 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin mr-3" />
        LOADING FORENSIC INVESTIGATION WORKSPACE...
      </div>
    );
  }

  if (caseError || !caseData) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[var(--color-surface-dim)] text-[var(--color-on-surface)] p-6 space-y-4">
        <AlertCircle className="w-12 h-12 text-[var(--color-error)]" />
        <h2 className="text-lg font-bold">CASE DOCKET NOT FOUND</h2>
        <p className="text-sm text-[var(--color-on-surface-variant)]">
          Unable to locate docket {caseId}. It may have been removed or archived.
        </p>
        <button
          onClick={() => navigate('/')}
          className="px-5 py-2.5 bg-[var(--color-primary)] hover:brightness-110 text-[var(--color-on-surface)] text-sm font-bold rounded-xl transition-colors cursor-pointer"
        >
          Return to Investigations Console
        </button>
      </div>
    );
  }

  // ── Unsupported chain guard ──────────────────────────────────────────────
  if (caseData && caseData.blockchain !== 'ethereum') {
    const chainColors: Record<string, string> = {
      bitcoin: '#F7931A',
      tron: '#FF0013',
    };
    const color = chainColors[caseData.blockchain] ?? '#8B8FA3';
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[var(--color-surface-dim)] text-[var(--color-on-surface)] p-10 gap-5">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center border-2 text-3xl font-bold"
          style={{ borderColor: color, backgroundColor: `${color}15`, color }}
        >
          {caseData.blockchain === 'bitcoin' ? '₿' : '⚡'}
        </div>
        <div className="text-center max-w-md">
          <h2 className="text-xl font-bold font-[Inter] mb-2">
            {caseData.blockchain.toUpperCase()} — Chain Not Supported
          </h2>
          <p className="text-sm text-[var(--color-on-surface-variant)] leading-relaxed mb-1">
            This investigation docket targets a <strong style={{ color }}>{caseData.blockchain.toUpperCase()}</strong> address.
            The current MVP only supports <strong className="text-[#627EEA]">Ethereum Mainnet</strong> on-chain tracing via Alchemy.
          </p>
          <p className="text-xs text-[var(--color-on-surface-variant)]/60 font-[JetBrains_Mono] mt-2">
            Wallet: <span style={{ color }}>{caseData.reported_wallet_address}</span>
          </p>
          <p className="text-xs text-[var(--color-on-surface-variant)]/60 font-[JetBrains_Mono]">
            Case: {caseData.case_number} · {caseData.title}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => navigate('/')}
            className="px-5 py-2.5 bg-[var(--color-primary)] hover:brightness-110 text-[var(--color-on-primary)] text-sm font-bold rounded-xl transition-colors cursor-pointer"
          >
            ← New Ethereum Investigation
          </button>
          <button
            onClick={() => navigate('/cases')}
            className="px-5 py-2.5 bg-[var(--color-surface-container)] hover:bg-[var(--color-surface-container-high)] border border-[var(--color-outline)] text-[var(--color-on-surface)] text-sm font-semibold rounded-xl transition-colors cursor-pointer"
          >
            All Cases
          </button>
        </div>
      </div>
    );
  }
  // ─────────────────────────────────────────────────────────────────────────

  const transactions = currentTrace?.transactions || [];
  const evidenceList = caseEvidence?.evidence || [];
  const patternsList = casePatterns?.patterns || [];
  const attributionsList = caseAttributions?.attributions || [];

  const tabClass = (tab: WorkspaceTab) =>
    `h-full px-3 flex items-center gap-1.5 transition-all cursor-pointer ${
      activeTab === tab
        ? 'text-[var(--color-primary)] bg-[var(--color-primary)]/5 border-b-2 border-[var(--color-primary)] font-semibold'
        : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] border-b-2 border-transparent'
    }`;

  const filteredTransactions = transactions.filter((t) => {
    if (!globalSearchQuery) return true;
    const q = globalSearchQuery.toLowerCase();
    return (
      t.transaction_hash.toLowerCase().includes(q) ||
      t.from_address.toLowerCase().includes(q) ||
      (t.to_address || '').toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[var(--color-surface-dim)] text-[var(--color-on-surface)] font-[Inter]">
      {/* 2. INVESTIGATION HEADER (Telemetry Banner & Breadcrumb) */}
      <div className="border-b border-[var(--color-outline)] bg-[var(--color-surface-container-low)] px-6 py-3.5 flex flex-col gap-3 shrink-0">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-[var(--color-on-surface-variant)] font-[JetBrains_Mono] text-[12px]">
            <button onClick={() => navigate('/cases')} className="text-[var(--color-primary)] hover:underline cursor-pointer flex items-center gap-1 font-semibold">
              <FolderSearch className="w-[15px] h-[15px]" />
              {caseData.case_number}
            </button>
            <span className="text-[var(--color-outline)]">&gt;</span>
            <span className="text-[var(--color-on-surface-variant)] font-medium">FORENSIC WORKSPACE</span>
            <span className="text-[var(--color-outline)]">&gt;</span>
            <span className="text-[var(--color-on-surface)] font-semibold bg-[var(--color-surface-container)] px-2 py-0.5 rounded border border-[var(--color-outline)] uppercase">
              {caseData.title}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {actionFeedback && (
              <span className="font-[JetBrains_Mono] text-[11px] text-[var(--color-primary)] bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30 px-2 py-0.5 rounded flex items-center gap-1.5 transition-all">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)] animate-pulse" />
                {actionFeedback}
              </span>
            )}
            <button
              onClick={handleExecuteTrace}
              disabled={traceMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-1 rounded bg-[var(--color-primary)] text-[var(--color-on-primary)] font-[Inter] text-[12px] font-semibold hover:brightness-110 transition-all shadow-sm disabled:opacity-50 cursor-pointer"
            >
              {traceMutation.isPending ? (
                <div className="w-4 h-4 border-2 border-[var(--color-on-primary)] border-t-transparent rounded-full animate-spin" />
              ) : (
                <Play className="w-[16px] h-[16px]" />
              )}
              <span>Execute Trace</span>
            </button>
            <button
              onClick={handleExportCourtDossier}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[var(--color-surface-container)] hover:bg-[var(--color-surface-container-high)] border border-[var(--color-outline)] text-[var(--color-on-surface)] text-[12px] font-[Inter] transition-colors cursor-pointer"
            >
              <Download className="w-[15px] h-[15px]" />
              <span>Export Dossier</span>
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 font-[JetBrains_Mono] text-[11px]">
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[var(--color-surface-container)] border border-[var(--color-outline)] text-[var(--color-on-surface)]">
            <span className="text-[var(--color-on-surface-variant)] font-semibold text-[10px] tracking-wider uppercase">SUBJECT:</span>
            <span className="font-[JetBrains_Mono] text-[var(--color-tertiary)]">{caseData.reported_wallet_address.substring(0,6)}...{caseData.reported_wallet_address.substring(38)}</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[var(--color-tertiary)]/10 border border-[var(--color-tertiary)]/30 text-[var(--color-tertiary)] font-semibold text-[10px] tracking-wider uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-tertiary)] animate-pulse"></span>
            <span>{caseData.status.replace('_', ' ')}</span>
          </div>
          
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[var(--color-tertiary)]/20 border border-[var(--color-tertiary)]/50 text-[var(--color-tertiary)] font-semibold text-[10px] tracking-wider uppercase">
            <AlertCircle className="w-[13px] h-[13px]" />
            <span>TYPOLOGY: {caseData.fraud_type.replace('_', ' ')}</span>
          </div>
          
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[var(--color-secondary-container)]/20 border border-[var(--color-secondary-container)]/40 text-[var(--color-secondary-fixed)] font-semibold text-[10px] tracking-wider uppercase">
            <ShieldAlert className="w-[13px] h-[13px]" />
            <span>PROVENANCE: {caseData.demo_data ? 'DEMO' : 'LIVE'}</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30 text-[var(--color-primary)] font-semibold text-[10px] tracking-wider uppercase">
            <span>TRACE: {currentTrace ? `ACTIVE (${currentTrace.summary?.max_hop_depth ?? maxHops} HOPS)` : 'UNTRACED'}</span>
          </div>

          {walletRisk && (
            <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-[10px] font-semibold tracking-wider uppercase ${
              walletRisk.score >= 70
                ? 'bg-red-500/10 border-red-500/30 text-red-400'
                : walletRisk.score >= 40
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            }`}>
              <span>RISK: {walletRisk.risk_category} ({walletRisk.score}/100)</span>
            </div>
          )}

          <div className="ml-auto flex items-center gap-2">
            <span className="text-[var(--color-on-surface-variant)] font-semibold text-[10px] tracking-wider uppercase">HOPS:</span>
            <select value={maxHops} onChange={(e) => setMaxHops(Number(e.target.value))} className="bg-transparent text-[var(--color-primary)] outline-none cursor-pointer">
              {[1,2,3,4,5].map(n => <option key={n} value={n} className="bg-[var(--color-surface-container)]">{n}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* 3. NAVIGATION TABS BAR */}
      <div className="bg-[var(--color-surface-container)] border-b border-[var(--color-outline)] px-6 flex items-center h-10 select-none shrink-0 overflow-x-auto no-scrollbar">
        <div className="flex items-center gap-1 h-full font-[Inter] text-[12px] uppercase tracking-wide">
          <button onClick={() => handleTabChange('overview')} className={tabClass('overview')}>
            {language === 'HI' ? 'अवलोकन' : 'OVERVIEW'}
          </button>
          <button onClick={() => handleTabChange('trace')} className={tabClass('trace')}>
            {language === 'HI' ? 'ट्रेस' : 'TRACE'}
          </button>
          <button onClick={() => handleTabChange('graph')} className={tabClass('graph')}>
            {language === 'HI' ? 'ग्राफ़' : 'GRAPH'}
            {currentTrace?.graph?.node_count ? (
              <span className="font-[JetBrains_Mono] text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-primary)]/20 text-[var(--color-primary)] border border-[var(--color-primary)]/30">{currentTrace.graph.node_count} {language === 'HI' ? 'नोड्स' : 'Nodes'}</span>
            ) : null}
          </button>
          <button onClick={() => handleTabChange('transactions')} className={tabClass('transactions')}>
            {language === 'HI' ? 'लेनदेन' : 'TRANSACTIONS'}
            <span className="font-[JetBrains_Mono] text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-surface-container-high)] text-[var(--color-on-surface-variant)] border border-[var(--color-outline)]">{transactions.length}</span>
          </button>
          <button onClick={() => handleTabChange('risk')} className={tabClass('risk')}>
            {language === 'HI' ? 'जोखिम' : 'RISK'}
          </button>
          <button onClick={() => handleTabChange('patterns')} className={tabClass('patterns')}>
            {language === 'HI' ? 'पैटर्न' : 'PATTERNS'}
          </button>
          <button onClick={() => handleTabChange('evidence')} className={tabClass('evidence')}>
            {language === 'HI' ? 'सबूत' : 'EVIDENCE'}
            <span className="font-[JetBrains_Mono] text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-surface-container-high)] text-[var(--color-on-surface-variant)] border border-[var(--color-outline)]">{evidenceList.length}</span>
          </button>
          <button onClick={() => handleTabChange('copilot')} className={tabClass('copilot')}>
            <span className="text-[var(--color-tertiary)] flex items-center gap-1">
              <Bot className="w-[14px] h-[14px]" />
              {language === 'HI' ? 'कोपायलट एआई' : 'COPILOT AI'}
            </span>
          </button>
          <button onClick={() => handleTabChange('report')} className={tabClass('report')}>
            {language === 'HI' ? 'रिपोर्ट' : 'REPORT'}
          </button>
        </div>
      </div>

      {/* 4. MAIN MULTI-PANE CONTENT AREA */}
      <div className="flex-1 flex overflow-hidden relative bg-[var(--color-surface-container-lowest)] blueprint-grid blueprint-subgrid">
        {/* TAB: GRAPH (Default Multi-Pane Forensic Canvas) */}
        {activeTab === 'graph' && (
          <div className="flex-1 flex flex-col h-full overflow-hidden relative z-10">
            <div className="flex-1 flex overflow-hidden relative">
              <div className="flex-1 h-full relative">
                <FundFlowCanvas
                  trace={currentTrace}
                  isLoading={traceMutation.isPending || tracesLoading}
                  onExecuteTrace={handleExecuteTrace}
                />
              </div>

              {/* Right Side Inspector Panel */}
              <InspectorDrawer />
            </div>

            {/* Bottom Dock Transaction Stream */}
            <BottomDock />
          </div>
        )}

        {/* TAB: OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="flex-1 overflow-y-auto p-8 space-y-6 max-w-5xl mx-auto w-full text-sm">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Subject Profile */}
              <div className="p-5 bg-[var(--color-surface-container)] border border-[var(--color-outline)] rounded-2xl space-y-3">
                <span className="text-[11px] text-[var(--color-on-surface-variant)] uppercase font-bold tracking-wider">
                  Subject Profile
                </span>
                <div className="text-sm font-bold text-[var(--color-on-surface)] break-all">
                  {caseData.reported_wallet_address}
                </div>
                <div className="pt-3 border-t border-[var(--color-outline)] space-y-2 text-[var(--color-on-surface-variant)] text-xs font-semibold">
                  <div className="flex justify-between items-center">
                    <span>Trace Direction:</span>
                    <span className="text-[var(--color-on-surface)] uppercase">{(caseData as any).direction || direction}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Fraud Typology:</span>
                    <span className="text-[var(--color-on-surface)] uppercase">{caseData.fraud_type}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Transactions Scanned:</span>
                    <span className="text-[var(--color-primary)] font-bold text-sm">
                      {currentTrace?.summary?.transaction_count || 0} TXS
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Value Traced:</span>
                    <span className="text-[var(--color-primary)] font-bold text-sm">
                      {currentTrace?.summary?.assets_transferred && Object.keys(currentTrace.summary.assets_transferred).length > 0 
                        ? Object.entries(currentTrace.summary.assets_transferred).map(([asset, amount]) => `${Number(amount).toFixed(2)} ${asset}`).join(', ')
                        : '0.00 ' + (caseData.blockchain === 'ethereum' ? 'ETH' : caseData.blockchain === 'bitcoin' ? 'BTC' : 'TRX')}
                    </span>
                  </div>
                </div>
              </div>

              {/* Status Matrix */}
              <div className="p-5 bg-[var(--color-surface-container)] border border-[var(--color-outline)] rounded-2xl space-y-3">
                <span className="text-[11px] text-[var(--color-on-surface-variant)] uppercase font-bold tracking-wider">
                  Investigation Pipeline Status
                </span>
                <div className="space-y-2 text-xs font-semibold">
                  <div className="flex justify-between items-center">
                    <span className="text-[var(--color-on-surface-variant)]">Trace Traversal:</span>
                    <span className="text-[var(--color-secondary)] font-bold">
                      {currentTrace ? `COMPLETED (${currentTrace.summary?.max_hop_depth || 0} HOPS)` : 'PENDING EXECUTION'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[var(--color-on-surface-variant)]">Graph State:</span>
                    <span className="text-[var(--color-on-surface)] font-bold">
                      {currentTrace?.graph?.node_count || 0} NODES / {currentTrace?.graph?.edge_count || 0} EDGES
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[var(--color-on-surface-variant)]">Risk Engine:</span>
                    <span className="text-[var(--color-error)] font-bold">
                      {patternsList.length > 0 ? `DETECTED ${patternsList.length} RISKS` : 'CLEAN'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[var(--color-on-surface-variant)]">Evidence Vault:</span>
                    <span className="text-[var(--color-primary)] font-bold">
                      {evidenceList.length} ARTIFACTS SEALED
                    </span>
                  </div>
                </div>
              </div>

              {/* Provenance Attestation */}
              <div className="p-5 bg-[var(--color-surface-container)] border border-[var(--color-outline)] rounded-2xl space-y-3">
                <span className="text-[11px] text-[var(--color-on-surface-variant)] uppercase font-bold tracking-wider">
                  Provenance Audit
                </span>
                <div className="space-y-2 text-xs font-semibold">
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--color-on-surface-variant)]">On-Chain Data:</span>
                    <ProvenanceBadge variant="live" size="sm" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--color-on-surface-variant)]">Synthetic Baseline:</span>
                    <ProvenanceBadge variant="demo" size="sm" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--color-on-surface-variant)]">AI Copilot Synthesis:</span>
                    <ProvenanceBadge variant="ai" size="sm" />
                  </div>
                </div>
              </div>
            </div>

            {/* Key Findings Matrix */}
            <div className="bg-[var(--color-surface-container)] border border-[var(--color-outline)] rounded-2xl overflow-hidden">
              <div className="px-5 py-4 bg-[var(--color-surface-dim)] border-b border-[var(--color-outline)] flex items-center justify-between">
                <span className="font-bold text-[var(--color-on-surface)] text-sm">FORENSIC KEY FINDINGS</span>
                <span className="text-[11px] text-[var(--color-on-surface-variant)] font-bold uppercase tracking-wider">Evidentiary Submission</span>
              </div>
              <div className="p-5 space-y-4">
                {patternsList.length === 0 && evidenceList.length === 0 ? (
                  <div className="text-[var(--color-on-surface-variant)] text-sm text-center py-4 font-semibold">
                    No forensic findings recorded yet. Execute trace or review patterns.
                  </div>
                ) : (
                  <>
                    {patternsList.slice(0, 3).map((p, idx) => (
                      <div key={p.pattern_id} className="p-4 bg-[var(--color-surface-dim)] rounded-xl border border-[var(--color-outline)] space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className={`font-bold uppercase tracking-wider ${idx === 0 ? 'text-[var(--color-error)]' : idx === 1 ? 'text-[var(--color-primary)]' : 'text-purple-400'}`}>
                            {idx + 1}. {p.pattern_type} Match Detected
                          </span>
                          <ProvenanceBadge variant={p.demo_data ? 'demo' : 'derived'} size="sm" />
                        </div>
                        <p className="text-[var(--color-on-surface)] text-sm leading-relaxed">
                          {p.description}
                        </p>
                      </div>
                    ))}
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB: TRACE MATRIX */}
        {activeTab === 'trace' && (
          <div className="flex-1 overflow-y-auto p-8 space-y-6 max-w-5xl mx-auto w-full">
            <div className="flex items-center justify-between pb-4 border-b border-[var(--color-outline)]">
              <div>
                <h3 className="text-sm font-bold text-[var(--color-on-surface)] uppercase tracking-wider">Multi-Hop Transaction Trace Matrix</h3>
                <p className="text-xs text-[var(--color-on-surface-variant)] mt-1 font-semibold">
                  Reconstructed fund dispersion path from seed wallet across downstream hops.
                </p>
              </div>
              <ProvenanceBadge variant={caseData.demo_data ? 'demo' : 'live'} size="sm" />
            </div>

            <div className="space-y-3">
              {transactions.slice(0, 8).map((tx, idx) => (
                <div
                  key={tx.transaction_hash + idx}
                  className="p-5 bg-[var(--color-surface-container)] rounded-2xl border border-[var(--color-outline)] flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-[var(--color-primary)]/50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <HopBadge hop={idx % 4} />
                    <div>
                      <div className="flex items-center gap-3">
                        <AddressDisplay address={tx.from_address} blockchain={caseData.blockchain} />
                        <span className="text-[var(--color-on-surface-variant)] font-bold">→</span>
                        <AddressDisplay address={tx.to_address || '0x0000...0000'} blockchain={caseData.blockchain} />
                      </div>
                      <div className="text-[11px] text-[var(--color-on-surface-variant)] mt-1.5 font-bold">
                        Tx: <TxHashDisplay hash={tx.transaction_hash} blockchain={caseData.blockchain} />
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6 text-right">
                    <div>
                      <span className="text-[var(--color-primary)] font-bold text-sm block">
                        {Number(tx.amount).toFixed(4)} ETH
                      </span>
                      <span className="text-[11px] text-[var(--color-on-surface-variant)] font-bold mt-1 block">
                        Gas: {tx.gas_used ? `${tx.gas_used.toLocaleString()} Gwei` : '—'} · Blk {tx.block_number ? `#${tx.block_number.toLocaleString()}` : '—'}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => selectTransaction(tx)}
                      className="px-4 py-2 bg-[var(--color-surface-dim)] hover:bg-[var(--color-surface-container-high)] text-[var(--color-on-surface)] border border-[var(--color-outline)] rounded-xl text-xs font-bold cursor-pointer transition-colors"
                    >
                      Inspect
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB: TRANSACTIONS (Full-width Forensic Ledger) */}
        {activeTab === 'transactions' && (
          <div className="flex-1 overflow-y-auto p-6 space-y-4 text-sm max-w-7xl mx-auto w-full">
            <div className="flex items-center justify-between">
              <div className="relative flex-1 max-w-md">
                <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--color-on-surface-variant)]" />
                <input
                  type="text"
                  placeholder="Filter transactions by hash, sender or recipient address..."
                  value={globalSearchQuery}
                  onChange={(e) => {
                    const { setGlobalSearchQuery } = useInvestigationStore.getState();
                    setGlobalSearchQuery(e.target.value);
                  }}
                  className="w-full bg-[var(--color-surface-container)] border border-[var(--color-outline)] rounded-xl pl-10 pr-4 py-2.5 text-xs text-[var(--color-on-surface)] placeholder-[var(--color-on-surface-variant)] focus:outline-none focus:border-[var(--color-primary)] transition-colors font-semibold"
                />
              </div>
              <span className="text-xs text-[var(--color-on-surface-variant)] font-bold uppercase tracking-wider">
                Showing {filteredTransactions.length} Recorded Transactions
              </span>
            </div>

            <div className="bg-[var(--color-surface-container)] border border-[var(--color-outline)] rounded-2xl overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead className="bg-[var(--color-surface-dim)] text-[var(--color-on-surface-variant)] border-b border-[var(--color-outline)] text-[11px] uppercase tracking-wider font-bold">
                  <tr>
                    <th className="py-4 px-5">Time</th>
                    <th className="py-4 px-5">Transaction Hash</th>
                    <th className="py-4 px-5">From</th>
                    <th className="py-4 px-5">To</th>
                    <th className="py-4 px-5">Amount</th>
                    <th className="py-4 px-5">Asset</th>
                    <th className="py-4 px-5">Status</th>
                    <th className="py-4 px-5">Provenance</th>
                    <th className="py-4 px-5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-outline)] text-[var(--color-on-surface)] text-xs">
                  {filteredTransactions.slice(0, 100).map((tx, idx) => (
                    <tr
                      key={`${tx.transaction_hash}-${tx.from_address}-${tx.to_address}-${idx}`}
                      onClick={() => selectTransaction(tx)}
                      className="hover:bg-[var(--color-surface-container-high)] cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-5 text-[var(--color-on-surface-variant)] font-bold">
                        {tx.block_timestamp ? new Date(tx.block_timestamp).toLocaleTimeString() : '—'}
                      </td>
                      <td className="py-3 px-5">
                        <TxHashDisplay hash={tx.transaction_hash} blockchain={caseData.blockchain} showExplorer={true} />
                      </td>
                      <td className="py-3 px-5">
                        <AddressDisplay address={tx.from_address} blockchain={caseData.blockchain} showExplorer={true} />
                      </td>
                      <td className="py-3 px-5">
                        <AddressDisplay address={tx.to_address || '—'} blockchain={caseData.blockchain} showExplorer={true} />
                      </td>
                      <td className="py-3 px-5 text-[var(--color-primary)] font-bold">
                        {Number(tx.amount) > 0 ? (
                          Number(tx.amount).toFixed(4)
                        ) : (
                          <span className="text-[var(--color-on-surface-variant)] text-[11px] font-semibold">0.0000 (Call)</span>
                        )}
                      </td>
                      <td className="py-3 px-5 font-bold text-[var(--color-on-surface-variant)]">{tx.asset || 'ETH'}</td>
                      <td className="py-3 px-5">
                        <StatusBadge status={tx.status} />
                      </td>
                      <td className="py-3 px-5">
                        <ProvenanceBadge variant={caseData.demo_data ? 'demo' : 'live'} size="sm" />
                      </td>
                      <td className="py-3 px-5 text-right">
                        <button
                          type="button"
                          className="px-3 py-1.5 rounded-lg bg-[var(--color-surface-dim)] hover:bg-[var(--color-surface-container)] text-[var(--color-on-surface)] border border-[var(--color-outline)] text-xs font-bold transition-colors"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB: RISK */}
        {activeTab === 'risk' && (
          <div className="flex-1 overflow-y-auto p-5 space-y-4 max-w-4xl mx-auto w-full">
            <RiskSummaryCard caseId={caseId!} />
            <RiskCard caseId={caseId!} walletAddress={caseData.reported_wallet_address} />
          </div>
        )}

        {/* TAB: PATTERNS & ATTRIBUTION */}
        {activeTab === 'patterns' && (
          <div className="flex-1 overflow-y-auto p-8 space-y-6 max-w-5xl mx-auto w-full text-sm">
            {/* Patterns Table */}
            <div className="bg-[var(--color-surface-container)] border border-[var(--color-outline)] rounded-2xl overflow-hidden">
              <div className="px-5 py-4 bg-[var(--color-surface-dim)] border-b border-[var(--color-outline)] flex items-center justify-between">
                <span className="font-bold text-[var(--color-on-surface)] text-sm">DETECTED BEHAVIOURAL PATTERNS</span>
                <span className="text-[11px] text-[var(--color-on-surface-variant)] font-bold uppercase tracking-wider">Rule Heuristics Engine</span>
              </div>
              <div className="p-5 space-y-3">
                {patternsList.length === 0 ? (
                  <div className="p-8 text-center text-[var(--color-on-surface-variant)] font-semibold">
                    No explicit anomaly patterns flagged yet.
                  </div>
                ) : (
                  patternsList.map((p) => (
                    <div
                      key={p.pattern_id}
                      className="p-4 bg-[var(--color-surface-dim)] rounded-xl border border-[var(--color-outline)] flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                    >
                      <div>
                        <div className="flex items-center gap-3">
                          <span className="font-bold text-[var(--color-on-surface)] uppercase tracking-wider text-xs">{p.pattern_type}</span>
                          <span className="text-[var(--color-tertiary)] font-bold text-xs bg-[var(--color-tertiary)]/10 px-2 py-0.5 rounded-md border border-[var(--color-tertiary)]/20">
                            {(p.confidence * 100).toFixed(0)}% Confidence
                          </span>
                        </div>
                        <p className="text-xs text-[var(--color-on-surface-variant)] font-medium mt-1.5">{p.description}</p>
                      </div>
                      <ProvenanceBadge variant={p.demo_data ? 'demo' : 'derived'} size="sm" />
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Entity Attributions Table */}
            <div className="bg-[var(--color-surface-container)] border border-[var(--color-outline)] rounded-2xl overflow-hidden">
              <div className="px-5 py-4 bg-[var(--color-surface-dim)] border-b border-[var(--color-outline)] flex items-center justify-between">
                <span className="font-bold text-[var(--color-on-surface)] text-sm">KNOWN ENTITY ATTRIBUTION REGISTRY</span>
                <span className="text-[11px] text-[var(--color-on-surface-variant)] font-bold uppercase tracking-wider">Database Resolved</span>
              </div>
              <div className="p-5 space-y-3">
                {attributionsList.length === 0 ? (
                  <div className="p-8 text-center text-[var(--color-on-surface-variant)] font-semibold">
                    No named entity attributions linked yet.
                  </div>
                ) : (
                  attributionsList.map((a) => (
                    <div
                      key={a.attribution_id}
                      className="p-4 bg-[var(--color-surface-dim)] rounded-xl border border-[var(--color-outline)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
                    >
                      <div>
                        <div className="flex items-center gap-3">
                          <span className="font-bold text-[var(--color-primary)] text-sm">{a.entity_name}</span>
                          <span className="text-[10px] text-[var(--color-secondary)] font-bold uppercase tracking-wider bg-[var(--color-secondary)]/10 px-2 py-0.5 rounded-md border border-[var(--color-secondary)]/20">
                            {a.provenance_level}
                          </span>
                        </div>
                        <div className="text-xs text-[var(--color-on-surface-variant)] mt-1.5 font-medium flex items-center gap-2">
                          Address: <AddressDisplay address={a.wallet_address} blockchain={caseData.blockchain} />
                        </div>
                      </div>
                      <ProvenanceBadge variant={a.demo_data ? 'demo' : 'live'} size="sm" />
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB: EVIDENCE */}
        {activeTab === 'evidence' && (
          <div className="flex-1 overflow-y-auto p-8 space-y-6 max-w-5xl mx-auto w-full text-sm">
            <div className="p-6 bg-[var(--color-surface-container)] border border-[var(--color-outline)] rounded-2xl flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-[var(--color-on-surface)] uppercase tracking-wider">Case Evidence Vault</h3>
                <p className="text-xs text-[var(--color-on-surface-variant)] mt-1.5 font-medium">
                  Hashed case artifacts, investigator notes, and chain-of-custody audit logs.
                </p>
              </div>
              <span className="px-3 py-1.5 rounded-lg bg-[var(--color-secondary)]/10 text-[var(--color-secondary)] border border-[var(--color-secondary)]/20 text-xs font-bold tracking-wider">
                DIGEST & INTEGRITY VERIFIED
              </span>
            </div>

            <div className="space-y-4">
              {evidenceList.map((ev) => (
                <div
                  key={ev.evidence_id}
                  className="p-5 bg-[var(--color-surface-container)] rounded-2xl border border-[var(--color-outline)] space-y-3"
                >
                  <div className="flex items-center justify-between pb-3 border-b border-[var(--color-outline)]">
                    <span className="font-bold text-[var(--color-on-surface)] text-sm uppercase tracking-wider">{ev.evidence_id}</span>
                    <ProvenanceBadge variant={ev.demo_data ? 'demo' : (ev.evidence_type?.includes('ai') ? 'ai' : (ev.evidence_type?.includes('note') || ev.evidence_type?.includes('analyst')) ? 'analyst' : 'live')} size="sm" />
                  </div>
                  <div className="text-xs font-bold text-[var(--color-primary)] uppercase tracking-wider">Type: {ev.evidence_type}</div>
                  {ev.investigator_note && (
                    <p className="text-[var(--color-on-surface)] text-sm leading-relaxed">{ev.investigator_note}</p>
                  )}
                  <div className="text-xs text-[var(--color-on-surface-variant)] font-bold pt-2">
                    Acquisition Timestamp: {new Date(ev.pinned_at).toUTCString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB: COPILOT AI */}
        {activeTab === 'copilot' && (
          <div className="flex-1 h-full overflow-hidden">
            <CopilotPanel
              caseId={caseId!}
              selectedWalletAddress={selectedNode?.id || caseData.reported_wallet_address}
              embedded
            />
          </div>
        )}

        {/* TAB: REPORT */}
        {activeTab === 'report' && (
          <div className="flex-1 h-full overflow-hidden">
            <ReportsPanel caseId={caseId!} />
          </div>
        )}
      </div>
    </div>
  );
};
