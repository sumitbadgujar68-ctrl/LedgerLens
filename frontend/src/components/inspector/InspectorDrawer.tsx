import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInvestigationStore } from '../../store/investigationStore';
import {
  X,
  ExternalLink,
  Hash,
  Wallet,
  ArrowRight,
  Plus,
  Bot,
} from 'lucide-react';
import { CopyButton, HopBadge, RiskBadge, TxHashDisplay } from '../common/Badge';
import { ProvenanceBadge } from '../common/ProvenanceBadge';

function getMetadataValue<T>(metadata: Record<string, unknown> | undefined, key: string, defaultValue: T): T {
  if (!metadata || !(key in metadata)) return defaultValue;
  const value = metadata[key];
  return value as T;
}

function formatAmount(amount: string | number | undefined, asset?: string | null): string {
  if (amount === undefined || amount === null) return '—';
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '—';
  const formatted = num.toFixed(4);
  return `${formatted} ${asset || 'ETH'}`;
}

function formatBlockNumber(block: number | string | null | undefined): string {
  if (block === null || block === undefined) return '—';
  const num = typeof block === 'string' ? parseInt(block, 10) : block;
  if (isNaN(num)) return '—';
  return `#${num.toLocaleString()}`;
}

function formatGas(gas: string | number | null | undefined): string {
  if (gas === null || gas === undefined) return '—';
  const num = typeof gas === 'string' ? parseInt(gas, 10) : gas;
  if (isNaN(num)) return '—';
  return `${num.toLocaleString()} Gwei`;
}

function formatTimestamp(ts: string | null | undefined): string {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return '—';
  }
}

