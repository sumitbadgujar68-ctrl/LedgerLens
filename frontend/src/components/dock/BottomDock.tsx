import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useInvestigationStore } from '../../store/investigationStore';
import { api } from '../../services/api';
import {
  Table,
  FileCheck2,
  ChevronUp,
  ChevronDown,
  Search,
  Crosshair,
} from 'lucide-react';
import { AddressDisplay, StatusBadge, TxHashDisplay } from '../common/Badge';
import { ProvenanceBadge } from '../common/ProvenanceBadge';

export const BottomDock: React.FC = () => {
  const {
    currentCase,
    currentTrace,
    activeBottomTab,
    setActiveBottomTab,
    selectTransaction,
    evidenceNotes,
  } = useInvestigationStore();

  const [isCollapsed, setIsCollapsed] = useState(false);
  const [filterQuery, setFilterQuery] = useState('');

  const transactions = currentTrace?.transactions || [];
  const caseId = currentCase?.case_id || '';

  const { data: caseEvidence } = useQuery({
    queryKey: ['case-evidence', caseId],
    queryFn: () => api.getCaseEvidence(caseId),
    enabled: !!caseId,
  });

  const { data: casePatterns } = useQuery({
    queryKey: ['case-patterns', caseId],
    queryFn: () => api.getCasePatterns(caseId),
    enabled: !!caseId,
  });

  const { data: caseAttributions } = useQuery({
    queryKey: ['case-attributions', caseId],
    queryFn: () => api.getCaseAttributions(caseId),
    enabled: !!caseId,
  });

  const evidenceRows = caseEvidence?.evidence ?? [];
  const patternRows = casePatterns?.patterns ?? [];
  const attributionRows = caseAttributions?.attributions ?? [];
  const findingsCount = patternRows.length + attributionRows.length;
  const evidenceCount = evidenceRows.length + evidenceNotes.length;

  const tabClass = (tab: string) =>
    `flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer border ${
      activeBottomTab === tab && !isCollapsed
        ? 'bg-[var(--color-surface-container)] text-[var(--color-primary)] border border-[var(--color-outline)] shadow-sm'
        : 'text-[var(--color-on-surface-variant)] border-transparent hover:text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)]'
    }`;

  // Filter transactions
  const filteredTxs = transactions.filter((t) => {
    if (!filterQuery) return true;
    const q = filterQuery.toLowerCase();
    return (
      t.transaction_hash.toLowerCase().includes(q) ||
      t.from_address.toLowerCase().includes(q) ||
      (t.to_address || '').toLowerCase().includes(q)
    );
  });

  return (
    <div
      className={`bg-[var(--color-surface-dim)] border-t border-[var(--color-outline)] transition-all duration-200 flex flex-col z-10 shrink-0 font-[Inter] ${
        isCollapsed ? 'h-14' : 'h-72'
      }`}
    >
      {/* Header Dock Bar */}
      <div className="h-14 px-4 bg-[var(--color-surface-dim)] flex items-center justify-between border-b border-[var(--color-outline)] shrink-0 select-none">
        <div className="flex items-center gap-2 font-[JetBrains_Mono]">
          <button
            type="button"
            onClick={() => {
              setActiveBottomTab('ledger');
              setIsCollapsed(false);
            }}
            className={tabClass('ledger')}
          >
            <Table className="w-3.5 h-3.5" />
            <span>TRANSACTIONS ({transactions.length})</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setActiveBottomTab('evidence');
              setIsCollapsed(false);
            }}
            className={tabClass('evidence')}
          >
            <FileCheck2 className="w-3.5 h-3.5" />
            <span>EVIDENCE ({evidenceCount})</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setActiveBottomTab('findings');
              setIsCollapsed(false);
            }}
            className={tabClass('findings')}
          >
            <Crosshair className="w-3.5 h-3.5" />
            <span>FINDINGS ({findingsCount})</span>
          </button>
        </div>

        <div className="flex items-center gap-3">
          {!isCollapsed && activeBottomTab === 'ledger' && (
            <div className="relative hidden sm:block">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-on-surface-variant)]" />
              <input
                type="text"
                placeholder="Filter hash or address..."
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
                className="w-56 bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] rounded-xl pl-9 pr-3 py-1.5 text-xs text-[var(--color-on-surface)] placeholder-[var(--color-on-surface-variant)]/50 focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-all font-[Inter]"
              />
            </div>
          )}

          <button
            type="button"
            onClick={() => setIsCollapsed((v) => !v)}
            className="p-1.5 rounded-lg text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)] border border-transparent transition-colors cursor-pointer"
            title={isCollapsed ? 'Expand Dock' : 'Collapse Dock'}
          >
            {isCollapsed ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Dock Body Content */}
      {!isCollapsed && (
        <div className="flex-1 overflow-auto bg-[var(--color-surface-container-lowest)]">
          {/* TAB 1: TRANSACTIONS LEDGER */}
          {activeBottomTab === 'ledger' && (
            <table className="w-full text-left border-collapse text-xs whitespace-nowrap">
              <thead className="bg-[var(--color-surface-container)] text-[var(--color-on-surface-variant)] border-b border-[var(--color-outline)] text-[11px] sticky top-0 uppercase tracking-wider font-bold font-[Inter]">
                <tr>
                  <th className="py-3 px-4">Time</th>
                  <th className="py-3 px-4">Tx Hash</th>
                  <th className="py-3 px-4">From</th>
                  <th className="py-3 px-4">To</th>
                  <th className="py-3 px-4">Value</th>
                  <th className="py-3 px-4">Asset</th>
                  <th className="py-3 px-4">Gas</th>
                  <th className="py-3 px-4">Block</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Provenance</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-outline)] text-[var(--color-on-surface)] font-medium font-[JetBrains_Mono]">
                {filteredTxs.length === 0 ? (
                  <tr>
                    <td colSpan={11} className="py-10 text-center text-[var(--color-on-surface-variant)] text-sm font-[Inter]">
                      No on-chain transactions recorded for this trace. Run a multi-hop trace to inspect fund movements.
                    </td>
                  </tr>
                ) : (
                  filteredTxs.slice(0, 100).map((tx, idx) => (
                    <tr
                      key={`${tx.transaction_hash}-${tx.from_address}-${tx.to_address}-${idx}`}
                      onClick={() => selectTransaction(tx)}
                      className="hover:bg-[var(--color-surface-container-high)] cursor-pointer transition-colors"
                    >
                      <td className="py-2.5 px-4 text-[var(--color-on-surface-variant)] text-[11px] font-bold">
                        {tx.block_timestamp ? new Date(tx.block_timestamp).toLocaleTimeString() : '—'}
                      </td>
                      <td className="py-2.5 px-4">
                        <TxHashDisplay hash={tx.transaction_hash} blockchain={currentCase?.blockchain} />
                      </td>
                      <td className="py-2.5 px-4">
                        <AddressDisplay address={tx.from_address} blockchain={currentCase?.blockchain} />
                      </td>
                      <td className="py-2.5 px-4">
                        <AddressDisplay address={tx.to_address || '—'} blockchain={currentCase?.blockchain} />
                      </td>
                      <td className="py-2.5 px-4 text-[var(--color-primary)] font-bold text-[13px]">
                        {Number(tx.amount).toFixed(4)}
                      </td>
                      <td className="py-2.5 px-4 text-[var(--color-on-surface)] font-bold">{tx.asset || 'ETH'}</td>
                      <td className="py-2.5 px-4 text-[var(--color-on-surface-variant)] font-bold">{tx.gas_used ? tx.gas_used.toLocaleString() : '—'}</td>
                      <td className="py-2.5 px-4 text-[var(--color-on-surface-variant)] font-bold">{tx.block_number ? `#${tx.block_number.toLocaleString()}` : '—'}</td>
                      <td className="py-2.5 px-4">
                        <StatusBadge status={tx.status} />
                      </td>
                      <td className="py-2.5 px-4">
                        <ProvenanceBadge variant={currentCase?.demo_data ? 'demo' : 'live'} size="sm" />
                      </td>
                      <td className="py-2.5 px-4 text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            selectTransaction(tx);
                          }}
                          className="px-3 py-1 rounded-lg bg-[var(--color-surface-container)] hover:bg-[var(--color-surface-container-highest)] text-[var(--color-primary)] border border-[var(--color-outline)] text-[11px] font-bold uppercase tracking-wider transition-colors font-[Inter]"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}

          {/* TAB 2: EVIDENCE VAULT */}
          {activeBottomTab === 'evidence' && (
            <div className="p-4 space-y-3 font-[Inter]">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {evidenceNotes.map((note) => (
                  <div
                    key={note.id}
                    className="p-3.5 bg-[var(--color-surface-container-low)] rounded-xl border border-[var(--color-outline)] space-y-2 relative overflow-hidden"
                  >
                    <div className="absolute top-0 left-0 w-1 h-full bg-[var(--color-primary)]/50" />
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[var(--color-on-surface)]">{note.author}</span>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-[var(--color-secondary)]/10 text-[var(--color-secondary)] border border-[var(--color-secondary)]/30 text-[10px] font-bold uppercase tracking-wider">
                          {note.tag}
                        </span>
                        <ProvenanceBadge
                          variant={note.content.includes('[DEMO DATA]') || currentCase?.demo_data ? 'demo' : 'analyst'}
                          size="sm"
                        />
                      </div>
                    </div>
                    <p className="text-sm font-medium text-[var(--color-on-surface-variant)] leading-relaxed">{note.content}</p>
                    <div className="pt-2 border-t border-[var(--color-outline)] flex items-center justify-between text-[10px] text-[var(--color-on-surface-variant)] font-semibold">
                      <span>{new Date(note.timestamp).toLocaleString()}</span>
                      <span className="text-[var(--color-primary)] uppercase tracking-wider">Sealed & Timestamped</span>
                    </div>
                  </div>
                ))}
                {evidenceRows.map((ev) => (
                  <div
                    key={ev.evidence_id}
                    className="p-3.5 bg-[var(--color-surface-container-low)] rounded-xl border border-[var(--color-outline)] space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[var(--color-primary)]">{ev.evidence_id}</span>
                      <ProvenanceBadge variant={ev.demo_data ? 'demo' : (ev.evidence_type?.includes('ai') ? 'ai' : (ev.evidence_type?.includes('note') || ev.evidence_type?.includes('analyst')) ? 'analyst' : 'live')} size="sm" />
                    </div>
                    <div className="text-xs text-[var(--color-on-surface)] font-medium">
                      Type: <span className="text-[var(--color-secondary)] ml-1">{ev.evidence_type}</span>
                    </div>
                    {ev.investigator_note && (
                      <p className="text-[11px] font-medium text-[var(--color-on-surface-variant)]">{ev.investigator_note}</p>
                    )}
                    <div className="text-[10px] text-[var(--color-on-surface-variant)] font-semibold">
                      Acquired: {new Date(ev.pinned_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: FINDINGS (PATTERNS & ATTRIBUTION) */}
          {activeBottomTab === 'findings' && (
            <div className="p-4 space-y-4 font-[Inter]">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Patterns */}
                <div className="space-y-2">
                  <div className="text-[11px] font-bold text-[var(--color-on-surface-variant)] uppercase tracking-wider">
                    BEHAVIOURAL PATTERNS ({patternRows.length})
                  </div>
                  {patternRows.length === 0 ? (
                    <div className="p-4 rounded-xl bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] text-[var(--color-on-surface-variant)] text-sm font-medium">
                      No pattern findings recorded.
                    </div>
                  ) : (
                    patternRows.map((p) => (
                      <div
                        key={p.pattern_id}
                        className="p-3 bg-[var(--color-surface-container-low)] rounded-xl border border-[var(--color-outline)] space-y-1.5 hover:border-[var(--color-primary)]/50 transition-colors"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-bold text-[var(--color-on-surface)] uppercase tracking-wider">
                            {(p.demo_label || p.pattern_type).replace(/_/g, ' ')}
                          </span>
                          <span className="text-[var(--color-error)] font-bold">
                            {(p.confidence * 100).toFixed(0)}% Confidence
                          </span>
                        </div>
                        <p className="text-xs text-[var(--color-on-surface-variant)] font-medium">{p.description}</p>
                        <ProvenanceBadge variant={p.demo_data ? 'demo' : (p.finding_source?.includes('live') ? 'live' : 'derived')} size="sm" />
                      </div>
                    ))
                  )}
                </div>

                {/* Attributions */}
                <div className="space-y-2">
                  <div className="text-[11px] font-bold text-[var(--color-on-surface-variant)] uppercase tracking-wider">
                    KNOWN ENTITY ATTRIBUTIONS ({attributionRows.length})
                  </div>
                  {attributionRows.length === 0 ? (
                    <div className="p-4 rounded-xl bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] text-[var(--color-on-surface-variant)] text-sm font-medium">
                      No attributions recorded yet.
                    </div>
                  ) : (
                    attributionRows.map((a) => (
                      <div
                        key={a.attribution_id}
                        className="p-3 bg-[var(--color-surface-container-low)] rounded-xl border border-[var(--color-outline)] space-y-1.5 hover:border-[var(--color-tertiary)]/50 transition-colors"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-bold text-[var(--color-primary)]">{a.entity_name}</span>
                          <span className="text-[10px] text-[var(--color-secondary)] font-bold uppercase tracking-wider">
                            {a.provenance_level}
                          </span>
                        </div>
                        <div className="text-xs text-[var(--color-on-surface-variant)] font-medium font-[JetBrains_Mono]">
                          Address: <AddressDisplay address={a.wallet_address} />
                        </div>
                        {a.disclaimer && (
                          <p className="text-[11px] text-[var(--color-tertiary)] font-medium italic">{a.disclaimer}</p>
                        )}
                        <ProvenanceBadge variant={a.demo_data ? 'demo' : 'live'} size="sm" />
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