export const InspectorDrawer: React.FC = () => {
  const navigate = useNavigate();
  const {
    isInspectorOpen,
    inspectorMode,
    selectedNode,
    selectedEdge,
    selectedTransaction,
    closeInspector,
    addEvidenceNote,
    currentCase,
  } = useInvestigationStore();

  const [noteContent, setNoteContent] = useState('');
  const [noteTag, setNoteTag] = useState<'lead' | 'custody' | 'subpoena' | 'general'>('lead');
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [isCopilotSummaryOpen, setIsCopilotSummaryOpen] = useState(false);

  if (!isInspectorOpen || !inspectorMode) {
    return null;
  }

  const handleAddNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteContent.trim()) return;

    addEvidenceNote({
      caseId: currentCase?.case_id || 'unassigned',
      author: 'Det. K. Vance · LL-8491',
      content: noteContent,
      tag: noteTag,
    });
    setNoteContent('');
    setShowNoteForm(false);
  };

  const metadata = selectedNode?.metadata || {};

  return (
    <aside className="w-96 bg-[var(--color-surface-dim)] border-l border-[var(--color-outline)] flex flex-col h-full overflow-hidden shadow-2xl shrink-0 z-20 font-[Inter]">
      {/* Header */}
      <div className="h-14 px-4 bg-[var(--color-surface-container)] border-b border-[var(--color-outline)] flex items-center justify-between shrink-0 select-none">
        <div className="flex items-center gap-3">
          {inspectorMode === 'node' && <Wallet className="w-4 h-4 text-[var(--color-primary)]" />}
          {inspectorMode === 'edge' && <ArrowRight className="w-4 h-4 text-[var(--color-primary)]" />}
          {inspectorMode === 'transaction' && <Hash className="w-4 h-4 text-[var(--color-primary)]" />}
          <span className="text-xs font-bold text-[var(--color-on-surface)] uppercase tracking-wider font-[JetBrains_Mono]">
            {inspectorMode === 'node' && 'Entity Inspector'}
            {inspectorMode === 'edge' && 'Transfer Inspector'}
            {inspectorMode === 'transaction' && 'Transaction Inspector'}
          </span>
        </div>
        <button
          onClick={closeInspector}
          className="p-1.5 rounded-lg text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)] transition-colors cursor-pointer"
          title="Close Inspector"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 blueprint-grid blueprint-subgrid">
        {/* Node Mode */}
        {inspectorMode === 'node' && selectedNode && (
          <>
            {/* Identity Card */}
            <div className="p-4 bg-[var(--color-surface-container-low)] rounded-2xl border border-[var(--color-outline)] space-y-3 relative z-10">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-wider font-[JetBrains_Mono]">Target Identifier</span>
                <HopBadge hop={selectedNode.hop} />
              </div>
              <div className="break-all select-all font-bold text-sm text-[var(--color-primary)] font-[JetBrains_Mono]">
                {selectedNode.id}
              </div>
              <div className="pt-3 border-t border-[var(--color-outline)] flex items-center justify-between">
                <CopyButton value={selectedNode.id} />
                <a
                  href={`https://etherscan.io/address/${selectedNode.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1.5 font-[JetBrains_Mono]"
                >
                  <span>Etherscan</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>

            {/* Risk & Classification Bar */}
            <div className="p-4 bg-[var(--color-surface-container-low)] rounded-2xl border border-[var(--color-outline)] space-y-3 relative z-10">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-wider font-[JetBrains_Mono]">Risk Assessment</span>
                <RiskBadge score={getMetadataValue(metadata, 'risk_score', undefined)} />
              </div>
              <div className="pt-2 flex flex-col gap-1">
                <span className="text-[11px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-wider font-[JetBrains_Mono]">Classification</span>
                <span className="text-sm font-bold text-[var(--color-on-surface)] font-[JetBrains_Mono]">
                  {getMetadataValue(metadata, 'entity_type', selectedNode.type || 'Unknown Entity')}
                </span>
              </div>
            </div>

            {/* Forensic Metadata Grid */}
            <div className="space-y-2 relative z-10">
              <div className="text-[11px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-wider px-1 font-[JetBrains_Mono]">Entity Metadata</div>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-[var(--color-surface-container-low)] rounded-xl border border-[var(--color-outline)]">
                  <span className="text-[var(--color-on-surface-variant)] font-semibold text-[10px] uppercase tracking-wider block mb-1 font-[JetBrains_Mono]">Total Outflow</span>
                  <span className="text-[var(--color-on-surface)] font-bold text-sm block font-[JetBrains_Mono]">
                    {metadata.total_outflow ? formatAmount(getMetadataValue(metadata, 'total_outflow', ''), getMetadataValue(metadata, 'asset', null)) : '—'}
                  </span>
                  <span className="text-[var(--color-on-surface-variant)] text-[11px] block mt-1 font-[JetBrains_Mono]">
                    {metadata.total_outflow_usd ? `~$${Number(getMetadataValue(metadata, 'total_outflow_usd', 0)).toLocaleString()} USD` : '—'}
                  </span>
                </div>
                <div className="p-3 bg-[var(--color-surface-container-low)] rounded-xl border border-[var(--color-outline)]">
                  <span className="text-[var(--color-on-surface-variant)] font-semibold text-[10px] uppercase tracking-wider block mb-1 font-[JetBrains_Mono]">Interactions</span>
                  <span className="text-[var(--color-on-surface)] font-bold text-sm block font-[JetBrains_Mono]">
                    {getMetadataValue(metadata, 'transaction_count', '—')} txs
                  </span>
                  <span className="text-[var(--color-primary)] text-[11px] font-semibold block mt-1 font-[JetBrains_Mono]">
                    {metadata.automated_ratio !== undefined ? `${Math.round(Number(getMetadataValue(metadata, 'automated_ratio', 0)) * 100)}% Automated` : '—'}
                  </span>
                </div>
                <div className="p-3 bg-[var(--color-surface-container-low)] rounded-xl border border-[var(--color-outline)]">
                  <span className="text-[var(--color-on-surface-variant)] font-semibold text-[10px] uppercase tracking-wider block mb-1 font-[JetBrains_Mono]">First Seen</span>
                  <span className="text-[var(--color-on-surface)] font-bold text-xs block font-[JetBrains_Mono]">
                    {metadata.first_seen_block ? formatBlockNumber(getMetadataValue(metadata, 'first_seen_block', null)) : '—'}
                  </span>
                  <span className="text-[var(--color-on-surface-variant)] text-[11px] block mt-1 font-[Inter]">
                    {getMetadataValue(metadata, 'first_seen', null) ? formatTimestamp(getMetadataValue(metadata, 'first_seen', null)) : '—'}
                  </span>
                </div>
                <div className="p-3 bg-[var(--color-surface-container-low)] rounded-xl border border-[var(--color-outline)]">
                  <span className="text-[var(--color-on-surface-variant)] font-semibold text-[10px] uppercase tracking-wider block mb-1 font-[JetBrains_Mono]">Last Active</span>
                  <span className="text-[var(--color-on-surface)] font-bold text-xs block font-[JetBrains_Mono]">
                    {metadata.last_seen_block ? formatBlockNumber(getMetadataValue(metadata, 'last_seen_block', null)) : '—'}
                  </span>
                  <span className="text-[var(--color-on-surface-variant)] text-[11px] block mt-1 font-[Inter]">
                    {getMetadataValue(metadata, 'last_seen', null) ? formatTimestamp(getMetadataValue(metadata, 'last_seen', null)) : '—'}
                  </span>
                </div>
              </div>
            </div>

            {/* Provenance Tags */}
            <div className="space-y-2 relative z-10">
              <div className="text-[11px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-wider px-1 font-[JetBrains_Mono]">Labels & Intel</div>
              <div className="flex flex-wrap gap-2">
                <ProvenanceBadge variant={currentCase?.demo_data ? 'demo' : 'live'} size="sm" />
                {getMetadataValue<string[]>(metadata, 'tags', []).includes('mixer') && (
                  <span className="px-2 py-1 rounded bg-[var(--color-error)]/10 text-[var(--color-error)] border border-[var(--color-error)]/30 text-[10px] font-bold tracking-wider font-[JetBrains_Mono]">
                    MIXER DETECTED
                  </span>
                )}
                {getMetadataValue<string[]>(metadata, 'tags', []).includes('cex') && (
                  <span className="px-2 py-1 rounded bg-[var(--color-tertiary)]/10 text-[var(--color-tertiary)] border border-[var(--color-tertiary)]/30 text-[10px] font-bold tracking-wider font-[JetBrains_Mono]">
                    CEX DEPOSIT
                  </span>
                )}
                {getMetadataValue(metadata, 'cluster_id', '') && (
                  <span className="px-2 py-1 rounded bg-[var(--color-surface-container-high)] text-[var(--color-on-surface-variant)] border border-[var(--color-outline)] text-[10px] font-bold tracking-wider font-[JetBrains_Mono]">
                    CLUSTER #{getMetadataValue(metadata, 'cluster_id', '')}
                  </span>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3 pt-4 border-t border-[var(--color-outline)] relative z-10">
              <button
                type="button"
                onClick={() => setShowNoteForm((v) => !v)}
                className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-xl bg-[var(--color-surface-container-low)] hover:bg-[var(--color-surface-container-high)] text-[var(--color-on-surface)] text-xs font-bold transition-colors cursor-pointer border border-[var(--color-outline)]"
              >
                <Plus className="w-4 h-4 text-[var(--color-primary)]" />
                <span>Add to Evidence</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  if (currentCase) {
                    navigate(`/cases/${currentCase.case_id}/copilot`);
                  }
                }}
                className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-xl bg-[var(--color-primary)] hover:brightness-110 text-[var(--color-on-primary)] text-xs font-bold transition-all cursor-pointer shadow-[0_0_15px_rgba(255,107,0,0.3)] hover:shadow-[0_0_20px_rgba(255,107,0,0.5)]"
              >
                <Bot className="w-4 h-4" />
                <span>Ask AI Copilot</span>
              </button>

              {/* Collapsible Evidence Note Form */}
              {showNoteForm && (
                <form
                  onSubmit={(e) => {
                    handleAddNote(e);
                    alert('Evidence saved successfully! Check the Evidence Vault.');
                  }}
                  className="p-4 bg-[var(--color-surface-container-low)] rounded-2xl border border-[var(--color-outline)] space-y-3"
                >
                  <div className="text-xs text-[var(--color-on-surface)] font-bold">New Note</div>
                  <textarea
                    value={noteContent}
                    onChange={(e) => setNoteContent(e.target.value)}
                    placeholder="Enter observation or custody annotation..."
                    rows={3}
                    className="w-full bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-xl p-3 text-xs text-[var(--color-on-surface)] placeholder-[var(--color-on-surface-variant)]/50 focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] resize-none transition-all duration-200"
                  />
                  <div className="flex items-center justify-between">
                    <select
                      value={noteTag}
                      onChange={(e) => setNoteTag(e.target.value as any)}
                      className="bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-lg px-2 py-1.5 text-[11px] font-semibold text-[var(--color-on-surface-variant)] focus:outline-none focus:border-[var(--color-primary)]"
                    >
                      <option value="lead">Lead</option>
                      <option value="custody">Custody</option>
                      <option value="subpoena">Subpoena</option>
                      <option value="general">General</option>
                    </select>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setShowNoteForm(false)}
                        className="px-3 py-1.5 rounded-lg bg-[var(--color-surface-container-low)] hover:bg-[var(--color-surface-container-high)] text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] border border-[var(--color-outline)] text-[11px] font-semibold transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-3 py-1.5 rounded-lg bg-[var(--color-primary)] hover:brightness-110 text-[var(--color-on-primary)] text-[11px] font-bold shadow-sm transition-colors cursor-pointer"
                      >
                        Save
                      </button>
                    </div>
                  </div>
                </form>
              )}
            </div>
          </>
        )}

        {/* Edge / Transaction Mode */}
        {(inspectorMode === 'edge' || inspectorMode === 'transaction') && (
          <div className="space-y-4 relative z-10">
            <div className="p-4 bg-[var(--color-surface-container-low)] rounded-2xl border border-[var(--color-outline)] space-y-3">
              <div className="text-[11px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-wider font-[JetBrains_Mono]">Transaction Hash</div>
              <TxHashDisplay
                hash={
                  selectedTransaction?.transaction_hash ||
                  selectedEdge?.transaction_hash ||
                  ''
                }
                blockchain={currentCase?.blockchain}
              />
            </div>

            <div className="p-4 bg-[var(--color-surface-container-low)] rounded-2xl border border-[var(--color-outline)] space-y-3 text-xs font-medium font-[JetBrains_Mono]">
              <div className="flex justify-between items-center">
                <span className="text-[var(--color-on-surface-variant)]">Value:</span>
                <span className="font-bold text-[var(--color-primary)] text-sm">
                  {formatAmount(
                    selectedTransaction?.amount ?? selectedEdge?.amount,
                    selectedTransaction?.asset ?? selectedEdge?.asset
                  )}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[var(--color-on-surface-variant)]">Token:</span>
                <span className="text-[var(--color-on-surface)]">
                  {selectedTransaction?.asset ?? selectedEdge?.asset ?? 'ETH (Native)'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[var(--color-on-surface-variant)]">Gas:</span>
                <span className="text-[var(--color-on-surface)] font-bold">
                  {formatGas(selectedTransaction?.gas_used ?? selectedTransaction?.total_fee)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[var(--color-on-surface-variant)]">Block:</span>
                <span className="text-[var(--color-on-surface)] font-bold">
                  {formatBlockNumber(selectedTransaction?.block_number)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[var(--color-on-surface-variant)]">Status:</span>
                <span className="text-[var(--color-secondary)] font-bold tracking-wider">
                  {selectedTransaction?.status ?? '—'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[var(--color-on-surface-variant)]">Timestamp:</span>
                <span className="text-[var(--color-on-surface)] font-bold">
                  {formatTimestamp(selectedTransaction?.block_timestamp ?? selectedEdge?.timestamp)}
                </span>
              </div>
            </div>

            <ProvenanceBadge variant="live" size="sm" />
          </div>
        )}
      </div>
    </aside>
  );
};